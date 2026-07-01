import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from os import path
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Note
    
    with app.app_context():
        db.create_all()
        _run_lightweight_migrations()

    @app.context_processor
    def inject_static_version():
        css = os.path.join(app.static_folder, 'style.css')
        version = int(os.path.getmtime(css)) if os.path.exists(css) else 0
        return {'static_version': version}

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def _run_lightweight_migrations():
    """Add newly-introduced columns to existing SQLite tables in place.

    db.create_all() only creates missing tables, not missing columns, so
    older databases won't have columns added after they were first created.
    """
    inspector = inspect(db.engine)
    existing = {col['name'] for col in inspector.get_columns('note')}
    if 'category' not in existing:
        db.session.execute(
            text("ALTER TABLE note ADD COLUMN category VARCHAR(150) DEFAULT 'Other'"))
        db.session.commit()


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')
