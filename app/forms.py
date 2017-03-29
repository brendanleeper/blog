from flask_wtf import Form
from wtforms import StringField, BooleanField, PasswordField
from wtforms.validators import DataRequired
from auth import user_manager

class MyLoginForm(Form):
    username = StringField('Username', [DataRequired()])
    password = PasswordField('Password', [DataRequired()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        self.username.errors = []
        self.password.errors = []

        user = user_manager.get(self.username.data)
        if not user:
            self.username.errors.append('Incorrect Information')
            return False
        if user and not user_manager.verify_password(self.password.data,user):
            self.username.errors.append('Incorrect Information')
            return False

        if user and user.password and user_manager.verify_password(self.password.data, user):
            return True # successfully authenticated

        return False # Unsuccessful authentication
