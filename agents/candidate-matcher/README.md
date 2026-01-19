# Candidate Matcher Agent

Agente AI specializzato nel matching tra candidati e needs/posizioni lavorative usando embeddings vettoriali e similarità coseno, con **Short-Term Memory per seguire la conversazione durante l'intervista iniziale**.

## Funzionalità

L'agente:
1. **Raccoglie informazioni** sul candidato attraverso conversazione naturale
2. **Ricorda la conversazione** usando la Short-Term Memory di Bedrock AgentCore
3. **Utilizza il tool MCP** `find_matching_needs` per trovare i 5 migliori needs compatibili
4. **Presenta i risultati** in modo chiaro con percentuale di compatibilità e motivazioni

## Novità: Short-Term Memory

✨ **L'agente ora ricorda tutto durante l'intervista!**

- **Carica il contesto**: All'inizio recupera gli ultimi 5 turni di conversazione
- **Continua naturalmente**: Non ripete domande già fatte
- **Mantiene i dati**: Per 7 giorni di follow-up con lo stesso candidato

## 📖 Documentazione

| Documento | Descrizione |
|-----------|------------|
| [QUICKSTART_MEMORY.md](./QUICKSTART_MEMORY.md) | **START HERE** - Setup in 5 minuti e test |
| [MEMORY_SETUP.md](./MEMORY_SETUP.md) | Setup dettagliato della memory resource |
| [MEMORY_ARCHITECTURE.md](./MEMORY_ARCHITECTURE.md) | Come funziona internamente l'agente |

## ⚙️ Permessi IAM Necessari

Per accedere alla memoria, la **IAM execution role dell'agente** deve avere i seguenti permessi:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:ListEvents",
        "bedrock-agentcore:CreateEvent",
        "bedrock-agentcore:GetMemory",
        "bedrock-agentcore:ListMemories"
      ],
      "Resource": "arn:aws:bedrock-agentcore:REGION:ACCOUNT_ID:memory/MEMORY_ID"
    }
  ]
}
```

**Perché servono questi permessi?**
- `ListEvents`: Permette all'agente di **leggere la cronologia** delle conversazioni salvate
- `CreateEvent`: Permette all'agente di **salvare nuovi turni** di conversazione
- `GetMemory`: Consente di recuperare informazioni sulla configurazione della memoria
- `ListMemories`: Permette di elencare le memorie disponibili

**Come applicare i permessi:**

```bash
# Sostituisci con i tuoi valori
ROLE_NAME="AmazonBedrockAgentCoreSDKRuntime-REGION-xxxxxx"
MEMORY_ID="candidate_matcher_stm-xxxxxxxxxx"
ACCOUNT_ID="123456789012"

# Aggiungi la policy alla role
aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name CandidateMatcherMemoryAccess \
  --policy-document file://memory-policy.json
```

> 💡 **Nota**: Il file `memory-policy.json` viene creato automaticamente dallo script `setup_memory.py`

## Quickstart con Memory

### 1. Setup della Memory (una volta sola)

```bash
# Setup automatico
python agents/candidate-matcher/setup_memory.py

# Oppure manuale
export MEMORY_ID=mem-xxxxxxxxxxxxxxxx
export ACTOR_ID=candidate-matcher
export AWS_REGION=us-east-1
```

### 2. Deploy dell'Agente

```bash
cd agents/candidate-matcher
agentcore launch
```

### 3. Test Multi-Turno

La memory permette una conversazione naturale su più messaggi:

```bash
# Primo turno - definisci il candidato
SESSION="candidate-123-$(date +%s)"
agentcore invoke '{"prompt":"Sono Marco, uno sviluppatore Python senior","session_id":"'$SESSION'"}'

# Secondo turno - l'agente ricorda!
agentcore invoke '{"prompt":"8 anni di esperienza, conosco AWS","session_id":"'$SESSION'"}'

