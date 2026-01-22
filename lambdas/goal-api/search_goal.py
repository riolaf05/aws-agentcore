import json
import boto3
import os
from boto3.dynamodb.conditions import Attr
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
    Lambda per cercare obiettivi per nome/titolo in DynamoDB.
    Recupera l'ID dell'obiettivo trovato per consentire la modifica.
    
    Query params:
    - titolo: titolo o parte del titolo dell'obiettivo (richiesto)
    - ambito: filtra per ambito (opzionale)
    - status: filtra per status (opzionale)
    - limit: numero massimo di risultati (default: 50)
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Parse request - gestisce sia API Gateway che Gateway MCP
    if 'queryStringParameters' in event:
        params = event.get('queryStringParameters') or {}
    else:
        params = event
    
    # Estrai parametri
    titolo = params.get('titolo')
    ambito = params.get('ambito')
    status = params.get('status')
    limit = int(params.get('limit', 50))
    
    # Validazione parametro obbligatorio
    if not titolo:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'error': 'Parametro mancante',
                'message': 'Parametro "titolo" è richiesto per la ricerca'
            })
        }
    
    try:
        # Costruisci espressione di filtro
        filter_expressions = []
        
        # Filtro per titolo (case-insensitive usando begin_with o contains)
        filter_expressions.append(
            Attr('titolo').contains(titolo)
        )
        
        if ambito:
            filter_expressions.append(Attr('ambito').eq(ambito))
        
        if status:
            filter_expressions.append(Attr('status').eq(status))
        
        # Combina i filtri con AND
        filter_expr = filter_expressions[0]
        for expr in filter_expressions[1:]:
            filter_expr = filter_expr & expr
        
        # Esegui scan con filtri
        scan_kwargs = {
            'FilterExpression': filter_expr,
            'Limit': limit
        }
        
        response = table.scan(**scan_kwargs)
        goals = response.get('Items', [])
        
        # Ordina per scadenza (più vicini prima)
        goals.sort(key=lambda x: x.get('scadenza', '9999-12-31'))
        
        print(f"Found {len(goals)} goals matching '{titolo}'")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'count': len(goals),
                'goals': goals,
                'search_query': titolo,
                'filters_applied': {
                    'ambito': ambito,
                    'status': status
                }
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error searching goals: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Errore durante la ricerca',
                'message': str(e)
            })
        }
