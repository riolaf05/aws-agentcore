import json
import boto3
import os
from datetime import datetime
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
    Lambda per aggiornare luoghi in DynamoDB.
    
    Payload:
    {
        "place_id": "uuid-del-luogo",
        "nome": "Ristorante La Pergola - Aggiornato",
        "descrizione": "Ristorante stellato...",
        "categoria": "ristorante",
        "indirizzo": "Via Alberto Cadlolo 101, 00136 Roma RM"
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
        
        # Prepara l'update
        update_expressions = []
        expression_values = {}
        expression_names = {}
        
        updatable_fields = ['nome', 'descrizione', 'categoria', 'indirizzo']
        
        for field in updatable_fields:
            if field in body:
                update_expressions.append(f'#{field} = :{field}')
                expression_values[f':{field}'] = body[field]
                expression_names[f'#{field}'] = field
        
        if not update_expressions:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Nessun campo da aggiornare fornito'
                })
            }
        
        # Aggiungi timestamp
        update_expressions.append('#updated_at = :updated_at')
        expression_values[':updated_at'] = datetime.utcnow().isoformat()
        expression_names['#updated_at'] = 'updated_at'
        
        # Esegui l'update
        response = table.update_item(
            Key={'place_id': place_id},
            UpdateExpression='SET ' + ', '.join(update_expressions),
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names,
            ReturnValues='ALL_NEW'
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Luogo aggiornato con successo',
                'place': response['Attributes']
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
