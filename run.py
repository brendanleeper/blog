from app import app, database
from app.models import User, Entry, FTSEntry, Project
from app.auth import user_manager

database.connect()
database.create_tables([User, Entry, FTSEntry, Project], safe=True)

user = user_manager.get(username='brendan')

if not user:
    User.create(username='brendan', password=user_manager.hashPassword('test'), email='test@test.com')
app.run(debug=True)
