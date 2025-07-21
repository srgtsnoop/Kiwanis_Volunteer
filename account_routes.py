# ACCOUNT BLUEPRINT SETUP
from flask import Blueprint, request, flash, redirect, url_for, render_template, abort
from flask_login import login_required, current_user
from app import db

account_bp = Blueprint('account', __name__)

@account_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form.get('full_name', current_user.full_name)
        current_user.email     = request.form.get('email', current_user.email)
        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('account.profile'))
    return render_template('profile.html', user=current_user)

@account_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_pw = request.form['old_password']
        new_pw = request.form['new_password']
        confirm = request.form['confirm_password']
        if not current_user.check_password(old_pw):
            flash('Old password is incorrect', 'danger')
        elif new_pw != confirm:
            flash('New passwords do not match', 'danger')
        else:
            current_user.set_password(new_pw)
            db.session.commit()
            flash('Password changed successfully', 'success')
            return redirect(url_for('account.profile'))
    return render_template('change_password.html')

# In your main app.py, register the blueprint near the top:
# from account_routes import account_bp
# app.register_blueprint(account_bp)
