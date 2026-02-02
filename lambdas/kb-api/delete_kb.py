"""
Lambda handler for Knowledge Base document deletion (DELETE).
Removes document from DynamoDB and S3 if applicable.
"""

import json
import boto3
import os
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
    Delete a KB document.
    
    Expected path parameters:
    - document_id: document ID to delete
    """
    
    try:
        # Extract document_id from path parameters or body
        path_params = event.get('pathParameters', {}) or {}
        document_id = path_params.get('document_id')
        
        if not document_id:
            # Try to get from body (JSON)
            try:
                body = json.loads(event.get('body', '{}'))
                document_id = body.get('document_id')
            except:
                pass
        
        if not document_id:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Missing document_id'})
            }
        
        logger.info(f"Deleting document: {document_id}")
        
        # Get document first to check if it has S3 file
        response = table.get_item(Key={'document_id': document_id})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Document not found'})
            }
        
        document = response['Item']
        
        # Delete from S3 if file exists
        if document.get('s3_key'):
            try:
                s3_client.delete_object(
                    Bucket=KB_BUCKET_NAME,
                    Key=document['s3_key']
                )
                logger.info(f"Deleted S3 object: {document['s3_key']}")
            except Exception as e:
                logger.error(f"Error deleting S3 object: {str(e)}")
                # Continue with DynamoDB deletion
        
        # Delete from DynamoDB
        try:
            table.delete_item(
                Key={
                    'document_id': document_id,
                    'created_at': document['created_at']
                }
            )
            logger.info(f"Deleted document metadata from DynamoDB: {document_id}")
        except Exception as e:
            logger.error(f"Error deleting from DynamoDB: {str(e)}")
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': f'Error deleting document: {str(e)}'})
            }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'Document deleted successfully',
                'document_id': document_id
            })
        }
    
    except Exception as e:
        logger.error(f"Error processing KB deletion: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }
