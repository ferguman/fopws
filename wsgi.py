from flask_socketio import SocketIO

from fopdcw import app, socketio

if __name__ == "__main__":
    #- app.run()
    socketio.run(app)
    #- socketio.run(app, host="127.0.0.1", port=5001)
