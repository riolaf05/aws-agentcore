# Needs API Lambda

API Lambda per gestire e cercare "needs" (esigenze) memorizzate in MongoDB.

## ⚠️ Informazione Importante

La Lambda è già deployata con il seguente nome:
- **Function Name**: `mg-matchguru-needs-search-dev`
- **ARN**: `arn:aws:lambda:us-east-1:879338784410:function:mg-matchguru-needs-search-dev`
- **Runtime**: Python 3.11

Questa cartella contiene la documentazione e i requisiti. Il codice si trova nel deployment AWS.

## Endpoints Supportati

- 📋 **GET /needs** - Elenca tutti i need disponibili
- 🔍 **GET /needs/{id}** - Recupera un need specifico per ID
- 🔎 **GET /search/{query}** - Cerca need per parola chiave

## Dipendenze

```
pymongo==4.6.1
boto3>=1.28
```

## Setup Agent

Per usare questa Lambda con l'agente `needs-reader`, segui i passaggi in:
- [NEEDS_GATEWAY_DEPLOYMENT.md](../../docs/NEEDS_GATEWAY_DEPLOYMENT.md)

## Testing

```bash
# Test la Lambda direttamente
aws lambda invoke \
    --function-name mg-matchguru-needs-search-dev \
    --payload '{"rawPath": "/needs", "requestContext": {"http": {"method": "GET"}}}' \
    response.json

cat response.json | jq .

# Test completo
python scripts/test_needs_api.py
```

## Configurazione del Gateway

Vedi [docs/NEEDS_GATEWAY_DEPLOYMENT.md](../../docs/NEEDS_GATEWAY_DEPLOYMENT.md) per:
1. Verificare/Creare il Gateway MCP
2. Configurare i target Lambda
3. Integrare con l'agente needs-reader

## Monitoraggio

### CloudWatch Logs

```bash
# Visualizza i log in tempo reale
aws logs tail /aws/lambda/mg-matchguru-needs-search-dev --follow

# Filtra gli errori
aws logs filter-log-events \
    --log-group-name /aws/lambda/mg-matchguru-needs-search-dev \
    --filter-pattern "ERROR"
```

### Invocare la Lambda

```bash
# List all needs
aws lambda invoke \
    --function-name mg-matchguru-needs-search-dev \
    --payload '{"rawPath": "/needs", "requestContext": {"http": {"method": "GET"}}}' \
    response.json

# Get by ID
aws lambda invoke \
    --function-name mg-matchguru-needs-search-dev \
    --payload '{"rawPath": "/needs/12345", "requestContext": {"http": {"method": "GET"}}}' \
    response.json

# Search by keyword
aws lambda invoke \
    --function-name mg-matchguru-needs-search-dev \
    --payload '{"rawPath": "/search/Python", "requestContext": {"http": {"method": "GET"}}}' \
    response.json
```

## Troubleshooting

### Errore: "Impossibile connettersi a MongoDB"
- Verifica che MongoDB sia raggiungibile dalla Lambda
- Controlla i Security Groups
- Verifica le credenziali in Secrets Manager

### Errore: "Parametro non trovato"
- Se `USE_PARAMETER_STORE=true`, verifica che i parametri esistano in Parameter Store

### Performance lenta
- Crea indici MongoDB sui campi ricercati
- Aumenta Memory della Lambda (CloudWatch → Metrics)

## Riferimenti

- [MongoDB Python Driver](https://docs.mongodb.com/drivers/python/)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/)
- [AgentCore Gateway Setup](../../docs/NEEDS_GATEWAY_DEPLOYMENT.md)
