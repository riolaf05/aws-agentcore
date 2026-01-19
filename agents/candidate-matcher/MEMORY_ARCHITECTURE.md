# Architettura della Short-Term Memory

## Come Funziona Internamente

### 1. Flusso di Caricamento della Memoria

Quando l'agente riceve un messaggio:

```python
# Step 1: Genera un session_id univoco (se non fornito)
session_id = payload.get("session_id", str(uuid.uuid4()))

# Step 2: Crea il memory manager
memory_manager = MemorySessionManager(
    memory_id=MEMORY_ID,
    region_name=REGION
)

# Step 3: Recupera gli ultimi 5 turni
last_turns = memory_manager.get_last_k_turns(
    actor_id=candidate_id,
    session_id=session_id,
    k=5
)

# Step 4: Formatta come contesto leggibile
memory_context = """
USER: Sono Marco, sviluppatore Python
ASSISTANT: Perfetto! Quanti anni di esperienza hai?
USER: 8 anni
ASSISTANT: Ottimo! Cosa sai di AWS?
"""

# Step 5: Aggiunge al system prompt
enhanced_prompt = system_prompt + f"\n\n📋 CONTESTO:\n{memory_context}"
```

### 2. Flusso di Salvataggio della Memoria

Dopo ogni risposta dell'agente:

```python
# Step 1: Estrai il messaggio dell'utente e la risposta
user_message = "8 anni di esperienza"
agent_response = "Ottimo! Conosci Docker?"

# Step 2: Crea i messaggi conversazionali
messages = [
    ConversationalMessage(user_message, MessageRole.USER),
    ConversationalMessage(agent_response, MessageRole.ASSISTANT)
]

# Step 3: Salva il turno nella memoria
memory_manager.add_turns(
    actor_id=candidate_id,
    session_id=session_id,
    messages=messages
)
```

## Memoria vs. Non-Memoria

### Senza Memory

```
Turno 1:
USER: "Sono Marco, sviluppatore Python con 8 anni di esperienza"
AGENT: "Grazie! Ho annotato che sei Marco con 8 anni..."

Turno 2:
USER: "Conosco AWS e Python"
AGENT: "Capito! E qual è il tuo ruolo attuale?" ❌ RIDONDANTE!
       (Non ricorda che ha già chiesto)
```

### Con Memory

```
Turno 1:
USER: "Sono Marco, sviluppatore Python con 8 anni di esperienza"
AGENT: "Grazie! Ho annotato che sei Marco con 8 anni..."
[SALVA: User message + Agent response]

Turno 2:
[CARICA MEMORIA del Turno 1]
USER: "Conosco AWS e Python"
AGENT: "Perfetto Marco! Parli anche lingue straniere?" ✅ CONTINUA!
       (Ricorda tutto e progredisce naturalmente)
[SALVA: Nuovo turno]
```

## Dettagli Tecnici

### Struttura dei Dati in Memoria

La memoria salva **events** con questa struttura:

```
Event {
  eventId: "evt-abc123def456"
  actorId: "candidate-123"
  sessionId: "session-456"
  eventTimestamp: 2025-01-16T12:34:56Z
  payload: [
    {
      conversational: {
        role: "USER"
        content: { text: "8 anni di esperienza" }
      }
    },
    {
      conversational: {
        role: "ASSISTANT"
        content: { text: "Perfetto! Conosci AWS?" }
      }
    }
  ]
}
```

### Namespaces e Organizzazione

Opzionalmente, puoi organizzare la memoria in namespaces:

```
/candidate-123/initial-interview
/candidate-123/follow-up
/candidate-123/preferences
```

Attualmente l'agente usa il formato:
- **Actor ID**: `candidate-id` (univoco per ogni candidato)
- **Session ID**: ID della conversazione (sempre crescente)

### Retention Policy

- **Event Expiry**: 7 giorni (configurabile)
- **Max Events per Session**: Illimitato
- **Max Turns per Retrieval**: 5 turni (ultimi 5 scambi)

Se hai molti turni:
```
Turn 5: [User | Assistant]
Turn 4: [User | Assistant]
Turn 3: [User | Assistant]
Turn 2: [User | Assistant]
Turn 1: [User | Assistant]  ← Viene caricato questo
        Turni precedenti vengono scartati
```

## Caso d'Uso Completo

### Scenario: Intervista con Marco

**Sessione**: `interview-marco-2025-01-16`

#### Turno 1

```
INPUT:
{
  "prompt": "Ciao, sono Marco",
  "session_id": "interview-marco-2025-01-16"
}

PROCESSING:
1. Genera candidato_id = "marco-candidate"
2. Recupera memoria per (marco-candidate, interview-marco-2025-01-16)
   → Nessun turno precedente
3. Passa il prompt senza contesto

OUTPUT:
"Ciao Marco! Sono qui per trovare i needs migliori per te.
Dimmi: qual è il tuo ruolo attuale?"

SAVE IN MEMORY:
User: "Ciao, sono Marco"
Assistant: "Ciao Marco! Sono qui per trovare..."
```

