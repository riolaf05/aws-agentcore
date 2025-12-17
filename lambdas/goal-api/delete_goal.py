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
table_name = os.environ.get('GOALS_TABLE_NAME', 'PersonalGoals')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Cancella un obiettivo esistente da DynamoDB
    
    Parametri richiesti:
    - goal_id: ID dell'obiettivo da cancellare
    """
    try:
        # Parsing parametri
        if isinstance(event, str):
            event = json.loads(event)
        
        goal_id = event.get('goal_id')
        
        # Validazione
        if not goal_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'goal_id è obbligatorio',
                    'message': 'Specificare l\'ID dell\'obiettivo da cancellare'
                }, cls=DecimalEncoder)
            }
        
        # Verifica esistenza obiettivo
        response = table.get_item(Key={'goal_id': goal_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Obiettivo non trovato',
                    'goal_id': goal_id
                }, cls=DecimalEncoder)
            }
        
        goal = response['Item']
        
        # Cancellazione
        table.delete_item(Key={'goal_id': goal_id})
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Obiettivo cancellato con successo',
                'goal_id': goal_id,
                'deleted_goal': {
                    'titolo': goal.get('titolo'),
                    'ambito': goal.get('ambito'),
                    'scadenza': goal.get('scadenza')
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
