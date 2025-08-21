#!/usr/bin/env python3
"""
Load a trained model and run inference on a live sample from Core Data via app.py style polling.
This script is a simple runner that mimics `sample/app.py` but calls the model for each event and prints a score.
"""
import argparse
import joblib
import time
import requests
import json
import os
import sys
# Ensure repo root is on sys.path so `import AITest...` works when running from this directory
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from AITest.preprocess.feature_utils import extract_numeric_features, vectorize_features


def load_model(path):
    data = joblib.load(path)
    return data['model'], data['keys']


def main(model_path, core_data_url, poll_interval=2):
    model, keys = load_model(model_path)
    print(f'Loaded model; keys={keys}')

    while True:
        try:
            resp = requests.get(f"{core_data_url}/event/all?offset=0&limit=5")
            if resp.status_code != 200:
                print('Core Data fetch failed')
                time.sleep(poll_interval)
                continue
            events = resp.json().get('events', [])
            for e in reversed(events):
                f = extract_numeric_features({'value': e.get('readings')})
                vec = vectorize_features(f, keys)
                try:
                    score = model.decision_function([vec])[0]
                except Exception as ex:
                    score = None
                print('Event id=', e.get('id'), 'device=', e.get('deviceName'), 'score=', score)
            time.sleep(poll_interval)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print('Error in polling loop', e)
            time.sleep(poll_interval)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--model', required=True)
    p.add_argument('--core', default='http://localhost:59880/api/v3')
    args = p.parse_args()
    main(args.model, args.core)
