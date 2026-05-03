# utils/helpers.py
from datetime import datetime

def parse_datetime(dt_string):
    """Convert string from HTML datetime-local input to datetime object"""
    if dt_string:
        try:
            return datetime.strptime(dt_string, '%Y-%m-%dT%H:%M')
        except ValueError:
            return None
    return None

def format_datetime(dt):
    """Convert datetime object to readable string"""
    if dt:
        return dt.strftime('%Y-%m-%d %H:%M')
    return None

def get_task_stats(tasks):
    """Calculate dashboard stats from a list of tasks"""
    total        = len(tasks)
    completed    = sum(1 for t in tasks if t.status == 'completed')
    pending      = total - completed
    high_priority = sum(1 for t in tasks if t.priority == 'high')
    percentage   = round((completed / total) * 100) if total > 0 else 0

    return {
        'total':        total,
        'completed':    completed,
        'pending':      pending,
        'high_priority': high_priority,
        'percentage':   percentage
    }