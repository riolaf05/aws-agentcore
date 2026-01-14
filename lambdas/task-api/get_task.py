"""
Lambda function per gestire GET requests dal database dei task.
Usata dall'Agent Core come tool per leggere task esistenti.
"""

import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('TASKS_TABLE_NAME', 'PersonalTasks')
table = dynamodb.Table(table_name)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Handler per recuperare task dal database.
    
    Query parameters supportati:
    - status: filtra per status (pending, in_progress, completed, cancelled)
    - priority: filtra per priorità (low, medium, high, urgent)
    - category: filtra per categoria
    - due_date: filtra per scadenza (today, tomorrow, week, month)
    - tags: filtra per tag (comma-separated)
    - limit: numero massimo di risultati
    """
    try:
        # Parse request - gestisce sia API Gateway che Gateway MCP
        if 'queryStringParameters' in event:
            # Chiamata da API Gateway
            params = event.get('queryStringParameters') or {}
        else:
            # Chiamata diretta da Gateway MCP
            params = event
        
        logger.info(f"Parametri ricerca: {json.dumps(params)}")
        
        status_filter = params.get('status')
        priority_filter = params.get('priority')
        category_filter = params.get('category')
        due_date_filter = params.get('due_date')
        tags_filter = params.get('tags')
        limit = int(params.get('limit', 100))
        
        # Get tasks from DynamoDB
        tasks = get_tasks(
            status=status_filter,
            priority=priority_filter,
            category=category_filter,
            due_date=due_date_filter,
            tags=tags_filter.split(',') if tags_filter else None,
            limit=limit
        )
        
        # Sort by priority and due date
        tasks = sort_tasks(tasks)
        
        # Prepare response
        response_body = {
            'success': True,
            'count': len(tasks),
            'tasks': tasks,
            'filters_applied': {
                'status': status_filter,
                'priority': priority_filter,
                'category': category_filter,
                'due_date': due_date_filter,
                'tags': tags_filter
            }
        }
        
        logger.info(f"Retrieved {len(tasks)} tasks")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_body, default=str)
        }
        
    except ValueError as e:
        logger.error(f"Invalid parameter: {e}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': 'Invalid parameter',
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


def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    due_date: Optional[str] = None,
    tags: Optional[List[str]] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Recupera task dal database con filtri opzionali.
    
    Args:
        status: Filtra per status
        priority: Filtra per priorità
        category: Filtra per categoria
        due_date: Filtra per scadenza (today, tomorrow, week, month)
        tags: Filtra per tag
        limit: Numero massimo di risultati
        
    Returns:
        Lista di task
    """
    try:
        # Build filter expression
        filter_expressions = []
        
        if status:
            filter_expressions.append(Attr('status').eq(status))
        
        if priority:
            filter_expressions.append(Attr('priority').eq(priority))
        
        if category:
            filter_expressions.append(Attr('category').eq(category))
        
        if due_date:
            due_date_range = get_due_date_range(due_date)
            if due_date_range:
                filter_expressions.append(
                    Attr('due_date').between(due_date_range[0], due_date_range[1])
                )
        
        if tags:
            for tag in tags:
                filter_expressions.append(Attr('tags').contains(tag))
        
        # Combine filters with AND
        filter_expression = None
        if filter_expressions:
            filter_expression = filter_expressions[0]
            for expr in filter_expressions[1:]:
                filter_expression = filter_expression & expr
        
        # Scan table (in production, consider using GSI for better performance)
        scan_params = {'Limit': limit}
        if filter_expression:
            scan_params['FilterExpression'] = filter_expression
        
        response = table.scan(**scan_params)
        tasks = response.get('Items', [])
        
        logger.info(f"Found {len(tasks)} tasks matching filters")
        return tasks
        
    except ClientError as e:
        logger.error(f"DynamoDB error: {e}")
        raise ValueError(f"Failed to retrieve tasks: {e.response['Error']['Message']}")


def get_due_date_range(due_date_filter: str) -> Optional[tuple]:
    """
    Calcola range di date per il filtro.
    
    Args:
        due_date_filter: today, tomorrow, week, month
        
    Returns:
        Tupla (start_date, end_date) come stringhe ISO
    """
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    if due_date_filter == 'today':
        start = today
        end = today + timedelta(days=1)
    elif due_date_filter == 'tomorrow':
        start = today + timedelta(days=1)
        end = today + timedelta(days=2)
    elif due_date_filter == 'week':
        start = today
        end = today + timedelta(days=7)
    elif due_date_filter == 'month':
        start = today
        end = today + timedelta(days=30)
    else:
        return None
    
    return (start.isoformat(), end.isoformat())


def sort_tasks(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ordina task per priorità e scadenza.
    
    Priorità: urgent > high > medium > low
    Poi per scadenza (più vicine prima)
    """
    priority_order = {'urgent': 0, 'high': 1, 'medium': 2, 'low': 3}
    
    def sort_key(task):
        priority_value = priority_order.get(task.get('priority', 'medium'), 2)
        due_date = task.get('due_date', '9999-12-31')
        return (priority_value, due_date)
    
    return sorted(tasks, key=sort_key)


def enrich_tasks_with_metadata(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Arricchisce task con metadata utili (es. giorni alla scadenza).
    """
    now = datetime.utcnow()
    
    for task in tasks:
        if task.get('due_date'):
            try:
                due_date = datetime.fromisoformat(task['due_date'])
                days_until = (due_date - now).days
                task['days_until_due'] = days_until
                task['is_overdue'] = days_until < 0
            except ValueError:
                pass
    
    return tasks
