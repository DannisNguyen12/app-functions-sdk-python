AITest
======

Purpose
-------
A small local workspace for prototyping AI models that operate on EdgeX data stored in Redis. This folder contains scripts to:

- extract sample events from Redis
- do lightweight preprocessing and feature extraction
- run a quick IsolationForest baseline
- persist trained models and artifacts
- integrate a small inference snippet into `sample/app.py`

Structure
---------
- `extract/` - Redis extractor and sampling scripts
- `preprocess/` - feature engineering helpers
- `models/` - trained model artifacts and metadata
- `notebooks/` - exploratory notebooks (optional)
- `scripts/` - quick runner scripts (train, evaluate, infer)
- `requirements.txt` - minimal Python deps for experiments

Quick start
-----------
1. Activate your project venv (from repo root):

```bash
source venv/bin/activate
cd app-functions-sdk-python
```

2. Run the extractor to sample data from Redis:

```bash
python AITest/extract/extract_sample.py --out AITest/data/redis_sample.jsonl --count 1000
```

3. Run the baseline trainer:

```bash
python train_isolation_forest.py --input /Users/dannynguyen/Downloads/TestEdgeX/app-functions-sdk-python/AITest/data/redis_sample.jsonl --out /Users/dannynguyen/Downloads/TestEdgeX/app-functions-sdk-python/AITest/models/if_model.joblib
```

4. Run the inference script against live data (prints scores):

```bash
python run_inference.py --model ../models/if_model.joblib
```

Notes
-----
- The extractor uses `redis` and `json`. If Redis is remote, pass host/port via environment variables or CLI args.
- This workspace is intentionally small and dependency-light to keep iteration fast.
