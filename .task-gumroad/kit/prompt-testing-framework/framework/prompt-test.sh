#!/usr/bin/env bash
# prompt-test.sh — CLI for running prompt test suites
# Copyright 2026 Edgeless Labs LLC — MIT License
#
# Usage:
#   ./framework/prompt-test.sh run <test_spec.yaml> [options]
#   ./framework/prompt-test.sh run-all <dir/> [options]
#   ./framework/prompt-test.sh validate <test_spec.yaml>
#   ./framework/prompt-test.sh list <test_spec.yaml>
#
# Options:
#   --model <model>           Override model in spec (default: claude-3-5-haiku-20241022)
#   --verbose                 Print full request/response for each test
#   --fail-threshold <0-1>    Fail exit code if pass rate below threshold (default: 1.0)
#   --output <file>           Write JSON results to file
#   --timeout <seconds>       Per-request timeout (default: 30)
#   --dry-run                 Print test plan without executing

set -euo pipefail

# ── Constants ──────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_DIR="$SCRIPT_DIR"
VERSION="1.0.0"
DEFAULT_MODEL="claude-3-5-haiku-20241022"
DEFAULT_TIMEOUT=30
DEFAULT_FAIL_THRESHOLD="1.0"
RESULTS_DIR="${PTF_RESULTS_DIR:-./results}"

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Utilities ─────────────────────────────────────────────────────────────────
log()    { echo -e "${BLUE}[ptf]${RESET} $*"; }
fail()   { echo -e "${RED}[fail]${RESET} $*"; }
warn()   { echo -e "${YELLOW}[warn]${RESET} $*"; }
header() { echo -e "\n${BOLD}${CYAN}$*${RESET}"; }
die()    { echo -e "${RED}[error]${RESET} $*" >&2; exit 2; }

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

# ── Dependency checks ─────────────────────────────────────────────────────────
check_deps() {
    require_cmd python3
    python3 -c "import yaml" 2>/dev/null || die "Python yaml module not found. Run: pip install pyyaml"
}

# ── YAML helpers (all via python3 -c to avoid heredoc parse issues) ───────────
yaml_get() {
    # yaml_get <file> <dotted.key> [default]
    python3 -c "
import yaml, sys
try:
    with open(sys.argv[1]) as f:
        data = yaml.safe_load(f)
    keys = sys.argv[2].split('.')
    val = data
    for k in keys:
        val = val.get(k) if isinstance(val, dict) else None
        if val is None:
            break
    print(val if val is not None else sys.argv[3])
except Exception:
    print(sys.argv[3])
" "$1" "$2" "${3:-}"
}

yaml_test_count() {
    python3 -c "
import yaml, sys
with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)
print(len(data.get('tests', [])))
" "$1"
}

yaml_test_name() {
    # yaml_test_name <file> <index>
    python3 -c "
import yaml, sys
with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)
tests = data.get('tests', [])
idx = int(sys.argv[2])
print(tests[idx].get('name', 'test_' + str(idx)) if idx < len(tests) else 'test_' + str(idx))
" "$1" "$2"
}

# ── run_single_test — delegates entirely to Python ────────────────────────────
run_single_test() {
    # run_single_test <spec_file> <test_index> <model> <timeout>
    # Prints JSON result to stdout
    python3 "$FRAMEWORK_DIR/_runner.py" "$1" "$2" "$3" "$4"
}

# ── Write the embedded Python runner on first use ─────────────────────────────
write_runner() {
    cat > "$FRAMEWORK_DIR/_runner.py" << 'PYEOF'
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
PYEOF
}

# ── cmd_run ────────────────────────────────────────────────────────────────────
cmd_run() {
    local spec_file=""
    local model="$DEFAULT_MODEL"
    local verbose=false
    local fail_threshold="$DEFAULT_FAIL_THRESHOLD"
    local output_file=""
    local timeout="$DEFAULT_TIMEOUT"
    local dry_run=false

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --model)           model="$2";           shift 2 ;;
            --verbose)         verbose=true;          shift ;;
            --fail-threshold)  fail_threshold="$2";   shift 2 ;;
            --output)          output_file="$2";      shift 2 ;;
            --timeout)         timeout="$2";          shift 2 ;;
            --dry-run)         dry_run=true;          shift ;;
            -*)                die "Unknown option: $1" ;;
            *)
                [[ -z "$spec_file" ]] && spec_file="$1"
                shift ;;
        esac
    done

    [[ -z "$spec_file" ]] && die "No test spec file provided. Usage: prompt-test.sh run <spec.yaml>"
    [[ -f "$spec_file" ]] || die "Test spec not found: $spec_file"

    # Ensure runner exists
    [[ -f "$FRAMEWORK_DIR/_runner.py" ]] || write_runner

    local suite_name
    suite_name=$(yaml_get "$spec_file" "name" "Unnamed Suite")
    local spec_model
    spec_model=$(yaml_get "$spec_file" "model" "$DEFAULT_MODEL")
    # CLI flag takes precedence
    [[ "$model" == "$DEFAULT_MODEL" ]] && model="$spec_model"

    local test_count
    test_count=$(yaml_test_count "$spec_file")

    header "Suite: $suite_name"
    log "Spec:  $spec_file"
    log "Model: $model"
    log "Tests: $test_count"
    echo ""

    if [[ "$dry_run" == "true" ]]; then
        log "Dry run — listing tests:"
        python3 -c "
