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

    @app.context_processor
    def inject_currency():
        from flask_login import current_user
        from .models import CURRENCIES
        code = getattr(current_user, 'currency', None) or 'USD'
        return {'currency_code': code,
                'currency_symbol': CURRENCIES.get(code, '$')}

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app


def _run_lightweight_migrations():
    inspector = inspect(db.engine)
    note_cols = {col['name'] for col in inspector.get_columns('note')}
    if 'category' not in note_cols:
        db.session.execute(
            text("ALTER TABLE note ADD COLUMN category VARCHAR(150) DEFAULT 'Other'"))
        db.session.commit()

    user_cols = {col['name'] for col in inspector.get_columns('user')}
    if 'currency' not in user_cols:
        db.session.execute(
            text("ALTER TABLE \"user\" ADD COLUMN currency VARCHAR(10) DEFAULT 'USD'"))
        db.session.commit()


def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')
