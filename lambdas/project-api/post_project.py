import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
import uuid

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
    Lambda per creare progetti in DynamoDB.
    
    Payload:
    {
        "ambito": "Reply",
        "titolo": "Sistema di Analytics",
        "github_url": "https://github.com/user/analytics-system",
        "descrizione": "Sistema di analytics real-time con dashboard interattive",
        "tag": ["Python", "AWS", "React", "DynamoDB"]
    }
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Parse request - gestisce sia API Gateway che Gateway MCP
    if 'body' in event and isinstance(event['body'], str):
        body = json.loads(event['body'])
    else:
        body = event
    
    # Estrai i dati del progetto
    ambito = body.get('ambito')
    titolo = body.get('titolo')
    github_url = body.get('github_url', '')
    descrizione = body.get('descrizione', '')
    tag = body.get('tag', [])
    
    # Validazione campi obbligatori
    if not ambito:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Campo "ambito" obbligatorio'})
        }
    
    if not titolo:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Campo "titolo" obbligatorio'})
        }
    
    # Validazione tag (deve essere lista)
    if not isinstance(tag, list):
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Campo "tag" deve essere un array'})
        }
    
    # Genera ID univoco
    project_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Prepara item per DynamoDB
    project_item = {
        'project_id': project_id,
        'ambito': ambito,
        'titolo': titolo,
        'github_url': github_url,
        'descrizione': descrizione,
        'tag': tag,
        'data_creazione': timestamp,
        'updated_at': timestamp
    }
    
    try:
        # Salva in DynamoDB
        table.put_item(Item=project_item)
        
        print(f"Project created successfully: {project_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Progetto creato con successo',
                'project_id': project_id,
                'project': project_item
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error creating project: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Errore durante la creazione: {str(e)}'})
        }
