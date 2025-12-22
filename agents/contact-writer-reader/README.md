# Contact Writer/Reader Agent

## Descrizione

Agente specializzato nella gestione dei contatti tramite Gateway MCP.

## Caratteristiche

- **Gateway MCP**: Si connette al Gateway per accedere alle Lambda Contact
- **OAuth2**: Autenticazione tramite Cognito
- **CRUD Completo**: Create, Read, Update, Delete contatti
- **Campi flessibili**: Tutti i campi sono opzionali

## Setup

```powershell
pip install -r requirements.txt

# Deploy
agentcore configure --entrypoint .\agent.py --name contact_writer_reader
agentcore launch
```

## Tool Disponibili

### post-contact
Crea un nuovo contatto. Tutti i campi sono opzionali:
- `nome`: Nome
- `cognome`: Cognome
- `email`: Email
- `telefono`: Telefono
- `descrizione`: Ruolo/Descrizione
- `dove_conosciuto`: Dove/quando conosciuto
- `note`: Note aggiuntive
- `url`: LinkedIn o altro profilo

### get-contact
Recupera contatti con filtri:
- `nome`: Filtra per nome (ricerca parziale)
- `cognome`: Filtra per cognome
- `email`: Filtra per email
- `dove_conosciuto`: Filtra per luogo di conoscenza
- `contact_id`: Recupera contatto specifico
- `limit`: Max risultati (default: 100)

### update-contact
Aggiorna un contatto esistente:
- `contact_id` (required): ID del contatto
- Altri campi opzionali da modificare

### delete-contact
Elimina un contatto:
- `contact_id` (required): ID del contatto da eliminare

## Esempi

### Aggiungi contatto
```json
{"prompt": "Aggiungi un contatto: Mario Rossi, email mario.rossi@example.com, conosciuto al AWS Summit"}
```

### Cerca contatti
```json
{"prompt": "Mostrami tutti i contatti conosciuti al AWS Summit"}
```

### Aggiorna contatto
```json
{"prompt": "Aggiorna il contatto di Mario Rossi con nuovo telefono +39 123 456 7890"}
```