# Terzo turno - continua naturalmente
agentcore invoke '{"prompt":"Parlo correntemente inglese","session_id":"'$SESSION'"}'
```

Se vuoi approfondire la memoria, vedi [MEMORY_SETUP.md](./MEMORY_SETUP.md)

## Schema di Input per il Tool

### Struttura JSON Completa

```json
{
  "candidate": {
    "id": "string (opzionale)",
    "name": "string (opzionale)",
    "surname": "string (opzionale)",
    "current_role": "string (OBBLIGATORIO)",
    "years_experience": "number (opzionale)",
    "province": "string (opzionale, es: MI, RM, TO)",
    "technologies": [
      {"skill_name": "string"}
    ],
    "hard_skills": [
      {"skill_name": "string"}
    ],
    "soft_skills": [
      {"skill_name": "string"}
    ],
    "languages": [
      {
        "language": "string",
        "proficiency": "string"
      }
    ]
  }
}
```

### Campi Obbligatori

⚠️ **CAMPO OBBLIGATORIO:**
- `current_role`: Ruolo attuale del candidato (es: "Senior Python Developer", "Data Scientist", "Project Manager")

### Campi Opzionali

Tutti gli altri campi sono opzionali ma **migliorano la qualità del matching**:

| Campo | Tipo | Descrizione | Esempio |
|-------|------|-------------|---------|
| `id` | string | ID univoco del candidato | "CAND-12345" |
| `name` | string | Nome del candidato | "Mario" |
| `surname` | string | Cognome del candidato | "Rossi" |
| `years_experience` | number | Anni totali di esperienza | 5 |
| `province` | string | Provincia di residenza | "MI", "RM", "TO" |
| `technologies` | array | Tecnologie conosciute | `[{"skill_name": "Python"}, {"skill_name": "AWS"}]` |
| `hard_skills` | array | Competenze tecniche | `[{"skill_name": "Machine Learning"}]` |
| `soft_skills` | array | Competenze trasversali | `[{"skill_name": "Leadership"}]` |
| `languages` | array | Lingue con livello | `[{"language": "Inglese", "proficiency": "C1"}]` |

### Esempi di Input

#### Esempio 1: Input Minimo (solo campo obbligatorio)

```json
{
  "candidate": {
    "current_role": "Senior Python Developer"
  }
}
```

#### Esempio 2: Input Completo

```json
{
  "candidate": {
    "id": "CAND-001",
    "name": "Mario",
    "surname": "Rossi",
    "current_role": "Senior Full Stack Developer",
    "years_experience": 7,
    "province": "MI",
    "technologies": [
      {"skill_name": "Python"},
      {"skill_name": "React"},
      {"skill_name": "AWS"},
      {"skill_name": "Docker"}
    ],
    "hard_skills": [
      {"skill_name": "API REST Design"},
      {"skill_name": "Database PostgreSQL"},
      {"skill_name": "CI/CD"},
      {"skill_name": "Microservices Architecture"}
    ],
    "soft_skills": [
      {"skill_name": "Team Leadership"},
      {"skill_name": "Problem Solving"},
      {"skill_name": "Agile/Scrum"}
    ],
    "languages": [
      {
        "language": "Italiano",
        "proficiency": "Madrelingua"
      },
      {
        "language": "Inglese",
        "proficiency": "C1"
      },
      {
        "language": "Spagnolo",
        "proficiency": "B2"
      }
    ]
  }
}
```

#### Esempio 3: Input Parziale (ruolo + tecnologie + esperienza)

```json
{
  "candidate": {
    "current_role": "Data Scientist",
    "years_experience": 3,
    "technologies": [
      {"skill_name": "Python"},
      {"skill_name": "TensorFlow"},
      {"skill_name": "Pandas"},
      {"skill_name": "SQL"}
    ],
    "hard_skills": [
      {"skill_name": "Machine Learning"},
      {"skill_name": "Deep Learning"},
      {"skill_name": "Data Visualization"}
    ]
  }
}
```

## Installazione

```bash
cd agents/candidate-matcher
pip install -r requirements.txt
```

## Configurazione

L'agente si connette al Gateway MCP con le seguenti credenziali (già configurate):

```python
CLIENT_ID = "40ipvfb7kr5hnjqm06555e5hlp"
CLIENT_SECRET = "6rtmm58udin800qd6eiufv8top19q615m57etqha4fn9opmbi3f"
TOKEN_URL = "https://agentcore-85bb2461.auth.us-east-1.amazoncognito.com/oauth2/token"
GATEWAY_URL = "https://taskapigateway-vveeifneus.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
```

## Test Locale

```bash
python agent.py
```

Poi invia un payload JSON:

```json
{
  "prompt": "Trova i migliori needs per un Senior Python Developer con 5 anni di esperienza, competenze in AWS, Docker e Machine Learning, che parla inglese fluente e risiede a Milano."
}
```

## Esempi di Conversazione

### Conversazione Guidata (l'agente chiede informazioni)

**Utente:** "Ciao, vorrei trovare needs per un candidato"

**Agente:** "Ciao! Sarò felice di aiutarti. Per iniziare, qual è il ruolo attuale del candidato?"

**Utente:** "Senior Full Stack Developer"

**Agente:** "Perfetto! Vuoi aggiungere altre informazioni per migliorare il matching? Ad esempio:
- Anni di esperienza
- Tecnologie conosciute
- Competenze tecniche e trasversali
- Lingue parlate
- Provincia di residenza"

**Utente:** "Sì, ha 7 anni di esperienza, conosce Python, React e AWS, parla inglese fluente e risiede a Milano"

**Agente:** [Usa il tool e presenta i risultati]

### Conversazione Diretta (tutte le info in un prompt)

**Utente:** "Trova i needs per un Data Scientist con 3 anni di esperienza, competenze in Python, TensorFlow, Machine Learning, inglese C1, provincia Milano"

**Agente:** [Usa immediatamente il tool e presenta i risultati]

## Output Atteso

L'agente restituisce i **top 5 needs** più compatibili con:
- **Titolo del need**
- **Azienda**
- **Località**
- **Similarity Score** (percentuale di compatibilità)
- **Motivo del match** (perché questo need è compatibile)

## Deployment su AgentCore Runtime

```bash
agentcore agent deploy \
    --name candidate-matcher \
    --region us-east-1 \
    --entrypoint invoke \
    --path agents/candidate-matcher/
