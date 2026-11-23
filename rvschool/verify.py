#!/usr/bin/env python3
"""Exercise only newly reserved IDs, always clean them up, and save evidence."""
import argparse
import json
import secrets
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

p = argparse.ArgumentParser()
p.add_argument('--base', default='https://petstore.swagger.rv-school.ru/api/v3')
p.add_argument('--baseline', action='store_true')
p.add_argument('--out', required=True)
args = p.parse_args()
report = {'base': args.base, 'baseline': args.baseline, 'requests': [], 'checks': []}
owned = []

def req(method, path, body=None):
    data = None if body is None else json.dumps(body).encode()
    r = Request(args.base + path, data=data, method=method,
                headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
    try:
        response = urlopen(r, timeout=25)
    except HTTPError as e:
        response = e
    with response:
        raw = response.read().decode()
        try:
            result = json.loads(raw)
        except ValueError:
            result = raw
        report['requests'].append({'method': method, 'path': path, 'request': body,
                                   'status': response.status, 'response': result})
        return response.status, result

def check(name, condition):
    report['checks'].append({'name': name, 'passed': bool(condition)})
    assert condition, name
    print('PASS', name, flush=True)

def pet(pid, status='available', name='petstore-status-regression'):
    return {'id': pid, 'name': name, 'photoUrls': ['https://example.com/test.png'],
            'category': {'id': 771, 'name': 'regression'},
            'tags': [{'id': 771, 'name': 'petstore-status-20261123'}], 'status': status}

def post_verify(pid, body, expected):
    status, result = req('POST', '/pet', body)
    check(f'POST {pid}: HTTP {expected}', status == expected)
    if expected == 404:
        check(f'POST {pid}: exact error body', result == {'code': 404, 'message': 'Invalid pet status'})
    return result

failure = None
try:
    start = 8_000_000_000_000 + secrets.randbelow(900_000_000_000)
    ids = [start + i for i in range(9)]
    for pid in ids:
        check(f'ID {pid} initially absent', req('GET', f'/pet/{pid}')[0] == 404)
        owned.append(pid)
    for pid, status in zip(ids[:3], ('available', 'pending', 'sold')):
        body = pet(pid, status)
        post_verify(pid, body, 200)
        code, result = req('GET', f'/pet/{pid}')
        check(f'{status}: GET matches created pet', code == 200 and result == body)
    for pid, status in zip(ids[3:5], ('unknown', 'arbitrary-invalid-20261123')):
        post_verify(pid, pet(pid, status), 200 if args.baseline else 404)
        check(f'{status}: GET after POST', req('GET', f'/pet/{pid}')[0] == (200 if args.baseline else 404))
    existing = ids[5]
    post_verify(existing, pet(existing, 'pending', 'original-preserved'), 200)
    before = req('GET', f'/pet/{existing}')[1]
    for status in ('unknown', 'arbitrary-invalid-20261123'):
        post_verify(existing, pet(existing, status, 'must-not-overwrite'), 200 if args.baseline else 404)
        code, after = req('GET', f'/pet/{existing}')
        check(f'{status}: existing record check', code == 200 and (args.baseline or after == before))
    missing = pet(ids[6])
    del missing['status']
    post_verify(ids[6], missing, 200)
    check('missing status: GET succeeds', req('GET', f'/pet/{ids[6]}')[0] == 200)
    post_verify(ids[7], pet(ids[7], None), 200)
    check('null status: GET succeeds', req('GET', f'/pet/{ids[7]}')[0] == 200)
    # PUT deliberately retains its previous permissive behavior.
    body = pet(ids[0], 'unknown', 'put-unchanged')
    check('PUT unknown retains HTTP 200', req('PUT', '/pet', body)[0] == 200)
    check('PUT unknown persists as before', req('GET', f'/pet/{ids[0]}') == (200, body))
    check('GET findByStatus remains available', req('GET', '/pet/findByStatus?status=available')[0] == 200)
    check('GET findByTags remains available', req('GET', '/pet/findByTags?tags=petstore-status-20261123')[0] == 200)
    check('GET store inventory remains available', req('GET', '/store/inventory')[0] == 200)
    if not args.baseline:
        status, spec = req('GET', '/openapi.json')
        response = spec['paths']['/pet']['post']['responses']['404']
        check('live OpenAPI documents 404', status == 200 and response['content']['application/json']['example'] == {'code': 404, 'message': 'Invalid pet status'})
except BaseException as e:
    failure = e
    report['failure'] = repr(e)
finally:
    report['cleanup'] = []
    for pid in owned:
        try:
            code, _ = req('GET', f'/pet/{pid}')
            if code == 200:
                req('DELETE', f'/pet/{pid}')
            absent = req('GET', f'/pet/{pid}')[0] == 404
            report['cleanup'].append({'id': pid, 'absent': absent})
        except Exception as e:
            report['cleanup'].append({'id': pid, 'error': repr(e)})
    Path(args.out).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    clean = len(report['cleanup']) == len(owned) and all(x.get('absent') for x in report['cleanup'])
    print('Cleanup:', 'PASS' if clean else 'FAIL', flush=True)
if failure:
    raise failure
assert clean, 'cleanup failed'
