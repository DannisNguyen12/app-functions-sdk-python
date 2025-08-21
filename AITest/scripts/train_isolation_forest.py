#!/usr/bin/env python3
"""
Train a simple IsolationForest on numeric features extracted from the extract JSONL.
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
from AITest.preprocess.feature_utils import (
    extract_numeric_features,
    vectorize_features,
    build_keys_from_samples,
    vectorize_with_cats,
)


def load_samples(path):
    samples = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            samples.append(json.loads(line))
    return samples


def collect_feature_keys(samples):
    # backward compatible wrapper: return features extracted for each sample
    feats = [extract_numeric_features(s) for s in samples]
    # use build_keys_from_samples to derive stable keys and category map
    keys, cat_map = build_keys_from_samples(samples)
    return keys, cat_map, feats


def build_matrix(feats, keys):
    mat = []
    for f in feats:
        mat.append(vectorize_features(f, keys))
    return mat


def train_if(input_path, out_path):
    samples = load_samples(input_path)
    keys, cat_map, feats = collect_feature_keys(samples)
    # build matrix using categorical-aware vectorizer
    mat = []
    for f in feats:
        mat.append(vectorize_with_cats(f, keys, cat_map))
    X = mat

    if not X:
        print('No numeric features found, aborting')
        return

    model = IsolationForest(n_estimators=100, contamination=0.01, random_state=42)
    model.fit(X)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    joblib.dump({'model': model, 'keys': keys, 'cat_map': cat_map}, out_path)
    print(f'Saved model to {out_path}')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    train_if(args.input, args.out)
