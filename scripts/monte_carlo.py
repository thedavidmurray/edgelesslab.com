#!/usr/bin/env python3
"""
Monte Carlo Builder - Python twin for the trading desk.
Input trade returns, equity curves, or parametric distributions.
Run trade-order shuffle, block bootstrap, parametric sims.
Get full output battery: fan charts, drawdowns, ruin probability, Sharpe CI, verdict.
Simulation. Not trading advice.
"""
# Updated for Monte Carlo Builder field note - edgeless-cc
import sys
import json
import argparse
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import pandas as pd


def mulberry32(a):
    """Deterministic RNG from JS port"""
    def _rng():
        nonlocal a
        a = (a + 0x6D2B79F5) & 0xFFFFFFFF
        t = (a ^ (a >> 15)) & 0xFFFFFFFF
        t = (t * 0x100000001) & 0xFFFFFFFF
        t = (t ^ (t >> 7)) & 0xFFFFFFFF
        t = (t * 0x3D20EFAD) & 0xFFFFFFFF
        t = (t ^ (t >> 14)) & 0xFFFFFFFF
        return t / 0x100000000
    return _rng


def gauss(rng):
    """Box-Muller transform for standard normal"""
    u = 0
    while u == 0:
        u = rng()
    return np.sqrt(-2 * np.log(u)) * np.cos(2 * np.pi * rng())


def phi(x):
    """CDF of standard normal (Abramowitz & Stegun 26.2.17)"""
    t = 1 / (1 + 0.2316419 * abs(x))
    d = 0.3989422804 * np.exp(-x * x / 2)
    p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))))
    return 1 - p if x > 0 else p


