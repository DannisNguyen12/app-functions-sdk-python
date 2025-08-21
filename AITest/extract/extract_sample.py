#!/usr/bin/env python3
"""
Sample extractor for EdgeX Redis data.
Writes a JSONL file with sampled events across keys.
"""
import argparse
import json
import os
import redis
from itertools import islice


def sample_redis(host: str, port: int, count: int, out_path: str, pattern: str = None, list_limit: int = 10, batch_size: int = 200):
    r = redis.Redis(host=host, port=port, decode_responses=True)

    # Use SCAN to iterate keys but stop early when we have enough
    cursor = 0
    sampled = []

    def write_out(samples):
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, 'a', encoding='utf-8') as f:
            for s in samples:
                f.write(json.dumps(s))
                f.write('\n')

    # helper to process a batch of keys with pipelines (TYPE then read)
    def process_batch(keys_batch):
        nonlocal sampled
        if not keys_batch:
            return
        # pipeline to get types
        pipe = r.pipeline()
        for k in keys_batch:
            pipe.type(k)
        types = pipe.execute()

        # second pipeline to fetch values for supported types; collect unsupported for safe per-key reads
        pipe2 = r.pipeline()
        supported_flags = []
        for k, t in zip(keys_batch, types):
            if t == 'string':
                pipe2.get(k); supported_flags.append(True)
            elif t == 'list':
                pipe2.lrange(k, 0, list_limit - 1); supported_flags.append(True)
            elif t == 'hash':
                pipe2.hgetall(k); supported_flags.append(True)
            elif t == 'set':
                pipe2.smembers(k); supported_flags.append(True)
            elif t == 'zset':
                pipe2.zrange(k, 0, -1); supported_flags.append(True)
            elif t == 'stream':
                # xrange returns stream entries; limit by list_limit
                try:
                    pipe2.xrange(k, min='-', max='+', count=list_limit)
                    supported_flags.append(True)
                except Exception:
                    # some redis-py versions may not support xrange in pipeline; mark unsupported
                    supported_flags.append(False)
            else:
                supported_flags.append(False)

        # Execute pipeline for the supported commands
        values = []
        if any(supported_flags):
            try:
                values = pipe2.execute()
            except Exception:
                # If pipeline fails for some reason, fall back to empty values and per-key reads below
                values = []

        # Map results back to keys; for unsupported or missing values do safe per-key reads
        values_iter = iter(values)
        for k, t, supported in zip(keys_batch, types, supported_flags):
            v = None
            if supported:
                try:
                    v = next(values_iter)
                except StopIteration:
                    v = None
            else:
                # safe per-key read depending on type, ignore wrong-type errors
                try:
                    if t == 'string':
                        v = r.get(k)
                    elif t == 'list':
                        v = r.lrange(k, 0, list_limit - 1)
                    elif t == 'hash':
                        v = r.hgetall(k)
                    elif t == 'set':
                        v = r.smembers(k)
                    elif t == 'zset':
                        v = r.zrange(k, 0, -1)
                    elif t == 'stream':
                        try:
                            v = r.xrange(k, min='-', max='+', count=list_limit)
                        except Exception:
                            v = None
                    else:
                        v = None
                except Exception:
                    v = None

            sampled.append({'key': k, 'type': t, 'value': v})

    # SCAN and process in batches until we have enough
    while True:
        if pattern:
            cursor, found = r.scan(cursor=cursor, match=pattern, count=batch_size)
        else:
            cursor, found = r.scan(cursor=cursor, count=batch_size)

        if found:
            # process in smaller batches to keep pipeline sizes reasonable
            it = iter(found)
            while True:
                batch = list(islice(it, batch_size))
                if not batch:
                    break
                process_batch(batch)
                if len(sampled) >= count:
                    write_out(sampled[:count])
                    print(f'Wrote {min(len(sampled), count)} samples to {out_path}')
                    return

        if cursor == 0 or cursor == '0':
            break

    # finished scanning but may have fewer than requested
    if sampled:
        write_out(sampled)
        print(f'Wrote {len(sampled)} samples to {out_path}')
    else:
        print('No keys found matching pattern' if pattern else 'No keys found in Redis')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='localhost')
    p.add_argument('--port', default=6379, type=int)
    p.add_argument('--count', default=1000 , type=int, help='Number of samples to collect')
    p.add_argument('--out', dest='out_path', default='AITest/data/redis_sample.jsonl')
    p.add_argument('--pattern', default=None, help='Optional key pattern (e.g., edgex* )')
    p.add_argument('--list-limit', default=10, type=int, help='Max elements to read from lists')
    p.add_argument('--batch-size', default=200, type=int, help='Keys per SCAN batch / pipeline')
    args = p.parse_args()

    # ensure relative output paths are anchored at the repository root (app-functions-sdk-python)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    out_path = args.out_path
    if not os.path.isabs(out_path):
        out_path = os.path.abspath(os.path.join(repo_root, out_path))

    # remove existing output to avoid appending to old runs
    try:
        if os.path.exists(out_path):
            os.remove(out_path)
    except Exception:
        pass

    sample_redis(args.host, args.port, args.count, out_path, pattern=args.pattern, list_limit=args.list_limit, batch_size=args.batch_size)
