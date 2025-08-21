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
python AITest/scripts/run_inference.py --model AITest/models/if_model.joblib
```

5. Run the forwarder (`sample/app.py`) with optional model inference:

```bash
python sample/app.py
```

If a model exists at `AITest/models/if_model.joblib` the forwarder will auto-load it at startup and print a model score and a human label (`normal` / `abnormal`) for each event. If the model or feature helpers are missing the forwarder will continue printing events but skip inference.

Notes
-----
- The extractor uses `redis` and `json`. If Redis is remote, pass host/port via environment variables or CLI args.
- This workspace is intentionally small and dependency-light to keep iteration fast.

Inference notes
---------------
- `sample/app.py` will attempt to auto-load `AITest/models/if_model.joblib` on startup and import the `AITest.preprocess.feature_utils` helpers.
- If the model file is not present or imports fail, the forwarder will still print events; see the startup diagnostic lines for `Model diagnostic` to confirm model discovery.
- To point the forwarder at a different model location you can move/rename the joblib file or run inference separately with `AITest/scripts/run_inference.py`.
