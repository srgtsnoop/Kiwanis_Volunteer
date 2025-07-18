from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import pathlib

# Resolve an absolute data directory
BASE_DIR = pathlib.Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "volunteer.db"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 1) Define your model(s)
class VolunteerEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))
    name = db.Column(db.String(100))
    event = db.Column(db.String(200))
    start_time = db.Column(db.String(5))
    end_time = db.Column(db.String(5))
    total_hours = db.Column(db.Float)
    notes = db.Column(db.String(300))

# 2) Create tables under the proper app context
with app.app_context():
    db.create_all()

# 3) Define routes
@app.route('/')
def index():
    entries = VolunteerEntry.query.order_by(VolunteerEntry.date.desc()).all()
    return render_template('index.html', entries=entries)

@app.route('/log', methods=['GET', 'POST'])
def log():
    if request.method == 'POST':
        name = request.form['name']
        event = request.form['event']
        date = request.form['date'] or datetime.today().strftime('%Y-%m-%d')
        start = request.form['start']
        end = request.form['end']
        notes = request.form['notes']

        try:
            start_dt = datetime.strptime(f"{date} {start}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{date} {end}",   "%Y-%m-%d %H:%M")
            total_hours = round((end_dt - start_dt).seconds / 3600, 2)
        except:
            total_hours = 0

        entry = VolunteerEntry(
            date=date,
            name=name,
            event=event,
            start_time=start,
            end_time=end,
            total_hours=total_hours,
            notes=notes
        )
        db.session.add(entry)
        db.session.commit()
        return redirect('/')
    return render_template('log.html')

@app.route('/summary')
def summary():
    summary_data = {}
    for e in VolunteerEntry.query.all():
        summary_data[e.name] = summary_data.get(e.name, 0) + e.total_hours
    return render_template('summary.html', totals=summary_data)

# 4) Run block for Render (uses $PORT and listens on 0.0.0.0)
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
