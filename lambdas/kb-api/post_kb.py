"""
Lambda handler for Knowledge Base document upload (POST).
Saves PDF files to S3 and text content to DynamoDB.
"""

import json
import boto3
import uuid
import os
from datetime import datetime
from base64 import b64decode
import logging

# Initialize AWS clients
s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

# Get environment variables
KB_DOCUMENTS_TABLE_NAME = os.environ.get('KB_DOCUMENTS_TABLE_NAME', 'PersonalKBDocuments')
KB_BUCKET_NAME = os.environ.get('KB_BUCKET_NAME', '')
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Configure logging
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

# Get DynamoDB table
table = dynamodb.Table(KB_DOCUMENTS_TABLE_NAME)


def lambda_handler(event, context):
    """
    Handle Knowledge Base document upload.
    
    Expected form data:
    - data: file (PDF) or text content
    - type: document type (e.g., 'meeting-notes')
    """
    
    try:
        logger.info(f"Received KB upload request. Body: {event.get('body', '')[:100]}")
        
        # Parse form data from event body
        body = event.get('body', '')
        is_base64 = event.get('isBase64Encoded', False)
        
        if is_base64:
            body = b64decode(body).decode('utf-8')
        
        # Extract form data from multipart form data
        doc_id = str(uuid.uuid4())
        content_type = event.get('headers', {}).get('content-type', '').lower()
        
        # Simple parsing for multipart form data
        boundary = None
        if 'boundary=' in content_type:
            boundary = content_type.split('boundary=')[1].split(';')[0].strip('"')
        
        if not boundary:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid form data format'})
            }
        
        # Extract fields from multipart body
        parts = body.split(f'--{boundary}')
        
        file_data = None
        file_name = None
        text_content = None
        doc_type = 'meeting-notes'  # default
        
        for part in parts:
            if 'Content-Disposition: form-data' not in part:
                continue
            
            # Extract field name and filename if present
            if 'filename=' in part:
                # This is a file
                lines = part.split('\r\n')
                for line in lines:
                    if 'filename=' in line:
                        file_name = line.split('filename=')[1].strip('"')
                        break
                
                # File data is after the headers (after double \r\n)
                split_part = part.split('\r\n\r\n', 1)
                if len(split_part) > 1:
                    file_data = split_part[1].rsplit('\r\n', 1)[0]
            
            elif 'name="type"' in part:
                # Extract document type
                split_part = part.split('\r\n\r\n', 1)
                if len(split_part) > 1:
                    doc_type = split_part[1].rsplit('\r\n', 1)[0].strip()
            
            elif 'name="data"' in part and 'filename=' not in part:
                # This is text content
                split_part = part.split('\r\n\r\n', 1)
                if len(split_part) > 1:
                    text_content = split_part[1].rsplit('\r\n', 1)[0].strip()
        
        # Validate that we have either file or text
        if not file_data and not text_content:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No file or text content provided'})
            }
        
        # Create document record
        document = {
            'document_id': doc_id,
            'created_at': datetime.utcnow().isoformat(),
            'tipo': doc_type,
            'is_pdf': file_data is not None,
            'file_name': file_name or 'N/A',
        }
        
        # If file, save to S3
        if file_data:
            try:
                s3_key = f"documents/{doc_id}/{file_name}"
                s3_client.put_object(
                    Bucket=KB_BUCKET_NAME,
                    Key=s3_key,
                    Body=file_data.encode('utf-8') if isinstance(file_data, str) else file_data,
                    ContentType='application/pdf'
                )
                document['s3_key'] = s3_key
                logger.info(f"File saved to S3: {s3_key}")
            except Exception as e:
                logger.error(f"Error saving file to S3: {str(e)}")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': f'Error saving file: {str(e)}'})
                }
        
        # If text, save to document
        if text_content:
            document['text_content'] = text_content
            logger.info(f"Text content saved for document {doc_id}")
        
        # Save document metadata to DynamoDB
        try:
            table.put_item(Item=document)
            logger.info(f"Document metadata saved to DynamoDB: {doc_id}")
        except Exception as e:
            logger.error(f"Error saving to DynamoDB: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Error saving document metadata: {str(e)}'})
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Document uploaded successfully',
                'document_id': doc_id,
                'document': document
            })
        }
    
    except Exception as e:
        logger.error(f"Error processing KB upload: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }
