import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
import uuid

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('GOALS_TABLE_NAME', 'PersonalGoals')
table = dynamodb.Table(table_name)

def decimal_default(obj):
    """Helper per serializzare Decimal in JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    """
    Lambda per creare obiettivi in DynamoDB.
    
    Payload:
    {
        "ambito": "Reply",
        "titolo": "Aumentare fatturato Q1",
        "descrizione": "Incrementare il fatturato del 20% nel primo trimestre",
        "scadenza": "2025-03-31",
        "metriche": {
            "completamento_percentuale": 0,
            "target_fatturato": 100000,
            "fatturato_attuale": 0
        },
        "priorita": "high",
        "sottotask": [
            {
                "titolo": "Pianificare campagna marketing",
                "scadenza": "2025-01-31",
                "completato": false
            },
            {
                "titolo": "Contattare 50 nuovi lead",
                "scadenza": "2025-02-15",
                "completato": false
            }
        ],
        "note": "Prima nota opzionale sull'obiettivo"
    }
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Parse request - gestisce sia API Gateway che Gateway MCP
    if 'body' in event and isinstance(event['body'], str):
        body = json.loads(event['body'])
    else:
        body = event
    
    # Estrai i dati dell'obiettivo
    ambito = body.get('ambito')
    titolo = body.get('titolo')
    descrizione = body.get('descrizione', '')
    scadenza = body.get('scadenza')  # Format: YYYY-MM-DD
    metriche = body.get('metriche', {})
    priorita = body.get('priorita', 'medium')
    sottotask = body.get('sottotask', [])
    note = body.get('note', '')  # Note iniziali opzionali
    
    # Validazione campi obbligatori
    if not ambito:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Campo "ambito" obbligatorio'})
        }
    
    if not titolo:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Campo "titolo" obbligatorio'})
        }
    
    if not scadenza:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Campo "scadenza" obbligatorio (format: YYYY-MM-DD)'})
        }
    
    # Validazione priorità
    valid_priorities = ['low', 'medium', 'high', 'urgent']
    if priorita not in valid_priorities:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': f'Priorità non valida. Usa: {", ".join(valid_priorities)}'})
        }
    
    # Genera ID univoco
    goal_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Prepara item per DynamoDB
    goal_item = {
        'goal_id': goal_id,
        'ambito': ambito,
        'titolo': titolo,
        'descrizione': descrizione,
        'scadenza': scadenza,
        'metriche': metriche,
        'priorita': priorita,
        'sottotask': sottotask,
        'note_history': [
            {
                'timestamp': timestamp,
                'note': note,
                'source': 'frontend'  # frontend o agent
            }
        ] if note else [],
        'status': 'active',
        'created_at': timestamp,
        'updated_at': timestamp
    }
    
    try:
        # Salva in DynamoDB
        table.put_item(Item=goal_item)
        
        print(f"Goal created successfully: {goal_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Obiettivo creato con successo',
                'goal_id': goal_id,
                'goal': goal_item
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error creating goal: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Errore durante la creazione: {str(e)}'})
        }
