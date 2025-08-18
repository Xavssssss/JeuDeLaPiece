import os
import random
import uuid
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = '6joqhm3h'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# Chaque room est une partie indépendante
rooms = {}

def PileFace():
    return 'pile' if random.randint(0,1) == 0 else 'face'

def charger_questions(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        return [ligne.strip() for ligne in f]

def tirer_question(liste_questions):
    if not liste_questions:
        return None
    question = random.choice(liste_questions)
    liste_questions.remove(question)
    return question

@app.route('/')
def index():
    return render_template('client.html')

# ----------- SOCKET EVENTS ------------

@socketio.on('createRoom')
def createRoom():
    """Crée une room unique pour un joueur"""
    room_id = str(uuid.uuid4())[:8]  # id court ex: 'a1b2c3d4'
    rooms[room_id] = {
        "joueurs": [],
        "questions": charger_questions("question.txt")
    }
    join_room(room_id)
    socketio.emit("roomCreated", room_id, to=request.sid)  # renvoie au client son id unique
    print("Nouvelle room créée:", room_id)

@socketio.on('NouvJoueur')
def ajoutJoueur(data):
    room = data['room']
    pseudo = data['pseudo']

    if room in rooms and pseudo not in rooms[room]["joueurs"]:
        rooms[room]["joueurs"].append(pseudo)
        print(pseudo, "ajouté dans", room)

    socketio.emit('majListe', rooms[room]["joueurs"], to=room)

@socketio.on('SupprimerJoueur')
def supprimerJoueur(data):
    room = data['room']
    pseudo = data['pseudo']
    if room in rooms and pseudo in rooms[room]["joueurs"]:
        rooms[room]["joueurs"].remove(pseudo)
        print(pseudo, "supprimé de", room)
    socketio.emit('majListe', rooms[room]["joueurs"], to=room)

@socketio.on('chargerQuestion')
def charger(data):
    room = data['room']
    if room in rooms:
        rooms[room]["questions"] = charger_questions('question.txt')
        print("Questions rechargées pour", room)

@socketio.on('lancerRound')
def lancerRound(data):
    room = data['room']
    if room in rooms and rooms[room]["joueurs"]:
        joueurEnCours = random.choice(rooms[room]["joueurs"])
        socketio.emit('AfficheNomJoueurR', joueurEnCours, to=room)

@socketio.on('demandeQuestion')
def demanderQuestion(data):
    room = data['room']
    if room in rooms:
        question = tirer_question(rooms[room]["questions"])
        socketio.emit('AfficherQuestion', question, to=room)

@socketio.on("envoyerResPileFace")
def envoyerRes(data):
    room = data['room']
    res = PileFace()
    socketio.emit('ResPileFace', res, to=room)

# ----------- MAIN -----------

if __name__ == '__main__':
    print("Serveur lancé avec rooms isolées")
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
