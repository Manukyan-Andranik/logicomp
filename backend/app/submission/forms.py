from flask_wtf import FlaskForm
from wtforms import TextAreaField, SelectField, SubmitField, FileField
from wtforms.validators import DataRequired, ValidationError
from werkzeug.utils import secure_filename

class SubmitSolutionForm(FlaskForm):
    language = SelectField('Programming Language', choices=[
        ('python', 'Python'),
        ('cpp', 'C++'),
        ('java', 'Java'),
        ('javascript', 'JavaScript')
    ], validators=[DataRequired()])
    code = TextAreaField('Source Code')
    source_file = FileField('Or upload source file')
    submit = SubmitField('Submit Solution')

    def validate(self, extra_validators=None):
        rv = super().validate(extra_validators=extra_validators)
        if not rv:
            return False

        if not self.code.data and not self.source_file.data:
            self.code.errors.append('You must provide either source code or a source file.')
            return False

        if self.source_file.data:
            filename = secure_filename(self.source_file.data.filename)
            if not filename.lower().endswith(('.py', '.cpp', '.java', '.js')):
                self.source_file.errors.append('Invalid file type. Please upload a valid source code file (.py, .cpp, .java, .js).')
                return False

        return True

