import json
import boto3
import os
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['CONTACTS_TABLE_NAME']
table = dynamodb.Table(table_name)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    Update an existing contact in DynamoDB
    Expected parameters in event:
    - contact_id (required): ID of the contact to update
    - nome, cognome, email, telefono, descrizione, dove_conosciuto, note, url (all optional)
    """
    try:
        # Parse body if it's a string
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        contact_id = body.get('contact_id')
        
        if not contact_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Parametro mancante',
                    'message': 'contact_id è richiesto'
                })
            }
        
        # Check if contact exists
        response = table.get_item(Key={'contact_id': contact_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Contatto non trovato',
                    'message': f'Nessun contatto con ID {contact_id}'
                })
            }
        
        # Build update expression dynamically
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        # All fields are updatable
        updatable_fields = [
            'nome', 'cognome', 'email', 'telefono', 
            'descrizione', 'dove_conosciuto', 'note', 'url', 'tipo'
        ]
        
        for field in updatable_fields:
            if field in body:
                placeholder = f'#{field}'
                value_placeholder = f':{field}'
                update_expression_parts.append(f'{placeholder} = {value_placeholder}')
                expression_attribute_names[placeholder] = field
                expression_attribute_values[value_placeholder] = body[field]
        
        # Always update updated_at timestamp
        update_expression_parts.append('#updated_at = :updated_at')
        expression_attribute_names['#updated_at'] = 'updated_at'
        expression_attribute_values[':updated_at'] = datetime.utcnow().isoformat()
        
        if len(update_expression_parts) == 1:  # Only timestamp
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Nessun campo da aggiornare',
                    'message': 'Fornire almeno un campo da modificare'
                })
            }
        
        update_expression = 'SET ' + ', '.join(update_expression_parts)
        
        # Perform update
        response = table.update_item(
            Key={'contact_id': contact_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        updated_contact = response['Attributes']
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Contatto aggiornato con successo',
                'contact': updated_contact
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error updating contact: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Errore interno del server',
                'message': str(e)
            })
        }
