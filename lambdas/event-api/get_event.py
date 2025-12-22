import json
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
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
    Lambda per recuperare eventi da DynamoDB con filtri.
    
    Query params:
    - nome: filtra per nome evento
    - luogo: filtra per luogo
    - data_inizio: filtra eventi da questa data
    - data_fine: filtra eventi fino a questa data
    - event_id: recupera un evento specifico
    - limit: numero massimo di risultati (default: 100)
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Parse request - gestisce sia API Gateway che Gateway MCP
    if 'queryStringParameters' in event:
        params = event.get('queryStringParameters') or {}
    else:
        params = event
    
    # Estrai parametri
    nome = params.get('nome')
    luogo = params.get('luogo')
    data_inizio = params.get('data_inizio')
    data_fine = params.get('data_fine')
    event_id = params.get('event_id')
    limit = int(params.get('limit', 100))
    
    try:
        # Se è richiesto un evento specifico
        if event_id:
            response = table.get_item(Key={'event_id': event_id})
            
            if 'Item' in response:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'event': response['Item']
                    }, default=decimal_default)
                }
            else:
                return {
                    'statusCode': 404,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'error': 'Evento non trovato',
                        'event_id': event_id
                    })
                }
        
        # Altrimenti scan con filtri
        scan_kwargs = {
            'Limit': limit
        }
        
        # Costruisci i filtri
        filter_expressions = []
        expression_values = {}
        expression_names = {}
        
        if nome:
            filter_expressions.append('contains(#nome, :nome)')
            expression_values[':nome'] = nome
            expression_names['#nome'] = 'nome'
        
        if luogo:
            filter_expressions.append('contains(#luogo, :luogo)')
            expression_values[':luogo'] = luogo
            expression_names['#luogo'] = 'luogo'
            
        if data_inizio:
            filter_expressions.append('#data >= :data_inizio')
            expression_values[':data_inizio'] = data_inizio
            expression_names['#data'] = 'data'
            
        if data_fine:
            filter_expressions.append('#data <= :data_fine')
            expression_values[':data_fine'] = data_fine
            expression_names['#data'] = 'data'
        
        # Applica i filtri se presenti
        if filter_expressions:
            scan_kwargs['FilterExpression'] = ' AND '.join(filter_expressions)
            scan_kwargs['ExpressionAttributeValues'] = expression_values
            scan_kwargs['ExpressionAttributeNames'] = expression_names
        
        response = table.scan(**scan_kwargs)
        events = response.get('Items', [])
        
        # Gestisci paginazione
        while 'LastEvaluatedKey' in response and len(events) < limit:
            scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = table.scan(**scan_kwargs)
            events.extend(response.get('Items', []))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'events': events[:limit],
                'count': len(events[:limit])
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