import yaml, sys
with open(sys.argv[1]) as f:
    spec = yaml.safe_load(f)
for i, t in enumerate(spec.get('tests', [])):
    assertions = [a.get('type', '?') for a in t.get('assertions', [])]
    name = t.get('name', 'test_' + str(i))
    print('  [' + str(i+1) + '] ' + name + ' (' + ', '.join(assertions) + ')')
" "$spec_file"
        return 0
    fi

    local passed=0 failed=0 errors=0
    local run_timestamp
    run_timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    local results_tmp
    results_tmp=$(mktemp)
    echo "[]" > "$results_tmp"

    local i=0
    while [[ $i -lt $test_count ]]; do
        local test_name
        test_name=$(yaml_test_name "$spec_file" "$i")

        printf "  [%d/%d] %-40s" "$((i+1))" "$test_count" "$test_name"

        local result_json
        result_json=$(run_single_test "$spec_file" "$i" "$model" "$timeout" 2>&1) || {
            echo -e " ${RED}ERROR${RESET}"
            errors=$((errors + 1))
            i=$((i + 1))
            continue
        }

        local test_failed test_error test_latency
        test_failed=$(echo "$result_json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('failed',0))")
        test_error=$(echo "$result_json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('error') or '')")
        test_latency=$(echo "$result_json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('latency_ms') or 0)")

        if [[ -n "$test_error" ]]; then
            echo -e " ${RED}ERROR${RESET} — $test_error"
            errors=$((errors + 1))
        elif [[ "$test_failed" -gt 0 ]]; then
            echo -e " ${RED}FAIL${RESET}  (${test_latency}ms)"
            failed=$((failed + 1))
            if [[ "$verbose" == "true" ]]; then
                echo "$result_json" | python3 -c "
import json,sys
d=json.load(sys.stdin)
for a in d.get('assertions',[]):
    if a.get('status') == 'fail':
        print('    [' + a['type'] + '] ' + str(a.get('reason','')))
out = d.get('output','')
if out:
    print('    output: ' + repr(out[:200]))
"
            fi
        else
            echo -e " ${GREEN}PASS${RESET}  (${test_latency}ms)"
            passed=$((passed + 1))
        fi

        # Append to results array
        python3 -c "
import json, sys
existing = json.loads(open(sys.argv[1]).read())
existing.append(json.loads(sys.argv[2]))
open(sys.argv[1], 'w').write(json.dumps(existing))
" "$results_tmp" "$result_json"

        i=$((i + 1))
    done

    local total=$((passed + failed + errors))
    local pass_rate=0
    if [[ $total -gt 0 ]]; then
        pass_rate=$(python3 -c "print(round($passed / $total, 4))")
    fi

    local pass_pct
    pass_pct=$(python3 -c "print(f'{$pass_rate*100:.1f}%')")

    echo ""
    echo "─────────────────────────────────────────────────"
    echo -e "  Passed:  ${GREEN}${passed}${RESET}"
    echo -e "  Failed:  ${RED}${failed}${RESET}"
    [[ $errors -gt 0 ]] && echo -e "  Errors:  ${YELLOW}${errors}${RESET}"
    echo "  Rate:    $pass_pct"
    echo "─────────────────────────────────────────────────"

    # Write output file
    local save_file="$output_file"
    if [[ -z "$save_file" ]]; then
        mkdir -p "$RESULTS_DIR"
        local slug
        slug=$(echo "$suite_name" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd '[:alnum:]-')
        save_file="${RESULTS_DIR}/run-${slug}-$(date +%Y%m%d-%H%M%S).json"
    fi

    python3 -c "
