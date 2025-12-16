# Orchestrator Agent

## Descrizione

L'Orchestrator è l'agente principale che coordina l'esecuzione di altri agenti specializzati. Usa `InvokeAgentHook` per delegare task specifici agli agenti appropriati.

## Caratteristiche

- **Memoria**: STM (Short Term Memory) per mantenere il contesto della conversazione
- **Planning**: Analizza la richiesta e crea un piano di azione
- **Multi-Agent Coordination**: Invoca altri agenti in sequenza o parallelo
- **Result Aggregation**: Combina i risultati di più agenti in una risposta coerente

## Agenti Gestiti

1. **task-writer**: Crea task su DynamoDB
2. **task-reader**: Legge task da DynamoDB  
3. **researcher**: Cerca informazioni su internet
4. **calculator**: Esegue calcoli matematici

## Setup

```powershell
# Installa dipendenze
pip install -r requirements.txt

# Test locale
python test_orchestrator.py

# Deploy
agentcore launch
```

## Configurazione

Prima del deploy, aggiorna gli ARN in [`agent.py`](agent.py):

```python
AGENTS = {
    "task-writer": "arn:aws:bedrock-agentcore:us-east-1:...",
    "task-reader": "arn:aws:bedrock-agentcore:us-east-1:...",
    "researcher": "arn:aws:bedrock-agentcore:us-east-1:...",
    "calculator": "arn:aws:bedrock-agentcore:us-east-1:..."
}
```

## Esempi

### Ricerca + Task Creation

```json
{
  "prompt": "Cerca informazioni su Docker Swarm e crea un task per studiarlo"
}
```

### Multi-Step Workflow

```json
{
  "prompt": "Cerca le ultime novità su Python 3.13, calcola quanti giorni mancano a Natale, e crea un task per preparare una presentazione"
}
```

## IAM Permissions

L'execution role deve avere:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agentcore:InvokeAgent"
      ],
      "Resource": [
        "arn:aws:bedrock-agentcore:us-east-1:879338784410:runtime/*"
      ]
    }
  ]
}
```

## Troubleshooting

- **Agent not found**: Verifica ARN in [`agent.py`](agent.py)
- **Access Denied**: Controlla IAM permissions dell'execution role
- **Timeout**: Aumenta timeout in configurazione agent
