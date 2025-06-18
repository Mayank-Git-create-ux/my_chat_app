from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO

# Initialize extensions globally
db = SQLAlchemy()
socketio = SocketIO(cors_allowed_origins="*")  # Enable CORS if frontend is separate
login_manager = LoginManager()

def create_app():
    # Serve /uploads/<filename> from uploads folder (for file preview/download)
    app = Flask(__name__, static_url_path='/uploads', static_folder='uploads')

    # Load config (make sure you have config/Config class defined)
    app.config.from_object('config.Config')

    # Initialize Flask extensions with the app
    db.init_app(app)
    socketio.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # Redirect unauthorized to this route

    # Register blueprints
    from app.routes import main, file_bp
    from .auth_routes import auth

    app.register_blueprint(main)
    app.register_blueprint(file_bp, url_prefix='/file')  # file upload/download
    app.register_blueprint(auth)

    # Register custom Socket.IO events
    from .socketio_events import register_socketio_events
    register_socketio_events(socketio)

    with app.app_context():
        db.create_all()

    return app
