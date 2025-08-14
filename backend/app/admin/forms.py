from flask_wtf import FlaskForm
from datetime import datetime
from wtforms import (
    StringField, TextAreaField, DateTimeField, IntegerField,
    BooleanField, SubmitField, FieldList, FormField
)
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.file import FileField, FileAllowed

class TestCaseForm(FlaskForm):
    class Meta:
        csrf = False  # Important to allow nested forms without CSRF issues

    expected_input = TextAreaField('Expected Input', validators=[DataRequired()])
    expected_output = TextAreaField('Expected Output', validators=[DataRequired()])
    is_sample = BooleanField('Is Sample')

class TestCaseUploadForm(FlaskForm):
    class Meta:
        csrf = False

    json_file = FileField('Upload Test Cases (JSON)', validators=[
        FileAllowed(['json'], 'Only JSON files allowed!')
    ])
    keep_existing = BooleanField('Keep existing test cases', default=True)

class CreateProblemForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    expected_input = TextAreaField('Expected Input')
    expected_output = TextAreaField('Expected Output')
    time_limit = IntegerField('Time Limit (seconds)', validators=[DataRequired(), NumberRange(min=1)])

    test_case_upload = FormField(TestCaseUploadForm)

    submit = SubmitField('Add Problem')

class EditProblemForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    expected_input = TextAreaField('Expected Input')
    expected_output = TextAreaField('Expected Output')
    time_limit = IntegerField('Time Limit (seconds)', validators=[DataRequired(), NumberRange(min=1)])

    test_case_upload = FormField(TestCaseUploadForm)

    submit = SubmitField('Update Problem')


class CreateContestForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    start_time = DateTimeField('Start Time', default=datetime.now().astimezone(), validators=[DataRequired()])
    end_time = DateTimeField('End Time', default=datetime.now().astimezone(), validators=[DataRequired()])
    is_public = BooleanField('Public Contest')
    submit = SubmitField('Create Contest')

class EditContestForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    start_time = DateTimeField('Start Time', validators=[DataRequired()])
    end_time = DateTimeField('End Time', validators=[DataRequired()])
    is_public = BooleanField('Public Contest')
    submit = SubmitField('Update Contest')

class GenerateCredentialsForm(FlaskForm):
    json_file = FileField('Upload JSON File', validators=[
        FileAllowed(['json'], 'Only .json files are allowed')
    ])
