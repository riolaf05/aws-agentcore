# 🚀 Quick Start - Multi-Agent System

## TL;DR

Sistema multi-agente con orchestratore che coordina:
- **Orchestrator**: Coordina gli altri agenti
- **Task Writer**: Crea task (✅ già deployato)
- **Task Reader**: Legge task (⏳ da deployare)
- **Researcher**: Cerca su internet (⏳ da deployare)
- **Calculator**: Calcola (✅ già deployato)

## ⚡ Deploy Rapido

### 1. Crea Gateway Target per GET tasks

```powershell
agentcore gateway create-mcp-gateway-target `
    --gateway-arn arn:aws:bedrock-agentcore:us-east-1:879338784410:gateway/taskapigateway-vveeifneus `
    --gateway-url https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp `
    --role-arn arn:aws:iam::879338784410:role/agentcore-taskapigateway-role `
    --name get-tasks `
    --target-type lambda `
    --region us-east-1 `
    --target-payload '{
      "lambdaArn": "arn:aws:lambda:us-east-1:879338784410:function:PersonalAssistant-TaskGet",
      "toolSchema": {
        "inlinePayload": [{
          "name": "get-tasks",
          "description": "Recupera task dal database. Supporta filtri per status, priority, category, due_date e tags.",
          "inputSchema": {
            "type": "object",
            "properties": {
              "status": {"type": "string", "description": "Filtra per status. Valori: pending, in_progress, completed, cancelled"},
              "priority": {"type": "string", "description": "Filtra per priorità. Valori: low, medium, high, urgent"},
              "category": {"type": "string", "description": "Filtra per categoria"},
              "due_date": {"type": "string", "description": "Filtra per scadenza. Valori: today, tomorrow, week, month, YYYY-MM-DD"},
              "tags": {"type": "string", "description": "Filtra per tag (separati da virgola)"},
              "limit": {"type": "number", "description": "Numero massimo risultati (default: 100)"}
            }
          }
        }]
      }
    }'
```

### 2. Deploy Researcher

```powershell
cd agents\researcher
pip install -r requirements.txt
python test_researcher.py
agentcore configure
agentcore launch
# Salva ARN: arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/researcher-XXXXX
```

### 3. Deploy Task Reader

```powershell
cd ..\task-reader
pip install -r requirements.txt
python test_task_reader.py
agentcore configure
agentcore launch
# Salva ARN: arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/task-reader-XXXXX
```

### 4. Aggiorna e Deploy Orchestrator

Apri [`agents\orchestrator\agent.py`](agents/orchestrator/agent.py) e aggiorna:

```python
AGENTS = {
    "task-writer": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/taskwriter-v5ts2W9Ghp",
    "task-reader": "ARN_DEL_TASK_READER",  # Inserisci qui
    "researcher": "ARN_DEL_RESEARCHER",    # Inserisci qui
    "calculator": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/calculator-lgV0vpGtcq"
}
```

Poi deploy:

```powershell
cd ..\orchestrator
pip install -r requirements.txt
agentcore configure
agentcore launch
```

### 5. Test

```powershell
# Test orchestrator
agentcore invoke '{"prompt": "Cerca informazioni su Docker e crea un task per studiarlo"}'

# Test task-reader
cd ..\task-reader
agentcore invoke '{"prompt": "Mostrami tutti i task con priorità alta"}'

# Test researcher
cd ..\researcher
agentcore invoke '{"prompt": "Cerca le novità di AWS Bedrock"}'
```

## 📋 Checklist

- [ ] Gateway Target `get-tasks` creato
- [ ] Researcher deployato (salva ARN)
- [ ] Task Reader deployato (salva ARN)
- [ ] Orchestrator aggiornato con ARN corretti
- [ ] Orchestrator deployato
- [ ] Test completati

## 🐛 Se qualcosa non funziona

1. **Gateway target non creato**: Verifica IAM permissions (vedi [MULTI_AGENT_SETUP.md](docs/MULTI_AGENT_SETUP.md))
2. **Agent deploy failed**: Controlla CloudWatch logs in `/aws/bedrock-agentcore/build/...`
3. **Orchestrator non trova agenti**: Verifica ARN in [`agent.py`](agents/orchestrator/agent.py)
4. **MCP connection failed**: Testa con [`scripts/test_mcp_gateway.py`](scripts/test_mcp_gateway.py)

Documentazione completa: [MULTI_AGENT_SETUP.md](docs/MULTI_AGENT_SETUP.md)
