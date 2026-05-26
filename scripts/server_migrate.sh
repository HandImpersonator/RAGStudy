#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

ok()   { echo -e "${GREEN}  ✓ $*${NC}"; }
info() { echo -e "${CYAN}  → $*${NC}"; }
warn() { echo -e "${YELLOW}  ⚠ $*${NC}"; }
err()  { echo -e "${RED}  ✗ $*${NC}" >&2; }
step() { echo -e "\n${BOLD}[${1}] ${2}${NC}"; }

SSH_PORT=22
TRANSFER_HF_CACHE=false
SKIP_HF_DOWNLOAD=true
SKIP_SERVER_RESTART=false
PULL_RESULTS=false
PULL_CACHE=false
PULL_BACKUP=false

REMOTE_PROJECT_DIR="~/TFG"
LOCAL_PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ $# -lt 1 ]]; then
    echo -e "${RED}Usage: $0 user@host [-p PORT] [--hf-cache] [--no-hf-dl] [--skip-server] [--pull]${NC}"
    exit 1
fi

REMOTE_HOST="$1"
shift

while [[ $# -gt 0 ]]; do
    case "$1" in
        -p|--port)       SSH_PORT="$2"; shift 2 ;;
        --hf-cache)      TRANSFER_HF_CACHE=true; shift ;;
        --no-hf-dl)      SKIP_HF_DOWNLOAD=true; shift ;;
        --skip-server)   SKIP_SERVER_RESTART=true; shift ;;
        --pull)          PULL_RESULTS=true; shift ;;
        --pull-cache)    PULL_CACHE=true; shift ;;
        --pull-backup)   PULL_BACKUP=true; shift ;;
        *) err "Unknown option: $1"; exit 1 ;;
    esac
done

SSH_OPTS=(-p "$SSH_PORT" -o ServerAliveInterval=30 -o ServerAliveCountMax=5 -i /home/stic/.ssh/tensordock_ed25519)
RSYNC_SSH="ssh -p ${SSH_PORT} -o ServerAliveInterval=30 -i /home/stic/.ssh/tensordock_ed25519"

if [[ "$PULL_CACHE" == "true" ]]; then
    echo -e "${BOLD}======================================================${NC}"
    echo -e "${BOLD}  PULLING CACHE (JSON FILES ONLY) FROM SERVER${NC}"
    echo -e "${BOLD}======================================================${NC}"
    info "Source: ${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/.cache/rag/"
    info "Dest:   ${LOCAL_PROJECT_ROOT}/.cache/rag/"
    info "Only *.json files are transferred (no .pkl / .faiss / .jsonl artifacts)."
    
    rsync -avz --progress \
        --include="*/" \
        --include="*.json" \
        --exclude="*" \
        -e "${RSYNC_SSH}" \
        "${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/.cache/rag/" \
        "${LOCAL_PROJECT_ROOT}/.cache/rag/"

    ok "Cache JSON files pulled successfully."
    info "Run the backfill script to patch old experiment logs:"
    info "  python3 scripts/backfill_timing_metrics.py --dry-run"
    info "  python3 scripts/backfill_timing_metrics.py"
    exit 0
fi

if [[ "$PULL_RESULTS" == "true" ]]; then
    echo -e "${BOLD}======================================================${NC}"
    echo -e "${BOLD}  PULLING RESULTS FROM SERVER${NC}"
    echo -e "${BOLD}======================================================${NC}"
    info "Source: ${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/logs/"
    info "Source: ${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/output/"
    info "Dest:   ${LOCAL_PROJECT_ROOT}/"

    rsync -avz --progress \
        -e "${RSYNC_SSH}" \
        "${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/logs/" \
        "${LOCAL_PROJECT_ROOT}/logs/"

    rsync -avz --progress \
        -e "${RSYNC_SSH}" \
        "${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/output/" \
        "${LOCAL_PROJECT_ROOT}/output/"

    ok "Results pulled successfully."
    exit 0
fi

if [[ "$PULL_BACKUP" == "true" ]]; then
    PULL_TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
    PULL_BACKUP_DIR="${LOCAL_PROJECT_ROOT}/backup/server_pull_${PULL_TIMESTAMP}"

    echo -e "${BOLD}======================================================${NC}"
    echo -e "${BOLD}  PULLING RESULTS FROM SERVER INTO BACKUP FOLDER${NC}"
    echo -e "${BOLD}======================================================${NC}"
    info "Source: ${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/logs/"
    info "Source: ${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/output/"
    info "Dest:   ${PULL_BACKUP_DIR}/"

    mkdir -p "${PULL_BACKUP_DIR}/logs"
    mkdir -p "${PULL_BACKUP_DIR}/output"

    rsync -avz --progress \
        -e "${RSYNC_SSH}" \
        "${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/logs/" \
        "${PULL_BACKUP_DIR}/logs/"

    rsync -avz --progress \
        -e "${RSYNC_SSH}" \
        "${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/output/" \
        "${PULL_BACKUP_DIR}/output/"

    ok "Results pulled successfully into backup folder:"
    info "${PULL_BACKUP_DIR}"
    exit 0
