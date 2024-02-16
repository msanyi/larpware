from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import Couriertask, Digitalmarketlisting, User
from database import db

admin_couriertasks_app = Blueprint('admin_couriertasks', __name__)


@admin_couriertasks_app.route('/tasks', methods=['GET'])
def list_tasks():
    tasks = Couriertask.query.filter(Couriertask.status != 'Completed').all()
    return render_template('admin_couriertasks.html', tasks=tasks)

@admin_couriertasks_app.route('/tasks/progress/<int:task_id>', methods=['POST'])
def progress_task(task_id):
    task = Couriertask.query.get(task_id)
    if not task:
        flash('Task not found.', 'danger')
        return redirect(url_for('admin_app.admin_couriertasks.list_tasks'))

    old_status = task.status

    if old_status == 'New':
        task.status = 'Pending'
    elif old_status == 'Pending':
        task.status = 'Completed'
    elif old_status == 'Completed':
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin_app.admin_couriertasks.list_tasks'))
    
    db.session.commit()
    flash('Task status updated.', 'success')
    return redirect(url_for('admin_app.admin_couriertasks.list_tasks'))

@admin_couriertasks_app.route('/tasks/regress/<int:task_id>', methods=['POST'])
def regress_task(task_id):
    task = Couriertask.query.get(task_id)
    if not task:
        flash('Task not found.', 'danger')
        return redirect(url_for('admin_app.admin_couriertasks.list_tasks'))

    old_status = task.status

    if old_status == 'New':
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin_app.admin_couriertasks.list_tasks'))
    elif old_status == 'Pending':
        task.status = 'New'
    elif old_status == 'Completed':
        task.status = 'Pending'
    
    db.session.commit()
    flash('Task status updated.', 'success')
    return redirect(url_for('admin_app.admin_couriertasks.list_tasks'))

@admin_couriertasks_app.route('/tasks/update/<int:task_id>', methods=['POST'])
def update_task(task_id):
    task = Couriertask.query.get(task_id)
    if not task:
        flash('Task not found.', 'danger')
        return redirect(url_for('admin_app.admin_couriertasks.list_tasks'))

    new_status = request.form.get('status')
    if new_status not in ['New', 'Pending', 'Completed']:
        flash('Invalid status.', 'danger')
        return redirect(url_for('admin_app.admin_couriertasks.list_tasks'))

    task.status = new_status
    db.session.commit()

    flash('Task status updated.', 'success')
    return redirect(url_for('admin_app.admin_couriertasks.list_tasks'))
