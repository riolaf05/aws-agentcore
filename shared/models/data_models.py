# Shared Models and Data Structures

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class TaskStatus(Enum):
    """Status possibili per un task."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Priorità possibili per un task."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskCategory(Enum):
    """Categorie predefinite per task."""
    WORK = "work"
    LEARNING = "learning"
    HEALTH = "health"
    PERSONAL = "personal"
    GENERAL = "general"


@dataclass
class Task:
    """
    Modello dati per un task.
    """
    task_id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    category: TaskCategory = TaskCategory.GENERAL
    due_date: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Converte task in dict per DynamoDB."""
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value if isinstance(self.status, TaskStatus) else self.status,
            'priority': self.priority.value if isinstance(self.priority, TaskPriority) else self.priority,
            'category': self.category.value if isinstance(self.category, TaskCategory) else self.category,
            'due_date': self.due_date,
            'tags': self.tags,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'completed_at': self.completed_at
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Task':
        """Crea Task da dict DynamoDB."""
        return cls(
            task_id=data['task_id'],
            title=data['title'],
            description=data.get('description', ''),
            status=TaskStatus(data.get('status', 'pending')),
            priority=TaskPriority(data.get('priority', 'medium')),
            category=TaskCategory(data.get('category', 'general')),
            due_date=data.get('due_date'),
            tags=data.get('tags', []),
            created_at=data.get('created_at', datetime.utcnow().isoformat()),
            updated_at=data.get('updated_at', datetime.utcnow().isoformat()),
            completed_at=data.get('completed_at')
        )


@dataclass
class Email:
    """
    Modello dati per un'email da Outlook.
    """
    id: str
    subject: str
    from_name: str
    from_email: str
    received_at: str
    is_important: bool = False
    is_read: bool = False
    has_attachments: bool = False
    preview: str = ""
    
    @classmethod
    def from_graph_api(cls, data: dict) -> 'Email':
        """Crea Email da risposta Microsoft Graph API."""
        return cls(
            id=data.get('id', ''),
            subject=data.get('subject', 'No subject'),
            from_name=data.get('from', {}).get('emailAddress', {}).get('name', 'Unknown'),
            from_email=data.get('from', {}).get('emailAddress', {}).get('address', ''),
            received_at=data.get('receivedDateTime', ''),
            is_important=data.get('importance') == 'high',
            is_read=data.get('isRead', False),
            has_attachments=data.get('hasAttachments', False),
            preview=data.get('bodyPreview', '')
        )


@dataclass
class BriefingData:
    """
    Modello dati per briefing giornaliero.
    """
    date: str
    tasks: List[Task]
    emails: List[Email]
    urgent_count: int = 0
    suggestions: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> dict:
        """Converte briefing in dict."""
        return {
            'date': self.date,
            'tasks': [t.to_dict() if isinstance(t, Task) else t for t in self.tasks],
            'emails': [e.__dict__ if isinstance(e, Email) else e for e in self.emails],
            'urgent_count': self.urgent_count,
            'suggestions': self.suggestions,
            'generated_at': self.generated_at
        }
