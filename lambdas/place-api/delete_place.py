import json
import boto3
import os
from decimal import Decimal

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
    Lambda per eliminare luoghi da DynamoDB.
    
    Payload:
    {
        "place_id": "uuid-del-luogo"
    }
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Parse request
    if 'body' in event and isinstance(event['body'], str):
        body = json.loads(event['body'])
    else:
        body = event
    
    place_id = body.get('place_id')
    
    if not place_id:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Il campo "place_id" è obbligatorio'
            })
        }
    
    try:
        # Verifica che il luogo esista
        response = table.get_item(Key={'place_id': place_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Luogo non trovato'
                })
            }
        
        deleted_place = response['Item']
        
        # Elimina il luogo
        table.delete_item(Key={'place_id': place_id})
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Luogo eliminato con successo',
                'deleted_place': deleted_place
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
