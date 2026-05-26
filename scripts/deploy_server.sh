#!/bin/bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

REMOTE_PORT="${2:-8000}"
REMOTE_DIR="~/tfg_llm_server"
MODELS=("llama3.2:latest" "mistral:7b" "llama3:8b")

if [ $# -ge 3 ]; then
    API_KEY="$3"
elif [ -n "${TFG_API_KEY:-}" ]; then
    API_KEY="${TFG_API_KEY}"
else
    API_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo -e "${YELLOW}Generated new API key: ${API_KEY}${NC}"
    echo -e "${YELLOW}Save this key! Add it to tfg.env as TFG_API_KEY${NC}"
fi

if [ $# -lt 1 ]; then
    echo -e "${RED}Usage: $0 <user@host> [port] [api-key]${NC}"
    echo "Example: $0 student@servidor.uni.es 8000 my-secret-key"
    echo ""
    echo "Environment variables:"
    echo "  TFG_API_KEY  - Shared API key (generated if not set)"
    exit 1
fi

REMOTE_HOST="$1"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} TFG RAG - Remote LLM Server Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Target: ${REMOTE_HOST}"
echo "Port:   ${REMOTE_PORT}"
echo "Dir:    ${REMOTE_DIR}"
echo ""

echo -e "${YELLOW}[1/5] Copying server files...${NC}"
ssh "${REMOTE_HOST}" "mkdir -p ${REMOTE_DIR}"
scp scripts/llm_server.py "${REMOTE_HOST}:${REMOTE_DIR}/llm_server.py"
echo -e "${GREEN}  ✓ Files copied${NC}"

echo -e "${YELLOW}[2/5] Installing Python dependencies...${NC}"
ssh "${REMOTE_HOST}" << 'DEPS_EOF'
cd ~/tfg_llm_server
python3 -m pip install --user fastapi uvicorn pydantic 2>/dev/null || \
    pip3 install --user fastapi uvicorn pydantic
echo "  Dependencies installed"
DEPS_EOF
echo -e "${GREEN}  ✓ Dependencies installed${NC}"

echo -e "${YELLOW}[3/5] Checking Ollama...${NC}"
ssh "${REMOTE_HOST}" << 'OLLAMA_EOF'
if command -v ollama &> /dev/null; then
    echo "  Ollama already installed: $(ollama --version 2>/dev/null || echo 'version unknown')"
else
    echo "  Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "  Ollama installed"
fi

# Ensure Ollama is serving
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "  Starting Ollama..."
    nohup ollama serve > /dev/null 2>&1 &
    sleep 3
fi
echo "  Ollama is running"
OLLAMA_EOF
echo -e "${GREEN}  ✓ Ollama ready${NC}"

echo -e "${YELLOW}[4/5] Pulling LLM models...${NC}"
for model in "${MODELS[@]}"; do
    echo "  Pulling ${model}..."
    ssh "${REMOTE_HOST}" "ollama pull ${model}" || echo "  Warning: Failed to pull ${model}"
done
echo -e "${GREEN}  ✓ Models ready${NC}"

echo -e "${YELLOW}[5/5] Starting LLM server...${NC}"
ssh "${REMOTE_HOST}" << SERVE_EOF
cd ~/tfg_llm_server

# Kill existing server if running
pkill -f "llm_server.py" 2>/dev/null || true
sleep 1

# Start server in background with API key
export TFG_API_KEY="${API_KEY}"
nohup python3 -m uvicorn llm_server:app \
    --host 0.0.0.0 \
    --port ${REMOTE_PORT} \
    > server.log 2>&1 &

sleep 2

# Verify server is running
if curl -s "http://localhost:${REMOTE_PORT}/health" > /dev/null 2>&1; then
    echo "  Server started successfully"
else
    echo "  Warning: Server may not have started. Check server.log"
fi
SERVE_EOF
echo -e "${GREEN}  ✓ Server started${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Server URL:  http://${REMOTE_HOST##*@}:${REMOTE_PORT}"
echo "Health:      http://${REMOTE_HOST##*@}:${REMOTE_PORT}/health"
echo "API Docs:    http://${REMOTE_HOST##*@}:${REMOTE_PORT}/docs"
echo "Models:      http://${REMOTE_HOST##*@}:${REMOTE_PORT}/models"
echo ""
echo -e "${YELLOW}API Key:     ${API_KEY}${NC}"
echo ""
echo "IMPORTANT: Update the following in src/pipeline/__init__.py:"
echo "  REMOTE_LLM_URL = \"http://${REMOTE_HOST##*@}:${REMOTE_PORT}\""
echo "  REMOTE_API_KEY = \"${API_KEY}\""
echo ""
echo "To use in pipeline:"
echo "  python3 scripts/run_pipeline.py --config 4"
echo "  (or --config 5 for optimized remote)"
echo ""
echo "To test authentication:"
echo "  curl -X POST http://${REMOTE_HOST##*@}:${REMOTE_PORT}/generate \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -H 'X-API-Key: ${API_KEY}' \\"
echo "    -d '{\"prompt\": \"Hello\", \"model\": \"llama3:8b\"}'"
echo ""
echo "To check logs on server:"
echo "  ssh ${REMOTE_HOST} 'tail -f ${REMOTE_DIR}/server.log'"
echo ""
echo "To stop server:"
echo "  ssh ${REMOTE_HOST} 'pkill -f llm_server.py'"




