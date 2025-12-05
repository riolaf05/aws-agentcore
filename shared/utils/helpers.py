"""
Utility functions condivise tra i componenti.
"""

import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timedelta
import hashlib


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """
    Configura logger con formato standard.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse date string in vari formati.
    """
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    return None


def format_date(dt: datetime, format_type: str = "iso") -> str:
    """
    Formatta datetime in vari formati.
    """
    if format_type == "iso":
        return dt.isoformat()
    elif format_type == "date":
        return dt.strftime('%Y-%m-%d')
    elif format_type == "datetime":
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    elif format_type == "friendly":
        return dt.strftime('%d %B %Y, %H:%M')
    else:
        return dt.isoformat()


def calculate_days_until(target_date: str) -> Optional[int]:
    """
    Calcola giorni fino a una data target.
    """
    target = parse_date(target_date)
    if not target:
        return None
    
    now = datetime.utcnow()
    delta = target - now
    return delta.days


def is_overdue(due_date: str) -> bool:
    """
    Verifica se una data è scaduta.
    """
    days = calculate_days_until(due_date)
    if days is None:
        return False
    return days < 0


def generate_task_id(title: str, timestamp: Optional[str] = None) -> str:
    """
    Genera ID univoco per task.
    """
    if not timestamp:
        timestamp = datetime.utcnow().isoformat()
    
    content = f"{title}_{timestamp}"
    hash_obj = hashlib.sha256(content.encode())
    return hash_obj.hexdigest()[:16]


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Tronca testo a lunghezza massima.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Parse JSON con fallback.
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = "{}") -> str:
    """
    Serialize JSON con fallback.
    """
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default


def batch_items(items: list, batch_size: int = 25) -> list:
    """
    Divide lista in batch.
    """
    return [items[i:i + batch_size] for i in range(0, len(items), batch_size)]


def sanitize_input(text: str) -> str:
    """
    Sanitize user input per sicurezza.
    """
    # Remove potential injection attempts
    dangerous_chars = ['<', '>', '&', '"', "'", '\\']
    for char in dangerous_chars:
        text = text.replace(char, '')
    
    return text.strip()


def format_markdown_message(
    title: str,
    sections: Dict[str, str],
    footer: Optional[str] = None
) -> str:
    """
    Formatta messaggio Telegram in Markdown.
    """
    message = f"**{title}**\n\n"
    
    for section_title, content in sections.items():
        message += f"**{section_title}**\n{content}\n\n"
    
    if footer:
        message += f"---\n{footer}"
    
    return message


def extract_command_args(text: str) -> tuple:
    """
    Estrae comando e argomenti da testo.
    """
    parts = text.split(maxsplit=1)
    command = parts[0].lower() if parts else ""
    args = parts[1] if len(parts) > 1 else ""
    
    return command, args