fi

echo -e "${BOLD}======================================================${NC}"
echo -e "${BOLD}  TFG RAG - SERVER MIGRATION${NC}"
echo -e "${BOLD}======================================================${NC}"
echo ""
echo "  Remote host : ${REMOTE_HOST}"
echo "  SSH port    : ${SSH_PORT}"
echo "  Remote dir  : ${REMOTE_PROJECT_DIR}"
echo "  HF cache    : $([ "$TRANSFER_HF_CACHE" = true ] && echo 'rsync from local' || echo 'download on server')"
echo ""

step "1/6" "Verify SSH connectivity"
if ! ssh "${SSH_OPTS[@]}" "${REMOTE_HOST}" "echo ok" > /dev/null 2>&1; then
    err "Cannot reach ${REMOTE_HOST} on port ${SSH_PORT}."
    err "Check SSH access before running this script."
    exit 1
fi
ok "SSH connection verified."

step "2/6" "Rsync project → server (source + corpus + eval, no logs/output/docs/cache)"
info "Transferring project files (~300 MB - corpus + code + eval)..."

rsync -avz --progress \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.git/' \
    --exclude '.idea/' \
    --exclude '.cache/' \
    --exclude 'logs/' \
    --exclude 'backup/' \
    --exclude 'output/' \
    --exclude 'data/' \
    --exclude 'docs/' \
    -e "${RSYNC_SSH}" \
    "${LOCAL_PROJECT_ROOT}/" \
    "${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/"

ok "Project synced to ${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/"

step "3/6" "Install Python dependencies on server"
info "Running pip install -r requirements.txt on server..."

ssh "${SSH_OPTS[@]}" "${REMOTE_HOST}" bash <<'DEPS'
set -euo pipefail
cd ~/TFG
echo "  Python: $(python3 --version)"

# Prefer pip3; fall back to pip
PIP="$(command -v pip3 2>/dev/null || command -v pip)"

# Install without upgrading system packages; --user if no venv
$PIP install --quiet --user -r requirements.txt

echo "  Dependencies installed."

# Verify critical imports - including scipy/numpy ABI compatibility.
# System scipy (apt/dnf, typically 1.7-1.9) breaks with pip numpy>=2.0
# because numpy.core was removed. The pip scipy must shadow the system one.
python3 -c "
import importlib, sys

missing = []
for mod in ['numpy', 'faiss', 'sentence_transformers', 'rank_bm25']:
    try:
        importlib.import_module(mod)
    except ImportError:
        missing.append(mod)
if missing:
    print('MISSING:', missing)
    sys.exit(1)

# Explicit scipy ABI check - catches numpy 2.x + old system scipy clash
try:
    from scipy.sparse import csr_matrix
except ImportError as e:
    print(f'scipy/numpy ABI conflict: {e}')
    print('Fix: pip install --user \"scipy>=1.14.0\"')
    sys.exit(1)

print('Core imports OK.')
"
DEPS

ok "Python dependencies installed and verified."

step "4/6" "Restart llm_server.py from project directory"

if [[ "$SKIP_SERVER_RESTART" == "true" ]]; then
    warn "Skipping server restart (--skip-server). Make sure it is already running."
else
    info "Stopping any existing llm_server.py process..."
    ssh "${SSH_OPTS[@]}" "${REMOTE_HOST}" bash <<'SERVERSTOP'
pkill -f "llm_server" 2>/dev/null && echo "  Old server process killed." || echo "  No existing process found."
sleep 2
SERVERSTOP

    info "Starting llm_server.py from project directory (reads tfg.env for config)..."
    ssh "${SSH_OPTS[@]}" "${REMOTE_HOST}" bash <<'SERVERSTART'
set -euo pipefail
cd ~/TFG

# Parse TFG_API_KEY from tfg.env (no python-dotenv dependency)
TFG_API_KEY_VALUE=$(grep -E '^TFG_API_KEY=' tfg.env | cut -d= -f2- | tr -d '[:space:]')
if [[ -z "$TFG_API_KEY_VALUE" ]]; then
    echo "  WARNING: TFG_API_KEY not found in tfg.env, using placeholder."
    TFG_API_KEY_VALUE="tfg-rag-2026-shared-secret-change-me"
