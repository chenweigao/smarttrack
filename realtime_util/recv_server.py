import threading
from receiver import Receiver
import socketserver
import datetime
import socket

from flask import Flask, render_template
from flask_socketio import SocketIO

async_mode = None
receiver_port = 9090

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode=async_mode)


def receiver_task():
    class EmitReceiver(Receiver):
        def notify(self, message: dict):
            message['address'] = self.request.getpeername()
            message['time'] = datetime.datetime.now()
            for k in message.keys():
                message[k] = str(message[k])
            print('EMIT', message)
            socketio.emit('event', message, namespace='/log')

    server = socketserver.ThreadingTCPServer(('', receiver_port), EmitReceiver)
    server.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.serve_forever()


@app.route("/")
def index():
    return render_template('index.html')


if __name__ == '__main__':
    # receiver_task()
    th = threading.Thread(target=receiver_task)
    th.start()
    socketio.run(app, debug=False, host='0.0.0.0', port=5050)
