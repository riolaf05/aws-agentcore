# 📝 Goal Notes Update - Struttura Modificata

## 📋 Sommario delle Modifiche

Implementazione completa della funzionalità di **note agli obiettivi** per tracciare gli aggiornamenti di progresso. Gli utenti possono ora aggiungere note:
- ✏️ **Manualmente dal frontend**
- 🤖 **Tramite agente (orchestrator)**

---

## 🔧 Modifiche Implementate

### 1. **Lambda Functions**

#### ✅ [lambdas/goal-api/post_goal.py](lambdas/goal-api/post_goal.py)
- ✨ Aggiunto parametro `note` opzionale per note iniziali
- ✨ Creazione di `note_history` come lista di oggetti con:
  - `timestamp`: quando è stata aggiunta la nota
  - `note`: testo della nota
  - `source`: "frontend" o "agent"

**Esempio payload:**
```json
{
  "ambito": "Reply",
  "titolo": "Aumentare fatturato Q1",
  "descrizione": "...",
  "scadenza": "2025-03-31",
  "priorita": "high",
  "note": "Prima nota opzionale"
}
```

---

#### ✅ [lambdas/goal-api/update_goal.py](lambdas/goal-api/update_goal.py)
- ✨ Parametro `note` per aggiungere nuove note alla history
- ✨ Parametro `note_source` opzionale (default: "frontend")
- ✨ Le note vengono accumulate in `note_history` con timestamp automatico

**Esempio payload:**
```json
{
  "goal_id": "abc-123",
  "title": "Nuovo titolo",
  "note": "Ho contattato 10 nuovi lead",
  "note_source": "frontend"
}
```

---

#### ✨ **NUOVO** [lambdas/goal-api/search_goal.py](lambdas/goal-api/search_goal.py)
- 🔍 Ricerca per **titolo/nome** dell'obiettivo
- 📊 Supporta filtri aggiuntivi: ambito, status, limit
- 🎯 Essenziale per permettere agenti e frontend di trovare l'ID dell'obiettivo per modificarlo

**Parametri:**
- `titolo` (obbligatorio): titolo o parte del titolo
- `ambito` (opzionale): filtra per ambito
- `status` (opzionale): filtra per status
- `limit` (default: 50): numero massimo risultati

**Esempio risposta:**
```json
{
  "count": 1,
  "goals": [
    {
      "goal_id": "abc-123",
      "titolo": "Aumentare fatturato Q1",
      "ambito": "Reply",
      "note_history": [
        {
          "timestamp": "2025-01-20T10:30:00",
          "note": "Prima nota",
          "source": "frontend"
        }
      ]
    }
  ]
}
```

---

### 2. **Backend Flask** [chat-frontend/backend.py](chat-frontend/backend.py)

#### ✨ Nuovi Endpoints

**GET `/api/goals/search`**
- Ricerca obiettivi per titolo
- Query params: `titolo`, `ambito`, `status`, `limit`
- Ritorna lista di obiettivi con `goal_id` per successive modifiche

```bash
GET /api/goals/search?titolo=Q1&ambito=Reply
```

**POST `/api/goals/<goal_id>/notes`**
- Aggiunge una nota a un obiettivo esistente
- Body: `{ "note": "testo nota", "note_source": "frontend" }`
- Equivalente a una PUT con parametro `note`

```bash
POST /api/goals/abc-123/notes
Content-Type: application/json
{
  "note": "Ho completato l'analisi di mercato",
  "note_source": "frontend"
}
```

#### ✨ Aggiornamento ARN Lambda
- `GOAL_SEARCH_LAMBDA_ARN` aggiunto alla configurazione

---

### 3. **Orchestrator Agent** [agents/orchestrator/agent.py](agents/orchestrator/agent.py)

#### ✨ System Prompt Aggiornato
- 📖 Documentazione completa della funzionalità di note
- 🎯 Esempi di routing per:
  - Ricerca obiettivo per nome
  - Aggiunta di note agli obiettivi
  - Aggiornamento stato con nota di progresso

**Nuovi esempi di comandi:**
```
"Aggiungi una nota all'obiettivo Q1 sales: Ho contattato 10 nuovi lead"
→ invoke_agent("project-goal-writer-reader", "Cerca l'obiettivo 'Aumentare fatturato Q1' e aggiungi nota: 'Ho contattato 10 nuovi lead'")

"Aggiorna lo stato dell'obiettivo Progetto AI con nota di progresso"
→ invoke_agent("project-goal-writer-reader", "...")
```

---

### 4. **Project-Goal-Writer-Reader Agent** [agents/project-goal-writer-reader/agent.py](agents/project-goal-writer-reader/agent.py)

#### ✨ System Prompt Completamente Riscritto

