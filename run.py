from app import create_app, socketio
from flask import request
from datetime import datetime
from app.models import Message
from app import db

app = create_app()


if __name__ == '__main__':
    socketio.run(app, debug=True)