#### Turno 2

```
INPUT:
{
  "prompt": "Sono uno sviluppatore Python senior",
  "session_id": "interview-marco-2025-01-16"
}

PROCESSING:
1. Usa lo stesso candidato_id = "marco-candidate"
2. Recupera memoria per (marco-candidate, interview-marco-2025-01-16)
   → Trova il Turno 1!
3. Formatta contesto:
   "USER: Ciao, sono Marco
    ASSISTANT: Ciao Marco! Sono qui per trovare..."
4. Aggiunge al prompt dell'agente

OUTPUT:
"Perfetto Marco! Ho notato che sei sviluppatore Python senior.
Quanti anni di esperienza hai in questo ruolo?"

SAVE IN MEMORY:
Aggiunge il Turno 2 alla sessione
```

#### Turno 3

```
INPUT:
{
  "prompt": "8 anni, e conosco AWS e Docker",
  "session_id": "interview-marco-2025-01-16"
}

PROCESSING:
1. Recupera memoria
   → Trova Turni 1 e 2!
2. Formatta contesto con 2 turni
3. Passa al modello

OUTPUT:
"Eccellente! 8 anni con Python, AWS e Docker è un profilo senior.
Parli altre lingue? Preferisci lavori remote o in ufficio?"

SAVE IN MEMORY:
Aggiunge il Turno 3
```

## Configurazione Avanzata

### Se Cambi il Number di Turni da Caricare

File: `agent.py`, linea ~80

```python
# Default: caricare ultimi 5 turni
last_turns = memory_manager.get_last_k_turns(
    actor_id=candidate_id,
    session_id=session_id,
    k=5  # ← Cambia questo numero
)
```

Raccomandazioni:
- `k=3`: Per conversazioni brevi (3-4 messaggi)
- `k=5`: Default - bilanciato (consiglato)
- `k=10`: Per interviste lunghe con molti dettagli

### Se Cambi il Periodo di Retention

File: `setup_memory.py`

```python
memory = client.create_memory_and_wait(
    event_expiry_days=7,  # ← Cambia questo
)
```

Raccomandazioni:
- `3`: Interviste giornaliere (budget ridotto)
- `7`: Default (1 settimana di follow-up)
- `14`: Follow-up prolungati
- `30`: Memoria a lungo termine

## Performance e Costi

### Latenza

```
Operation          Latency
─────────────────────────
Recupera memoria   ~200ms
Salva turno        ~100ms
Total per turno    ~300ms
```

Non è immediato, ma percepibile solo in batch.

### Costi

Per 1000 candidati con 10 messaggi medi (~100 KB totale):

```
Storage:     100 KB × 0.50 $/GB/mese = $0.00005
API Calls:   20,000 calls × $0.0001 = $2
Total:       ~$2/mese
```

Molto economico anche per migliaia di candidati.

## Debugging

### Vedere cosa è in Memoria

```bash
aws bedrock-agentcore list-events \
  --memory-id mem-xxxxx \
  --actor-id candidate-123 \
  --session-id interview-marco-2025-01-16 \
  --region us-east-1
```

### Pulire una Sessione

```python
from bedrock_agentcore.memory import MemorySessionManager

manager = MemorySessionManager(
    memory_id="mem-xxxxx",
    region_name="us-east-1"
)

# Elimina tutti gli events di una sessione
events = manager.list_events(
    actor_id="candidate-123",
    session_id="interview-marco-2025-01-16"
)

for event in events:
    manager.delete_event(
        actor_id="candidate-123",
        session_id="interview-marco-2025-01-16",
        event_id=event["eventId"]
    )
```

### Log di Debug

Nel file `agent.py`, aggiungi print per vedere cosa sta accadendo:

```python
# Linea ~110
if MEMORY_ID:
    try:
        print(f"📚 Caricando memoria per session: {session_id}")
        last_turns = memory_manager.get_last_k_turns(...)
        print(f"   Trovati {len(last_turns)} turni")
        
        if last_turns:
            print(f"   Contesto caricato: {memory_context[:100]}...")
    except Exception as e:
        print(f"   ❌ Errore: {e}")
```

Poi vedi l'output con:
```bash
agentcore launch --verbose
```

## Prossimo Livello: Long-Term Memory

Se vuoi che Marco venga **riconosciuto anche la prossima settimana** con le sue preferenze:

1. Crea una memoria con `semanticMemoryStrategy`
2. L'agente estrarrà automaticamente:
   - Preferenze: "Preferisco Python e AWS"
   - Fatti: "Marco ha 8 anni di esperienza"
   - Lingue: "Parla inglese fluentemente"

3. Nella prossima conversazione:
```
USER: "Ciao, sono Marco di nuovo"
AGENT: "Bentornato Marco! So che preferisci Python e AWS.
        Vuoi cercare nuove posizioni?"
```

Vedi `MEMORY_SETUP.md` sezione "Passare a Long-Term Memory" per i dettagli.
