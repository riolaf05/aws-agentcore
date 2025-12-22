import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
import uuid

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('EVENTS_TABLE_NAME', 'PersonalEvents')
table = dynamodb.Table(table_name)

def decimal_default(obj):
    """Helper per serializzare Decimal in JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    """
    Lambda per creare eventi in DynamoDB.
    
    Payload:
    {
        "nome": "AWS Summit 2024",
        "data": "2024-06-15",
        "luogo": "Milano Convention Center",
        "descrizione": "La più grande conferenza AWS in Italia..."
    }
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Parse request - gestisce sia API Gateway che Gateway MCP
    if 'body' in event and isinstance(event['body'], str):
        body = json.loads(event['body'])
    else:
        body = event
    
    # Estrai i dati dell'evento
    nome = body.get('nome', '')
    data = body.get('data', '')
    luogo = body.get('luogo', '')
    descrizione = body.get('descrizione', '')
    
    # Validazione
    if not nome:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Il campo "nome" è obbligatorio'
            })
        }
    
    try:
        # Crea l'evento
        event_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'event_id': event_id,
            'nome': nome,
            'data': data,
            'luogo': luogo,
            'descrizione': descrizione,
            'created_at': timestamp,
            'updated_at': timestamp
        }
        
        # Salva in DynamoDB
        table.put_item(Item=item)
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Evento creato con successo',
                'event': item
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Errore interno del server',
                'details': str(e)
            })
        }
