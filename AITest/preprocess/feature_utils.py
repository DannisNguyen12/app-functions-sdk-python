#!/usr/bin/env python3
"""
Helpers to convert raw Redis event payloads into numeric feature vectors.
This is intentionally minimal - extend by device/profile as needed.
"""
import json
from typing import Any, Dict, List


def extract_numeric_features(sample: Dict[str, Any]) -> Dict[str, Any]:
    """Try to extract numeric features from sample['value'].
    Returns a flat dict of feature_name -> value
    """
    val = sample.get('value')
    features = {}

    # If value is a dict with numeric fields, grab them
    if isinstance(val, dict):
        for k, v in val.items():
            try:
                features[k] = float(v)
            except Exception:
                continue
    # If value is a JSON string try parse
    elif isinstance(val, str):
        try:
            obj = json.loads(val)
            if isinstance(obj, dict):
                for k, v in obj.items():
                    try:
                        features[k] = float(v)
                    except Exception:
                        continue
        except Exception:
            pass
    # If value is a list, try parse numeric entries
    elif isinstance(val, list):
        for i, item in enumerate(val):
            try:
                features[f'item_{i}'] = float(item)
            except Exception:
                continue

    return features


def vectorize_features(dict_features: Dict[str, float], keys: List[str]) -> List[float]:
    """Given a dict of features and a canonical key order, return a dense vector.
    Missing keys are filled with 0.0
    """
    return [float(dict_features.get(k, 0.0)) for k in keys]
