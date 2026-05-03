from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from models.user import db
from models.task import Task
from utils.helpers import parse_datetime, get_task_stats
from datetime import datetime, date
import sqlalchemy as sa

tasks = Blueprint('tasks', __name__)


# ── Shared sort helper ─────────────────────────────────────────────────────────
def _apply_sort(query, sort_by):
    """Return query with the requested sort order applied."""
    if sort_by == 'due_date':
        # MySQL doesn't support NULLS LAST — push NULLs to the bottom with a CASE
        null_last = sa.case((Task.due_date == None, 1), else_=0)
        return query.order_by(null_last, Task.due_date.asc())
    elif sort_by == 'priority':
        # SQLAlchemy 2.x db.case() takes a dict or list of (condition, value) tuples
        priority_order = sa.case(
            (Task.priority == 'high',   1),
            (Task.priority == 'medium', 2),
            (Task.priority == 'low',    3),
            else_=4
        )
        return query.order_by(priority_order)
    else:
        return query.order_by(Task.created_at.desc())


# ── Dashboard ──────────────────────────────────────────────────────────────────
@tasks.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    sort_by = request.args.get('sort', 'created_at')
    query = Task.query.filter_by(user_id=current_user.id)
    query = _apply_sort(query, sort_by)

    user_tasks = query.all()
    stats = get_task_stats(user_tasks)
    today = date.today()

    return render_template('dashboard.html',
                           tasks=user_tasks,
                           stats=stats,
                           today=today,
                           current_sort=sort_by)


# ── GET all tasks (JSON API) ───────────────────────────────────────────────────
@tasks.route('/', methods=['GET'])
@login_required
def get_tasks():
    status   = request.args.get('status')
    priority = request.args.get('priority')
    sort_by  = request.args.get('sort', 'created_at')

    query = Task.query.filter_by(user_id=current_user.id)

    if status in ('pending', 'completed'):
        query = query.filter_by(status=status)
    if priority in ('low', 'medium', 'high'):
        query = query.filter_by(priority=priority)

    query = _apply_sort(query, sort_by)

    return jsonify([t.to_dict() for t in query.all()])


# ── GET single task (JSON API) ─────────────────────────────────────────────────
@tasks.route('/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    return jsonify(task.to_dict())


# ── Add task ───────────────────────────────────────────────────────────────────
@tasks.route('/add', methods=['POST'])
@login_required
def add_task():
    data = request.get_json(silent=True) or {}

    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'Task title is required'}), 400

    task = Task(
        title=title,
        description=(data.get('description') or '').strip() or None,
        priority=data.get('priority', 'medium'),
        due_date=parse_datetime(data.get('due_date')),
        user_id=current_user.id,
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


# ── Update task ────────────────────────────────────────────────────────────────
@tasks.route('/update/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    data = request.get_json(silent=True) or {}

    title = (data.get('title') or '').strip()
    if not title:
        return jsonify({'error': 'Task title is required'}), 400

    task.title       = title
    task.description = (data.get('description') or '').strip() or None
    task.priority    = data.get('priority', task.priority)
    task.due_date    = parse_datetime(data.get('due_date'))

    db.session.commit()
    return jsonify(task.to_dict())


# ── Toggle complete ────────────────────────────────────────────────────────────
@tasks.route('/complete/<int:task_id>', methods=['PATCH'])
@login_required
def complete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.status = 'pending' if task.status == 'completed' else 'completed'
    db.session.commit()
    return jsonify(task.to_dict())


# ── Delete task ────────────────────────────────────────────────────────────────
@tasks.route('/delete/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deleted'}), 200


# ── Search tasks (JSON API) ────────────────────────────────────────────────────
@tasks.route('/search', methods=['GET'])
@login_required
def search_tasks():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify([])

    results = Task.query.filter(
        Task.user_id == current_user.id,
        Task.title.ilike(f'%{q}%')
    ).order_by(Task.created_at.desc()).all()

    return jsonify([t.to_dict() for t in results])