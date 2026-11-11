#!/usr/bin/env bash
# Local, nonbillable checks; student TODO failures are reported separately.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/activate.sh"
log_dir="artifacts/local-setup/check-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$log_dir"

python --version | tee "$log_dir/python.log"
uv pip check --python .venv/bin/python 2>&1 | tee "$log_dir/dependencies.log"
make verify-sources 2>&1 | tee "$log_dir/sources.log"
uv run pytest tests/test_smoke.py tests/test_infrastructure.py -q 2>&1 | tee "$log_dir/infrastructure.log"

set +e
uv run assignment-doctor --offline 2>&1 | tee "$log_dir/doctor-offline.log"
doctor_status=${PIPESTATUS[0]}
make test 2>&1 | tee "$log_dir/tests.log"
test_status=${PIPESTATUS[0]}
set -e

printf '\n日志：%s\nDoctor 退出码：%s\n作业测试退出码：%s（初始 TODO 未实现时会失败）\n' "$log_dir" "$doctor_status" "$test_status"
if (( doctor_status != 0 || test_status != 0 )); then
    exit 1
fi
