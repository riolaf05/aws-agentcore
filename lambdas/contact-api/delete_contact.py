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
table_name = os.environ.get('CONTACTS_TABLE_NAME', 'PersonalContacts')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    """
    Cancella un contatto esistente da DynamoDB
    
    Parametri richiesti:
    - contact_id: ID del contatto da cancellare
    """
    try:
        # Parsing parametri
        if isinstance(event, str):
            event = json.loads(event)
        
        contact_id = event.get('contact_id')
        
        # Validazione
        if not contact_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'contact_id è obbligatorio',
                    'message': 'Specificare l\'ID del contatto da cancellare'
                }, cls=DecimalEncoder)
            }
        
        # Verifica esistenza contatto
        response = table.get_item(Key={'contact_id': contact_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Contatto non trovato',
                    'contact_id': contact_id
                }, cls=DecimalEncoder)
            }
        
        contact = response['Item']
        
        # Cancellazione
        table.delete_item(Key={'contact_id': contact_id})
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Contatto cancellato con successo',
                'contact_id': contact_id,
                'deleted_contact': {
                    'nome': contact.get('nome', ''),
                    'cognome': contact.get('cognome', ''),
                    'email': contact.get('email', '')
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
