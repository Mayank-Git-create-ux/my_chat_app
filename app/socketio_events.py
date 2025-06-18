from flask import request
from app import db
from app.models import Message
from flask_socketio import emit, join_room, leave_room, disconnect
from datetime import datetime

# Track active users per room and map SID to user/room
active_users_per_room = {}
sid_to_user_room = {}

def register_socketio_events(socketio):
    @socketio.on('join')
    def handle_join(data):
        room = data['room']
        user = data['user']
        sid = request.sid

        join_room(room)

        # Update tracking
        active_users_per_room.setdefault(room, set()).add(user)
        sid_to_user_room[sid] = (user, room)

        # Send message history
        messages = Message.query.filter_by(room=room).order_by(Message.timestamp.asc()).limit(50).all()
        for msg in messages:
            emit('receive_message', {
                'id': msg.id,
                'user': msg.username,
                'message': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'is_old': True
            }, room=sid)

        # Send user joined announcement
        emit('receive_message', {
            'user': 'System',
            'message': f"{user} joined the room.",
            'timestamp': datetime.utcnow().isoformat()
        }, room=room)

        # Broadcast active user count
        emit('room_user_count', {
            'room': room,
            'count': len(active_users_per_room[room])
        }, room=room)

        # NEW: Broadcast user list
        emit('room_user_list', {
            'room': room,
            'users': list(active_users_per_room[room])
        }, room=room)

    @socketio.on('send_message')
    def handle_send_message(data):
        data['timestamp'] = datetime.utcnow().isoformat()

        new_msg = Message(
            username=data['user'],
            content=data['message'],
            room=data['room']
        )
        db.session.add(new_msg)
        db.session.commit()

        emit('receive_message', {
            'id': new_msg.id,
            'user': new_msg.username,
            'message': new_msg.content,
            'timestamp': new_msg.timestamp.isoformat()
        }, room=data['room'])

    @socketio.on('edit_message')
    def handle_edit(data):
        print("Edit event received:", data)
        msg = Message.query.get(data['id'])
        if msg and msg.username == data['user']:
            msg.content = data['new_message']
            db.session.commit()
            emit('message_edited', {
                'id': msg.id,
                'new_message': msg.content
            }, room=data['room'])

    @socketio.on('delete_message')
    def handle_delete(data):
        print("Delete event received:", data)
        msg = Message.query.get(data['id'])
        if msg and msg.username == data['user']:
            db.session.delete(msg)
            db.session.commit()
            emit('message_deleted', {
                'id': data['id']
            }, room=data['room'])

    @socketio.on('disconnect')
    def handle_disconnect():
        sid = request.sid
        user_room = sid_to_user_room.get(sid)
        if user_room:
            user, room = user_room

            # Remove user from active list
            if room in active_users_per_room and user in active_users_per_room[room]:
                active_users_per_room[room].remove(user)

                # Broadcast updated count
                emit('room_user_count', {
                    'room': room,
                    'count': len(active_users_per_room[room])
                }, room=room)

                # NEW: Broadcast updated user list
                emit('room_user_list', {
                    'room': room,
                    'users': list(active_users_per_room[room])
                }, room=room)

            # Clean up mapping
            del sid_to_user_room[sid]

    # Live typing
    @socketio.on('typing')
    def handle_typing(data):
        user = data['user']
        room = data['room']
        emit('user_typing', {'user': user}, room=room, include_self=False)

    @socketio.on('stop_typing')
    def handle_stop_typing(data):
        user = data['user']
        room = data['room']
        emit('user_stopped_typing', {'user': user}, room=room, include_self=False)

    # read tick
    @socketio.on('message_read')
    def handle_message_read(data):
        msg_id = data['id']
        user = data['user']
        room = data['room']

        emit('message_read_ack', {
            'id': msg_id,
            'user': user
        }, room=room, include_self=False)

    # file upload
    @socketio.on('file_uploaded')
    def handle_file_uploaded(data):
        emit('file_shared', data, room=data['room'], include_self=False)

