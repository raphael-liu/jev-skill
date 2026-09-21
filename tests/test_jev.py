import copy
import importlib.util
import io
import http.client
import json
import pathlib
import socket
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

PATH = pathlib.Path(__file__).resolve().parents[1] / 'skills/jev-skill/scripts/jev.py'
spec = importlib.util.spec_from_file_location('jev', PATH)
jev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jev)

REQUEST = {'model': 'jev-latest', 'state': 'Example', 'questions': {
    'route': {'type': 'choice', 'instructions': 'Pick', 'criteria': {'a': None, 'b': 'B'}},
    'rating': {'type': 'score', 'instructions': {}, 'criteria': ['Low', 'High']},
    'urgent': {'type': 'noul', 'instructions': [], 'criteria': {'true': 'Yes', 'false': 'No'}}}}
RESPONSE = {'model': 'jev-1.13.0', 'answers': {
    'route': {'type': 'choice', 'choice': 'a', 'probabilities': {'a': .8, 'b': .2}, 'confidence': .5},
    'rating': {'type': 'score', 'score': .25, 'legend': {'0': 'Low', '1': 'High'}, 'probabilities': {'0': .75, '1': .25}, 'confidence': .4},
    'urgent': {'type': 'noul', 'noul': .7}}}

class FakeResponse(io.BytesIO):
    status = 200

class ClientTests(unittest.TestCase):
    def run_client(self, response=None, exception=None, key='secret', dry_run=False):
        transport = unittest.mock.Mock()
        if exception:
            transport.side_effect = exception
        else:
            transport.return_value = FakeResponse(json.dumps(response or RESPONSE).encode())
        result = jev.run(REQUEST, api_key=key, timeout=10, dry_run=dry_run, transport=transport)
        return result, transport

    def test_success_all_types_and_unknown_usage(self):
        result, transport = self.run_client()
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['response'], RESPONSE)
        self.assertEqual(result['usage'], 'unknown')
        self.assertGreaterEqual(result['elapsed_s'], 0)
        request = transport.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.typesafe.ai/v1/systemone')
        self.assertEqual(request.get_header('Authorization'), 'Bearer secret')
        self.assertEqual(json.loads(request.data), REQUEST)
        transport.assert_called_once()

    def test_known_usage(self):
        response = copy.deepcopy(RESPONSE)
        response['usage'] = {'input_tokens': 10, 'output_tokens': 3}
        result, _ = self.run_client(response)
        self.assertEqual(result['usage'], response['usage'])

    def test_http_errors_never_expose_body_or_key(self):
        for code in (401, 503):
            with self.subTest(code=code):
                result, transport = self.run_client(exception=urllib.error.HTTPError('https://api.typesafe.ai', code, 'secret', {}, io.BytesIO(b'sensitive body')))
                self.assertEqual(result['error'], 'http_error')
                self.assertEqual(result['http_status'], code)
                self.assertNotIn('secret', json.dumps(result))
                self.assertNotIn('sensitive', json.dumps(result))
                transport.assert_called_once()

    def test_timeout(self):
        for exc in (socket.timeout('secret'), urllib.error.URLError(socket.timeout('secret'))):
            result, _ = self.run_client(exception=exc)
            self.assertEqual(result['error'], 'timeout')

    def test_http_transport_failures(self):
        for exc in (http.client.IncompleteRead(b'private', 100),
                    http.client.RemoteDisconnected('private'),
                    http.client.BadStatusLine('private')):
            result, transport = self.run_client(exception=exc)
            self.assertEqual(result['error'], 'network_error')
            self.assertNotIn('private', json.dumps(result))
            transport.assert_called_once()

    def test_missing_key(self):
        result, transport = self.run_client(key=None)
        self.assertEqual(result['error'], 'missing_api_key')
        transport.assert_not_called()

    def test_dry_run_without_key_or_network(self):
        result, transport = self.run_client(key=None, dry_run=True)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['validation'], 'passed')
        self.assertNotIn('response', result)
        transport.assert_not_called()

    def test_invalid_responses(self):
        changes = [lambda r: r['answers']['route'].update(choice='b'),
                   lambda r: r['answers']['urgent'].update(noul=float('nan')),
                   lambda r: r['answers'].pop('urgent'),
                   lambda r: r['answers']['urgent'].update(noul=True),
                   lambda r: r['answers']['route'].update(probabilities={'a': .8, 'c': .2}),
                   lambda r: r['answers']['route'].update(confidence=1.1),
                   lambda r: r['answers']['rating'].update(score=.8),
                   lambda r: r['answers']['rating'].update(legend={'1': 'Low', '2': 'High'}),
                   lambda r: r.update(usage={'input_tokens': True}),
                   lambda r: r['answers']['route'].update(probabilities={'a': .7, 'b': .2})]
        for change in changes:
            response = copy.deepcopy(RESPONSE)
            change(response)
            result, _ = self.run_client(response)
            self.assertEqual(result['error'], 'invalid_response')

    def test_malformed_json(self):
        transport = unittest.mock.Mock(return_value=FakeResponse(b'not json sensitive'))
        result = jev.run(REQUEST, api_key='secret', transport=transport)
        self.assertEqual(result['error'], 'invalid_response')

    def test_invalid_request(self):
        for criteria in ({'only': None}, {str(i): None for i in range(256)}):
            request = copy.deepcopy(REQUEST)
            request['questions']['route']['criteria'] = criteria
            with self.assertRaises(ValueError):
                jev.validate_request(request)
        for criteria in (['only'], ['x'] * 11):
            request = copy.deepcopy(REQUEST)
            request['questions']['rating']['criteria'] = criteria
            with self.assertRaises(ValueError):
                jev.validate_request(request)

    def test_cli_exit_codes_and_file_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / 'request.json'
            path.write_text(json.dumps(REQUEST), encoding='utf-8')
            with patch('sys.stdout', new_callable=io.StringIO) as output:
                self.assertEqual(jev.main(['--request', str(path), '--dry-run']), 0)
                self.assertEqual(json.loads(output.getvalue())['validation'], 'passed')
            with patch.dict('os.environ', {}, clear=True), patch('sys.stdout', new_callable=io.StringIO) as output:
                self.assertEqual(jev.main(['--request', str(path)]), 2)
                self.assertEqual(json.loads(output.getvalue())['error'], 'missing_api_key')
            path.write_text('invalid private body', encoding='utf-8')
            with patch('sys.stdout', new_callable=io.StringIO) as output:
                self.assertEqual(jev.main(['--request', str(path)]), 2)
                self.assertNotIn('private', output.getvalue())

    def test_redirects_blocked(self):
        with self.assertRaises(urllib.error.HTTPError) as caught:
            jev.NoRedirect().redirect_request(None, None, 307, 'redirect', {}, 'https://evil.example')
        caught.exception.close()

if __name__ == '__main__':
    unittest.main()
