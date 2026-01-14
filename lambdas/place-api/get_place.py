import json
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
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
    Lambda per recuperare luoghi da DynamoDB con filtri.
    
    Query params:
    - nome: filtra per nome luogo
    - categoria: filtra per categoria (ristorante, sport, agriturismo, etc.)
    - indirizzo: filtra per indirizzo/posizione
    - place_id: recupera un luogo specifico
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
    categoria = params.get('categoria')
    indirizzo = params.get('indirizzo')
    place_id = params.get('place_id')
    limit = int(params.get('limit', 100))
    
    try:
        # Se è richiesto un luogo specifico
        if place_id:
            response = table.get_item(Key={'place_id': place_id})
            
            if 'Item' in response:
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'place': response['Item']
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
                        'error': 'Luogo non trovato',
                        'place_id': place_id
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
        
        if categoria:
            filter_expressions.append('#categoria = :categoria')
            expression_values[':categoria'] = categoria
            expression_names['#categoria'] = 'categoria'
            
        if indirizzo:
            filter_expressions.append('contains(#indirizzo, :indirizzo)')
            expression_values[':indirizzo'] = indirizzo
            expression_names['#indirizzo'] = 'indirizzo'
        
        # Applica i filtri se presenti
        if filter_expressions:
            scan_kwargs['FilterExpression'] = ' AND '.join(filter_expressions)
            scan_kwargs['ExpressionAttributeValues'] = expression_values
            scan_kwargs['ExpressionAttributeNames'] = expression_names
        
        response = table.scan(**scan_kwargs)
        places = response.get('Items', [])
        
        # Gestisci paginazione
        while 'LastEvaluatedKey' in response and len(places) < limit:
            scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            response = table.scan(**scan_kwargs)
            places.extend(response.get('Items', []))
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'places': places[:limit],
                'count': len(places[:limit])
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
