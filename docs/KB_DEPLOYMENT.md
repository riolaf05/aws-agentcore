# Knowledge Base Implementation - Deployment Guide

## Cosa è stato implementato

### 1. Infrastructure (CDK)
- **S3 Bucket** per memorizzare i file PDF
- **DynamoDB Table** (PersonalKBDocuments) per i metadati dei documenti
- **3 Lambda Functions**:
  - `PersonalAssistant-KBPost`: Upload documenti
  - `PersonalAssistant-KBGet`: Recupero documenti
  - `PersonalAssistant-KBDelete`: Eliminazione documenti

### 2. Backend (Flask)
- **3 nuovi endpoint**:
  - `GET /api/kb`: Recupera lista documenti
  - `POST /api/kb`: Carica nuovo documento (PDF o testo)
  - `DELETE /api/kb/<document_id>`: Elimina documento

### 3. Frontend
- **Tabella documenti KB**: Mostra tutti i documenti caricati con data
- **Funzionalità**:
  - Upload PDF o testo
  - Visualizzazione documenti in tabella
  - Eliminazione documenti
  - Aggiornamento automatico dopo upload

## Deployment Steps

### 1. Deploy CDK Stack

```powershell
cd infrastructure/cdk-app
cdk deploy
```

Questo creerà:
- Bucket S3: `personal-assistant-kb-<ACCOUNT_ID>`
- DynamoDB Table: `PersonalKBDocuments`
- 3 Lambda Functions

**Nota**: Prendi nota degli ARN delle Lambda dall'output del deploy.

### 2. Aggiorna Backend

Modifica `chat-frontend/backend.py` con i nuovi ARN:

```python
KB_POST_LAMBDA_ARN = "arn:aws:lambda:REGION:ACCOUNT:function:PersonalAssistant-KBPost"
KB_GET_LAMBDA_ARN = "arn:aws:lambda:REGION:ACCOUNT:function:PersonalAssistant-KBGet"
KB_DELETE_LAMBDA_ARN = "arn:aws:lambda:REGION:ACCOUNT:function:PersonalAssistant-KBDelete"
```

### 3. Avvia Backend

```powershell
cd chat-frontend
python backend.py
```

### 4. Test

1. Apri il frontend: `http://localhost:5000` (o dove è hostato)
2. Vai nella sezione "Knowledge-base"
3. Clicca "Aggiungi" per caricare un PDF o testo
4. Verifica che il documento appaia nella tabella

## Struttura Dati

### DynamoDB Table Schema

```javascript
{
    "document_id": "uuid",
    "created_at": "2024-01-01T12:00:00",
    "tipo": "meeting-notes",
    "is_pdf": true,
    "file_name": "documento.pdf",
    "s3_key": "documents/uuid/documento.pdf",  // solo per PDF
    "text_content": "testo..."  // solo per testo
}
```

### S3 Structure

```
personal-assistant-kb-<account-id>/
  └── documents/
      └── <document_id>/
          └── <filename>.pdf
```

## Features

### Upload
- Supporta PDF e testo
- Valida formato PDF
- Salva PDF in S3
- Salva testo in DynamoDB
- Metadati salvati in DynamoDB

### Visualizzazione
- Tabella con tutti i documenti
- Mostra tipo, nome/contenuto, data
- Icone differenti per PDF e testo

### Eliminazione
- Elimina da S3 (se PDF)
- Elimina da DynamoDB
- Conferma prima dell'eliminazione

## Troubleshooting

### Lambda non trovata
Verifica che gli ARN nel backend.py siano corretti.

### Errore upload
Controlla i permessi Lambda:
- S3: GetObject, PutObject, DeleteObject
- DynamoDB: GetItem, PutItem, DeleteItem, Query, Scan

### Documenti non caricati
Verifica il backend Flask sia in esecuzione e gli endpoint rispondano:
```powershell
curl http://localhost:5000/api/kb
```

## Next Steps

1. Integrare con N8N (se necessario)
2. Aggiungere filtri per tipo documento
3. Implementare ricerca documenti
4. Aggiungere preview PDF
5. Implementare versioning documenti