```

## Troubleshooting

### Errore: "current_role is required"

Il campo `current_role` è obbligatorio. Assicurati che l'utente fornisca almeno il ruolo attuale del candidato.

### Errore: "Unauthorized"

Verifica che le credenziali Cognito siano corrette e che il token non sia scaduto.

### Nessun risultato restituito

- Verifica che il candidato abbia un profilo abbastanza dettagliato
- Il tool restituisce fino a 5 needs, se non ci sono match, restituisce array vuoto
- Controlla che ci siano needs nel database MongoDB

## Architettura

```
┌──────────────────┐
│ Candidate Matcher│
│      Agent       │
└────────┬─────────┘
         │ (OAuth2)
         ▼
┌──────────────────────────────┐
│  AgentCore Gateway MCP       │
│  + find_matching_needs tool  │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────┐
│ Candidate Match      │
│   Lambda Function    │
│  - Vector Embeddings │
│  - Cosine Similarity │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│   MongoDB           │
│   (needs collection) │
└──────────────────────┘
```

## Tool MCP: find_matching_needs

Il tool utilizza:
- **Embeddings vettoriali** per rappresentare skills, esperienze e preferenze
- **Similarità coseno** per calcolare la compatibilità tra candidato e needs
- **Ranking** per ordinare i needs dal più al meno compatibile
- **Top 5 results** per presentare solo i migliori match

## Note Importanti

1. **Più informazioni = Match migliore**: Anche se solo `current_role` è obbligatorio, fornire più informazioni (tecnologie, skills, lingue, esperienza) migliora significativamente la qualità del matching.

2. **Formato Skills**: Le skills devono essere array di oggetti con chiave `skill_name`:
   ```json
   [{"skill_name": "Python"}, {"skill_name": "AWS"}]
   ```

3. **Formato Lingue**: Le lingue devono avere sia `language` che `proficiency`:
   ```json
   [{"language": "Inglese", "proficiency": "C1"}]
   ```

4. **Province**: Usa sigle a 2 lettere (MI, RM, TO, etc.)
