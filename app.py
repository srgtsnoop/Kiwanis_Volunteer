import os
from pathlib import Path
from datetime import datetime
import io
import pandas as pd
import click

from dotenv import load_dotenv
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, abort, send_file
)
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

# Load environment variables
load_dotenv()

# Resolve project directories
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Flask app setup
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret')

# Database configuration
# e.g. sqlite for dev; override via DATABASE_URL in env
default_db = DATA_DIR / 'volunteer.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    f"sqlite:///{default_db.as_posix()}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the shared SQLAlchemy instance
db.init_app(app)

# Flask-Login setup
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Role hierarchy and decorator
ROLE_LEVEL = {
    'volunteer': 0,
    'reporter':  1,
    'admin':     2,
}

def role_required(min_role):
    """Abort with 403 unless current_user.role ≥ min_role."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_role = getattr(current_user, 'role', None)
            if user_role is None or ROLE_LEVEL.get(user_role, 0) < ROLE_LEVEL[min_role]:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator

# Expose ROLE_LEVEL to Jinja
app.jinja_env.globals.update(ROLE_LEVEL=ROLE_LEVEL)

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register account routes blueprint
from account_routes import account_bp
app.register_blueprint(account_bp)

from admin_routes import admin_bp
app.register_blueprint(admin_bp)


# CLI command: initialize the database
@app.cli.command('init-db')
def init_db():
    """Create the database tables."""
    db.create_all()
    click.echo('Initialized the database.')

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

    # GET: show edit form
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
import io
import pandas as pd
from flask import send_file

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
