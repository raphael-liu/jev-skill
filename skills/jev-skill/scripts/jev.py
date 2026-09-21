#!/usr/bin/env python3
"""One bounded TypeSafe Jev request; standard library only, no retries or actions."""
import argparse
import http.client
import json
import math
import os
import socket
import sys
import time
import urllib.error
import urllib.request

ENDPOINT = 'https://api.typesafe.ai/v1/systemone'
TOLERANCE = 1e-4


def require(condition):
    if not condition:
        raise ValueError('Invalid schema')


def structured(value):
    return isinstance(value, (str, dict, list))


def finite_json(value):
    if isinstance(value, float):
        require(math.isfinite(value))
    elif isinstance(value, dict):
        for key, item in value.items():
            require(isinstance(key, str))
            finite_json(item)
    elif isinstance(value, list):
        for item in value:
            finite_json(item)


def number(value, low, high):
    require(type(value) in (int, float))
    require(math.isfinite(value) and low <= value <= high)


def validate_request(request):
    require(isinstance(request, dict))
    finite_json(request)
    require(isinstance(request.get('model'), str) and bool(request['model'].strip()))
    require(structured(request.get('state')))
    questions = request.get('questions')
    require(isinstance(questions, dict) and bool(questions))
    for question_id, question in questions.items():
        require(isinstance(question_id, str) and isinstance(question, dict))
        require(structured(question.get('instructions')))
        kind = question.get('type')
        criteria = question.get('criteria')
        if kind == 'choice':
            require(isinstance(criteria, dict) and 2 <= len(criteria) <= 255)
            require(all(isinstance(k, str) and (v is None or structured(v)) for k, v in criteria.items()))
        elif kind == 'score':
            require(isinstance(criteria, list) and 2 <= len(criteria) <= 10)
            require(all(structured(v) for v in criteria))
        elif kind == 'noul':
            if 'criteria' in question:
                require(isinstance(criteria, dict) and set(criteria) <= {'true', 'false'})
                require(all(structured(v) for v in criteria.values()))
        else:
            raise ValueError('Invalid question type')
    return request


def probabilities(answer, keys):
    distribution = answer.get('probabilities')
    require(isinstance(distribution, dict) and set(distribution) == set(keys))
    for value in distribution.values():
        number(value, 0, 1)
    require(abs(sum(distribution.values()) - 1) <= TOLERANCE)
    number(answer.get('confidence'), 0, 1)
    return distribution


def validate_response(response, request):
    require(isinstance(response, dict))
    finite_json(response)
    require(isinstance(response.get('model'), str) and bool(response['model'].strip()))
    answers = response.get('answers')
    require(isinstance(answers, dict) and set(answers) == set(request['questions']))
    for question_id, question in request['questions'].items():
        answer = answers[question_id]
        require(isinstance(answer, dict) and answer.get('type') == question['type'])
        kind = question['type']
        if kind == 'noul':
            number(answer.get('noul'), 0, 1)
        elif kind == 'choice':
            distribution = probabilities(answer, question['criteria'])
            choice = answer.get('choice')
            require(isinstance(choice, str) and choice in distribution)
            require(distribution[choice] == max(distribution.values()))
        else:
            keys = {str(i) for i in range(len(question['criteria']))}
            distribution = probabilities(answer, keys)
            legend = answer.get('legend')
            require(isinstance(legend, dict) and set(legend) == keys)
            require(all(isinstance(v, str) for v in legend.values()))
            number(answer.get('score'), 0, len(keys) - 1)
            expected = sum(int(k) * p for k, p in distribution.items())
            require(abs(answer['score'] - expected) <= TOLERANCE)
    if 'usage' in response:
        require(isinstance(response['usage'], dict))
        for key in ('input_tokens', 'output_tokens'):
            if key in response['usage']:
                value = response['usage'][key]
                require(type(value) is int and value >= 0)
    return response


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Reject all redirects so Authorization can never follow a new host."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(ENDPOINT, code, 'Redirect rejected', headers, None)


def run(request, api_key=None, timeout=10, dry_run=False, transport=None):
    started = time.perf_counter()

    def result(status, **fields):
        return dict(status=status, elapsed_s=round(time.perf_counter() - started, 6), **fields)

    try:
        validate_request(request)
        number(timeout, 0.001, 300)
    except (ValueError, TypeError, OverflowError):
        return result('error', error='invalid_request')
    if dry_run:
        return result('ok', validation='passed')
    if not isinstance(api_key, str) or not api_key.strip():
        return result('error', error='missing_api_key')
    if '\r' in api_key or '\n' in api_key:
        return result('error', error='invalid_api_key')
    http_request = urllib.request.Request(
        ENDPOINT, data=json.dumps(request, allow_nan=False).encode('utf-8'),
        headers={'Authorization': 'Bearer ' + api_key, 'Content-Type': 'application/json'}, method='POST')
    if transport is None:
        transport = urllib.request.build_opener(NoRedirect()).open
    try:
        with transport(http_request, timeout=timeout) as response:
            if response.status != 200:
                return result('error', error='http_error', http_status=response.status)
            payload = response.read()
        validated = validate_response(json.loads(payload), request)
    except urllib.error.HTTPError as error:
        error.close()
        return result('error', error='http_error', http_status=error.code)
    except (TimeoutError, socket.timeout):
        return result('error', error='timeout')
    except urllib.error.URLError as error:
        code = 'timeout' if isinstance(error.reason, (TimeoutError, socket.timeout)) else 'network_error'
        return result('error', error=code)
    except (ValueError, TypeError, UnicodeError, OverflowError, RecursionError):
        return result('error', error='invalid_response')
    except (OSError, http.client.HTTPException):
        return result('error', error='network_error')
    usage = validated.get('usage', 'unknown')
    if isinstance(usage, dict):
        usage = {key: usage.get(key, 'unknown') for key in ('input_tokens', 'output_tokens')}
    return result('ok', response=validated, usage=usage)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request', required=True, help='Path to a UTF-8 JSON request')
    parser.add_argument('--timeout', type=float, default=10, help='Timeout seconds (0.001–300; default 10)')
    parser.add_argument('--dry-run', action='store_true', help='Validate only; no API key or network needed')
    args = parser.parse_args(argv)
    started = time.perf_counter()
    try:
        with open(args.request, encoding='utf-8') as source:
            request = json.load(source)
    except (OSError, ValueError, UnicodeError, RecursionError):
        output = {'status': 'error', 'error': 'invalid_request_file', 'elapsed_s': round(time.perf_counter() - started, 6)}
    else:
        output = run(request, api_key=os.environ.get('TYPESAFE_API_KEY'), timeout=args.timeout, dry_run=args.dry_run)
    print(json.dumps(output, ensure_ascii=False, allow_nan=False))
    return 0 if output['status'] == 'ok' else 2


if __name__ == '__main__':
    sys.exit(main())
