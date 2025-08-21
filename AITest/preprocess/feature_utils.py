#!/usr/bin/env python3
"""
Helpers to convert raw Redis event payloads into numeric feature vectors.
This is intentionally minimal - extend by device/profile as needed.
"""
import json
from typing import Any, Dict, List, Iterable, Tuple
from collections import Counter, defaultdict


def extract_numeric_features(sample: Dict[str, Any]) -> Dict[str, Any]:
    """Try to extract numeric features from sample['value'].
    Returns a flat dict of feature_name -> value
    """
    val = sample.get('value')
    features = {}

    # If value is a dict with fields, try multiple coercions
    if isinstance(val, dict):
        for k, v in val.items():
            # booleans -> 0/1
            if isinstance(v, bool):
                features[k] = 1.0 if v else 0.0
                continue
            # numeric-like
            try:
                features[k] = float(v)
                continue
            except Exception:
                pass
            # strings -> keep raw for categorical handling (mark with prefix)
            if isinstance(v, str):
                features[f'_cat_{k}'] = v
                continue
    # If value is a JSON string try parse
    elif isinstance(val, str):
        try:
            obj = json.loads(val)
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, bool):
                        features[k] = 1.0 if v else 0.0
                        continue
                    try:
                        features[k] = float(v)
                        continue
                    except Exception:
                        pass
                    if isinstance(v, str):
                        features[f'_cat_{k}'] = v
                        continue
        except Exception:
            pass
    # If value is a list, try parse numeric entries (and strings as categorical)
    elif isinstance(val, list):
        for i, item in enumerate(val):
            if isinstance(item, bool):
                features[f'item_{i}'] = 1.0 if item else 0.0
                continue
            try:
                features[f'item_{i}'] = float(item)
                continue
            except Exception:
                pass
            if isinstance(item, str):
                features[f'_cat_item_{i}'] = item
                continue

    return features


def vectorize_features(dict_features: Dict[str, float], keys: List[str]) -> List[float]:
    """Given a dict of features and a canonical key order, return a dense vector.
    Missing keys are filled with 0.0
    """
    return [float(dict_features.get(k, 0.0)) for k in keys]


def build_keys_from_samples(samples: Iterable[Dict[str, Any]], max_ohe: int = 10) -> Tuple[List[str], Dict[str, List[str]]]:
    """Build a stable list of keys for vectorization from a set of extracted feature dicts.

    - samples: iterable of raw samples (each sample is passed to extract_numeric_features)
    - max_ohe: for categorical fields, keep one-hot for top-K categories; rest map to 'other'

    Returns (keys, cat_map) where keys is the canonical key order and cat_map maps field -> list of categories used for OHE.
    """
    cat_counts = defaultdict(Counter)
    numeric_keys = set()

    for s in samples:
        f = extract_numeric_features(s)
        for k, v in f.items():
            if k.startswith('_cat_'):
                field = k[len('_cat_'):]
                cat_counts[field][str(v)] += 1
            else:
                numeric_keys.add(k)

    # decide OHE categories
    cat_map = {}
    for field, counter in cat_counts.items():
        top = [c for c, _ in counter.most_common(max_ohe)]
        cat_map[field] = top

    # build keys: sorted numeric keys, then for each categorical field add ohe columns
    keys = sorted([k for k in numeric_keys if not k.startswith('_cat_')])
    for field in sorted(cat_map.keys()):
        for c in cat_map[field]:
            keys.append(f'{field}__is_{c}')
        keys.append(f'{field}__is_other')

    return keys, cat_map


def vectorize_with_cats(dict_features: Dict[str, Any], keys: List[str], cat_map: Dict[str, List[str]]) -> List[float]:
    """Vectorize features that may include categorical raw values from extract_numeric_features.

    - dict_features may contain keys like '_cat_field': 'value'
    - keys is the canonical list from build_keys_from_samples
    - cat_map maps field -> top categories
    """
    out = []
    # precompute categorical raw values
    cats = {}
    for k, v in dict_features.items():
        if k.startswith('_cat_'):
            cats[k[len('_cat_'):]] = str(v)

    for key in keys:
        # categorical one-hot key format: field__is_{category}
        if '__is_' in key:
            field, _, cat = key.partition('__is_')
            val = 0.0
            if field in cats:
                if cat == 'other':
                    if cats[field] not in cat_map.get(field, []):
                        val = 1.0
                else:
                    if cats[field] == cat:
                        val = 1.0
            out.append(float(val))
        else:
            out.append(float(dict_features.get(key, 0.0)))

    return out
