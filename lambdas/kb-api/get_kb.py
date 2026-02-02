"""
Lambda handler for Knowledge Base document retrieval (GET).
Returns list of all KB documents with metadata.
"""

import json
import boto3
import os
import logging
from decimal import Decimal

# Initialize AWS clients
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


class DecimalEncoder(json.JSONEncoder):
    """Helper class to convert DynamoDB Decimal types to float"""
    def default(self, o):
        if isinstance(o, Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


def lambda_handler(event, context):
    """
    Retrieve all KB documents.
    
    Query parameters:
    - tipo: filter by document type (optional)
    """
    
    try:
        logger.info("Received KB GET request")
        
        # Extract query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        doc_type = query_params.get('tipo')
        
        # Query documents
        if doc_type:
            # Use GSI to filter by type
            response = table.query(
                IndexName='TypeIndex',
                KeyConditionExpression='tipo = :tipo',
                ExpressionAttributeValues={
                    ':tipo': doc_type
                },
                ScanIndexForward=False  # Sort by created_at descending
            )
        else:
            # Scan all documents
            response = table.scan()
        
        documents = response.get('Items', [])
        
        # Sort by created_at descending if not already sorted
        documents.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        logger.info(f"Retrieved {len(documents)} documents")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'documents': documents,
                'count': len(documents)
            }, cls=DecimalEncoder)
        }
    
    except Exception as e:
        logger.error(f"Error retrieving KB documents: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }
