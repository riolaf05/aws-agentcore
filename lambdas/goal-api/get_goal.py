import json
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

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
    Lambda per recuperare obiettivi da DynamoDB con filtri.
    
    Query params:
    - ambito: filtra per ambito (es. Reply, matchguru)
    - status: filtra per status (active, completed, cancelled)
    - priorita: filtra per priorità (low, medium, high, urgent)
    - goal_id: recupera un obiettivo specifico
    - limit: numero massimo di risultati (default: 100)
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Parse request - gestisce sia API Gateway che Gateway MCP
    if 'queryStringParameters' in event:
        params = event.get('queryStringParameters') or {}
    else:
        params = event
    
    # Estrai parametri
    ambito = params.get('ambito')
    status = params.get('status')
    priorita = params.get('priorita')
    goal_id = params.get('goal_id')
    limit = int(params.get('limit', 100))
    
    try:
        # Se è richiesto un goal specifico
        if goal_id:
            response = table.get_item(Key={'goal_id': goal_id})
            
            if 'Item' in response:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'count': 1,
                        'goals': [response['Item']]
                    }, default=decimal_default)
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Obiettivo non trovato'})
                }
        
        # Altrimenti, scan con filtri
        scan_kwargs = {
            'Limit': limit
        }
        
        # Costruisci espressione di filtro
        filter_expressions = []
        
        if ambito:
            filter_expressions.append(Attr('ambito').eq(ambito))
        
        if status:
            filter_expressions.append(Attr('status').eq(status))
        
        if priorita:
            filter_expressions.append(Attr('priorita').eq(priorita))
        
        # Applica filtri se presenti
        if filter_expressions:
            filter_expr = filter_expressions[0]
            for expr in filter_expressions[1:]:
                filter_expr = filter_expr & expr
            scan_kwargs['FilterExpression'] = filter_expr
        
        # Esegui scan
        response = table.scan(**scan_kwargs)
        goals = response.get('Items', [])
        
        # Ordina per scadenza (più vicini prima)
        goals.sort(key=lambda x: x.get('scadenza', '9999-12-31'))
        
        print(f"Found {len(goals)} goals")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'count': len(goals),
                'goals': goals,
                'filters_applied': {
                    'ambito': ambito,
                    'status': status,
                    'priorita': priorita
                }
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error retrieving goals: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Errore durante il recupero: {str(e)}'})
        }
