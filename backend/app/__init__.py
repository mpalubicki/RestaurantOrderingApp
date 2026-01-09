from flask import Flask
from .config import Config
from .extensions import mongo, db, login_manager, csrf
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Enable CORS for APIs
    CORS(app)

    # Init extensions
    mongo.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    login_manager.login_view = "auth.login"

    # Register blueprints
    from .routes.auth_routes import auth_bp
    from .routes.menu_routes import menu_bp
    from .routes.order_routes import order_bp
    from .routes.admin_routes import admin_bp
    from .routes.api_routes import api_bp
    from .routes.main_routes import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(order_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    return app