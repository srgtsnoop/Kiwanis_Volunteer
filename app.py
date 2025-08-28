import os
from pathlib import Path
from datetime import datetime
import io

import pandas as pd
import click
from dotenv import load_dotenv

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, abort, send_file
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from flask_mail import Mail, Message

from models import db, User, VolunteerEntry
from forms import BulkHoursForm


# Role guard + hierarchy
from utils import ROLE_LEVEL, role_required

# Shared db & models
from models import db, User, VolunteerEntry

# Load .env
load_dotenv()

# forgot password
from flask_mail import Mail, Message

mail = Mail()  # create the extension object first

app = Flask(__name__)

# ✅ LOAD CONFIG HERE (your existing environment switch)
if os.environ.get("RENDER") == "true" or os.environ.get("ON_RENDER") == "true":
    app.config.from_object("config.ProductionConfig")
elif os.environ.get("FLASK_ENV") == "development":
    app.config.from_object("config.DevelopmentConfig")
elif os.environ.get("FLASK_ENV") == "testing":
    app.config.from_object("config.TestingConfig")
else:
    app.config.from_object("config.DevelopmentConfig")

# now that app.config is populated, init mail
mail.init_app(app)


# Init DB
db.init_app(app)

# Login manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Expose roles to Jinja
app.jinja_env.globals.update(ROLE_LEVEL=ROLE_LEVEL)

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ——— Now and only now import & register blueprints ———
from account_routes import account_bp
app.register_blueprint(account_bp)

from admin_routes import admin_bp
app.register_blueprint(admin_bp)

# ——— CLI command to init-db & seed Admin ———
@app.cli.command('init-db')
def init_db():
    """Create tables & seed default Admin."""
    db.create_all()
    click.echo('Initialized the database.')

    # Seed a default Admin account
    admin_username = 'Admin'
    admin_email    = 'wilker.ben@gmail.com'
    admin_pw       = 'kiwanis'
    full_name      = 'Administrator'

    if not User.query.filter_by(username=admin_username).first():
        admin = User(
            full_name=full_name,
            username=admin_username,
            email=admin_email,
            role='admin'
        )
        admin.set_password(admin_pw)
        db.session.add(admin)
        db.session.commit()
        click.echo(f'Created Admin user "{admin_username}".')
    else:
        click.echo(f'Admin user "{admin_username}" already exists.')


