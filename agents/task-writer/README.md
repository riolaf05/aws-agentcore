# TaskWriter Agent

Agente AWS Bedrock AgentCore per la creazione e gestione di task in DynamoDB tramite Gateway MCP.

## Caratteristiche

- ✅ **Integrazione MCP**: Utilizza il Gateway MCP per comunicare con Lambda functions
- ✅ **DynamoDB**: Scrive e legge task da DynamoDB tramite API Lambda
- ✅ **OAuth2 Cognito**: Autenticazione sicura con AWS Cognito
- ✅ **Senza Memoria**: Agente stateless per operazioni CRUD semplici
- ✅ **ARM64**: Ottimizzato per AWS Graviton (performance migliori)

## Architettura

```
User Request
    ↓
TaskWriter Agent (Bedrock AgentCore)
    ↓
Gateway MCP (taskapigateway-vveeifneus)
    ↓
Lambda Functions (task-api-post, task-api-get)
    ↓
DynamoDB (tasks-table)
```

## Strumenti Disponibili

### 1. create_task_in_dynamodb
Crea un nuovo task in DynamoDB.

**Parametri:**
- `title` (str): Titolo del task
- `description` (str): Descrizione dettagliata
- `priority` (str): Priorità (low, medium, high)

**Esempio:**
```python
create_task_in_dynamodb(
    title="Implementare autenticazione",
    description="Aggiungere OAuth2 flow con Cognito",
    priority="high"
)
```

### 2. list_tasks_from_dynamodb
Recupera un elenco di task da DynamoDB.

**Parametri:**
- `status` (str, opzionale): Filtra per status (pending, in_progress, completed)
- `limit` (int): Numero massimo di task da recuperare (default: 10)

**Esempio:**
```python
list_tasks_from_dynamodb(status="pending", limit=5)
```

## Configurazione

### Variabili d'Ambiente

Le seguenti variabili sono configurate in `.bedrock_agentcore.yaml`:

```yaml
environment:
  variables:
    GATEWAY_MCP_URL: https://taskapigateway-vveeifneus.gateway...
    GATEWAY_CLIENT_ID: 40ipvfb7kr5hnjqm06555e5hlp
    GATEWAY_CLIENT_SECRET: # Da configurare
    PYTHONPATH: /app/src
    LOG_LEVEL: INFO
```

### Gateway MCP

- **Gateway ID**: taskapigateway-vveeifneus
- **URL**: https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp
- **Cognito User Pool**: us-east-1_F8frcQSD7
- **Client ID**: 40ipvfb7kr5hnjqm06555e5hlp

### Permessi IAM

L'agente richiede i seguenti permessi (configurati automaticamente):

1. **Gateway MCP**: InvokeGateway, GetGateway
2. **Lambda**: InvokeFunction per task-api-*
3. **DynamoDB**: PutItem, GetItem, Query, Scan, UpdateItem
4. **Cognito**: InitiateAuth, GetUser
5. **CloudWatch**: Logs
6. **Secrets Manager**: GetSecretValue per client secret

## Deployment

### 1. Build e Deploy su AWS

```powershell
cd agents/task-writer
agentcore launch
```

### 2. Test dell'Agente

```powershell
# Crea un nuovo task
agentcore invoke '{"prompt": "Crea un task: implementare API REST con priorità alta"}'

# Lista task
agentcore invoke '{"prompt": "Mostrami tutti i task pending"}'
```

### 3. Monitoraggio

```powershell
# Visualizza logs in tempo reale
aws logs tail /aws/bedrock-agentcore/runtimes/taskwriter-* --follow

# Visualizza status
agentcore status
```

## Test Locale

```powershell
# Attiva virtual environment
& .venv\Scripts\Activate.ps1

# Installa dipendenze
cd agents/task-writer
pip install -r requirements.txt

# Esegui localmente
cd src/task_writer_agent
python agent.py

# Testa con curl
curl http://localhost:8080/invocations -X POST -H "Content-Type: application/json" -d '{\"prompt\": \"Crea un task di test\"}'
```

## TODO

- [ ] Implementare `fetch_access_token()` con Cognito OAuth2
- [ ] Creare client secret in Secrets Manager
- [ ] Verificare i nomi degli strumenti MCP nel gateway
- [ ] Aggiungere retry logic per chiamate Lambda
- [ ] Implementare update e delete task
- [ ] Aggiungere validazione input

## Risorse

- [Gateway MCP Configuration](../../docs/GATEWAY_SETUP.md)
- [Lambda Functions](../../lambdas/task-api/)
- [DynamoDB Schema](../../docs/DYNAMODB_SCHEMA.md)
- [Cognito Authentication](../../docs/GATEWAY_IMPLEMENTATION.md)
