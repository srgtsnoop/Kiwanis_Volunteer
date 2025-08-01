from flask_wtf import FlaskForm
from wtforms import StringField, DateField, FloatField, SelectMultipleField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class BulkHoursForm(FlaskForm):
    event = StringField('Event Name', validators=[DataRequired()])
    date = DateField('Date', validators=[DataRequired()])
    start_time = StringField('Start Time')
    end_time = StringField('End Time')
    total_hours = FloatField('Total Hours', validators=[DataRequired()])
    volunteers = SelectMultipleField('Volunteers', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Submit')
