# Event & Place Writer Agent

Agente AI specializzato nella gestione di **Eventi** e **Luoghi**.

## Funzionalità

### Eventi
Gestisce eventi con le seguenti operazioni:
- **Crea evento**: Aggiunge nuovi eventi al sistema
- **Leggi evento**: Recupera dettagli di eventi esistenti
- **Aggiorna evento**: Modifica informazioni di eventi
- **Elimina evento**: Rimuove eventi dal sistema

**Campi evento:**
- `nome` (obbligatorio): Nome dell'evento
- `data`: Data dell'evento (formato YYYY-MM-DD)
- `luogo`: Dove si svolge l'evento
- `descrizione`: Descrizione dettagliata

**Feature speciale:** Per generare descrizioni dettagliate degli eventi, l'agente invoca automaticamente l'agente **researcher** per recuperare informazioni online sull'evento.

### Luoghi
Gestisce luoghi con le seguenti operazioni:
- **Crea luogo**: Aggiunge nuovi luoghi al sistema
- **Leggi luogo**: Recupera dettagli di luoghi esistenti
- **Aggiorna luogo**: Modifica informazioni di luoghi
- **Elimina luogo**: Rimuove luoghi dal sistema

**Campi luogo:**
- `nome` (obbligatorio): Nome del luogo
- `descrizione`: Descrizione del luogo
- `categoria`: Tipologia (ristorante, sport, agriturismo, museo, teatro, cinema, etc.)
- `indirizzo`: Indirizzo completo

### Caricamento Multiplo
L'agente supporta il caricamento di più eventi o luoghi in sequenza. Basta fornire una lista e l'agente processerà ogni elemento invocando i tool MCP più volte.

## Esempio d'uso

```
"Crea un evento chiamato AWS Summit Milano per il 15 giugno 2024"

"Aggiungi un ristorante chiamato La Pergola, categoria ristorante, indirizzo Via Cadlolo 101 Roma"

"Carica questi eventi: 1) Concerto U2 il 10 luglio 2024 2) Mostra Van Gogh il 5 agosto 2024"
```

## Deploy

```powershell
cd agents/event-place-writer
agentcore agent deploy
```

## Tool MCP Utilizzati

- `post-event`, `get-event`, `update-event`, `delete-event`
- `post-place`, `get-place`, `update-place`, `delete-place`
