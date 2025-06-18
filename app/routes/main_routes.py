from flask import Blueprint, redirect, render_template, request, session, url_for
from flask_login import login_required, current_user

from app.models import Message
from app import db

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    return render_template('chat.html', username=current_user.username)

@main.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'POST':
        room = request.form.get('custom_room') or request.form.get('room')
        session['room'] = room
        return redirect(url_for('main.chat_room'))
    return render_template('select_room.html')  # new template with room dropdown


@main.route('/chatroom')
@login_required
def chat_room():
    if 'room' not in session:
        return redirect(url_for('main.chat'))

    room = session['room']
    
    # 🔍 Fetch all messages for the room from the DB
    messages = Message.query.filter_by(room=room).order_by(Message.timestamp.asc()).all()

    return render_template(
        'chat.html',
        username=current_user.username,
        room=room,
        messages=messages  # ✅ Pass messages to the template
    )

