# Guida: Aggiungere una Nuova Funzionalità all'App

Questo documento descrive passo-passo come abbiamo aggiunto la funzionalità **Contatti** al sistema Personal Assistant, includendo backend Lambda, agent con MCP, frontend e integrazione completa.

## Panoramica della Funzionalità

La funzionalità Contatti permette di:
- Creare contatti con 8 campi: nome, cognome, email, telefono, descrizione, dove_conosciuto, note, url
- Recuperare contatti con filtri multipli
- Aggiornare informazioni dei contatti esistenti
- Eliminare contatti
- Delegare operazioni tramite orchestrator all'agent specializzato

---

## 📋 Checklist Completa

- [x] **Step 1**: Lambda Functions CRUD (POST, GET, UPDATE, DELETE)
- [x] **Step 2**: Agent Specializzato con MCP Gateway
- [x] **Step 3**: Infrastruttura CDK (DynamoDB + Lambda)
- [x] **Step 4**: Gateway MCP Targets (4 tools)
- [x] **Step 5**: Frontend UI (HTML + CSS + JavaScript)
- [x] **Step 6**: Backend API Flask (4 endpoints)
- [x] **Step 7**: Orchestrator Integration
- [x] **Step 8**: Deploy e Test

---

## Step 1: Lambda Functions CRUD

### 1.1 Creare le Directory
```bash
mkdir lambdas/contact-api
```

### 1.2 POST Contact (lambdas/contact-api/post_contact.py)
```python
import boto3
import json
import uuid
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('CONTACTS_TABLE_NAME', 'PersonalContacts')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    contact_data = {
        'contact_id': str(uuid.uuid4()),
        'nome': event.get('nome', ''),
        'cognome': event.get('cognome', ''),
        'email': event.get('email', ''),
        'telefono': event.get('telefono', ''),
        'descrizione': event.get('descrizione', ''),
        'dove_conosciuto': event.get('dove_conosciuto', ''),
        'note': event.get('note', ''),
        'url': event.get('url', ''),
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }
    
    table.put_item(Item=contact_data)
    return contact_data
```

**Campi chiave:**
- `contact_id`: UUID generato automaticamente
- `created_at`, `updated_at`: Timestamp ISO 8601
- Tutti gli altri campi sono opzionali

### 1.3 GET Contact (lambdas/contact-api/get_contact.py)
```python
def lambda_handler(event, context):
    # Supporta filtri: nome, cognome, email, dove_conosciuto, contact_id
    # Usa Scan con FilterExpression per ricerca flessibile
    # Ordina per created_at DESC
```

**Caratteristiche:**
- Ricerca con `contains` per nome, cognome, email, dove_conosciuto
- Ricerca esatta per `contact_id`
- Parametro `limit` per paginazione (default: 100)

### 1.4 UPDATE Contact (lambdas/contact-api/update_contact.py)
```python
def lambda_handler(event, context):
    # Costruisce dinamicamente UpdateExpression
    # Aggiorna solo i campi forniti
    # Auto-aggiorna updated_at
```

**Logica importante:**
- Solo i campi presenti nell'evento vengono aggiornati
- `contact_id` obbligatorio
- `updated_at` viene sempre aggiornato

### 1.5 DELETE Contact (lambdas/contact-api/delete_contact.py)
```python
def lambda_handler(event, context):
    contact_id = event.get('contact_id')
    # Verifica esistenza prima di eliminare
    table.delete_item(Key={'contact_id': contact_id})
```

### 1.6 requirements.txt
```
boto3>=1.34.0
```

---

## Step 2: Agent Specializzato con MCP

### 2.1 Creare Agent Directory
```bash
mkdir agents/contact-writer-reader
```

### 2.2 Agent Code (agents/contact-writer-reader/agent.py)

**Componenti chiave:**

