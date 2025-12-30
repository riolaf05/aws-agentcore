# Task Reader Agent

## Descrizione

Agente specializzato nella lettura e recupero di task dal database DynamoDB tramite Gateway MCP.

## Caratteristiche

- **Gateway MCP**: Si connette al Gateway per accedere alla Lambda GET
- **OAuth2**: Autenticazione tramite Cognito
- **Filtri Avanzati**: Supporta filtri per status, priority, category, due_date, tags
- **No Memory**: Stateless, ogni invocazione è indipendente

## Setup

```powershell
pip install -r requirements.txt

# Test locale
python test_task_reader.py

# Deploy
agentcore launch
```

## Tool Disponibili

Il tool `get-tasks` supporta questi parametri:

- `status`: pending | in_progress | completed | cancelled
- `priority`: low | medium | high | urgent
- `category`: work | personal | learning | etc.
- `due_date`: today | tomorrow | week | month | YYYY-MM-DD
- `tags`: comma-separated (es: "python,aws")
- `limit`: max risultati (default: 100)

## Esempi

### Tutti i task

```json
{"prompt": "Mostrami tutti i task"}
```

### Task con priorità alta

```json
{"prompt": "Dammi i task con priorità alta"}
```

### Task in scadenza

```json
{"prompt": "Quali task scadono questa settimana?"}
```

## Configurazione Gateway

Il tool viene esposto tramite Gateway Target:

```powershell
agentcore gateway create-mcp-gateway-target \
  --name get-tasks \
  --target-type lambda \
  --target-payload '{"lambdaArn": "arn:aws:lambda:us-east-1:...:function:PersonalAssistant-TaskGet", ...}'
```

Vedi [MULTI_AGENT_SETUP.md](../../docs/MULTI_AGENT_SETUP.md) per dettagli completi.

# WebSocket Agent & Echo Server

## Descrizione

Agente e server WebSocket di esempio per testare la comunicazione bi-direzionale con Node.js.

## File principali
- `server.js`: WebSocket server (Node.js)
- `client.js`: WebSocket client (Node.js)
- `Dockerfile`: per containerizzare il server

## Setup

```bash
npm install express ws
```

## Avvio server

```bash
node server.js
```

## Avvio client (in altro terminale)

```bash
node client.js
```

## Test
Il client invia un messaggio JSON, il server risponde con echo. Puoi estendere la logica per integrare MCP o Bedrock agent.

## Docker

Per buildare il container:
```bash
docker build -t websocket-server .
docker run -p 8080:8080 websocket-server
```

## Endpoint disponibili
- `/ws` (WebSocket)
- `/ping` (HTTP GET)
- `/health` (HTTP GET)

## Esempio di messaggio
```json
{"message": "Ciao server!"}
```

## Note
- Puoi modificare la logica in `server.js` per integrare tool MCP o logica custom.
- Il client può essere usato come base per testare agenti Bedrock con streaming.
