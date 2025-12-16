# Setup Multi-Agent System - Guida Completa

## 📋 Panoramica

Sistema multi-agente coordinato con 5 agenti specializzati:

1. **Orchestrator** - Coordina gli altri agenti usando boto3 `invoke_agent_runtime`
2. **Task Writer** - Crea task su DynamoDB (via Gateway MCP → Lambda POST)
3. **Task Reader** - Legge task da DynamoDB (via Gateway MCP → Lambda GET)  
4. **Researcher** - Ricerca web con DuckDuckGo (regione Italia)
5. **Calculator** - Calcoli matematici (con memoria STM + LTM) ✅ già deployato

## 🎯 Prerequisiti

- AWS Account configurato
- Bedrock AgentCore SDK installato: `pip install bedrock-agentcore`
- AWS CLI configurato
- CDK installato: `npm install -g aws-cdk`
- Python 3.11+

## 🚀 Deployment da Zero

### Passo 1: Deploy Infrastruttura AWS (Lambda + DynamoDB)

```powershell
cd C:\Users\r.laface\Desktop\Codice\aws-agentcore\infrastructure\cdk-app

cdk deploy
```

**Risorse create:**
- DynamoDB table: `PersonalTasks`
- Lambda: `PersonalAssistant-TaskPost`
- Lambda: `PersonalAssistant-TaskGet`

### Passo 2: Crea Gateway MCP Target per GET Tasks

Il target `save-task` (POST) dovrebbe già esistere. Aggiungi il GET:

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

### Passo 3: Verifica Gateway Tools

```powershell
cd C:\Users\r.laface\Desktop\Codice\aws-agentcore\scripts

python test_mcp_gateway.py
```

**Output atteso:**
```json
{
  "tools": [
    {"name": "save-task___save-task"},
    {"name": "get-tasks___get-tasks"},
    {"name": "x_amz_bedrock_agentcore_search"}
  ]
}
```

### Passo 4: Deploy Researcher Agent

```powershell
cd ..\agents\researcher

pip install -r requirements.txt

python test_researcher.py

agentcore configure --entrypoint .\agent.py --name researcher

agentcore launch
```

**Salva l'ARN:** `arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/researcher-XXXXX`

### Passo 5: Deploy Task Reader Agent

```powershell
cd ..\task-reader

pip install -r requirements.txt

python test_task_reader.py

agentcore configure --entrypoint .\agent.py --name task-reader

agentcore launch
```

**Salva l'ARN:** `arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/task_reader-XXXXX`

### Passo 6: Aggiorna e Deploy Orchestrator

**6.1 Aggiorna ARN in agent.py:**

Apri `agents\orchestrator\agent.py` e modifica:

```python
AGENTS = {
    "task-writer": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/taskwriter-v5ts2W9Ghp",
    "task-reader": "ARN_PASSO_5",
    "researcher": "ARN_PASSO_4",
    "calculator": "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/calculator-lgV0vpGtcq"
}
```

**6.2 Deploy:**

```powershell
cd ..\orchestrator

pip install -r requirements.txt

python agent.py

agentcore configure --entrypoint .\agent.py --name orchestrator

agentcore launch
```

## ✅ Test del Sistema

### Test Singoli Agenti

```powershell
cd agents\researcher
agentcore invoke "{`"prompt`": `"Cerca le ultime novità su AWS Bedrock`"}"

cd ..\task-reader
agentcore invoke "{`"prompt`": `"Mostrami i task con priorità alta`"}"

cd ..\task-writer
agentcore invoke "{`"prompt`": `"Crea un task per studiare Python async`"}"
```

### Test Orchestrator (Multi-Agente)

```powershell
cd ..\orchestrator

agentcore invoke "{`"prompt`": `"Crea un task per comprare il pane`"}"

agentcore invoke "{`"prompt`": `"Cerca le novità di Python 3.13, poi crea un task per studiarle`"}"

agentcore invoke "{`"prompt`": `"Mostrami i task completati e conta quanti sono`"}"
```

## 🧹 Cleanup - Rimuovi Tutto

### 1. Elimina Agenti

```powershell
agentcore list

agentcore delete --agent-id orchestrator-XXXXX
agentcore delete --agent-id researcher-XXXXX
agentcore delete --agent-id task_reader-XXXXX
agentcore delete --agent-id taskwriter-v5ts2W9Ghp
agentcore delete --agent-id calculator-lgV0vpGtcq
```

### 2. Rimuovi Gateway Targets

Console AWS → Bedrock AgentCore → Gateway → taskapigateway-vveeifneus → Targets → Delete

### 3. Elimina Infrastruttura

```powershell
cd infrastructure\cdk-app

cdk destroy
```

### 4. Cleanup Manuale

```powershell
aws logs delete-log-group --log-group-name /aws/bedrock-agentcore/runtime/orchestrator-XXXXX
aws logs delete-log-group --log-group-name /aws/bedrock-agentcore/runtime/researcher-XXXXX
aws logs delete-log-group --log-group-name /aws/bedrock-agentcore/runtime/task_reader-XXXXX

aws ecr delete-repository --repository-name bedrock-agentcore-orchestrator --force
aws ecr delete-repository --repository-name bedrock-agentcore-researcher --force
aws ecr delete-repository --repository-name bedrock-agentcore-task-reader --force

aws dynamodb delete-table --table-name PersonalTasks
```

### 5. Verifica

```powershell
agentcore list

aws lambda list-functions --query 'Functions[?contains(FunctionName, `PersonalAssistant`)].FunctionName'

aws dynamodb list-tables
```

## 🐛 Troubleshooting

**AccessDeniedException su CreateGatewayTarget**
→ Aggiungi policy IAM con permessi `bedrock-agentcore:*GatewayTarget*`

**Agent not found nell'Orchestrator**
→ Verifica ARN con `agentcore list` e aggiorna `AGENTS` in agent.py

**MCP connection failed**
→ Testa con `scripts/test_mcp_gateway.py`

**Lambda timeout**
→ Aumenta timeout in CDK: `timeout: Duration.seconds(60)`, poi `cdk deploy`