fi

# Start server in background; logs to ~/TFG/logs/llm_server.log
mkdir -p logs
nohup env TFG_API_KEY="${TFG_API_KEY_VALUE}" \
    python3 scripts/llm_server.py \
    > logs/llm_server.log 2>&1 &

echo "  Server PID: $!"
sleep 3

# Quick health check
if curl -s http://localhost:8000/health -X POST \
    -H 'Content-Type: application/json' \
    -d '{}' > /dev/null 2>&1; then
    echo "  Server health check passed."
else
    echo "  WARNING: Health check did not respond (server may still be starting)."
    echo "  Check ~/TFG/logs/llm_server.log"
fi
SERVERSTART

    ok "llm_server.py started. Server log: ${REMOTE_HOST}:~/TFG/logs/llm_server.log"
fi

step "5/6" "HuggingFace models"

if [[ "$TRANSFER_HF_CACHE" == "true" ]]; then
    info "Rsyncing local HF cache to server (~6.9 GB, this will take a while)..."
    LOCAL_HF_CACHE="${HOME}/.cache/huggingface/"
    if [[ ! -d "$LOCAL_HF_CACHE" ]]; then
        err "Local HF cache not found at ${LOCAL_HF_CACHE}"
        err "Run python3 scripts/preload_models.py locally first."
        exit 1
    fi
    rsync -avz --progress \
        -e "${RSYNC_SSH}" \
        "${LOCAL_HF_CACHE}" \
        "${REMOTE_HOST}:~/.cache/huggingface/"
    ok "HF cache transferred."
fi

if [[ "$SKIP_HF_DOWNLOAD" == "false" ]]; then
    info "Running preload_models.py on server (downloads/validates all HF models)..."
    info "This may take several minutes if models are not cached."
    ssh "${SSH_OPTS[@]}" "${REMOTE_HOST}" bash <<'PRELOAD'
set -euo pipefail
cd ~/TFG
python3 scripts/preload_models.py
PRELOAD
    ok "HF models preloaded and validated."
else
    warn "Skipping preload_models.py (--no-hf-dl). Ensure the HF cache is present on server."
fi

step "6/6" "Smoke test - dry run on server"
info "Running quick dry-run to verify the full pipeline initialises correctly..."

ssh "${SSH_OPTS[@]}" "${REMOTE_HOST}" bash <<'SMOKETEST'
set -euo pipefail
cd ~/TFG
export HF_HUB_OFFLINE=1

python3 scripts/run_retriever_comparison.py \
    --dataset hotpotqa \
    --max-samples 2 \
    --dry-run \
    2>&1 | tail -20
SMOKETEST

ok "Smoke test passed."

echo ""
echo -e "${BOLD}======================================================${NC}"
echo -e "${GREEN}${BOLD}  MIGRATION COMPLETE${NC}"
echo -e "${BOLD}======================================================${NC}"
echo ""
echo "  Project on server : ${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/"
echo "  Server log        : ${REMOTE_HOST}:${REMOTE_PROJECT_DIR}/logs/llm_server.log"
echo ""
echo -e "${BOLD}Run experiments on server:${NC}"
echo ""
echo "  ssh ${REMOTE_HOST} -p ${SSH_PORT}"
echo "  cd ~/TFG"
echo "  export HF_HUB_OFFLINE=1"
echo "  python3 scripts/run_retriever_comparison.py \\"
echo "      --dataset hotpotqa --max-samples 10"
echo ""
echo -e "${BOLD}Or run in the background and detach:${NC}"
echo ""
echo "  ssh ${REMOTE_HOST} -p ${SSH_PORT}"
echo "  cd ~/TFG && export HF_HUB_OFFLINE=1"
echo "  nohup python3 scripts/run_retriever_comparison.py \\"
echo "      --dataset hotpotqa --max-samples 10 \\"
echo "      > logs/run_\$(date +%Y%m%d_%H%M%S).log 2>&1 &"
echo "  echo \"PID: \$!\""
echo ""
echo -e "${BOLD}Pull results back when done:${NC}"
echo ""
echo "  ./scripts/server_migrate.sh ${REMOTE_HOST} -p ${SSH_PORT} --pull"
echo ""
echo -e "${BOLD}Pull cache JSON files for timing backfill:${NC}"
echo ""
echo "  ./scripts/server_migrate.sh ${REMOTE_HOST} -p ${SSH_PORT} --pull-cache"
echo "  python3 scripts/backfill_timing_metrics.py --dry-run"
echo "  python3 scripts/backfill_timing_metrics.py"
echo ""

