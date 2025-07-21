# ACCOUNT BLUEPRINT SETUP
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

account_bp = Blueprint(
    'account',
    __name__,
    template_folder='templates',   # or wherever your templates live
    url_prefix=''                  # or '/account' if you prefer
)

@account_bp.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.full_name = request.form['full_name']
        current_user.email     = request.form['email']
        # … any other fields …
        db.session.commit()
        flash('Profile updated', 'success')
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
