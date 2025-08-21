#!/usr/bin/env python3
"""
Train a simple IsolationForest on numeric features extracted from the sample JSONL.
"""
import argparse
import json
import os
import sys
# Ensure repo root is on sys.path so `import AITest...` works when running from this directory
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from sklearn.ensemble import IsolationForest
import joblib
from collections import Counter
from AITest.preprocess.feature_utils import extract_numeric_features, vectorize_features


def load_samples(path):
    samples = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            samples.append(json.loads(line))
    return samples


def collect_feature_keys(samples):
    keys = Counter()
    feats = []
    for s in samples:
        f = extract_numeric_features(s)
        feats.append(f)
        for k in f.keys():
            keys[k] += 1
    # choose top N keys
    common = [k for k, _ in keys.most_common(50)]
    return common, feats


def build_matrix(feats, keys):
    mat = []
    for f in feats:
        mat.append(vectorize_features(f, keys))
    return mat


def train_if(input_path, out_path):
    samples = load_samples(input_path)
    keys, feats = collect_feature_keys(samples)
    X = build_matrix(feats, keys)

    if not X:
        print('No numeric features found, aborting')
        return

    model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
    model.fit(X)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    joblib.dump({'model': model, 'keys': keys}, out_path)
    print(f'Saved model to {out_path}')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    train_if(args.input, args.out)
