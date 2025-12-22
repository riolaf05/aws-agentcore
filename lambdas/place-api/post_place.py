import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
import uuid

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('PLACES_TABLE_NAME', 'PersonalPlaces')
table = dynamodb.Table(table_name)

def decimal_default(obj):
    """Helper per serializzare Decimal in JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    """
    Lambda per creare luoghi in DynamoDB.
    
    Payload:
    {
        "nome": "Ristorante La Pergola",
        "descrizione": "Ristorante stellato con vista panoramica su Roma...",
        "categoria": "ristorante",
        "indirizzo": "Via Alberto Cadlolo 101, 00136 Roma RM"
    }
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Parse request - gestisce sia API Gateway che Gateway MCP
    if 'body' in event and isinstance(event['body'], str):
        body = json.loads(event['body'])
    else:
        body = event
    
    # Estrai i dati del luogo
    nome = body.get('nome', '')
    descrizione = body.get('descrizione', '')
    categoria = body.get('categoria', '')
    indirizzo = body.get('indirizzo', '')
    
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
        # Crea il luogo
        place_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        item = {
            'place_id': place_id,
            'nome': nome,
            'descrizione': descrizione,
            'categoria': categoria,
            'indirizzo': indirizzo,
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
                'message': 'Luogo creato con successo',
                'place': item
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
