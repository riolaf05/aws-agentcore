import json
import boto3
import os
from datetime import datetime
from decimal import Decimal
import uuid

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
    Lambda per creare contatti in DynamoDB.
    
    Payload:
    {
        "nome": "Mario",
        "cognome": "Rossi",
        "email": "mario.rossi@example.com",
        "telefono": "+39 123 456 7890",
        "descrizione": "CEO di TechCompany",
        "dove_conosciuto": "Conferenza AWS Summit 2024",
        "note": "Interessato a collaborazioni su AI",
        "url": "https://linkedin.com/in/mariorossi"
    }
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Parse request - gestisce sia API Gateway che Gateway MCP
    if 'body' in event and isinstance(event['body'], str):
        body = json.loads(event['body'])
    else:
        body = event
    
    # Estrai i dati del contatto (tutti opzionali)
    nome = body.get('nome', '')
    cognome = body.get('cognome', '')
    email = body.get('email', '')
    telefono = body.get('telefono', '')
    descrizione = body.get('descrizione', '')
    dove_conosciuto = body.get('dove_conosciuto', '')
    note = body.get('note', '')
    url = body.get('url', '')
    
    # Genera ID univoco
    contact_id = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat()
    
    # Prepara item per DynamoDB
    contact_item = {
        'contact_id': contact_id,
        'nome': nome,
        'cognome': cognome,
        'email': email,
        'telefono': telefono,
        'descrizione': descrizione,
        'dove_conosciuto': dove_conosciuto,
        'note': note,
        'url': url,
        'created_at': timestamp,
        'updated_at': timestamp
    }
    
    try:
        # Salva in DynamoDB
        table.put_item(Item=contact_item)
        
        print(f"Contact created successfully: {contact_id}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Contatto creato con successo',
                'contact_id': contact_id,
                'contact': contact_item
            }, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error creating contact: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Errore durante la creazione: {str(e)}'})
        }
