#!/usr/bin/env python3
"""
_runner.py — Internal test runner called by prompt-test.sh.
Not intended for direct use.
"""
from __future__ import annotations
import json, sys, time, os, re
from difflib import SequenceMatcher
import urllib.request, urllib.error

def call_anthropic(model, system_prompt, user_input, timeout):
    api_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        raise ValueError('ANTHROPIC_API_KEY not set')
    payload = {'model': model, 'max_tokens': 2048, 'messages': [{'role': 'user', 'content': user_input}]}
    if system_prompt:
        payload['system'] = system_prompt
    req = urllib.request.Request(
        'https://api.anthropic.com/v1/messages',
        data=json.dumps(payload).encode(),
        headers={'x-api-key': api_key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())['content'][0]['text']

def call_openai(model, system_prompt, user_input, timeout):
    api_key = os.environ.get('OPENAI_API_KEY', '')
    if not api_key:
        raise ValueError('OPENAI_API_KEY not set')
    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': user_input})
    req = urllib.request.Request(
        'https://api.openai.com/v1/chat/completions',
        data=json.dumps({'model': model, 'messages': messages, 'max_tokens': 2048}).encode(),
        headers={'Authorization': f'Bearer {api_key}', 'content-type': 'application/json'},
        method='POST'
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())['choices'][0]['message']['content']

def call_model(model, system_prompt, user_input, timeout):
    if model.startswith('claude'):
        return call_anthropic(model, system_prompt, user_input, timeout)
    return call_openai(model, system_prompt, user_input, timeout)

def check_assertion(assertion, output):
    atype = assertion.get('type', '')
    ci = assertion.get('case_insensitive', False)
    out_cmp = output.lower() if ci else output

    if atype in ('llm_judge', 'rubric'):
        return 'deferred', None

    if atype == 'contains':
        val = assertion.get('value', '')
        v = val.lower() if ci else val
        if v in out_cmp:
            return 'pass', None
        return 'fail', f"output does not contain '{val}'"

    if atype == 'not_contains':
        val = assertion.get('value', '')
        v = val.lower() if ci else val
        if v not in out_cmp:
            return 'pass', None
        return 'fail', f"output contains forbidden string '{val}'"

    if atype == 'exact_match':
        expected = assertion.get('value', '')
        if output.strip() == expected.strip():
            return 'pass', None
        return 'fail', f"expected '{expected}', got '{output[:80]}'"

    if atype == 'fuzzy_match':
        expected = assertion.get('value', '')
        threshold = float(assertion.get('threshold', 0.8))
        ratio = SequenceMatcher(None, output.lower(), expected.lower()).ratio()
        if ratio >= threshold:
            return 'pass', None
        return 'fail', f"similarity {ratio:.2f} below threshold {threshold}"

    if atype == 'regex':
        pattern = assertion.get('pattern', '')
        flags = re.IGNORECASE if ci else 0
        if re.search(pattern, output, flags):
            return 'pass', None
        return 'fail', f"output does not match pattern '{pattern}'"

    if atype == 'json_valid':
        try:
            json.loads(output)
            return 'pass', None
        except json.JSONDecodeError as e:
            return 'fail', f"invalid JSON: {e}"

    if atype == 'json_schema':
        try:
            data = json.loads(output)
        except json.JSONDecodeError as e:
            return 'fail', f"invalid JSON: {e}"
        schema = assertion.get('schema', {})
        for field in schema.get('required', []):
            if field not in data:
                return 'fail', f"missing required field: {field}"
        type_map = {'string': str, 'number': (int, float), 'boolean': bool,
                    'array': list, 'object': dict, 'integer': int}
        for field, spec in schema.get('properties', {}).items():
            if field in data and spec.get('type') in type_map:
                if not isinstance(data[field], type_map[spec['type']]):
                    return 'fail', f"field '{field}' expected type {spec['type']}"
        return 'pass', None

    if atype == 'not_empty':
        if output.strip():
            return 'pass', None
        return 'fail', 'output is empty'

    if atype == 'max_length':
        limit = int(assertion.get('value', 1000))
        if len(output) <= limit:
            return 'pass', None
        return 'fail', f"output length {len(output)} exceeds limit {limit}"

    if atype == 'min_length':
        minimum = int(assertion.get('value', 1))
        if len(output) >= minimum:
            return 'pass', None
        return 'fail', f"output length {len(output)} below minimum {minimum}"

    return 'fail', f"unknown assertion type: {atype}"

def main():
    import yaml
    spec_file = sys.argv[1]
    test_index = int(sys.argv[2])
    model = sys.argv[3]
    timeout = int(sys.argv[4])

    with open(spec_file) as f:
        spec = yaml.safe_load(f)

    test = spec['tests'][test_index]
    test_name = test.get('name', f'test_{test_index}')
    input_text = test.get('input', '')
    assertions = test.get('assertions', [])
    test_model = test.get('model') or model

    # Load system prompt
    system_prompt = ''
    template_path = spec.get('prompt_template') or test.get('prompt_template')
    if template_path:
        base_dir = os.path.dirname(os.path.abspath(spec_file))
        for candidate in [os.path.join(base_dir, template_path), template_path]:
            if os.path.exists(candidate):
                with open(candidate) as f:
                    system_prompt = f.read().strip()
                break

    # Variable substitution
    for k, v in test.get('variables', {}).items():
        input_text = input_text.replace(f'{{{{{k}}}}}', str(v))

    result = {
        'name': test_name, 'input': input_text, 'model': test_model,
        'assertions': [], 'passed': 0, 'failed': 0, 'deferred': 0,
        'error': None, 'output': None, 'latency_ms': None,
    }

    start = time.time()
    try:
        output = call_model(test_model, system_prompt, input_text, timeout)
        result['latency_ms'] = int((time.time() - start) * 1000)
        result['output'] = output
    except Exception as e:
        result['error'] = str(e)
        result['latency_ms'] = int((time.time() - start) * 1000)
        print(json.dumps(result))
        return

    for assertion in assertions:
        status, reason = check_assertion(assertion, output)
        ar = {'type': assertion.get('type', '?'), 'status': status}
        if status == 'deferred':
            ar['assertion'] = assertion
            result['deferred'] += 1
        elif status == 'pass':
            result['passed'] += 1
        else:
            ar['reason'] = reason
            result['failed'] += 1
        result['assertions'].append(ar)

    print(json.dumps(result))

if __name__ == '__main__':
    main()