import json, sys
save_file = sys.argv[1]
results_tmp = sys.argv[2]
suite = sys.argv[3]
spec_file = sys.argv[4]
model = sys.argv[5]
timestamp = sys.argv[6]
total = int(sys.argv[7])
passed = int(sys.argv[8])
failed = int(sys.argv[9])
errors = int(sys.argv[10])
pass_rate = float(sys.argv[11])
with open(results_tmp) as f:
    tests = json.load(f)
report = {
    'suite': suite, 'spec_file': spec_file, 'model': model,
    'timestamp': timestamp,
    'summary': {'total': total, 'passed': passed, 'failed': failed,
                'errors': errors, 'pass_rate': pass_rate},
    'tests': tests
}
with open(save_file, 'w') as f:
    json.dump(report, f, indent=2)
print(save_file)
" "$save_file" "$results_tmp" "$suite_name" "$spec_file" "$model" \
  "$run_timestamp" "$total" "$passed" "$failed" "$errors" "$pass_rate"

    rm -f "$results_tmp"
    log "Results saved: $save_file"

    # Check fail threshold
    local threshold_ok
    threshold_ok=$(python3 -c "print('yes' if $pass_rate >= $fail_threshold else 'no')")
    if [[ "$threshold_ok" == "no" ]]; then
        echo ""
        fail "Pass rate ${pass_pct} is below threshold ${fail_threshold}"
        exit 1
    fi

    [[ $failed -eq 0 && $errors -eq 0 ]]
}

