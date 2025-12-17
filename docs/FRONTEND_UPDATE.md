# Personal Assistant - Frontend con Gestione Obiettivi e Progetti

## Modifiche Implementate

### 1. API Gateway (CDK)

Aggiunto endpoint per goals e projects in `personal-assistant-stack.ts`:

```typescript
// POST /goals
const goalsResource = taskApi.root.addResource('goals');
goalsResource.addMethod('POST', new apigateway.LambdaIntegration(goalPostLambda));
goalsResource.addMethod('GET', new apigateway.LambdaIntegration(goalGetLambda));

// POST /projects
const projectsResource = taskApi.root.addResource('projects');
projectsResource.addMethod('POST', new apigateway.LambdaIntegration(projectPostLambda));
projectsResource.addMethod('GET', new apigateway.LambdaIntegration(projectGetLambda));
```

### 2. Frontend Redesign

**Nuova struttura con sidebar:**
- **Menu Laterale**: Navigazione tra Chat, Obiettivi, Progetti
- **Sezione Chat**: Interfaccia esistente invariata
- **Sezione Obiettivi**: Form creazione + lista con filtri
- **Sezione Progetti**: Form creazione + lista con filtri

**File modificati:**
- `index.html`: Aggiunto sidebar + nuove sezioni
- `style.css`: Nuovo layout responsive con sidebar
- `app.js`: Gestione navigazione + CRUD per goals/projects

### 3. Backend Proxy Esteso

**Nuovi endpoint in `backend.py`:**
- `GET /api/goals` → Invoca GoalGetLambda
- `POST /api/goals` → Invoca GoalPostLambda
- `GET /api/projects` → Invoca ProjectGetLambda
- `POST /api/projects` → Invoca ProjectPostLambda

Il backend invoca **direttamente le Lambda** tramite boto3, mantenendo compatibilità con AgentCore Gateway.

## Deploy

### 1. Deploy Infrastructure

```powershell
cd infrastructure\cdk-app
cdk deploy
```

Salva gli ARN delle Lambda dagli output.

### 2. Aggiorna Backend (Opzionale)

Se gli ARN sono diversi, modifica `chat-frontend/backend.py`:

```python
GOAL_POST_LAMBDA_ARN = "arn:aws:lambda:..."
GOAL_GET_LAMBDA_ARN = "arn:aws:lambda:..."
PROJECT_POST_LAMBDA_ARN = "arn:aws:lambda:..."
PROJECT_GET_LAMBDA_ARN = "arn:aws:lambda:..."
```

### 3. Avvia Backend

```powershell
cd chat-frontend
python backend.py
```

### 4. Apri Frontend

Apri `chat-frontend/index.html` nel browser o usa Live Server.

## Utilizzo

### Chat
- Usa la chat per interagire con l'orchestrator
- L'orchestrator può creare/leggere goals e projects via AgentCore Gateway

### Obiettivi
1. Click su **🎯 Obiettivi** nel menu
2. **+ Nuovo Obiettivo** per creare
3. Filtra per ambito/status/priorità
4. Visualizza scadenze, metriche, sottotask

### Progetti
1. Click su **💼 Progetti** nel menu
2. **+ Nuovo Progetto** per creare
3. Filtra per ambito/tecnologia
4. Visualizza GitHub URL, tecnologie usate

## Architettura

```
Frontend (HTML/CSS/JS)
    ↓ HTTP
Backend Flask (localhost:5000)
    ↓ boto3.lambda.invoke()
Lambda Functions (AWS)
    ↓
DynamoDB Tables
```

**Doppio accesso alle Lambda:**
1. **Frontend → Backend → Lambda** (invocazione diretta)
2. **Orchestrator → AgentCore Gateway → Lambda** (via MCP tools)

Questo garantisce che le stesse Lambda funzionino sia per l'interfaccia utente che per l'orchestrator AI.

## Prossimi Passi

1. Deploy con `cdk deploy`
2. Testa creazione goals/projects via interfaccia
3. Verifica che l'orchestrator possa ancora usare i tool save-goal/get-goals
4. (Opzionale) Aggiungi autenticazione con Cognito per produzione
5. (Opzionale) Deploy frontend su S3 + CloudFront
