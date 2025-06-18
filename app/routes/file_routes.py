from flask import Blueprint, request, current_app, send_from_directory
from flask_socketio import emit
from werkzeug.utils import secure_filename
import os
from app import socketio

bp = Blueprint('file', __name__)

# Routes:
# - POST /upload         -> to upload a file and emit a socket event
# - GET  /uploads/<file> -> to serve uploaded files

@bp.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files or 'username' not in request.form or 'room' not in request.form:
        return 'Missing file, username, or room', 400

    file = request.files['file']
    username = request.form['username']
    room = request.form['room']

    if file.filename == '':
        return 'No selected file', 400

    filename = secure_filename(file.filename)

    # Get full upload folder path
    upload_folder = os.path.join(current_app.root_path, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)  # Create folder if it doesn't exist

    # Save file
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    # Emit to the room about the new file
    socketio.emit('file_message', {
        'username': username,
        'file_url': f'/uploads/{filename}',
        'file_name': filename,
        'room': room
    }, room=room)

    return 'File uploaded', 200


@bp.route('/uploads/<filename>')
def uploaded_file(filename):
    upload_folder = os.path.join(current_app.root_path, 'uploads')
    return send_from_directory(upload_folder, filename)