# ── cmd_run_all ────────────────────────────────────────────────────────────────
cmd_run_all() {
    local suite_dir=""
    local extra_args=()

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --model|--fail-threshold|--output|--timeout)
                extra_args+=("$1" "$2"); shift 2 ;;
            --verbose|--dry-run)
                extra_args+=("$1"); shift ;;
            *)
                [[ -z "$suite_dir" ]] && suite_dir="$1"
                shift ;;
        esac
    done

    [[ -z "$suite_dir" ]] && die "No suite directory provided"
    [[ -d "$suite_dir" ]] || die "Suite directory not found: $suite_dir"

    local specs=()
    while IFS= read -r -d '' f; do
        specs+=("$f")
    done < <(find "$suite_dir" -name "test_spec.yaml" -print0 2>/dev/null | sort -z)

    if [[ ${#specs[@]} -eq 0 ]]; then
        warn "No test_spec.yaml files found in $suite_dir"
        exit 0
    fi

    header "Running ${#specs[@]} test suite(s)"

    local total_passed=0 total_failed=0

    local spec
    for spec in "${specs[@]}"; do
        if cmd_run "$spec" "${extra_args[@]:-}"; then
            total_passed=$((total_passed + 1))
        else
            total_failed=$((total_failed + 1))
        fi
        echo ""
    done

    header "All Suites Summary"
    echo -e "  Suites passed: ${GREEN}${total_passed}${RESET}"
    echo -e "  Suites failed: ${RED}${total_failed}${RESET}"

    [[ $total_failed -eq 0 ]]
}

# ── cmd_validate ───────────────────────────────────────────────────────────────
cmd_validate() {
    local spec_file="${1:-}"
    [[ -z "$spec_file" ]] && die "No spec file provided"
    [[ -f "$spec_file" ]] || die "Spec file not found: $spec_file"

    python3 -c "
import yaml, sys

VALID_TYPES = {
    'contains', 'not_contains', 'exact_match', 'fuzzy_match',
    'regex', 'json_valid', 'json_schema', 'not_empty',
    'max_length', 'min_length', 'llm_judge', 'rubric'
}

errors = []
warnings = []

with open(sys.argv[1]) as f:
    try:
        spec = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print('[error] Invalid YAML: ' + str(e))
        sys.exit(1)

if not isinstance(spec, dict):
    errors.append('Spec must be a YAML mapping')

if 'name' not in spec:
    warnings.append(\"Missing 'name' field\")

if 'tests' not in spec:
    errors.append(\"Missing required 'tests' field\")
elif not isinstance(spec['tests'], list) or len(spec['tests']) == 0:
    errors.append(\"'tests' must be a non-empty list\")
else:
    for i, test in enumerate(spec['tests']):
        if not isinstance(test, dict):
            errors.append('tests[' + str(i) + ']: must be a mapping')
            continue
        tname = test.get('name', '?')
        if 'input' not in test:
            warnings.append('tests[' + str(i) + '] (' + tname + '): missing input')
        if not test.get('assertions'):
            warnings.append('tests[' + str(i) + '] (' + tname + '): no assertions')
        else:
            for j, a in enumerate(test['assertions']):
                atype = a.get('type', '')
                if atype not in VALID_TYPES:
                    errors.append('tests[' + str(i) + '].assertions[' + str(j) + ']: unknown type ' + repr(atype))
                if atype == 'llm_judge' and 'criteria' not in a:
                    errors.append('tests[' + str(i) + '].assertions[' + str(j) + ']: llm_judge requires criteria')
                if atype in ('contains', 'not_contains', 'exact_match') and 'value' not in a:
                    errors.append('tests[' + str(i) + '].assertions[' + str(j) + ']: ' + atype + ' requires value')
                if atype == 'regex' and 'pattern' not in a:
                    errors.append('tests[' + str(i) + '].assertions[' + str(j) + ']: regex requires pattern')

for w in warnings:
    print('[warn]  ' + w)
for e in errors:
    print('[error] ' + e)

if errors:
    print('Validation FAILED (' + str(len(errors)) + ' errors, ' + str(len(warnings)) + ' warnings)')
    sys.exit(1)
else:
    count = len(spec.get('tests', []))
    msg = '[ok] Valid spec — ' + str(count) + ' test(s)'
    if warnings:
        msg += ' (' + str(len(warnings)) + ' warnings)'
    print(msg)
" "$spec_file"
}

# ── cmd_list ──────────────────────────────────────────────────────────────────
cmd_list() {
    local spec_file="${1:-}"
    [[ -z "$spec_file" ]] && die "No spec file provided"
    [[ -f "$spec_file" ]] || die "Spec file not found: $spec_file"

    python3 -c "
import yaml, sys
with open(sys.argv[1]) as f:
    spec = yaml.safe_load(f)
name = spec.get('name', 'Unnamed')
model = spec.get('model', 'default')
tests = spec.get('tests', [])
print('Suite: ' + name)
print('Model: ' + model)
print('Tests: ' + str(len(tests)))
print()
for i, t in enumerate(tests):
    assertions = [a.get('type', '?') for a in t.get('assertions', [])]
    tname = t.get('name', 'test_' + str(i))
    print('  [' + str(i+1).rjust(2) + '] ' + tname.ljust(40) + ' [' + ', '.join(assertions) + ']')
" "$spec_file"
}

# ── cmd_help ──────────────────────────────────────────────────────────────────
cmd_help() {
    cat <<'HELP'
prompt-test v1.0.0 — Prompt Testing Framework CLI

USAGE
  prompt-test.sh <command> [options]

COMMANDS
  run <spec.yaml>           Run a single test suite
  run-all <dir/>            Run all test_spec.yaml files in a directory
  validate <spec.yaml>      Validate a test spec without running it
  list <spec.yaml>          List tests in a spec file
  help                      Show this help

RUN OPTIONS
  --model <model>           Override model (default: claude-3-5-haiku-20241022)
  --verbose                 Print full output and assertion details on failure
  --fail-threshold <0-1>    Fail if pass rate below threshold (default: 1.0)
  --output <file>           Write JSON results to file
  --timeout <seconds>       Per-request timeout (default: 30)
  --dry-run                 List tests without executing

ENVIRONMENT
  ANTHROPIC_API_KEY         Required for Claude models
  OPENAI_API_KEY            Required for GPT models
  PTF_RESULTS_DIR           Directory for results output (default: ./results)

EXAMPLES
  ./framework/prompt-test.sh run test-suites/accuracy/test_spec.yaml
  ./framework/prompt-test.sh run test-suites/accuracy/test_spec.yaml --verbose
  ./framework/prompt-test.sh run-all test-suites/ --fail-threshold 0.9
  ./framework/prompt-test.sh validate test-suites/edge-cases/test_spec.yaml
  ./framework/prompt-test.sh list test-suites/accuracy/test_spec.yaml

MODELS
  claude-3-5-haiku-20241022    Fast, cheap (default)
  claude-3-5-sonnet-20241022   Balanced
  claude-opus-4-5              Most capable
  gpt-4o-mini                  OpenAI fast
  gpt-4o                       OpenAI capable

HELP
}

# ── Entry point ────────────────────────────────────────────────────────────────
main() {
    check_deps

    local command="${1:-help}"
    shift || true

    case "$command" in
        run)         cmd_run "$@" ;;
        run-all)     cmd_run_all "$@" ;;
        validate)    cmd_validate "$@" ;;
        list)        cmd_list "$@" ;;
        help|-h|--help) cmd_help ;;
        version|-v|--version) echo "prompt-test v$VERSION" ;;
        *) die "Unknown command: $command. Run 'prompt-test.sh help' for usage." ;;
    esac
}

main "$@"
