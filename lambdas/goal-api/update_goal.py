import json
import boto3
import os
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['GOALS_TABLE_NAME']
table = dynamodb.Table(table_name)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    Update an existing goal in DynamoDB
    Expected parameters in event:
    - goal_id (required): ID of the goal to update
    - title (optional): New title
    - description (optional): New description
    - deadline (optional): New deadline
    - priority (optional): New priority
    - status (optional): New status
    - note (optional): Add a note to note_history
    - note_source (optional): Source of the note (frontend, agent) default: frontend
    """
    try:
        # Parse body if it's a string
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        goal_id = body.get('goal_id')
        
        if not goal_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Parametro mancante',
                    'message': 'goal_id è richiesto'
                })
            }
        
        # Check if goal exists
        response = table.get_item(Key={'goal_id': goal_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Obiettivo non trovato',
                    'message': f'Nessun obiettivo con ID {goal_id}'
                })
            }
        
        existing_goal = response['Item']
        
        # Build update expression dynamically
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        # Fields mapping: frontend field -> DynamoDB column
        updatable_fields = {
            'ambito': 'ambito',
            'title': 'titolo',
            'description': 'descrizione',
            'deadline': 'scadenza',
            'priority': 'priorita',
            'status': 'status',
            'metriche': 'metriche'
        }
        
        for frontend_field, db_column in updatable_fields.items():
            if frontend_field in body:
                placeholder = f'#{db_column}'
                value_placeholder = f':{db_column}'
                update_expression_parts.append(f'{placeholder} = {value_placeholder}')
                expression_attribute_names[placeholder] = db_column
                expression_attribute_values[value_placeholder] = body[frontend_field]
        
        # Gestisci l'aggiunta di una nota alla history
        if 'note' in body and body['note']:
            note_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'note': body['note'],
                'source': body.get('note_source', 'frontend')
            }
            
            # Se note_history non esiste, inizializzala
            if 'note_history' not in existing_goal:
                existing_goal['note_history'] = []
            
            # Aggiungi la nota
            existing_goal['note_history'].append(note_entry)
            
            # Aggiorna l'espressione per note_history
            placeholder = '#note_history'
            value_placeholder = ':note_history'
            update_expression_parts.append(f'{placeholder} = {value_placeholder}')
            expression_attribute_names[placeholder] = 'note_history'
            expression_attribute_values[value_placeholder] = existing_goal['note_history']
        
        # Always update updated_at timestamp
        update_expression_parts.append('#updated_at = :updated_at')
        expression_attribute_names['#updated_at'] = 'updated_at'
        expression_attribute_values[':updated_at'] = datetime.utcnow().isoformat()
        
        if not update_expression_parts or len(update_expression_parts) == 1:
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
            Key={'goal_id': goal_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        updated_goal = response['Attributes']
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Obiettivo aggiornato con successo',
                'goal': updated_goal
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error updating goal: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Errore interno del server',
                'message': str(e)
            })
        }
