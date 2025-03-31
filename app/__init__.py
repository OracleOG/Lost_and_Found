# app/__init__.py
from flask import Flask, send_from_directory
from flask_wtf.csrf import CSRFProtect
from flask_sqlalchemy import SQLAlchemy
from .config import Config
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()
migrate = Migrate()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure config are set
    if not app.config['SECRET_KEY']:
        raise ValueError("No SECRET_KEY set for Flask application")

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth_bp.login'
    login_manager.login_message_category = "danger"

    # Import models after db initialization to avoid circular imports
    from .models.user import User
    from .models.role import Role
    from .models.item import Item
    from .models.match import Match
    from .models.claim import Claim
    from .models.contact import Contact
    from .models.test import Test
    from .models.db_storage import DBStorage

    # Create application context and initialize database
    with app.app_context():
        # Create DBStorage instance
        storage = DBStorage(db)
       
        # Create all tables
        db.create_all()

    # Register user loader
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Custom Jinja filter
    def get_filename(path):
        return os.path.basename(path)
    app.jinja_env.filters['get_filename'] = get_filename

    # Route for uploaded files
    @app.route('/images/<filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Ensure the upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Register blueprints
    from .main.v2.create_request import create_request_bp
    from .main.v2.general_routes import general_bp
    from .main.v2.home_route import home_bp
    from .main.v2.quality_checker import quality_checker_bp
    from .main.v2.user_profile import user_profile_bp
    from .main.v2.authentication_routes import auth_bp
    from .apis.v2.items_route import item_bp_api
    from .apis.v2.claims_routes import claim_bp_api
    from .apis.v2.matches_routes import match_bp_api

    app.register_blueprint(create_request_bp)
    app.register_blueprint(general_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(quality_checker_bp)
    app.register_blueprint(user_profile_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(item_bp_api)
    app.register_blueprint(claim_bp_api)
    app.register_blueprint(match_bp_api)

    # Exempt API blueprints from CSRF protection
    csrf.exempt(item_bp_api)
    csrf.exempt(claim_bp_api)
    csrf.exempt(match_bp_api)

    return app