"""
Lambda function per gestire POST requests al database dei task.
Usata dall'Agent Core come tool per creare nuovi task.
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, List
import boto3
from botocore.exceptions import ClientError
import uuid

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TASKS_TABLE_NAME', 'PersonalTasks')
table = dynamodb.Table(table_name)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler per creare nuovi task nel database.
    
    Expected body format:
    {
        "tasks": [
            {
                "title": "Task title",
                "description": "Task description",
                "due_date": "2024-12-31",
                "priority": "high",
                "category": "work",
                "tags": ["python", "learning"]
            }
        ]
    }
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        tasks = body.get('tasks', [])
        
        if not tasks:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'error': 'No tasks provided',
                    'message': 'Request body must contain a "tasks" array'
                })
            }
        
        # Validate and create tasks
        created_tasks = []
        errors = []
        
        for task_data in tasks:
            try:
                task = create_task(task_data)
                created_tasks.append(task)
            except ValueError as e:
                errors.append({
                    'task': task_data.get('title', 'Unknown'),
                    'error': str(e)
                })
        
        # Prepare response
        response_body = {
            'success': True,
            'created_count': len(created_tasks),
            'tasks': created_tasks
        }
        
        if errors:
            response_body['errors'] = errors
            response_body['error_count'] = len(errors)
        
        logger.info(f"Created {len(created_tasks)} tasks successfully")
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_body, default=str)
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {e}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid JSON',
                'message': str(e)
            })
        }
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        }


def create_task(task_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Crea un task nel database DynamoDB.
    
    Args:
        task_data: Dati del task da creare
        
    Returns:
        Task creato con ID e timestamp
        
    Raises:
        ValueError: Se i dati del task non sono validi
    """
    # Validate required fields
    if not task_data.get('title'):
        raise ValueError("Task title is required")
    
    # Generate task ID and timestamps
    task_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()
    
    # Build task item
    task_item = {
        'task_id': task_id,
        'title': task_data['title'],
        'description': task_data.get('description', ''),
        'status': task_data.get('status', 'pending'),
        'priority': task_data.get('priority', 'medium'),
        'category': task_data.get('category', 'general'),
        'due_date': task_data.get('due_date'),
        'tags': task_data.get('tags', []),
        'created_at': now,
        'updated_at': now,
        'completed_at': None
    }
    
    # Remove None values
    task_item = {k: v for k, v in task_item.items() if v is not None}
    
    try:
        # Save to DynamoDB
        table.put_item(Item=task_item)
        logger.info(f"Task created: {task_id} - {task_item['title']}")
        return task_item
        
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        raise ValueError(f"Failed to create task: {e.response['Error']['Message']}")


def validate_priority(priority: str) -> bool:
    """Valida che la priorità sia valida."""
    return priority in ['low', 'medium', 'high', 'urgent']


def validate_status(status: str) -> bool:
    """Valida che lo status sia valido."""
    return status in ['pending', 'in_progress', 'completed', 'cancelled']
