# Short-Term Memory per Candidate Matcher

## Cos'è la Short-Term Memory (STM)?

La Short-Term Memory di Bedrock AgentCore consente all'agente candidate-matcher di **ricordare la conversazione durante l'intervista iniziale** con il candidato.

### Come funziona:

1. **Raccolta**: Ogni messaggio dello scambio conversazionale viene automaticamente salvato nella memoria
2. **Recupero**: All'inizio di una nuova interazione, gli ultimi 5 turni di conversazione vengono caricati
3. **Contesto**: Questi turni vengono forniti all'agente come contesto per continuare la conversazione in modo coerente

## Setup della Memory

### Step 1: Creare una Memory Resource

```bash
# Esegui lo script di setup della memoria
python scripts/create_memory.py
```

Se non hai lo script, crealo manualmente:

```python
from bedrock_agentcore.memory import MemoryClient

client = MemoryClient(region_name="us-east-1")

# Crea memoria per STM (Short-Term Memory)
memory = client.create_memory_and_wait(
    name="candidate-matcher-stm",
    strategies=[],  # STM non ha bisogno di strategie
    event_expiry_days=7,  # Mantiene le conversazioni per 7 giorni
    memory_execution_role_arn="arn:aws:iam::YOUR_ACCOUNT_ID:role/agentcore-taskapigateway-role"
)

print(f"Memory ID: {memory['id']}")
```

### Step 2: Nota il Memory ID

Dall'output del comando precedente, copia il **Memory ID**. Ne avrai bisogno per il deployment.

### Step 3: Deploy dell'Agente con Memory

```bash
# Setta la variabile di ambiente
export MEMORY_ID=mem-xxxxxxxxxxxxxxxx  # Sostituisci con il tuo Memory ID

# Deploy l'agente
cd agents/candidate-matcher
agentcore launch
```

Oppure aggiungi alla configurazione `.bedrock_agentcore.yaml`:

```yaml
agents:
  candidate_matcher:
    environment_variables:
      MEMORY_ID: mem-xxxxxxxxxxxxxxxx
      ACTOR_ID: candidate-matcher
      AWS_REGION: us-east-1
```

## Funzionamento nell'Agente

### Caricamento della Memoria

All'avvio di ogni richiesta, l'agente:

1. Recupera gli ultimi 5 turni di conversazione dalla memory
2. Li formatta in modo leggibile
3. Li aggiunge al system prompt come contesto

```python
# Esempio di contesto caricato:
"📋 CONTESTO DELLA CONVERSAZIONE PRECEDENTE:
USER: Sono uno sviluppatore Python senior
ASSISTANT: Perfetto! Quanti anni di esperienza hai?
USER: 8 anni di esperienza
ASSISTANT: Ottimo! Conosci anche AWS e Docker?"
```

### Salvataggio della Conversazione

Dopo ogni interazione, l'agente:

1. Cattura il messaggio dell'utente
2. Cattura la risposta dell'agente
3. Salva entrambi nella memory come un "turno" di conversazione

## Input/Output con Memory

### Formato di Input

```json
{
  "prompt": "Grazie, e per quanto riguarda le lingue?",
  "session_id": "candidate-123-session-456",
  "candidate_id": "candidate-123"
}
```

**Campi:**
- `prompt` (required): Il messaggio dell'utente
- `session_id` (optional): ID univoco della sessione. Se non fornito, ne viene generato uno
- `candidate_id` (optional): ID del candidato. Default: "candidate"

### Formato di Output

```json
{
  "message": "Mi piacerebbe sapere se parli inglese...",
  "matches": [...]  // Se il tool è stato invocato
}
```

## Flusso Conversazionale Completo

### Primo Messaggio (Nuova Sessione)

```
USER: "Ciao, sono Marco, uno sviluppatore Python"

AGENT (senza contesto precedente):
"Ciao Marco! Sono qui per aiutarti a trovare i needs più adatti. 
Confirmi che il tuo ruolo attuale è 'Senior Python Developer'?
Quanti anni di esperienza hai?"

[SALVA in memoria: 
  USER: "Ciao, sono Marco, uno sviluppatore Python"
  ASSISTANT: "Ciao Marco! Sono qui..."]
```

### Secondo Messaggio (Stessa Sessione)

```
USER: "8 anni, e conosco AWS"

AGENT (CARICA MEMORIA):
Contesto: "USER: Ciao, sono Marco, uno sviluppatore Python
ASSISTANT: Ciao Marco! Sono qui per aiutarti..."

"Perfetto Marco! 8 anni di esperienza con AWS è un'ottima base.
Conosci anche Docker o altri strumenti DevOps?"

[SALVA in memoria il nuovo turno]
```

## Monitoraggio della Memory

### Visualizzare i Dati in Memoria

```bash
# Usa AWS CLI per vedere gli events
aws bedrock-agentcore list-events \
  --memory-id mem-xxxxxxxxxxxxxxxx \
  --actor-id candidate-123 \
  --session-id candidate-123-session-456 \
  --region us-east-1
```

### Pulire la Memoria (se necessario)

```python
from bedrock_agentcore.memory import MemoryClient

client = MemoryClient(region_name="us-east-1")

# Elimina tutti i record di una sessione specifica
client.delete_all_long_term_memories_in_namespace(
    namespace="candidate-123/session-456"
)
```

## Vantaggi dell'STM

✅ **Conversazione Naturale**: L'agente ricorda tutto quello che è stato detto
✅ **Coerenza**: Non ripete domande già fatte
✅ **Contesto**: Comprende riferimenti a informazioni precedenti
✅ **Persistenza**: I dati rimangono per 7 giorni
✅ **Semplicità**: Nessuna configurazione di estratzioni o strategie

## Passare a Long-Term Memory (LTM)

Se vuoi che l'agente **ricordi i candidati anche dopo 7 giorni**, puoi creare una memoria con strategie semantiche:

```python
from bedrock_agentcore.memory import MemoryClient

client = MemoryClient(region_name="us-east-1")

# Memoria con LTM
memory = client.create_memory_and_wait(
    name="candidate-matcher-ltm",
    strategies=[
        # Estrae preferenze personali
        {
            "userPreferenceMemoryStrategy": {
                "name": "candidate_preferences",
                "namespaces": ["/candidate/preferences/{actorId}"]
            }
        },
        # Estrae fatti su candidati
        {
            "semanticMemoryStrategy": {
                "name": "candidate_facts",
                "namespaces": ["/candidate/facts/{actorId}"]
            }
        }
    ],
    event_expiry_days=365  # 1 anno
)
```

## Troubleshooting

### ❌ "MEMORY_ID not found"

```
Soluzione: Assicurati che la variabile di ambiente MEMORY_ID sia settata:
export MEMORY_ID=mem-xxxxxxxxxxxxxxxx
```

### ❌ "Access Denied" su Memory

```
Soluzione: Verifica che la IAM role abbia questi permessi:
- bedrock-agentcore:CreateEvent
- bedrock-agentcore:ListEvents
- bedrock-agentcore:GetEvent
```

### ❌ Memory vuota anche con session_id

```
Soluzione: Controlla che l'actor_id matches:
- Se salvi con actor_id="candidate-123"
- Devi caricare con actor_id="candidate-123"
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│   USER INPUT (Prompt)                               │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  MemorySessionManager        │
        │  - Recupera ultimi 5 turni   │
        │  - Formatta come contesto    │
        └──────────────────┬───────────┘
                           │
                           ▼
            ┌──────────────────────────────┐
            │  AGENT SYSTEM PROMPT         │
            │  + Memory Context            │
            │  + MCP Tools (Gateway)       │
            └──────────────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │  Bedrock Claude      │
                    │  - Processa prompt   │
                    │  - Invoca tool se    │
                    │    necessario        │
                    └──────────────────┬───┘
                                       │
                                       ▼
                    ┌──────────────────────────────┐
                    │  AGENT RESPONSE              │
                    │  + Salva turno in memory     │
                    └──────────────────┬───────────┘
                                       │
                                       ▼
                            ┌──────────────────┐
                            │  USER OUTPUT     │
                            │  (Risposta)      │
                            └──────────────────┘
```

## Variabili d'Ambiente

| Variabile | Descrizione | Obbligatorio | Default |
|-----------|-------------|--------------|---------|
| `MEMORY_ID` | ID della memory resource | No | (disabled) |
| `ACTOR_ID` | ID dell'attore nella memory | No | "candidate-matcher" |
| `AWS_REGION` | Regione AWS | No | "us-east-1" |

## Costi

- **Memory Storage**: $0.50 per GB al mese
- **STM Event**: Incluso nel Memory Storage
- **API Calls**: $0.0001 per call

Per 1000 candidati con 10 messaggi ciascuno (~50KB dati):
- Storage: ~$0.02/mese
- API Calls: ~$0.10

## Prossimi Passi

1. ✅ Setup della Memory
2. ✅ Deploy dell'agente con MEMORY_ID
3. ✅ Testa la conversazione multi-turno
4. ⏭️ (Opzionale) Aggiungi LTM per memoria persistente cross-session
5. ⏭️ (Opzionale) Crea dashboard per visualizzare le memory retrieval
