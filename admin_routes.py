# admin_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, User, VolunteerEntry
from utils  import role_required


admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/entries')
@login_required
@role_required('admin')
def list_entries():
    """
    List **all** volunteer entries for admins to edit or delete.
    """
    entries = VolunteerEntry.query.order_by(VolunteerEntry.date.desc()).all()
    return render_template('admin_entries.html', entries=entries)

@admin_bp.route('/')
@login_required
@role_required('admin')
def admin_index():
    return render_template('admin_index.html')

@admin_bp.route('/users')
@login_required
@role_required('admin')
def list_users():
    users = User.query.order_by(User.full_name).all()
    return render_template('admin_users.html', users=users)


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        # Basic info
        user.full_name = request.form['full_name']
        user.email     = request.form['email']
        user.role      = request.form['role']
        # Optional password reset
        new_pw = request.form.get('new_password')
        if new_pw:
            user.set_password(new_pw)
            flash('Password was reset', 'info')
        db.session.commit()
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.list_users'))

    # GET: render form
    return render_template('admin_edit_user.html', user=user,
                           roles=['volunteer','reporter','admin'])


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    # Delete their entries first (or configure cascade)
    VolunteerEntry.query.filter_by(user_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} deleted', 'warning')
    return redirect(url_for('admin.list_users'))