# Authentication routes
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        full_name = request.form['full_name']
        username  = request.form['username']
        email     = request.form['email']
        password  = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('That username is taken', 'warning')
            return redirect(url_for('register'))
        if User.query.filter_by(email=email).first():
            flash('That email is already registered', 'warning')
            return redirect(url_for('register'))

        user = User(
            full_name=full_name,
            username=username,
            email=email,
            role='volunteer'
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    return render_template('forgot_password.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Volunteer hours routes
@app.route('/')
@login_required
def index():
    entries = VolunteerEntry.query.filter_by(user_id=current_user.id).order_by(
        VolunteerEntry.date.desc()
    ).all()
    return render_template('index.html', entries=entries)

@app.route('/log', methods=['GET', 'POST'])
@login_required
def log():
    if request.method == 'POST':
        event = request.form['event']
        date  = request.form.get('date') or datetime.today().strftime('%Y-%m-%d')
        start = request.form['start']
        end   = request.form['end']
        notes = request.form['notes']
        try:
            start_dt = datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M")
            end_dt   = datetime.strptime(f"{date} {end}",   "%Y-%m-%d %H:%M")
            total_h  = round((end_dt - start_dt).seconds / 3600, 2)
        except Exception:
            total_h = 0
        entry = VolunteerEntry(
            user_id=current_user.id,
            date=date,
            event=event,
            start_time=start,
            end_time=end,
            total_hours=total_h,
            notes=notes
        )
        db.session.add(entry)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('log.html')

@app.route('/summary')
@login_required
def summary():
    totals = {}
    for e in VolunteerEntry.query.filter_by(user_id=current_user.id):
        full = e.user.full_name
        totals[full] = totals.get(full, 0) + e.total_hours
    return render_template('summary.html', totals=totals)

from datetime import datetime
from flask import abort

@app.route('/entry/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_entry(id):
    entry = VolunteerEntry.query.get_or_404(id)
    if entry.user_id != current_user.id and current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        # Update from form
        entry.date       = request.form.get('date', entry.date)
        entry.event      = request.form.get('event', entry.event)
        entry.start_time = request.form.get('start', entry.start_time)
        entry.end_time   = request.form.get('end', entry.end_time)
        entry.notes      = request.form.get('notes', entry.notes)
        # Recompute hours
        try:
            start_dt = datetime.strptime(f"{entry.date} {entry.start_time}", "%Y-%m-%d %H:%M")
            end_dt   = datetime.strptime(f"{entry.date} {entry.end_time}",   "%Y-%m-%d %H:%M")
            entry.total_hours = round((end_dt - start_dt).seconds / 3600, 2)
        except ValueError:
            pass

        db.session.commit()
        flash('Entry updated successfully', 'success')
        if current_user.role == 'admin':
            return redirect(url_for('admin.list_entries'))
        else:
            return redirect(url_for('index'))
    return render_template('edit_entry.html', entry=entry)


@app.route('/entry/<int:id>/delete', methods=['POST'])
@login_required
def delete_entry(id):
    entry = VolunteerEntry.query.get_or_404(id)
    # Allow owner or admin
    if entry.user_id != current_user.id and current_user.role != 'admin':
        abort(403)

    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted', 'warning')

    # Redirect based on role
    if current_user.role == 'admin':
        return redirect(url_for('admin.list_entries'))
    else:
        return redirect(url_for('index'))

#Building Reports Tab

@app.route('/report', methods=['GET', 'POST'])
@login_required
@role_required('reporter')
def report():
    totals = {}
    start_date = request.form.get('start_date')
    end_date   = request.form.get('end_date')

    if request.method == 'POST':
        # Validate inputs
        try:
            # Dates in YYYY-MM-DD format
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_dt   = datetime.strptime(end_date,   '%Y-%m-%d').date()
        except (TypeError, ValueError):
            flash('Please enter valid start and end dates', 'danger')
            return render_template('report.html',
                                   totals=None,
                                   start_date=start_date,
                                   end_date=end_date)

        if start_dt > end_dt:
            flash('Start date must be on or before end date', 'danger')
            return render_template('report.html',
                                   totals=None,
                                   start_date=start_date,
                                   end_date=end_date)

        # Query entries in date range
        # Since VolunteerEntry.date is stored as 'YYYY-MM-DD', string comparison works
        entries = VolunteerEntry.query\
            .filter(VolunteerEntry.date >= start_date)\
            .filter(VolunteerEntry.date <= end_date)\
            .all()

        # Aggregate by full name
        for e in entries:
            full = e.user.full_name
            totals[full] = totals.get(full, 0) + e.total_hours

        if not totals:
            flash('No records found in that date range.', 'info')

    return render_template('report.html',
                           totals=totals if request.method=='POST' else None,
                           start_date=start_date,
                           end_date=end_date)
    
def is_reporter_or_admin():
    return current_user.role in ['reporter', 'admin']

@app.route('/bulk-add-hours', methods=['GET', 'POST'])
@login_required
def bulk_add_hours():
    if not is_reporter_or_admin():
        flash("You don't have permission to access this page.", "danger")
        return redirect(url_for('index'))

    form = BulkHoursForm()
    form.volunteers.choices = [(u.id, u.full_name) for u in User.query.order_by(User.full_name).all()]

    if request.method == "POST":
        # Use request.form to get the data directly
        event = request.form['event']
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        notes = request.form.get('notes', '')
        volunteer_ids = request.form.getlist('volunteers')

        try:
            start_dt = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
            total_hours = round((end_dt - start_dt).seconds / 3600, 2)
        except Exception:
            total_hours = 0

        for volunteer_id in volunteer_ids:
            user = User.query.get(int(volunteer_id))
            entry = VolunteerEntry(
                user_id=user.id,
                date=date,
                name=user.full_name,
                event=event,
                start_time=start_time,
                end_time=end_time,
                total_hours=total_hours,
                notes=notes
            )
            db.session.add(entry)
        db.session.commit()
        flash('Bulk volunteer hours added!', 'success')
        return redirect(url_for('index'))

    return render_template('bulk_add_hours.html', form=form)


@app.route('/report/export/xlsx')
@login_required
@role_required('reporter')
def export_xlsx():
    # Grab the same form values from query string
    start_date = request.args.get('start_date')
    end_date   = request.args.get('end_date')

    # Re‑validate dates
    try:
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date,   '%Y-%m-%d')
    except Exception:
        flash('Invalid date range for export', 'danger')
        return redirect(url_for('report'))

    # Query entries in that range
    entries = VolunteerEntry.query \
        .filter(VolunteerEntry.date >= start_date) \
        .filter(VolunteerEntry.date <= end_date) \
        .all()

    # Build DataFrame
    data = []
    for e in entries:
        data.append({
            'Full Name': e.user.full_name,
            'Date':      e.date,
            'Event':     e.event,
            'Start':     e.start_time,
            'End':       e.end_time,
            'Hours':     e.total_hours,
            'Notes':     e.notes
        })
    df = pd.DataFrame(data)

    # Write to in-memory buffer
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
    output.seek(0)

    filename = f'report_{start_date}_to_{end_date}.xlsx'
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@app.route('/report/export/xlsx_totals')
@login_required
@role_required('reporter')
def export_xlsx_totals():
    start_date = request.args.get('start_date')
    end_date   = request.args.get('end_date')

    # Validate dates
    try:
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date,   '%Y-%m-%d')
    except Exception:
        flash('Invalid date range for totals export', 'danger')
        return redirect(url_for('report'))

    # Aggregate total hours per volunteer
    entries = (VolunteerEntry.query
               .filter(VolunteerEntry.date >= start_date)
               .filter(VolunteerEntry.date <= end_date)
               .all())

    totals = {}
    for e in entries:
        name = e.user.full_name
        totals[name] = totals.get(name, 0) + e.total_hours

    df = pd.DataFrame(
        [{'Full Name': n, 'Total Hours': h} for n, h in totals.items()]
    )

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Totals')
    buf.seek(0)

    filename = f'totals_{start_date}_to_{end_date}.xlsx'
    return send_file(
        buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


@app.route('/report/export/xlsx_events')
@login_required
@role_required('reporter')
def export_xlsx_events():
    start_date = request.args.get('start_date')
    end_date   = request.args.get('end_date')

    # Validate dates
    try:
        datetime.strptime(start_date, '%Y-%m-%d')
        datetime.strptime(end_date,   '%Y-%m-%d')
    except Exception:
        flash('Invalid date range for events export', 'danger')
        return redirect(url_for('report'))

    # List every event worked
    entries = (VolunteerEntry.query
               .filter(VolunteerEntry.date >= start_date)
               .filter(VolunteerEntry.date <= end_date)
               .all())

    data = []
    for e in entries:
        data.append({
            'Full Name': e.user.full_name,
            'Date':       e.date,
            'Event':      e.event,
            'Start':      e.start_time,
            'End':        e.end_time,
            'Hours':      e.total_hours,
            'Notes':      e.notes or ''
        })

    df = pd.DataFrame(data)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Events')
    buf.seek(0)

    filename = f'events_{start_date}_to_{end_date}.xlsx'
    return send_file(
        buf,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


# Run server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
