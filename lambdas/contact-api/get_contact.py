import json
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('CONTACTS_TABLE_NAME', 'PersonalContacts')
table = dynamodb.Table(table_name)

def decimal_default(obj):
    """Helper per serializzare Decimal in JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    """
    Lambda per recuperare contatti da DynamoDB con filtri.
    
    Query params:
    - nome: filtra per nome
    - cognome: filtra per cognome
    - email: filtra per email
    - dove_conosciuto: filtra per luogo/evento di conoscenza
    - contact_id: recupera un contatto specifico
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
    cognome = params.get('cognome')
    email = params.get('email')
    dove_conosciuto = params.get('dove_conosciuto')
    tipo = params.get('tipo')
    contact_id = params.get('contact_id')
    limit = int(params.get('limit', 100))
    
    try:
        # Se è richiesto un contatto specifico
        if contact_id:
            response = table.get_item(Key={'contact_id': contact_id})
            
            if 'Item' in response:
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'count': 1,
                        'contacts': [response['Item']]
                    }, default=decimal_default)
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Contatto non trovato'})
                }
        
        # Altrimenti, scan con filtri
        scan_kwargs = {
            'Limit': limit
        }
        
        # Costruisci espressione di filtro
        filter_expressions = []
        if nome:
            filter_expressions.append(Attr('nome').contains(nome))
        if cognome:
            filter_expressions.append(Attr('cognome').contains(cognome))
        if email:
            filter_expressions.append(Attr('email').contains(email))
        if dove_conosciuto:
            filter_expressions.append(Attr('dove_conosciuto').contains(dove_conosciuto))
        if tipo:
            filter_expressions.append(Attr('tipo').contains(tipo))
        # Applica filtri se presenti
        if filter_expressions:
            filter_expr = filter_expressions[0]
            for expr in filter_expressions[1:]:
                filter_expr = filter_expr & expr
            scan_kwargs['FilterExpression'] = filter_expr
        
        # Esegui scan
        response = table.scan(**scan_kwargs)
        contacts = response.get('Items', [])
        
        # Ordina per data creazione (più recenti prima)
        contacts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        print(f"Found {len(contacts)} contacts")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'count': len(contacts),
                'contacts': contacts,
                'filters_applied': {
                    'nome': nome,
                    'cognome': cognome,
                    'email': email,
                    'dove_conosciuto': dove_conosciuto,
                    'tipo': tipo
                }
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error retrieving contacts: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Errore durante il recupero: {str(e)}'})
        }