def phi_inv(p):
    """Inverse CDF of standard normal (Abramowitz & Stegun 26.2.23)"""
    a = [-39.6968302866538, 220.946098424521, -275.928510446969, 138.357751867269, -30.6647980661472, 2.50662827745924]
    b = [-54.4760987982241, 161.585836858041, -155.698979859887, 66.8013118877197, -13.2806815528857]
    c = [-0.00778489400243029, -0.322396458041136, -2.40075827716184, -2.54973253934373, 4.37466414146497, 2.93816398269878]
    d = [0.00778469570904146, 0.32246712907004, 2.445134137143, 3.75440866190742]
    
    if p < 0.02425:
        q = np.sqrt(-2 * np.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > 1 - 0.02425:
        q = np.sqrt(-2 * np.log(1 - p))
        return -((((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1))
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def sample_normal(rng, n, mean, std):
    arr = np.zeros(n)
    for i in range(n):
        arr[i] = mean + std * gauss(rng)
    return arr


def sample_t(rng, n, nu, mean, std):
    # Student-t via normal / sqrt(chi2/nu) — all using seeded rng
    arr = np.zeros(n)
    for i in range(n):
        z = gauss(rng)
        # Chi-squared via sum of squared normals, using seeded rng
        chi2 = np.sum([gauss(rng)**2 for _ in range(int(nu))])
        arr[i] = mean + std * z * np.sqrt(nu / chi2)
    return arr


def sample_bootstrap(rng, data):
    n = len(data)
    arr = np.zeros(n)
    for i in range(n):
        arr[i] = data[int(rng() * n)]
    return arr


def run_shuffle_trades(returns, n_sims, seed):
    n = len(returns)
    rng = mulberry32(seed)
    all_paths = np.zeros((n_sims, n + 1))
    all_paths[:, 0] = 1.0
    
    for sim in range(n_sims):
        shuffled = returns.copy()
        # Fisher-Yates shuffle
        for i in range(n - 1, 0, -1):
            j = int(rng() * (i + 1))
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
        
        cum = 1.0
        for i in range(n):
            # Apply transaction cost + slippage (bps per $1M, proportional to position size)
            total_cost = cost_bps / 10000 + slippage_bps / 10000 * cum
            cum *= (1 + shuffled[i] - total_cost)
            all_paths[sim, i + 1] = cum
    
    return all_paths


def run_block_bootstrap(returns, n_sims, seed, block_size=10):
    n = len(returns)
    rng = mulberry32(seed)
    all_paths = np.zeros((n_sims, n + 1))
    all_paths[:, 0] = 1.0
    
    for sim in range(n_sims):
        cum = 1.0
        i = 0
        while i < n:
            start = int(rng() * (n - block_size))
            for j in range(min(block_size, n - i)):
                cum *= (1 + returns[start + j] - (cost_bps / 10000 + slippage_bps / 10000 * cum))
                all_paths[sim, i + j + 1] = cum
            i += block_size
    
    return all_paths


def run_resample(returns, n_sims, seed):
    n = len(returns)
    rng = mulberry32(seed)
    all_paths = np.zeros((n_sims, n + 1))
    all_paths[:, 0] = 1.0
    
    for sim in range(n_sims):
        cum = 1.0
        for i in range(n):
            idx = int(rng() * n)
            cum *= (1 + returns[idx] - (cost_bps / 10000 + slippage_bps / 10000 * cum))
            all_paths[sim, i + 1] = cum
    
    return all_paths


def run_parametric(n_sims, seed, n_obs, dist_type, nu, mean, std):
    rng = mulberry32(seed)
    all_paths = np.zeros((n_sims, n_obs + 1))
    all_paths[:, 0] = 1.0
    
    for sim in range(n_sims):
        # Generate all returns for this simulation
        if dist_type == 'normal':
            ret = sample_normal(rng, n_obs, mean, std)
        elif dist_type == 't':
            ret = sample_t(rng, n_obs, nu, mean, std)
        elif dist_type == 'bootstrap':
            ret = sample_bootstrap(rng, returns)  # assumes returns is already populated
        else:
            ret = sample_normal(rng, n_obs, mean, std)
        
        cum = 1.0
        for i in range(n_obs):
            total_cost = cost_bps / 10000 + slippage_bps / 10000 * cum
            cum *= (1 + ret[i] - total_cost)
            all_paths[sim, i + 1] = cum
    
    return all_paths


def run_random_entry(returns, n_sims, seed):
    n = len(returns)
    rng = mulberry32(seed)
    all_paths = np.zeros((n_sims, n + 1))
    all_paths[:, 0] = 1.0
    
    for sim in range(n_sims):
        cum = 1.0
        for i in range(n):
            side = 1 if rng() < 0.5 else -1
            ret = side * abs(returns[i])
            cum *= (1 + ret - (cost_bps / 10000 + slippage_bps / 10000 * cum))
            all_paths[sim, i + 1] = cum
    
    return all_paths


def compute_stats(paths, n_obs):
    n_sims = paths.shape[0]
    terminal = paths[:, -1]
    
    # Max drawdown
    max_dd = np.zeros(n_sims)
    for s in range(n_sims):
        peak = 1.0
        max_dd_s = 0.0
        for t in range(n_obs + 1):
            if paths[s, t] > peak:
                peak = paths[s, t]
            dd = (peak - paths[s, t]) / peak
            if dd > max_dd_s:
                max_dd_s = dd
        max_dd[s] = max_dd_s
    
    # Sharpe ratios
    sharpe = np.zeros(n_sims)
    for s in range(n_sims):
        daily = (paths[s, 1:] / paths[s, :-1]) - 1
        if len(daily) > 1:
            mean = np.mean(daily)
            var = np.var(daily, ddof=1)
            sd = np.sqrt(var) if var > 0 else 0
            sharpe[s] = mean / sd * np.sqrt(252) if sd > 0 else 0
    
    # Percentiles
    def pct(arr, p):
        return np.percentile(arr, p * 100)
    
    return {
        'terminal': {
            'mean': np.mean(terminal),
            'p1': pct(terminal, 0.01),
            'p5': pct(terminal, 0.05),
            'p50': pct(terminal, 0.5),
            'p95': pct(terminal, 0.95),
            'p99': pct(terminal, 0.99)
        },
        'maxDD': {
            'mean': np.mean(max_dd),
            'p1': pct(max_dd, 0.01),
            'p5': pct(max_dd, 0.05),
            'p50': pct(max_dd, 0.5),
            'p95': pct(max_dd, 0.95),
            'p99': pct(max_dd, 0.99)
        },
        'ruin': np.sum(terminal < 1) / n_sims,
        'sharpe': {
            'mean': np.mean(sharpe),
            'p5': pct(sharpe, 0.05),
            'p95': pct(sharpe, 0.95)
        }
    }


def load_csv(filepath: str) -> List[float]:
    """Load CSV of returns (one per line or comma-separated)"""
    with open(filepath, 'r') as f:
        text = f.read().strip()
    returns = []
    for token in text.replace('\n', ',').split(','):
        token = token.strip()
        if token:
            returns.append(float(token))
    return returns


def load_equity(filepath: str) -> Tuple[List[float], List[float]]:
    """Load equity curve, convert to returns"""
    with open(filepath, 'r') as f:
        text = f.read().strip()
    equity = []
    for token in text.replace('\n', ',').split(','):
        token = token.strip()
        if token:
            equity.append(float(token))
    returns = [equity[i] / equity[i-1] - 1 for i in range(1, len(equity))]
    return returns, equity


def main():
    parser = argparse.ArgumentParser(description='Monte Carlo Builder - Python twin')
    parser.add_argument('--source', choices=['csv', 'equity', 'param'], default='csv',
                       help='Data source type')
    parser.add_argument('--file', type=str, help='Input file (CSV or equity curve)')
    parser.add_argument('--mean', type=float, default=0.0005, help='Mean return for parametric')
    parser.add_argument('--std', type=float, default=0.01, help='Std dev for parametric')
    parser.add_argument('--dist', choices=['normal', 't', 'bootstrap'], default='normal',
                       help='Distribution for parametric')
    parser.add_argument('--nu', type=float, default=5, help='Degrees of freedom for t')
    parser.add_argument('--nobs', type=int, default=252, help='Number of observations for parametric')
    parser.add_argument('--n-sims', type=int, default=1000, help='Number of simulations')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--cost', type=float, default=5, help='Transaction cost per trade (bps)')
    parser.add_argument('--slippage', type=float, default=10, help='Slippage (bps per $1M)')
    parser.add_argument('--random-entry', action='store_true', help='Run random-entry test')
    parser.add_argument('--output', type=str, default='monte_carlo_results.json', help='Output JSON file')
    
    args = parser.parse_args()
    
    global cost_bps, slippage_bps, random_entry, returns, equity, n_sims, seed, dist_type, nu, mean, std, n_obs
    cost_bps = args.cost
    slippage_bps = args.slippage
    random_entry = args.random_entry
    n_sims = args.n_sims
    seed = args.seed
    dist_type = args.dist
    nu = args.nu
    mean = args.mean
    std = args.std
    n_obs = args.nobs
    
    # Load data
    if args.source == 'csv' and args.file:
        returns = load_csv(args.file)
        equity = []
        for r in returns:
            equity.append(equity[-1] * (1 + r) if equity else 1.0)
    elif args.source == 'equity' and args.file:
        returns, equity = load_equity(args.file)
    else:
        # Parametric - no file needed
        returns = []
        equity = []
    
    if len(returns) == 0 and args.source in ['csv', 'equity']:
        print("Error: No returns data loaded")
        sys.exit(1)
    
    print(f"Monte Carlo Builder - Python Twin")
    print(f"Source: {args.source}, N={len(returns) if returns else n_obs}, Sims={n_sims}, Seed={seed}")
    print(f"Cost: {cost_bps}bps, Slippage: {slippage_bps}bps, Random entry: {random_entry}")
    print()
    
    # Run simulations
    runs = []
    
    if args.source in ['csv', 'equity'] and returns:
        # 1. Shuffle
        paths = run_shuffle_trades(returns, n_sims, seed)
        stats = compute_stats(paths, len(returns))
        runs.append({'name': 'Trade-order shuffle', 'stats': stats})
        
        # 2. Block bootstrap
        paths = run_block_bootstrap(returns, n_sims, seed)
        stats = compute_stats(paths, len(returns))
        runs.append({'name': 'Block bootstrap', 'stats': stats})
        
        # 3. Resample
        paths = run_resample(returns, n_sims, seed)
        stats = compute_stats(paths, len(returns))
        runs.append({'name': 'Resampling with replacement', 'stats': stats})
        
        # 4. Parametric
        paths = run_parametric(n_sims, seed, len(returns), 'normal', 5, mean, std)
        stats = compute_stats(paths, len(returns))
        runs.append({'name': 'Parametric sim', 'stats': stats})
        
        # 5. Random entry (optional)
        if random_entry:
            paths = run_random_entry(returns, n_sims, seed)
            stats = compute_stats(paths, len(returns))
            runs.append({'name': 'Random-entry permutation', 'stats': stats})
    else:
        # Parametric source only
        paths = run_parametric(n_sims, seed, n_obs, dist_type, nu, mean, std)
        stats = compute_stats(paths, n_obs)
        runs.append({'name': 'Parametric sim', 'stats': stats})
    
    # Output JSON
    result = {
        'timestamp': pd.Timestamp.now().isoformat(),
        'source': args.source,
        'n_sims': n_sims,
        'seed': seed,
        'cost_bps': cost_bps,
        'slippage_bps': slippage_bps,
        'random_entry': random_entry,
        'runs': [
            {
                'name': r['name'],
                'n': len(returns) if returns else n_obs,
                'stats': r['stats']
            }
            for r in runs
        ]
    }
    
    with open(args.output, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Results saved to {args.output}")
    print()
    
    # Print verdict
    for r in runs:
        stats = r['stats']
        print(f"{r['name']}:")
        print(f"  Terminal wealth: {stats['terminal']['p50']:.2f} ({stats['terminal']['p5']:.2f}-{stats['terminal']['p95']:.2f})")
        print(f"  Max drawdown: {stats['maxDD']['p50']*100:.1f}% ({stats['maxDD']['p5']*100:.1f}%-{stats['maxDD']['p95']*100:.1f}%)")
        print(f"  Probability of ruin: {stats['ruin']*100:.1f}%")
        print(f"  Sharpe mean: {stats['sharpe']['mean']:.2f} ({stats['sharpe']['p5']:.2f}-{stats['sharpe']['p95']:.2f})")
        if stats['ruin'] > 0.5:
            print(f"  ⚠️  High ruin probability - NO EDGE")
        elif stats['sharpe']['mean'] > 1 and stats['ruin'] < 0.1:
            print(f"  ✅  Sharpe > 1, low ruin - Possible edge")
        else:
            print(f"  ❓  Inconclusive - No edge declared")
        print()


if __name__ == '__main__':
    main()
