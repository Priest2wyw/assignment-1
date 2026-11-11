#!/usr/bin/env bash
# Usage: source scripts/local/activate.sh (Bash)
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    echo "请用 source scripts/local/activate.sh 激活当前终端。" >&2
    exit 1
fi

_assignment_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
if [[ ! -x "$_assignment_root/.venv/bin/python" ]]; then
    echo "缺少 .venv，请先按 SETUP.zh-CN.md 完成安装。" >&2
    unset _assignment_root
    return 1
fi

source /home/youwei/anaconda3/etc/profile.d/conda.sh
conda activate "$_assignment_root/.local/conda-python" || return 1
source "$_assignment_root/.venv/bin/activate"

# Keep this assignment on its upstream lockfile and official package index.
export UV_NO_CONFIG=1
export UV_DEFAULT_INDEX=https://pypi.org/simple
export UV_INDEX_URL=https://pypi.org/simple
export UV_LOCKED=true
export UV_PYTHON="$_assignment_root/.local/conda-python/bin/python"
export UV_PROJECT_ENVIRONMENT="$_assignment_root/.venv"
export CONDA_PKGS_DIRS="$_assignment_root/.local/conda-pkgs"
export PATH="$HOME/.local/bin:$PATH"
cd -- "$_assignment_root" || return 1
unset _assignment_root
