import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

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
    Lambda per aggiornare eventi in DynamoDB.
    
    Payload:
    {
        "event_id": "uuid-dell-evento",
        "nome": "AWS Summit 2024 - Updated",
        "data": "2024-06-16",
        "luogo": "Milano Convention Center",
        "descrizione": "La più grande conferenza AWS in Italia - aggiornato..."
    }
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Parse request
    if 'body' in event and isinstance(event['body'], str):
        body = json.loads(event['body'])
    else:
        body = event
    
    event_id = body.get('event_id')
    
    if not event_id:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Il campo "event_id" è obbligatorio'
            })
        }
    
    try:
        # Verifica che l'evento esista
        response = table.get_item(Key={'event_id': event_id})
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'Evento non trovato'
                })
            }
        
        # Prepara l'update
        update_expressions = []
        expression_values = {}
        expression_names = {}
        
        updatable_fields = ['nome', 'data', 'luogo', 'descrizione']
        
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
            Key={'event_id': event_id},
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
                'message': 'Evento aggiornato con successo',
                'event': response['Attributes']
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
