import datetime
from flask import Markup
from flask_login import UserMixin, current_user
from peewee import *
from playhouse.sqlite_ext import *
from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from markdown.extensions.extra import ExtraExtension
from micawber import bootstrap_basic, parse_html
from micawber.cache import Cache as OEmbedCache

from app import app, flask_db, database, oembed_providers

class BaseModel(flask_db.Model):
    class Meta:
        database = database

class User(BaseModel, UserMixin):
    id = IntegerField(primary_key=True)
    username = TextField(unique=True)
    password = TextField()
    authenticated = BooleanField(default=False)
    ts_created = DateTimeField(default=datetime.datetime.now(), index=True)
    ts_modified = DateTimeField(default=datetime.datetime.now(), index=True)

    def save(self, *args, **kwargs):
        ts_modified = datetime.datetime.now()
        return super(User, self).save(*args, **kwargs)

    def is_active(self):
        return True

    def get_id(self):
        return self.username

    def is_authenticated(self):
        return self.authenticated

    def is_anonymous(self):
        return False

class Project(BaseModel):
    name = CharField()
    slug = CharField(unique=True)
    desc = TextField()
    ts_created = DateTimeField(default=datetime.datetime.now(), index=True)
    ts_modified = DateTimeField(default=datetime.datetime.now(), index=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = re.sub('[^\w]+', '-', self.name.lower())
        self.ts_modified = datetime.datetime.now()
        ret = super(Project, self).save(*args, **kwargs)
        return ret

    @property
    def html_content(self):
        hilite = CodeHiliteExtension(linenums=False, css_class='highlight')
        extras = ExtraExtension()
        markdown_content = markdown(self.desc, extensions=[hilite, extras])
        oembed_content = parse_html(
            markdown_content,
            oembed_providers,
            urlize_all=True,
            maxwidth=app.config['SITE_WIDTH'])
        return Markup(oembed_content)

class FTSEntry(FTSModel):
    entry_id = IntegerField()
    content = TextField()

    class Meta:
        database = database

class Entry(BaseModel):
    title = CharField()
    slug = CharField(unique=True)
    content = TextField()
    published = BooleanField(index=True)
    author = ForeignKeyField(User, related_name='entries')

    ts_created = DateTimeField(default=datetime.datetime.now(), index=True)
    ts_modified = DateTimeField(default=datetime.datetime.now(), index=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = re.sub('[^\w]+', '-', self.title.lower())
        self.ts_modified = datetime.datetime.now()
        self.author = current_user.id
        ret = super(Entry, self).save(*args, **kwargs)

        # Store search content.
        self.update_search_index()
        return ret

    def update_search_index(self):
        try:
            fts_entry = FTSEntry.get(FTSEntry.entry_id == self.id)
        except FTSEntry.DoesNotExist:
            fts_entry = FTSEntry(entry_id=self.id)
            force_insert = True
        else:
            force_insert = False
        fts_entry.content = '\n'.join((self.title, self.content))
        fts_entry.save(force_insert=force_insert)

    @property
    def html_content(self):
        hilite = CodeHiliteExtension(linenums=False, css_class='highlight')
        extras = ExtraExtension()
        markdown_content = markdown(self.content, extensions=[hilite, extras])
        oembed_content = parse_html(
            markdown_content,
            oembed_providers,
            urlize_all=True,
            maxwidth=app.config['SITE_WIDTH'])
        return Markup(oembed_content)

    @classmethod
    def public(cls):
        return Entry.select().where(Entry.published == True)

    @classmethod
    def search(cls, query):
        words = [word.strip() for word in query.split() if word.strip()]
        if not words:
            # Return empty query.
            return Entry.select().where(Entry.id == 0)
        else:
            search = ' '.join(words)

        return (FTSEntry
                .select(
                    FTSEntry,
                    Entry,
                    FTSEntry.rank().alias('score'))
                .join(Entry, on=(FTSEntry.entry_id == Entry.id).alias('entry'))
                .where(
                    (Entry.published == True) &
                    (FTSEntry.match(search)))
                .order_by(SQL('score').desc()))

    @classmethod
    def drafts(cls):
        return Entry.select().where(Entry.published == False)
