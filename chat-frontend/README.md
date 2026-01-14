# Chat Frontend per Orchestrator

Interfaccia web per interagire con l'Orchestrator Agent tramite chat.

## 🚀 Avvio Rapido

### 1. Installa dipendenze backend

```powershell
pip install -r requirements.txt
```

### 2. Configura l'ARN dell'Orchestrator

Apri `backend.py` e aggiorna:

```python
ORCHESTRATOR_ARN = "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/orchestrator-XXXXX"
```

Con il tuo ARN dell'orchestrator deployato.

### 3. Avvia il backend proxy

```powershell
python backend.py
```

Il backend sarà disponibile su `http://localhost:5000`

### 4. Apri la Chat

Apri `index.html` nel browser (doppio click o):

```powershell
start index.html
```

Oppure usa un server HTTP locale:

```powershell
# Python
python -m http.server 3000

# Node.js
npx http-server -p 3000
```

Poi apri: http://localhost:3000

## 💡 Funzionalità

- **Chat interattiva**: Interfaccia moderna e responsive
- **Gestione sessioni**: Ogni sessione mantiene la memoria della conversazione
- **Status indicator**: Mostra se l'orchestrator è raggiungibile
- **Nuova sessione**: Resetta la conversazione mantenendo l'orchestrator attivo
- **Error handling**: Gestione errori con messaggi user-friendly

## 🎯 Esempi di Utilizzo

### Creare Task
```
Crea un task per comprare il pane domani
```

### Ricerca + Task
```
Cerca le novità su Python 3.13 e crea un task per studiarle
```

### Lettura Task
```
Mostrami tutti i task con priorità alta
```

### Calcoli
```
Quanto fa 156 * 234?
```

### Conversazione con Memoria
```
1. "Mi chiamo Rosario"
2. "Come mi chiamo?" → Risponde "Rosario"
```

## ⚙️ Configurazione

### Backend (backend.py)
```python
ORCHESTRATOR_ARN = "arn:..."  # ARN orchestrator deployato
REGION = "us-east-1"
```

### Frontend (app.js)
```javascript
const CONFIG = {
    ORCHESTRATOR_URL: 'http://localhost:5000/invoke',
    ACTOR_ID: 'chat-user'
};
```

## 🔧 Troubleshooting

**Errore: "Disconnesso"**
- Verifica che il backend proxy sia avviato su porta 5000
- Controlla che l'ORCHESTRATOR_ARN in backend.py sia corretto
- Verifica le credenziali AWS (il backend usa boto3)

**Errore CORS**
- Se usi Chrome, avvialo con: `chrome.exe --disable-web-security --user-data-dir="%TEMP%\chrome-dev"`
- Oppure usa un server HTTP locale invece di aprire direttamente l'HTML

**L'orchestrator non ricorda**
- Verifica che `memory-config.json` abbia il memory ID corretto
- Controlla i log dell'orchestrator per errori di memoria

## 📝 Note

- La memoria della conversazione è persistente finché usi lo stesso `session_id`
- Clicca "Nuova Sessione" per iniziare una nuova conversazione
- I session ID sono univoci e generati automaticamente
