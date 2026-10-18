/**
 * SubprocessBridge -- JSON-RPC over stdin/stdout to a sidecar process.
 *
 * Use this when your TypeScript MCP server needs to call into Python (or any
 * other language) without standing up an HTTP service. We spawn a child
 * process, write newline-delimited JSON-RPC requests on stdin, and parse
 * responses from stdout.
 *
 * Pairs with `scripts/bridge.py`. The Python side reads one JSON request per
 * line and writes one JSON response per line. `flush()` is critical there or
 * we'll hang waiting for buffered output.
 *
 * Features:
 *   - Per-call timeout with cleanup
 *   - Crash recovery: if the child exits, all pending calls reject
 *   - Backpressure: writes are awaited
 *   - stderr is forwarded so Python tracebacks are visible
 */

import { spawn, type ChildProcessWithoutNullStreams } from "node:child_process";

export interface BridgeOptions {
  command: string;          // e.g. "python3"
  args: string[];           // e.g. ["scripts/bridge.py"]
  cwd?: string;
  timeoutMs?: number;       // default 30s
  env?: NodeJS.ProcessEnv;
  onStderr?: (chunk: string) => void;
}

interface PendingCall {
  resolve: (value: unknown) => void;
  reject: (err: Error) => void;
  timer: NodeJS.Timeout;
  method: string;
}

export class BridgeError extends Error {
  constructor(message: string, public readonly method?: string) {
    super(message);
    this.name = "BridgeError";
  }
}

export class SubprocessBridge {
  private proc: ChildProcessWithoutNullStreams;
  private pending = new Map<number, PendingCall>();
  private nextId = 1;
  private buffer = "";
  private dead = false;
  private exitReason: string | null = null;
  private timeoutMs: number;

  constructor(private opts: BridgeOptions) {
    this.timeoutMs = opts.timeoutMs ?? 30_000;
    this.proc = spawn(opts.command, opts.args, {
      cwd: opts.cwd,
      env: opts.env ?? process.env,
      stdio: ["pipe", "pipe", "pipe"],
    });

    this.proc.stdout.setEncoding("utf8");
    this.proc.stderr.setEncoding("utf8");

    this.proc.stdout.on("data", (chunk: string) => this.onStdout(chunk));
    this.proc.stderr.on("data", (chunk: string) => {
      if (opts.onStderr) opts.onStderr(chunk);
      else process.stderr.write(`[bridge:stderr] ${chunk}`);
    });

    this.proc.on("exit", (code, signal) => {
      this.dead = true;
      this.exitReason = `exited code=${code} signal=${signal}`;
      this.failAllPending(new BridgeError(this.exitReason));
    });

    this.proc.on("error", (err) => {
      this.dead = true;
      this.exitReason = `spawn error: ${err.message}`;
      this.failAllPending(new BridgeError(this.exitReason));
    });
  }

  /** Send a JSON-RPC call and await the response. */
  call<T = unknown>(method: string, params: unknown = {}): Promise<T> {
    if (this.dead) {
      return Promise.reject(new BridgeError(`bridge dead: ${this.exitReason}`, method));
    }
    const id = this.nextId++;
    const payload = JSON.stringify({ id, method, params }) + "\n";

    return new Promise<T>((resolve, reject) => {
      const timer = setTimeout(() => {
        if (this.pending.has(id)) {
          this.pending.delete(id);
          reject(new BridgeError(`timeout after ${this.timeoutMs}ms calling ${method}`, method));
        }
      }, this.timeoutMs);

      this.pending.set(id, {
        resolve: resolve as (v: unknown) => void,
        reject,
        timer,
        method,
      });

      const ok = this.proc.stdin.write(payload, (err) => {
        if (err) {
          clearTimeout(timer);
          this.pending.delete(id);
          reject(new BridgeError(`stdin write failed: ${err.message}`, method));
        }
      });
      // Apply backpressure if the kernel buffer is full.
      if (!ok) {
        this.proc.stdin.once("drain", () => {});
      }
    });
  }

  isAlive(): boolean {
    return !this.dead;
  }

  /** Stop the bridge cleanly. Pending calls reject. */
  destroy(signal: NodeJS.Signals = "SIGTERM"): void {
    if (this.dead) return;
    try {
      this.proc.stdin.end();
    } catch {}
    try {
      this.proc.kill(signal);
    } catch {}
    this.dead = true;
    this.failAllPending(new BridgeError("bridge destroyed"));
  }

  private onStdout(chunk: string) {
    this.buffer += chunk;
    let nl: number;
    // eslint-disable-next-line no-cond-assign
    while ((nl = this.buffer.indexOf("\n")) !== -1) {
      const line = this.buffer.slice(0, nl).trim();
      this.buffer = this.buffer.slice(nl + 1);
      if (!line) continue;

      let response: any;
      try {
        response = JSON.parse(line);
      } catch {
        // Non-JSON line (e.g. a stray print). Forward it to stderr for debug.
        process.stderr.write(`[bridge:stdout-noise] ${line}\n`);
        continue;
      }

      const id = response?.id as number | undefined;
      if (id == null) continue;
      const p = this.pending.get(id);
      if (!p) continue;
      this.pending.delete(id);
      clearTimeout(p.timer);

      if (response.error) {
        p.reject(new BridgeError(String(response.error), p.method));
      } else {
        p.resolve(response.result);
      }
    }
  }

  private failAllPending(err: BridgeError) {
    for (const [id, p] of this.pending) {
      clearTimeout(p.timer);
      p.reject(err);
      this.pending.delete(id);
    }
  }
}

export function createBridge(opts: BridgeOptions): SubprocessBridge {
  return new SubprocessBridge(opts);
}
