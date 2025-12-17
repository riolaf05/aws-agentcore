import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

# Custom JSON encoder per gestire Decimal di DynamoDB
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('PROJECTS_TABLE_NAME', 'PersonalProjects')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Cancella un progetto esistente da DynamoDB
    
    Parametri richiesti:
    - project_id: ID del progetto da cancellare
    """
    try:
        # Parsing parametri
        if isinstance(event, str):
            event = json.loads(event)
        
        project_id = event.get('project_id')
        
        # Validazione
        if not project_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'project_id è obbligatorio',
                    'message': 'Specificare l\'ID del progetto da cancellare'
                }, cls=DecimalEncoder)
            }
        
        # Verifica esistenza progetto
        response = table.get_item(Key={'project_id': project_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Progetto non trovato',
                    'project_id': project_id
                }, cls=DecimalEncoder)
            }
        
        project = response['Item']
        
        # Cancellazione
        table.delete_item(Key={'project_id': project_id})
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Progetto cancellato con successo',
                'project_id': project_id,
                'deleted_project': {
                    'titolo': project.get('titolo'),
                    'ambito': project.get('ambito'),
                    'github_url': project.get('github_url', '')
                },
                'timestamp': datetime.utcnow().isoformat()
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Errore durante la cancellazione: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Errore interno del server',
                'message': str(e)
            }, cls=DecimalEncoder)
        }