```python
# 1. MCP Client Setup
from mcp.client.streamablehttp_client import StreamableHTTPTransport

CLIENT_ID = os.environ.get('COGNITO_CLIENT_ID')
CLIENT_SECRET = os.environ.get('COGNITO_CLIENT_SECRET')
GATEWAY_URL = "https://taskapigateway-vveeifneus.gateway..."

# 2. System Prompt
SYSTEM_PROMPT = """Sei un agente specializzato nella gestione di contatti.
Campi disponibili (tutti opzionali):
- nome, cognome, email, telefono
- descrizione, dove_conosciuto, note, url
"""

# 3. Tool Definitions (usati dal MCP Gateway)
tools = [
    "post-contact___post-contact",    # Crea contatto
    "get-contact___get-contact",      # Recupera contatti
    "update-contact___update-contact",# Aggiorna contatto
    "delete-contact___delete-contact" # Elimina contatto
]

# 4. Agent invocation con MCP
async with mcp_client as client:
    result = await client.call_tool("post-contact___post-contact", arguments)
```

### 2.3 Requirements
```
strands-agents==0.0.7
bedrock-agentcore==0.1.12
mcp==1.1.2
```

### 2.4 README con Esempi
Creare `agents/contact-writer-reader/README.md` con esempi d'uso.

---

## Step 3: Infrastruttura CDK

### 3.1 DynamoDB Table

Aggiungere in `infrastructure/cdk-app/lib/personal-assistant-stack.ts`:

```typescript
// Contact Table con GSI per ricerca per nome
const contactsTable = new dynamodb.Table(this, 'ContactsTable', {
  partitionKey: { name: 'contact_id', type: dynamodb.AttributeType.STRING },
  billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
  removalPolicy: cdk.RemovalPolicy.RETAIN,
  pointInTimeRecovery: true,
});

contactsTable.addGlobalSecondaryIndex({
  indexName: 'NameIndex',
  partitionKey: { name: 'cognome', type: dynamodb.AttributeType.STRING },
  sortKey: { name: 'nome', type: dynamodb.AttributeType.STRING },
  projectionType: dynamodb.ProjectionType.ALL,
});
```

### 3.2 Lambda Functions

```typescript
// ContactPost Lambda
const contactPostLambda = new lambda.Function(this, 'ContactPostLambda', {
  runtime: lambda.Runtime.PYTHON_3_11,
  handler: 'post_contact.lambda_handler',
  code: lambda.Code.fromAsset('../../lambdas/contact-api'),
  timeout: cdk.Duration.seconds(30),
  memorySize: 256,
  environment: {
    CONTACTS_TABLE_NAME: contactsTable.tableName,
  },
  logRetention: logs.RetentionDays.ONE_WEEK,
});

contactsTable.grantWriteData(contactPostLambda);

// Ripetere per ContactGet, ContactUpdate, ContactDelete
// - ContactGet: grantReadData
// - ContactUpdate: grantReadWriteData
// - ContactDelete: grantReadWriteData
```

### 3.3 CloudFormation Outputs

```typescript
new cdk.CfnOutput(this, 'ContactPostLambdaArn', {
  value: contactPostLambda.functionArn,
});
new cdk.CfnOutput(this, 'ContactGetLambdaArn', {
  value: contactGetLambda.functionArn,
});
new cdk.CfnOutput(this, 'ContactUpdateLambdaArn', {
  value: contactUpdateLambda.functionArn,
});
new cdk.CfnOutput(this, 'ContactDeleteLambdaArn', {
  value: contactDeleteLambda.functionArn,
});
new cdk.CfnOutput(this, 'ContactsTableName', {
  value: contactsTable.tableName,
});
```

### 3.4 Deploy CDK

```bash
cd infrastructure/cdk-app
cdk deploy --require-approval never
```

**Salvare gli ARN dall'output!**

---

## Step 4: Gateway MCP Targets

### 4.1 Creare JSON Payload Files

Creare 4 file in `scripts/`:

**contact-post-payload.json:**
```json
{
  "lambdaArn": "arn:aws:lambda:us-east-1:ACCOUNT:function:PersonalAssistant-ContactPost",
  "toolSchema": {
    "inlinePayload": [{
      "name": "post-contact",
      "description": "Crea un nuovo contatto...",
      "inputSchema": {
        "type": "object",
        "properties": {
          "nome": {"type": "string", "description": "Nome del contatto"},
          // ... altri campi
        }
      }
    }]
  }
}
```

Ripetere per `get`, `update`, `delete`.

### 4.2 Creare Gateway Targets

```powershell
# Attivare venv
.\.venv\Scripts\Activate.ps1

# POST
agentcore gateway create-mcp-gateway-target `
  --gateway-arn arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:gateway/NAME `
  --gateway-url https://GATEWAY_URL/mcp `
  --role-arn arn:aws:iam::ACCOUNT:role/ROLE_NAME `
  --name post-contact `
  --target-type lambda `
  --region us-east-1 `
  --target-payload (Get-Content scripts\contact-post-payload.json -Raw)

# Ripetere per get-contact, update-contact, delete-contact
```

### 4.3 Verificare Targets

```bash
cd scripts
python test_mcp_gateway.py | Select-String "contact"
```

Dovresti vedere:
- `delete-contact___delete-contact`
- `get-contact___get-contact`
- `post-contact___post-contact`
- `update-contact___update-contact`

---

## Step 5: Frontend UI

### 5.1 HTML - Sidebar Navigation

In `chat-frontend/index.html`, aggiungere:

```html
<a href="#" class="nav-item" data-view="contacts">
    <span class="nav-icon">👤</span>
    <span class="nav-text">Contatti</span>
</a>
```

### 5.2 HTML - Contacts View

```html
<div id="contactsView" class="view">
    <div class="section-container">
        <div class="section-header">
            <div>
                <h1>👤 Contatti</h1>
                <div class="counter-badge">
                    <span id="contactsCounter">0</span> contatti caricati
                </div>
            </div>
            <button id="newContactBtn" class="primary-btn">+ Nuovo Contatto</button>
        </div>

        <!-- Form di creazione (hidden by default) -->
        <div id="contactForm" class="form-container" style="display: none;">
            <!-- 8 campi: nome, cognome, email, telefono, 
                 descrizione, dove_conosciuto, note, url -->
        </div>

        <!-- Filtri -->
        <div class="filters-container">
            <input type="text" id="contactFilterNome" placeholder="Filtra per nome...">
            <input type="text" id="contactFilterCognome" placeholder="Filtra per cognome...">
            <input type="text" id="contactFilterDove" placeholder="Filtra per dove conosciuto...">
            <button id="refreshContactsBtn">🔄 Aggiorna</button>
        </div>

        <!-- Lista contatti -->
        <div id="contactsList" class="items-list"></div>
    </div>
</div>
```

### 5.3 HTML - Edit Modal

```html
<div id="editContactModal" class="modal" style="display: none;">
    <div class="modal-content">
        <div class="modal-header">
            <h2>✏️ Modifica Contatto</h2>
            <button class="modal-close" onclick="closeEditContactModal()">&times;</button>
        </div>
        <form id="editContactForm" onsubmit="handleUpdateContact(event)">
            <!-- Stesso form della creazione ma con ID hidden -->
        </form>
    </div>
</div>
```

### 5.4 JavaScript - Event Listeners

In `chat-frontend/app.js`, aggiungere:

```javascript
// DOM Elements
const newContactBtn = document.getElementById('newContactBtn');
const contactForm = document.getElementById('contactForm');
const createContactForm = document.getElementById('createContactForm');
const cancelContactBtn = document.getElementById('cancelContactBtn');
const contactsList = document.getElementById('contactsList');
const refreshContactsBtn = document.getElementById('refreshContactsBtn');

// Event Listeners in init()
newContactBtn.addEventListener('click', () => contactForm.style.display = 'block');
cancelContactBtn.addEventListener('click', () => {
    contactForm.style.display = 'none';
    createContactForm.reset();
});
createContactForm.addEventListener('submit', handleCreateContact);
refreshContactsBtn.addEventListener('click', loadContacts);
contactFilterNome.addEventListener('input', loadContacts);
contactFilterCognome.addEventListener('input', loadContacts);
contactFilterDove.addEventListener('input', loadContacts);

// switchView() - aggiungere
if (viewName === 'contacts') {
    loadContacts();
}
```

### 5.5 JavaScript - CRUD Functions

```javascript
async function loadContacts() {
    const params = new URLSearchParams();
    if (nomeFilter) params.append('nome', nomeFilter);
    if (cognomeFilter) params.append('cognome', cognomeFilter);
    if (doveFilter) params.append('dove_conosciuto', doveFilter);
    
    const response = await fetch(`${CONFIG.API_URL}/contacts?${params}`);
    const data = await response.json();
    displayContacts(data.contacts || []);
}

