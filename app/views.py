from flask import render_template, flash, redirect, request, url_for
from flask_login import login_user, logout_user, current_user, login_required
from playhouse.flask_utils import get_object_or_404
from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.extra import ExtraExtension
from micawber import bootstrap_basic, parse_html
from micawber.cache import Cache as OEmbedCache

from app import app, login_manager
from .forms import MyLoginForm
from app.models import User, Entry, Project
from app.auth import user_manager


def object_list(template_name, qr, var_name='object_list', **kwargs):
    kwargs.update(
        page=int(request.args.get('page', 1)),
        pages=qr.count() / 20 + 1
    )
    kwargs[var_name] = qr.paginate(kwargs['page'])
    return render_template(template_name, **kwargs)

@login_manager.user_loader
def user_loader(user_id):
    """Given *user_id*, return the associated User object.
    :param unicode user_id: user_id (email) user to retrieve
    """

    return user_manager.get(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = MyLoginForm()
    if form.validate_on_submit():
        # Login and validate the user.
        # user should be an instance of your `User` class
        login_user(user_manager.get(form.username.data))

        flash('Logged in successfully.', 'success')

        next = request.args.get('next')
        if next == "/logout":
            next = None
        return redirect(next or url_for('index'))
    return render_template('login.html', title='Login', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
def index():
    search_query = request.args.get('q')
    if search_query:
        query = Entry.search(search_query)
    else:
        query = Entry.public().order_by(Entry.ts_created.desc())
    return object_list('index.html', query)

@app.route('/drafts')
@login_required
def drafts():
    query = Entry.drafts().order_by(Entry.ts_created.desc())
    return object_list('index.html', query)

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        if request.form.get('title') and request.form.get('content'):
            entry = Entry.create(
                title=request.form['title'],
                content=request.form['content'],
                published=request.form.get('published') or False)
            flash('Entry created successfully.', 'success')
            if entry.published:
                return redirect(url_for('detail', slug=entry.slug))
            else:
                return redirect(url_for('edit', slug=entry.slug))
        else:
            flash('Title and Content are required.', 'danger')
    else:
        entry = False
    return render_template('createentry.html', entry=entry)

@app.route('/projects')
@login_required
def projects():
    user = current_user
    query = Project.select().order_by(Project.ts_created.desc())
    return object_list('projects.html', query)

@app.route('/ideas')
@login_required
def ideas():
    user = current_user
    return "you did it"

@app.route('/<slug>')
def detail(slug):
    if current_user.is_authenticated:
        query = Entry.select()
    else:
        query = Entry.public()
    entry = get_object_or_404(query, Entry.slug == slug)
    return render_template('details.html', entry=entry)

@app.route('/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit(slug):
    entry = get_object_or_404(Entry, Entry.slug == slug)
    if request.method == 'POST':
        if request.form.get('title') and request.form.get('content'):
            entry.title = request.form['title']
            entry.content = request.form['content']
            entry.published = request.form.get('published') or False
            entry.save()

            flash('Entry saved successfully.', 'success')
            if entry.published:
                return redirect(url_for('detail', slug=entry.slug))
            else:
                return redirect(url_for('edit', slug=entry.slug))
        else:
            flash('Title and Content are required.', 'danger')

    return render_template('edit.html', entry=entry)