Aggiunto flusso di lavoro dettagliato:

```
FLUSSO DI LAVORO:
1. Se l'utente vuole aggiungere una nota a un obiettivo:
   a. Usa search-goal per cercare l'obiettivo per nome
   b. Recupera l'ID dell'obiettivo dai risultati
   c. Usa update-goal con il parametro "note" per aggiungere la nota
   d. La nota verrà aggiunta alla history con timestamp e fonte (frontend/agent)

2. Se l'utente vuole visualizzare le note di un obiettivo:
   a. Usa search-goal o get-goal per recuperare l'obiettivo
   b. Mostra il campo "note_history" che contiene tutte le note con timestamp
```

**Tools disponibili:**
- `post-goal`: creare nuovo obiettivo
- `get-goal`: leggere obiettivi (con filtri)
- `search-goal`: 🆕 cercare per titolo
- `update-goal`: aggiornare obiettivo + aggiungere note
- `delete-goal`: eliminare obiettivo

---

### 5. **Frontend Web** [chat-frontend/index.html](chat-frontend/index.html)

#### ✨ Modal di Edit Obiettivo Aggiornato

**Nuovi elementi nel form:**
1. **Campo note** - Textarea per aggiungere nuove note
   ```html
   <textarea id="editGoalNote" rows="3" 
     placeholder="Descrivi il progresso o gli aggiornamenti..."></textarea>
   ```

2. **Sezione Storico Note** - Visualizzazione read-only della history
   - Mostra tutte le note precedenti
   - Badge che indica se aggiunta da "frontend" o "agent"
   - Timestamp formattato
   - Testo della nota

**UI Elements:**
- 📝 Label con icona per il campo note
- 📋 Sezione collassabile con storico
- Badge colorate: 👤 Frontend (blue), 🤖 Agent (green)
- Timestamps leggibili

---

### 6. **Frontend JavaScript** [chat-frontend/app.js](chat-frontend/app.js)

#### ✨ Funzioni Aggiornate

**`editGoal(goalId)`**
- Carica l'obiettivo dal backend
- Popola i campi della form
- **Nuovo:** Mostra storico note con formattazione
- **Nuovo:** Badge che indica source (frontend/agent)

**`handleUpdateGoal(e)`**
- Cattura il valore dal campo note
- **Nuovo:** Se nota presente, aggiunge parametri:
  - `note`: testo della nota
  - `note_source`: "frontend"
- Invia la PUT al backend con nota inclusa

---

### 7. **Stili CSS** [chat-frontend/modal-styles.css](chat-frontend/modal-styles.css)

#### ✨ Nuovi Stili per Note

```css
.notes-header          /* Header della sezione */
.notes-history         /* Container storico (scrollable) */
.note-item            /* Singolo item della nota */
.note-timestamp       /* Timestamp formattato */
.note-source          /* Badge fonte della nota */
.note-source.agent    /* Variante per note da agente */
.note-content         /* Testo della nota con word-wrap */
```

**Caratteristiche:**
- Max-height 300px con scroll custom
- Design card minimalista
- Colori distintivi per source (frontend vs agent)
- Preserva white-space per note multi-riga

---

## 🔄 Flusso di Lavoro Completo

### Scenario 1: Aggiunta di Nota da Frontend

```
1. User → Frontend: "Modifica obiettivo Q1"
   ↓
2. editGoal(id) → GET /api/goals?goal_id=xxx
   ↓
3. Mostra modal con storico note e campo per nuova nota
   ↓
4. User scrive nota: "Ho contattato 10 lead"
   ↓
5. handleUpdateGoal() → PUT /api/goals
   {
     "goal_id": "xxx",
     "note": "Ho contattato 10 lead",
     "note_source": "frontend"
   }
   ↓
6. Lambda update_goal.py aggiunge nota a note_history
   ↓
7. DynamoDB: note_history aggiornata con timestamp
```

---

### Scenario 2: Aggiunta di Nota da Orchestrator

```
1. User → Orchestrator: "Aggiorna obiettivo Q1 con nota"
   ↓
2. Orchestrator → invoke_agent("project-goal-writer-reader", ...)
   ↓
3. Agent:
   a. invoke search-goal(titolo="Q1")
   b. Riceve goal_id da risultati
   c. invoke update-goal(goal_id, note="...", note_source="agent")
   ↓
4. Lambda update_goal.py:
   - Aggiunge nota a note_history
   - source = "agent"
   - Timestamp automatico
   ↓
5. DynamoDB aggiornata
```

---

## 📊 Struttura Dati Goal

