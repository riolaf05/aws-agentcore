import json
import boto3
import os
from decimal import Decimal
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['PROJECTS_TABLE_NAME']
table = dynamodb.Table(table_name)

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def lambda_handler(event, context):
    """
    Update an existing project in DynamoDB
    Expected parameters in event:
    - project_id (required): ID of the project to update
    - title (optional): New title
    - description (optional): New description
    - github_url (optional): New GitHub URL
    - tech_stack (optional): New tech stack
    - status (optional): New status
    """
    try:
        # Parse body if it's a string
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event
        
        project_id = body.get('project_id')
        
        if not project_id:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Parametro mancante',
                    'message': 'project_id è richiesto'
                })
            }
        
        # Check if project exists
        response = table.get_item(Key={'project_id': project_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'Progetto non trovato',
                    'message': f'Nessun progetto con ID {project_id}'
                })
            }
        
        # Build update expression dynamically
        update_expression_parts = []
        expression_attribute_values = {}
        expression_attribute_names = {}
        
        # Fields mapping: frontend field -> DynamoDB column
        updatable_fields = {
            'ambito': 'ambito',
            'title': 'titolo',
            'description': 'descrizione',
            'github_url': 'github_url',
            'tech_stack': 'tag',
            'status': 'status'
        }
        
        for frontend_field, db_column in updatable_fields.items():
            if frontend_field in body:
                placeholder = f'#{db_column}'
                value_placeholder = f':{db_column}'
                update_expression_parts.append(f'{placeholder} = {value_placeholder}')
                expression_attribute_names[placeholder] = db_column
                expression_attribute_values[value_placeholder] = body[frontend_field]
        
        # Always update updated_at timestamp
        update_expression_parts.append('#updated_at = :updated_at')
        expression_attribute_names['#updated_at'] = 'updated_at'
        expression_attribute_values[':updated_at'] = datetime.utcnow().isoformat()
        
        if not update_expression_parts:
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
            Key={'project_id': project_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues='ALL_NEW'
        )
        
        updated_project = response['Attributes']
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Progetto aggiornato con successo',
                'project': updated_project
            }, cls=DecimalEncoder)
        }
        
    except Exception as e:
        print(f"Error updating project: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Errore interno del server',
                'message': str(e)
            })
        }
