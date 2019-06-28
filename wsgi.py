from flask_socketio import SocketIO

from fopdcw import app

if __name__ == "__main__":
    #- app.run()
    socketio.run(app)
