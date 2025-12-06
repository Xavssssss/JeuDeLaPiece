import os
import random
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_socketio import SocketIO, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = '6joqhm3h'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# Dictionnaire des rooms indépendantes
rooms = {}

# ---------------- FONCTIONS ----------------

def PileFace():
    return 'pile' if random.randint(0,1) == 0 else 'face'

def charger_questions(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        return [ligne.strip() for ligne in f if ligne.strip()]

def tirer_question(liste_questions):
    if not liste_questions:
        return "PLUS DE QUESTIONS DISPONIBLES"
    question = random.choice(liste_questions)
    liste_questions.remove(question)
    return question

def tirage(room):
    if not rooms[room]["tirage"]:
        # si tirage vide → recharger la base pour continuer les rounds
        rooms[room]["tirage"] = rooms[room]["base"][:]

    nomSortie = random.choice(rooms[room]["tirage"])

    # Ajouter +1 chance aux autres joueurs
    for joueur in rooms[room]["base"]:
        if joueur != nomSortie:
            rooms[room]["tirage"].append(joueur)

    return nomSortie

# ---------------- ROUTE ----------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/client')
def client():
    return render_template('client.html')

# ---------------- SOCKET EVENTS ----------------

@socketio.on('NouvJoueur')
def ajoutJoueur(data):
    room = data['room']
    pseudo = data['pseudo']

    if room not in rooms:
        rooms[room] = {
            "joueurs": [],
            "questions": charger_questions("question.txt"),
            "base": [],
            "tirage": []
        }
    
    if pseudo not in rooms[room]["joueurs"]:
        rooms[room]["joueurs"].append(pseudo)
        print(pseudo, "ajouté dans", room)

    join_room(room)
    socketio.emit('majListe', rooms[room]["joueurs"], to=room)

@socketio.on('SupprimerJoueur')
def supprimerJoueur(data):
    room = data['room']
    pseudo = data['pseudo']
    if room in rooms and pseudo in rooms[room]["joueurs"]:
        rooms[room]["joueurs"].remove(pseudo)
        print(pseudo, "supprimé de", room)
    socketio.emit('majListe', rooms[room]["joueurs"], to=room)

@socketio.on('lancerRound')
def lancerRound(data):
    room = data['room']

    if room in rooms and rooms[room]["joueurs"]:
        if not rooms[room]["base"]:
            rooms[room]["base"] = rooms[room]["joueurs"][:]
            rooms[room]["tirage"] = rooms[room]["joueurs"][:]

        joueurEnCours = tirage(room)
        print("Round lancé dans", room, "->", joueurEnCours)
        socketio.emit('AfficheNomJoueurR', joueurEnCours, to=room)

@socketio.on('demandeQuestion')
def demanderQuestion(data):
    room = data['room']
    if room in rooms:
        question = tirer_question(rooms[room]["questions"])
        socketio.emit('AfficherQuestion', question, to=room)
        print("Question envoyée dans", room, ":", question)

@socketio.on("envoyerResPileFace")
def envoyerRes(data):
    room = data['room']
    res = PileFace()
    socketio.emit('ResPileFace', res, to=room)

@socketio.on('resetRoom')
def reset_room(data):
    room = data['room']
    if room in rooms:
        rooms[room]["joueurs"].clear()
        rooms[room]["base"].clear()
        rooms[room]["tirage"].clear()
        rooms[room]["questions"] = charger_questions("question.txt")
        print("Room reset :", room)
        socketio.emit('majListe', [], to=room)

# ---------------- MAIN ----------------
if __name__ == '__main__':
    print("Serveur lancé avec rooms isolées")
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
