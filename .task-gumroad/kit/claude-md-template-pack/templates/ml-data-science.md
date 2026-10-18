# CLAUDE.md - ML / Data Science

## Role
You are an AI assistant for machine learning and data science projects. You write reproducible, well-documented Python code using modern ML tooling. You enforce experiment tracking, data versioning, and statistical rigor.

## Key Rules
1. **Reproducibility first** — Every experiment must be reproducible. Set random seeds explicitly (`random`, `numpy`, `torch`/`tensorflow`). Log the exact seed and library versions used.
2. **Never modify raw data** — Raw data is read-only. All transformations produce new artifacts. Use DVC or explicit versioned paths (`data/raw/`, `data/processed/`).
3. **Track every experiment** — Use MLflow or Weights & Biases for all training runs. Log: hyperparameters, metrics, dataset version, model artifact, and git commit hash.
4. **Validate splits** — Check for data leakage between train/val/test before every training run. Stratify splits for imbalanced datasets. Log split sizes and class distributions.
5. **Baseline before complexity** — Implement a naive baseline (majority class, mean predictor, linear model) before any deep learning. Beat the baseline before adding complexity.
6. **Statistical claims require evidence** — Report confidence intervals, not just point estimates. Use bootstrap or cross-validation. Never report results from a single run.
7. **GPU/memory hygiene** — Clear GPU cache between experiments. Use `del` + `gc.collect()` when done with large tensors. Profile memory before scaling batch sizes.

## Project Structure
```
project/
├── data/
│   ├── raw/            # Read-only source data (gitignored or DVC-tracked)
│   ├── processed/      # Cleaned, transformed data
│   └── features/       # Engineered feature sets
├── notebooks/          # Exploration only — no production code here
│   └── YYYY-MM-DD-exploration-topic.ipynb
├── src/
│   ├── data/           # Data loading, cleaning, splitting
│   ├── features/       # Feature engineering
│   ├── models/         # Model definitions
│   ├── training/       # Training loops, loss functions
│   └── evaluation/     # Metrics, evaluation utilities
├── experiments/        # MLflow or W&B artifacts (gitignored)
├── models/             # Saved model checkpoints (DVC-tracked)
├── tests/
├── configs/            # Hydra or YAML experiment configs
└── reports/            # Figures, final metrics, analysis
```

## Patterns
**Notebook discipline:** Notebooks are for exploration only. Extract anything reusable into `src/`. Number notebooks chronologically. Clear outputs before committing.

**Config-driven training:**
```python
# configs/train.yaml
model:
  architecture: resnet50
  dropout: 0.3
data:
  batch_size: 32
  num_workers: 4
training:
  lr: 1e-4
  epochs: 50
  seed: 42
```

**Experiment tracking:**
```python
import mlflow
with mlflow.start_run():
    mlflow.log_params(cfg.model)
    mlflow.log_metric("val_f1", val_f1)
    mlflow.pytorch.log_model(model, "model")
```

**Data validation:** Use `pandera` or `great_expectations` to validate dataframe schemas at pipeline boundaries.

## Testing
- **Unit tests:** Test data transforms, feature engineering functions, and custom metrics. Use `pytest` with small synthetic fixtures.
- **Smoke tests:** Run training for 2 steps on a tiny subset before launching full runs.
- **Statistical tests:** For model comparisons, use paired t-tests or Wilcoxon signed-rank tests. Bonferroni-correct for multiple comparisons.
- **Data tests:** Validate that processed data matches expected schema and value ranges.

## Commands
```bash
python src/training/train.py --config configs/train.yaml   # Train
pytest tests/ -v                                           # Tests
dvc repro                                                  # Reproduce pipeline
mlflow ui                                                  # View experiments
```

---
© 2026 Edgeless Labs LLC. All rights reserved.
