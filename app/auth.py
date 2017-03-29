from flask import render_template, flash, redirect
from flask_login import current_user
from app import app, login_manager
from models import User
import hashlib
from functools import wraps

class UserHasher():
    def hashPassword(self, password):
        return hashlib.sha256(password + (password[::-1])).hexdigest()

    def hashEmail(self, email):
        return hashlib.sha256(email + (email[::-1])).hexdigest()

    def comparePassword(self, password, passwordhash):
        return self.hashPassword(password) == passwordhash

    def compareEmail(self, email, emailhash):
        return self.hashEmail(email) == emailhash

    def getUser(self, username):
        return User(username=username)

class UserManager():
    user_hasher = UserHasher()

    def verify_password(self, password, user):
        return self.user_hasher.comparePassword(password, user.password)

    def get(self, username):
        try:
            user = User.get(username=username)
        except:
            return None
        return user

    def hashPassword(self, password):
        return self.user_hasher.hashPassword(password)


user_manager = UserManager()

@login_manager.user_loader
def load_user(user_id):
    return user_manager.get(user_id)