### Prima
```json
{
  "goal_id": "xxx",
  "ambito": "Reply",
  "titolo": "Aumentare fatturato Q1",
  "descrizione": "...",
  "scadenza": "2025-03-31",
  "priorita": "high",
  "status": "active",
  "sottotask": [...],
  "metriche": {...},
  "created_at": "2025-01-20T...",
  "updated_at": "2025-01-20T..."
}
```

### Dopo ✨
```json
{
  "goal_id": "xxx",
  "ambito": "Reply",
  "titolo": "Aumentare fatturato Q1",
  "descrizione": "...",
  "scadenza": "2025-03-31",
  "priorita": "high",
  "status": "active",
  "sottotask": [...],
  "metriche": {...},
  "note_history": [                      // 🆕 NUOVO CAMPO
    {
      "timestamp": "2025-01-20T10:30:00",
      "note": "Ho contattato 10 nuovi lead",
      "source": "frontend"                // frontend o agent
    },
    {
      "timestamp": "2025-01-21T14:15:00",
      "note": "Completata analisi competitor",
      "source": "agent"
    }
  ],
  "created_at": "2025-01-20T...",
  "updated_at": "2025-01-21T14:15:00"   // Aggiornato ad ogni modifica
}
```

---

## 🚀 Deploy Checklist

### Lambda Functions
- [ ] Deploy `search_goal.py` come nuova Lambda
- [ ] Deploy aggiornato `post_goal.py`
- [ ] Deploy aggiornato `update_goal.py`
- [ ] Aggiornare ARN in backend.py: `GOAL_SEARCH_LAMBDA_ARN`
- [ ] Verificare permessi IAM (DynamoDB Scan)

### Backend
- [ ] Deploy aggiornato `backend.py` con nuovi endpoint
- [ ] Testare GET `/api/goals/search`
- [ ] Testare POST `/api/goals/<id>/notes`

### Frontend
- [ ] Deploy aggiornato `index.html` con nuova UI
- [ ] Deploy aggiornato `app.js` con nuove funzioni
- [ ] Deploy aggiornato `modal-styles.css` con nuovi stili
- [ ] Testare aggiunta nota nel modal

### Agenti
- [ ] Deploy aggiornato `orchestrator/agent.py`
- [ ] Deploy aggiornato `project-goal-writer-reader/agent.py`
- [ ] Testare invocazione con nota

---

## 🧪 Test Cases

### Test 1: Creare Obiettivo con Nota Iniziale
```bash
curl -X POST http://localhost:5000/api/goals \
  -H "Content-Type: application/json" \
  -d '{
    "ambito": "Reply",
    "titolo": "Test Goal",
    "scadenza": "2025-03-31",
    "note": "Nota iniziale"
  }'
```
✅ Response: goal_id + note_history con 1 item

---

### Test 2: Ricerca per Titolo
```bash
curl "http://localhost:5000/api/goals/search?titolo=Q1"
```
✅ Response: Lista goals con goal_id + note_history

---

### Test 3: Aggiungere Nota via Frontend
```bash
curl -X PUT http://localhost:5000/api/goals \
  -H "Content-Type: application/json" \
  -d '{
    "goal_id": "xxx",
    "note": "Ho contattato 10 lead",
    "note_source": "frontend"
  }'
```
✅ Response: Goal aggiornato con nota in note_history

---

### Test 4: Aggiungere Nota via Agent
Simulare orchestrator che chiama project-goal-writer-reader:
1. Search-goal per nome
2. Riceve goal_id
3. Update-goal con note_source="agent"
✅ Verifica note_history con source="agent"

---

## 📝 Note Tecniche

### DynamoDB
- `note_history` è una lista (L) di mappe (M)
- Ogni nota è una mappa con 3 attributi stringa
- Non c'è GSI/index specifico (non necessario, già filtrato su goal_id)
- TTL non implementato (note rimangono indefinitivamente)

### Limiti
- Nessun limite numero di note per goal (considerare per scalabilità)
- Dimensione massima goal item: 400KB (DynamoDB)
- ~2000 note di ~500 bytes ciascuna per goal

### Sicurezza
- Le note non contengono identificatori sensibili
- note_source è indicativo (non per autorizzazione)
- Backend valida goal_id prima di aggiornamento

---

## 🎯 Prossimi Passi (Optional)

1. **Ricerca nelle note** - Implementare search/filter su note_history
2. **Editing note** - Permettere modifica di note precedenti
3. **Delete note** - Rimuovere note specifiche
4. **Versioning** - Tracciare chi ha modificato cosa
5. **Mentions** - @mention altri utenti nelle note
6. **Rich text** - Supporto per Markdown nelle note

---

## 📞 Supporto

Per problemi o domande:
1. Verificare ARN Lambda aggiornati
2. Controllare permessi IAM DynamoDB
3. Verificare formati JSON nei payload
4. Testare endpoint con curl/Postman

