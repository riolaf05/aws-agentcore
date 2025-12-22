import json
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('PROJECTS_TABLE_NAME', 'PersonalProjects')
table = dynamodb.Table(table_name)

def decimal_default(obj):
    """Helper per serializzare Decimal in JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    """
    Lambda per recuperare progetti da DynamoDB con filtri.
    
    Query params:
    - ambito: filtra per ambito (es. Reply, MatchGuru)
    - tag: filtra per tecnologia/tag specifico
    - project_id: recupera un progetto specifico
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
    tag = params.get('tag')
    project_id = params.get('project_id')
    limit = int(params.get('limit', 100))
    
    try:
        # Se è richiesto un progetto specifico
        if project_id:
            response = table.get_item(Key={'project_id': project_id})
            
            if 'Item' in response:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'count': 1,
                        'projects': [response['Item']]
                    }, default=decimal_default)
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Progetto non trovato'})
                }
        
        # Altrimenti, scan con filtri
        scan_kwargs = {
            'Limit': limit
        }
        
        # Costruisci espressione di filtro
        filter_expressions = []
        
        if ambito:
            filter_expressions.append(Attr('ambito').eq(ambito))
        
        if tag:
            # Filtra progetti che contengono il tag
            filter_expressions.append(Attr('tag').contains(tag))
        
        # Applica filtri se presenti
        if filter_expressions:
            filter_expr = filter_expressions[0]
            for expr in filter_expressions[1:]:
                filter_expr = filter_expr & expr
            scan_kwargs['FilterExpression'] = filter_expr
        
        # Esegui scan
        response = table.scan(**scan_kwargs)
        projects = response.get('Items', [])
        
        # Ordina per data creazione (più recenti prima)
        projects.sort(key=lambda x: x.get('data_creazione', ''), reverse=True)
        
        print(f"Found {len(projects)} projects")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'count': len(projects),
                'projects': projects,
                'filters_applied': {
                    'ambito': ambito,
                    'tag': tag
                }
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error retrieving projects: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Errore durante il recupero: {str(e)}'})
        }
