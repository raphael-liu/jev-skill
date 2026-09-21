#!/usr/bin/env python3
"""Recompute published aggregates from sanitized measurements; no API calls."""
import csv
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parent


def read(name):
    with (ROOT / 'data' / name).open() as stream:
        return list(csv.DictReader(stream))


def usage(rows, key):
    values = [r[key] for r in rows]
    return {'reported_sum': sum(int(v) for v in values if v != ''),
            'missing_rows': sum(v == '' for v in values)}


def main():
    rows = read('structured.csv')
    assert len(rows) == 416
    test = [r for r in rows if r['phase'] == 'test']
    result = {}
    for arm in 'ABC':
        group = [r for r in test if r['arm'] == arm]
        assert len(group) == 80
        result[arm] = {
            'n': len(group),
            'exact': sum(int(r['exact_correct']) for r in group),
            'mean_s': mean(float(r['e2e_s']) for r in group),
            'direct': sum(int(r['direct']) for r in group),
            'wrong_direct': sum(int(r['direct']) and not int(r['exact_correct']) for r in group),
            'scenarios': {},
            'usage': {key: usage(group, key) for key in group[0] if key.endswith('_tokens')},
        }
        for scenario in ('snake', 'mr', 'crash', 'drn'):
            subset = [r for r in group if r['scenario'] == scenario]
            assert len(subset) == 20
            result[arm]['scenarios'][scenario] = {
                'exact': sum(int(r['exact_correct']) for r in subset),
                'mean_s': mean(float(r['e2e_s']) for r in subset),
            }
    assert [result[a]['exact'] for a in 'ABC'] == [78, 66, 76]
    assert result['C']['direct'] == 63 and result['C']['wrong_direct'] == 2
    result['all_phases_reported_usage'] = {
        arm: {key: usage([r for r in rows if r['arm'] == arm], key)
              for key in rows[0] if key.endswith('_tokens')}
        for arm in 'ABC'
    }
    pilot = read('pilot.csv')
    result['pilot_percent_change'] = {}
    for scenario in dict.fromkeys(r['scenario'] for r in pilot):
        pair = {r['arm']: float(r['e2e_s']) for r in pilot if r['scenario'] == scenario}
        result['pilot_percent_change'][scenario] = (pair['C'] / pair['A'] - 1) * 100
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
