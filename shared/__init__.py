# Shared Package
__version__ = "1.0.0"

from .models.data_models import Task, Email, BriefingData, TaskStatus, TaskPriority, TaskCategory
from .utils.helpers import (
    setup_logger,
    parse_date,
    format_date,
    calculate_days_until,
    is_overdue,
    generate_task_id,
    truncate_text,
    safe_json_loads,
    safe_json_dumps,
    format_markdown_message
)

__all__ = [
    'Task',
    'Email',
    'BriefingData',
    'TaskStatus',
    'TaskPriority',
    'TaskCategory',
    'setup_logger',
    'parse_date',
    'format_date',
    'calculate_days_until',
    'is_overdue',
    'generate_task_id',
    'truncate_text',
    'safe_json_loads',
    'safe_json_dumps',
    'format_markdown_message'
]
