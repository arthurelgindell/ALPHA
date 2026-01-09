# ARTHUR Tailscale Network - User Guide

**Last Updated:** 2026-01-08
**Tested:** All services verified operational
**For:** Claude Code nodes and API consumers

---

## Quick Reference

| Service | URL | Purpose |
|---------|-----|---------|
| **Expert API** | `https://air.tail5f2bae.ts.net` | Claude Code expert channels |
| **LM Studio (ALPHA)** | `https://alpha.tail5f2bae.ts.net/v1` | Local LLM inference |
| **LM Studio (BETA)** | `https://beta.tail5f2bae.ts.net/v1` | Local LLM inference |
| **LanceDB** | `https://beta.tail5f2bae.ts.net:8443` | Vector database |

---

## 1. Network Overview

### Tailnet Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                    tail5f2bae.ts.net                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │     AIR     │    │    ALPHA    │    │    BETA     │         │
│  │ 100.79.73.73│    │100.76.246.64│    │100.117.121.73│        │
│  │   (macOS)   │    │   (macOS)   │    │   (macOS)   │         │
│  │             │    │             │    │             │         │
│  │ Expert API  │    │  LM Studio  │    │  LM Studio  │         │
│  │  :8080      │    │   :1234     │    │   :1234     │         │
│  │             │    │             │    │  LanceDB    │         │
│  │             │    │             │    │   :8000     │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                 │
│  ┌─────────────┐                                               │
│  │    GAMMA    │                                               │
│  │100.102.59.5 │                                               │
│  │   (Linux)   │                                               │
│  │             │                                               │
│  │  (compute)  │                                               │
│  └─────────────┘                                               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Node Roles

| Node | IP | OS | Role | Services |
|------|----|----|------|----------|
| **AIR** | 100.79.73.73 | macOS | Command Center | Expert API |
| **ALPHA** | 100.76.246.64 | macOS | Compute | LM Studio |
| **BETA** | 100.117.121.73 | macOS | Compute | LM Studio, LanceDB |
| **GAMMA** | 100.102.59.5 | Linux | Compute | General |

---

## 2. SSH Access

### Tailscale SSH (No Keys Required)

All nodes support identity-based SSH via Tailscale. No SSH keys needed.

```bash
# Access by hostname (MagicDNS)
ssh alpha
ssh beta
ssh gamma

# Access by FQDN
ssh alpha.tail5f2bae.ts.net

# Access by Tailscale IP
ssh 100.76.246.64
```

### Verify SSH Status

```bash
# Check if Tailscale SSH is enabled
tailscale status

# Should show nodes with no relay indicator for direct connections
```

---

## 3. Expert API (AIR)

The Expert API provides HTTP access to Claude Code expert channels.

### Base URL

```
https://air.tail5f2bae.ts.net
```

### Available Channels

| Channel | Purpose | Example Use |
|---------|---------|-------------|
| `claude-code` | Claude API, prompts, tools | Prompt review, tool design |
| `lm-studio` | Local LLM operations | Model listing, inference routing |
| `tailscale` | Network configuration | ACLs, serve status |

### API Endpoints

#### Health Check

```bash
curl https://air.tail5f2bae.ts.net/health
```

Response:
```json
{
  "status": "healthy",
  "channels": ["claude-code", "lm-studio", "tailscale"],
  "tasks": {"pending": 0, "running": 0, "completed": 5, "total": 5}
}
```

#### Submit a Task

```bash
curl -X POST https://air.tail5f2bae.ts.net/claude-code/task \
  -H "Content-Type: application/json" \
  -d '{"task": "What are Claude Code best practices for prompt engineering?"}'
```

Response:
```json
{
  "task_id": "a1b2c3d4",
  "channel": "claude-code",
  "status": "pending",
  "poll_url": "/status/a1b2c3d4"
}
```

#### Poll for Results

```bash
curl https://air.tail5f2bae.ts.net/status/a1b2c3d4
```

Response (when complete):
```json
{
  "task_id": "a1b2c3d4",
  "channel": "claude-code",
  "status": "completed",
  "result": "{ ... claude response ... }",
  "duration": 11.5,
  "submitted_by": "user@example.com"
}
```

#### Get Recent Tasks

```bash
curl https://air.tail5f2bae.ts.net/claude-code/recent?limit=5
```

#### List Channels

```bash
curl https://air.tail5f2bae.ts.net/channels
```

### Python Client Example

```python
import requests
import time

BASE_URL = "https://air.tail5f2bae.ts.net"

def ask_expert(channel: str, task: str, timeout: int = 300) -> dict:
    """Submit a task to an expert channel and wait for results."""

    # Submit task
    response = requests.post(
        f"{BASE_URL}/{channel}/task",
        json={"task": task, "timeout": timeout}
    )
    task_id = response.json()["task_id"]

    # Poll for results
    while True:
        status = requests.get(f"{BASE_URL}/status/{task_id}").json()
        if status["status"] in ["completed", "error"]:
            return status
        time.sleep(2)

# Example usage
result = ask_expert("claude-code", "Explain the Tool Use API")
print(result["result"])
```

---

## 4. LM Studio Integration

### Available Models

#### ALPHA Node

| Model | Type | Use Case |
|-------|------|----------|
| `glm-4.6v-flash` | Chat | Fast inference, general purpose |
| `nvidia-nemotron-3-nano-30b-a3b-mlx` | Chat | Higher quality, MLX optimized |
| `text-embedding-nomic-embed-text-v1.5` | Embeddings | 768-dimension vectors |

#### BETA Node

| Model | Type | Use Case |
|-------|------|----------|
| `nvidia/nemotron-3-nano` | Chat | Fast inference |
| `text-embedding-nomic-embed-text-v1.5` | Embeddings | 768-dimension vectors |

### API Endpoints

#### List Models

```bash
# ALPHA
curl https://alpha.tail5f2bae.ts.net/v1/models | jq '.data[].id'

# BETA
curl https://beta.tail5f2bae.ts.net/v1/models | jq '.data[].id'
```

#### Chat Completions

```bash
curl -X POST https://alpha.tail5f2bae.ts.net/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "glm-4.6v-flash",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

#### Embeddings

```bash
curl -X POST https://alpha.tail5f2bae.ts.net/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{
    "model": "text-embedding-nomic-embed-text-v1.5",
    "input": "Your text to embed"
  }'
```

### Python Client (OpenAI SDK Compatible)

```python
from openai import OpenAI

# Create client for ALPHA
alpha = OpenAI(
    base_url="https://alpha.tail5f2bae.ts.net/v1",
    api_key="not-needed"  # No auth required within tailnet
)

# Create client for BETA
beta = OpenAI(
    base_url="https://beta.tail5f2bae.ts.net/v1",
    api_key="not-needed"
)

# Chat completion
response = alpha.chat.completions.create(
    model="glm-4.6v-flash",
    messages=[{"role": "user", "content": "Hello!"}],
    max_tokens=100
)
print(response.choices[0].message.content)

# Embeddings
embeddings = alpha.embeddings.create(
    model="text-embedding-nomic-embed-text-v1.5",
    input=["Text to embed", "Another text"]
)
print(f"Dimensions: {len(embeddings.data[0].embedding)}")  # 768
```

### Load Balancing Example

```python
import random
from openai import OpenAI

NODES = [
    ("alpha", "https://alpha.tail5f2bae.ts.net/v1"),
    ("beta", "https://beta.tail5f2bae.ts.net/v1"),
]

def get_random_client():
    """Get a random LM Studio client for load distribution."""
    name, url = random.choice(NODES)
    return name, OpenAI(base_url=url, api_key="not-needed")

# Use random node
node, client = get_random_client()
print(f"Using {node}")
response = client.chat.completions.create(
    model="nvidia/nemotron-3-nano",  # Available on both
    messages=[{"role": "user", "content": "Hello"}]
)
```

---

## 5. LanceDB (Vector Database)

### Endpoint

```
https://beta.tail5f2bae.ts.net:8443
```

### Health Check

```bash
curl https://beta.tail5f2bae.ts.net:8443/health
```

### Python Client

```python
import lancedb

# Connect to remote LanceDB
db = lancedb.connect("https://beta.tail5f2bae.ts.net:8443")

# List tables
print(db.table_names())

# Create/access table
table = db.create_table("my_vectors", data=[
    {"id": 1, "vector": [0.1, 0.2, ...], "text": "Hello"}
])

# Search
results = table.search([0.1, 0.2, ...]).limit(10).to_list()
```

---

## 6. Service Discovery

### Check All Services

```bash
#!/bin/bash
# check-services.sh

echo "=== AIR - Expert API ==="
curl -s https://air.tail5f2bae.ts.net/health | jq -r '.status'

echo "=== ALPHA - LM Studio ==="
curl -s https://alpha.tail5f2bae.ts.net/v1/models | jq -r '.data | length' | xargs -I{} echo "{} models available"

echo "=== BETA - LM Studio ==="
curl -s https://beta.tail5f2bae.ts.net/v1/models | jq -r '.data | length' | xargs -I{} echo "{} models available"

echo "=== BETA - LanceDB ==="
curl -s https://beta.tail5f2bae.ts.net:8443/health && echo "healthy" || echo "not responding"
```

### Python Service Discovery

```python
import requests

SERVICES = {
    "expert_api": "https://air.tail5f2bae.ts.net/health",
    "lm_studio_alpha": "https://alpha.tail5f2bae.ts.net/v1/models",
    "lm_studio_beta": "https://beta.tail5f2bae.ts.net/v1/models",
    "lancedb": "https://beta.tail5f2bae.ts.net:8443/health",
}

def check_services():
    """Check all service health."""
    status = {}
    for name, url in SERVICES.items():
        try:
            r = requests.get(url, timeout=5)
            status[name] = "healthy" if r.ok else f"error: {r.status_code}"
        except Exception as e:
            status[name] = f"unreachable: {e}"
    return status

print(check_services())
```

---

## 7. Troubleshooting

### Connection Issues

```bash
# Check Tailscale status
tailscale status

# Check if node is reachable
tailscale ping alpha

# Check serve configuration on a node
ssh alpha "tailscale serve status"
```

### Service Not Responding

```bash
# Check if service is running on the node
ssh alpha "lsof -i :1234"  # LM Studio port
ssh air "lsof -i :8080"    # Expert API port

# Check service logs
ssh air "tail -50 /Users/arthurdell/ARTHUR/expert_api/api.log"
```

### SSL/TLS Errors

Tailscale Serve provides automatic HTTPS certificates. If you see certificate errors:

```bash
# Verify certificate
curl -v https://alpha.tail5f2bae.ts.net/v1/models 2>&1 | grep "subject:"

# Should show: subject: CN=alpha.tail5f2bae.ts.net
```

### Authentication

All services are internal to the tailnet - no additional authentication required. Your Tailscale identity is passed via headers:

```bash
# Check your identity
curl -s https://air.tail5f2bae.ts.net/health -v 2>&1 | grep Tailscale
```

---

## 8. For Claude Code Nodes

### Environment Setup

Add to your shell configuration:

```bash
# ~/.zshrc or ~/.bashrc

# Tailscale service endpoints
export EXPERT_API_URL="https://air.tail5f2bae.ts.net"
export LM_STUDIO_ALPHA="https://alpha.tail5f2bae.ts.net/v1"
export LM_STUDIO_BETA="https://beta.tail5f2bae.ts.net/v1"
export LANCEDB_URL="https://beta.tail5f2bae.ts.net:8443"
```

### Using Expert API from Claude Code

When running on any tailnet node, you can query the Expert API:

```python
import os
import requests

def ask_claude_expert(question: str) -> str:
    """Ask the Claude Code expert channel a question."""
    url = os.environ.get("EXPERT_API_URL", "https://air.tail5f2bae.ts.net")

    # Submit
    r = requests.post(f"{url}/claude-code/task", json={"task": question})
    task_id = r.json()["task_id"]

    # Poll
    import time
    while True:
        status = requests.get(f"{url}/status/{task_id}").json()
        if status["status"] == "completed":
            return status["result"]
        if status["status"] == "error":
            raise Exception(status["error"])
        time.sleep(2)
```

### Using Local LLMs from Claude Code

```python
from openai import OpenAI
import os

def get_local_llm():
    """Get a local LLM client."""
    return OpenAI(
        base_url=os.environ.get("LM_STUDIO_ALPHA", "https://alpha.tail5f2bae.ts.net/v1"),
        api_key="not-needed"
    )

# Quick inference without Claude API costs
llm = get_local_llm()
response = llm.chat.completions.create(
    model="glm-4.6v-flash",
    messages=[{"role": "user", "content": "Summarize this text..."}]
)
```

---

## 9. Security Notes

- **Internal Only:** All services are tailnet-only (not exposed to public internet)
- **Identity Headers:** Requests include `Tailscale-User-Login` for attribution
- **No API Keys:** Authentication handled by Tailscale identity
- **Encrypted:** All traffic encrypted via Tailscale's WireGuard mesh
- **SSH:** Identity-based, no key management required

---

## 10. Quick Test Script

Save and run to verify all services:

```bash
#!/bin/bash
# test-all-services.sh

echo "🔍 Testing ARTHUR Tailscale Services"
echo "====================================="

echo -n "Expert API (AIR): "
curl -sf https://air.tail5f2bae.ts.net/health | jq -r '.status' || echo "FAILED"

echo -n "LM Studio (ALPHA): "
curl -sf https://alpha.tail5f2bae.ts.net/v1/models | jq -r '.data | length' | xargs -I{} echo "{} models" || echo "FAILED"

echo -n "LM Studio (BETA): "
curl -sf https://beta.tail5f2bae.ts.net/v1/models | jq -r '.data | length' | xargs -I{} echo "{} models" || echo "FAILED"

echo -n "LanceDB (BETA): "
curl -sf https://beta.tail5f2bae.ts.net:8443/health > /dev/null && echo "healthy" || echo "FAILED"

echo -n "SSH to ALPHA: "
ssh -o ConnectTimeout=5 alpha "echo OK" 2>/dev/null || echo "FAILED"

echo -n "SSH to BETA: "
ssh -o ConnectTimeout=5 beta "echo OK" 2>/dev/null || echo "FAILED"

echo -n "SSH to GAMMA: "
ssh -o ConnectTimeout=5 gamma "echo OK" 2>/dev/null || echo "FAILED"

echo "====================================="
echo "✅ Tests complete"
```

---

## Appendix: Service Ports

| Node | Service | Internal Port | External URL |
|------|---------|---------------|--------------|
| AIR | Expert API | 8080 | `https://air.tail5f2bae.ts.net` |
| ALPHA | LM Studio | 1234 | `https://alpha.tail5f2bae.ts.net/v1` |
| BETA | LM Studio | 1234 | `https://beta.tail5f2bae.ts.net/v1` |
| BETA | LanceDB | 8000 | `https://beta.tail5f2bae.ts.net:8443` |
