from wtforms import StringField, TextAreaField, SelectField, DateField, IntegerField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm


class NewGroup(FlaskForm):

    name = StringField('Name', validators=[DataRequired()], render_kw={"placeholder": "Name"})
    type = SelectField('Last Name', validators=[DataRequired()],
                       choices=[('basic', 'Basic'), ('project', 'Project'), ('design', 'Design & Marketing')])


class NewUser(FlaskForm):

    first_name = StringField('First Name', validators=[DataRequired()], render_kw={"placeholder": "First Name"})
    last_name = StringField('Last Name', validators=[DataRequired()], render_kw={"placeholder": "Last Name"})
    group = SelectField('Group', validators=[DataRequired()], render_kw={"placeholder": "Group"})
    fixed_capacity = StringField('Fixed Capacity', validators=[DataRequired()],
                                 render_kw={"placeholder": "Fixed Capacity"})
    variable_capacity = StringField('Variable Capacity', validators=[DataRequired()],
                                    render_kw={"placeholder": "Variable Capacity"})
    trello_id = StringField('Trello Id', validators=[DataRequired()], render_kw={"placeholder": "Trello Id"})


class NewProject(FlaskForm):

    name = StringField('Name', validators=[DataRequired()], render_kw={"placeholder": "Name"})
    type = StringField('Type', validators=[DataRequired()], render_kw={"placeholder": "Type"})
    status = SelectField('Status', validators=[DataRequired()], render_kw={"placeholder": "Status", "id": "select-choice"},
                         choices=[(None, 'Select One'), ('Pending', 'Pending'), ('Discovery', 'Discovery'),
                                  ('Design', 'Design'), ('Development', 'Development'), ('Done', 'Done')])
    start_date = DateField('Start Date', validators=[DataRequired()], format='%Y-%m-%d',
                           render_kw={"placeholder": "Start Date", "type": "date", "": ""}, )
    description = TextAreaField('Description', validators=[DataRequired()], render_kw={"placeholder": "Description"})


class NewAction(FlaskForm):

    name = StringField('Name', validators=[DataRequired()], render_kw={"placeholder": "Name"})
    time = StringField('Time', validators=[DataRequired()], render_kw={"placeholder": "Time"})
    assignee = SelectField('Assignee', validators=[DataRequired()], render_kw={"placeholder": "Assignee", "id": "select-choice"})
    project = SelectField('Project', validators=[DataRequired()], render_kw={"placeholder": "Project", "id": "select-choice"})
    start_date = DateField('Start Date', validators=[DataRequired()], format='%Y-%m-%d',
                           render_kw={"placeholder": "Start Date", "type": "date", "": ""}, )

    priority = IntegerField('Priority Position', render_kw={"placeholder": """Complete if you want to override currently 
                                               defined priority. Otherwise leave blank"""})
    description = TextAreaField('Description', render_kw={"placeholder": "Description"})