function displayContacts(contacts) {
    // Aggiorna counter
    document.getElementById('contactsCounter').textContent = contacts.length;
    
    // Genera HTML per ogni contatto
    contactsList.innerHTML = contacts.map(contact => `
        <div class="item-card">
            <h3>${contact.nome} ${contact.cognome}</h3>
            <div>${contact.email}</div>
            <div>${contact.telefono}</div>
            <!-- ... -->
            <button onclick="editContact('${contact.contact_id}')">✏️</button>
            <button onclick="deleteContact('${contact.contact_id}')">🗑️</button>
        </div>
    `).join('');
}

async function handleCreateContact(e) {
    e.preventDefault();
    const contactData = {
        nome: document.getElementById('contactNome').value.trim(),
        // ... altri campi
    };
    
    await fetch(`${CONFIG.API_URL}/contacts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(contactData)
    });
    
    await loadContacts();
}

async function editContact(contactId) {
    // Carica contatto
    // Popola modal
    // Mostra modal
}

async function handleUpdateContact(e) {
    e.preventDefault();
    // PUT request
}

async function deleteContact(contactId, contactName) {
    if (!confirm(`Eliminare ${contactName}?`)) return;
    
    await fetch(`${CONFIG.API_URL}/contacts`, {
        method: 'DELETE',
        body: JSON.stringify({ contact_id: contactId })
    });
    
    await loadContacts();
}

function closeEditContactModal() {
    document.getElementById('editContactModal').style.display = 'none';
}
```

---

## Step 6: Backend API Flask

### 6.1 Aggiungere Lambda ARNs

In `chat-frontend/backend.py`:

```python
CONTACT_POST_LAMBDA_ARN = "arn:aws:lambda:us-east-1:ACCOUNT:function:PersonalAssistant-ContactPost"
CONTACT_GET_LAMBDA_ARN = "arn:aws:lambda:us-east-1:ACCOUNT:function:PersonalAssistant-ContactGet"
CONTACT_UPDATE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:ACCOUNT:function:PersonalAssistant-ContactUpdate"
CONTACT_DELETE_LAMBDA_ARN = "arn:aws:lambda:us-east-1:ACCOUNT:function:PersonalAssistant-ContactDelete"
```

### 6.2 GET Endpoint

```python
@app.route('/api/contacts', methods=['GET'])
def get_contacts():
    # Estrai query params
    nome = request.args.get('nome', '')
    cognome = request.args.get('cognome', '')
    email = request.args.get('email', '')
    dove_conosciuto = request.args.get('dove_conosciuto', '')
    contact_id = request.args.get('contact_id', '')
    limit = request.args.get('limit', '100')
    
    # Costruisci payload
    payload = {}
    if nome: payload['nome'] = nome
    if cognome: payload['cognome'] = cognome
    # ... altri filtri
    
    # Invoca Lambda
    response = lambda_client.invoke(
        FunctionName=CONTACT_GET_LAMBDA_ARN,
        InvocationType='RequestResponse',
        Payload=json.dumps(payload)
    )
    
    result = json.loads(response['Payload'].read())
    return jsonify(result), 200
```

### 6.3 POST Endpoint

```python
@app.route('/api/contacts', methods=['POST'])
def create_contact():
    data = request.get_json()
    
    response = lambda_client.invoke(
        FunctionName=CONTACT_POST_LAMBDA_ARN,
        InvocationType='RequestResponse',
        Payload=json.dumps(data)
    )
    
    result = json.loads(response['Payload'].read())
    return jsonify(result), 200
```

### 6.4 PUT e DELETE Endpoints

Stesso pattern di POST, ma con Lambda ARN appropriati.

### 6.5 Aggiornare Help Text

```python
if __name__ == '__main__':
    print("Endpoints disponibili:")
    # ... esistenti
    print("  GET  /api/contacts    - Recupera contatti")
    print("  POST /api/contacts    - Crea contatto")
    print("  PUT  /api/contacts    - Aggiorna contatto")
    print("  DELETE /api/contacts  - Cancella contatto")
```

---

## Step 7: Orchestrator Integration

### 7.1 Aggiungere ARN Agent

In `agents/orchestrator/agent.py`:

```python
AGENTS = {
    "researcher": "arn:aws:...",
    "calculator": "arn:aws:...",
    "project_goal_writer_reader": "arn:aws:...",
    "contact_writer_reader": "arn:aws:bedrock-agentcore:us-east-1:ACCOUNT:runtime/contact_writer_reader-XXXXX"
}
```

### 7.2 Aggiornare System Prompt

```python
SYSTEM_PROMPT = """...

- **contact_writer_reader**: Gestisce contatti personali e professionali (CRUD completo)
  ARN: {contact_arn}
  Usa questo agente per:
  - Creare, leggere, aggiornare o eliminare contatti
  - Gestire informazioni come nome, cognome, email, telefono, descrizione, 
    dove_conosciuto, note, url

...

Esempi di routing:
...
- "Aggiungi un contatto per Mario Rossi" → invoke_agent("contact-writer-reader", "...")
- "Mostrami i contatti conosciuti a Roma" → invoke_agent("contact-writer-reader", "...")
...
""".format(
    researcher_arn=AGENTS["researcher"],
    calculator_arn=AGENTS["calculator"],
    project_goal_arn=AGENTS["project_goal_writer_reader"],
    contact_arn=AGENTS["contact_writer_reader"]
)
```

### 7.3 Aggiornare Tool Docstring

```python
@tool
def invoke_agent(agent_name: str, prompt: str) -> str:
    """Invoca un agente specializzato con un prompt specifico.
    
    Args:
        agent_name: Nome dell'agente da invocare. 
                   Valori: researcher, calculator, 
                   project-goal-writer-reader, contact-writer-reader
        prompt: Il prompt da inviare all'agente
    """
```

---

## Step 8: Deploy e Test

### 8.1 Deploy Contact Agent

```bash
cd agents/contact-writer-reader

# Configura
agentcore configure --entrypoint .\agent.py --name contact_writer_reader

# Scegli:
# - Deployment: Container
# - Memory: orchestrator_mem (riusa esistente)
# - Authorization: IAM

# Launch
agentcore launch

# Salva ARN dall'output!
```

### 8.2 Aggiornare Orchestrator ARN

Aggiornare `AGENTS["contact_writer_reader"]` con il nuovo ARN.

### 8.3 Re-deploy Orchestrator

```bash
cd agents/orchestrator
agentcore launch --auto-update-on-conflict
```

### 8.4 Avviare Backend

```bash
cd chat-frontend
python backend.py
```

### 8.5 Aprire Frontend

```bash
start index.html
```

### 8.6 Test Completo

**Via Chat:**
```
aggiungi un nuovo contatto: Mario Rossi, email mario.rossi@example.com, 
conosciuto a AWS Summit 2024
```

**Via UI:**
1. Clicca su "👤 Contatti" nella sidebar
2. Clicca "+ Nuovo Contatto"
3. Compila il form
4. Verifica che appaia nella lista
5. Testa Edit e Delete

---

## 🎯 Pattern Generale per Nuove Funzionalità

Quando aggiungi una nuova funzionalità (es. "Tasks", "Notes", "Events"):

### 1. Backend Layer
- [ ] Crea 4 Lambda (POST, GET, UPDATE, DELETE) in `lambdas/FEATURE-api/`
- [ ] Definisci schema dati (campi obbligatori/opzionali)
- [ ] Gestisci Decimal serialization per DynamoDB

### 2. Infrastructure Layer
- [ ] Aggiungi DynamoDB Table in CDK stack
- [ ] Aggiungi Global Secondary Index se necessari
- [ ] Crea 4 Lambda Functions in CDK
- [ ] Configura environment variables e IAM permissions
- [ ] Aggiungi CloudFormation Outputs per ARN
- [ ] Deploy con `cdk deploy`

### 3. Agent Layer
- [ ] Crea directory `agents/FEATURE-writer-reader/`
- [ ] Implementa agent.py con MCP client
- [ ] Definisci system_prompt con schema campi
- [ ] Crea requirements.txt
- [ ] Crea 4 JSON payload files per gateway targets
- [ ] Crea gateway targets con `agentcore gateway create-mcp-gateway-target`
- [ ] Verifica con `test_mcp_gateway.py`
- [ ] Deploy agent con `agentcore configure` e `agentcore launch`

### 4. Orchestrator Layer
- [ ] Aggiungi ARN agent in `AGENTS` dict
- [ ] Aggiorna `SYSTEM_PROMPT` con descrizione e esempi
- [ ] Aggiorna docstring di `invoke_agent` tool
- [ ] Re-deploy orchestrator

### 5. Backend API Layer
- [ ] Aggiungi Lambda ARNs in `backend.py`
- [ ] Crea 4 route: GET, POST, PUT, DELETE `/api/FEATURE`
- [ ] Implementa invocazione Lambda con boto3
- [ ] Gestisci error handling e logging
- [ ] Aggiorna help text

### 6. Frontend Layer
- [ ] Aggiungi nav item in sidebar (HTML)
- [ ] Crea view section (HTML)
- [ ] Crea form di creazione (HTML)
- [ ] Crea edit modal (HTML)
- [ ] Aggiungi filtri (HTML)
- [ ] Implementa DOM elements in app.js
- [ ] Aggiungi event listeners in `init()`
- [ ] Implementa funzioni: load, display, create, edit, delete
- [ ] Aggiungi switch case in `switchView()`
- [ ] Aggiungi counter badge

### 7. Testing
- [ ] Test CRUD via frontend UI
- [ ] Test CRUD via chat orchestrator
- [ ] Test filtri e ricerca
- [ ] Test edit modal
- [ ] Verifica counter badge
- [ ] Test error handling

---

## 📝 Note Importanti

### Sicurezza
- **IAM Only**: Nessun API Gateway pubblico, solo Lambda invoke via IAM
- **OAuth2**: Agent usa OAuth2 per autenticarsi al MCP Gateway
- **CORS**: Flask backend ha CORS abilitato solo per localhost

### Performance
- **DynamoDB**: Usa PAY_PER_REQUEST billing
- **Lambda**: Timeout 30s, Memory 256MB
- **Logs**: Retention 7 giorni
- **GSI**: Usa indici per query frequenti

### Convenzioni
- **Naming**: `FEATURE-api` per Lambda, `FEATURE_writer_reader` per agent
- **ARN**: Salva sempre ARN dopo deploy per reference
- **Fields**: Usa snake_case per DynamoDB, camelCase opzionale per frontend
- **IDs**: Usa UUID v4 per primary keys

### Troubleshooting
- **Lambda invoke fails**: Verifica IAM permissions in backend.py
- **Agent non risponde**: Controlla ARN in orchestrator e che agent sia ACTIVE
- **Gateway target non trovato**: Verifica con `test_mcp_gateway.py`
- **Frontend non carica**: Verifica backend sia running su :5000
- **CORS errors**: Riavvia backend Flask

---

## 🔗 File di Riferimento

- **Lambda Code**: `lambdas/contact-api/*.py`
- **Agent Code**: `agents/contact-writer-reader/agent.py`
- **CDK Stack**: `infrastructure/cdk-app/lib/personal-assistant-stack.ts`
- **Gateway Docs**: `docs/CONTACT_GATEWAY_COMMANDS.md`
- **Frontend HTML**: `chat-frontend/index.html`
- **Frontend JS**: `chat-frontend/app.js`
- **Backend API**: `chat-frontend/backend.py`
- **Orchestrator**: `agents/orchestrator/agent.py`

---

## ✅ Validazione Finale

La funzionalità è completa quando:

1. ✅ CDK deploy mostra tutti gli ARN
2. ✅ 4 gateway targets attivi in `test_mcp_gateway.py`
3. ✅ Agent deployato e ACTIVE
4. ✅ Orchestrator include nuovo agent nell'ARN dict
5. ✅ Backend mostra endpoint nella console startup
6. ✅ Frontend mostra nav item e view
7. ✅ Create via UI funziona
8. ✅ Create via chat funziona
9. ✅ Read/List funziona con filtri
10. ✅ Update via modal funziona
11. ✅ Delete con conferma funziona
12. ✅ Counter badge si aggiorna

---

**Data documento**: Dicembre 2025  
**Versione**: 1.0  
**Autore**: AI Assistant + User
