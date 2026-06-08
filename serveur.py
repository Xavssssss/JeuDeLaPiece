import os
import random
import math
import eventlet
from collections import Counter

eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = '6joqhm3h'
socketio = SocketIO(app, async_mode='eventlet', cors_allowed_origins="*")

# =========================================================
# ===================== GLOBAL STATE ======================
# =========================================================

rooms = {}

# =========================================================
# ===================== ROOM SYSTEM =======================
# =========================================================

def get_room(mode, room):
    return f"{mode}:{room}"

# =========================================================
# ===================== COMMON UTILS ======================
# =========================================================

def PileFace():
    return 'pile' if random.randint(0, 1) == 0 else 'face'


def charger_questions(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        return [ligne.strip() for ligne in f if ligne.strip()]


def tirer_question(liste_questions):
    if not liste_questions:
        return "PLUS DE QUESTIONS DISPONIBLES"
    q = random.choice(liste_questions)
    liste_questions.remove(q)
    return q


def tirage(room):
    if not rooms[room]["tirage"]:
        rooms[room]["tirage"] = rooms[room]["base"][:]

    nom = random.choice(rooms[room]["tirage"])

    for j in rooms[room]["base"]:
        if j != nom:
            rooms[room]["tirage"].append(j)

    return nom


# =========================================================
# ========================= ROUTES ========================
# =========================================================

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/client')
def client():
    return render_template('client.html')


@app.route('/clientCasino')
def casino():
    return render_template('casinoClient.html')


@app.route('/clientNoArg')
def noArg():
    return render_template('clientNoArg.html')


# =========================================================
# ====================== NORMAL MODE ======================
# =========================================================

@socketio.on('NouvJoueur')
def ajoutJoueur(data):
    room = get_room("normal", data['room'])
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

    join_room(room)
    socketio.emit('majListe', rooms[room]["joueurs"], to=room)


@socketio.on('SupprimerJoueur')
def supprimerJoueur(data):
    room = get_room("normal", data['room'])
    pseudo = data['pseudo']

    if room in rooms and pseudo in rooms[room]["joueurs"]:
        rooms[room]["joueurs"].remove(pseudo)

    socketio.emit('majListe', rooms[room]["joueurs"], to=room)


@socketio.on('lancerRound')
def lancerRound(data):
    room = get_room("normal", data['room'])

    if room in rooms and rooms[room]["joueurs"]:
        if not rooms[room]["base"]:
            rooms[room]["base"] = rooms[room]["joueurs"][:]
            rooms[room]["tirage"] = rooms[room]["joueurs"][:]

        joueur = tirage(room)
        socketio.emit('AfficheNomJoueurR', joueur, to=room)


@socketio.on('demandeQuestion')
def demanderQuestion(data):
    room = get_room("normal", data['room'])

    if room in rooms:
        q = tirer_question(rooms[room]["questions"])
        socketio.emit('AfficherQuestion', q, to=room)


@socketio.on("envoyerResPileFace")
def envoyerRes(data):
    room = get_room("normal", data['room'])
    socketio.emit('ResPileFace', PileFace(), to=room)


@socketio.on('resetRoom')
def reset_room(data):
    room = get_room("normal", data['room'])

    if room in rooms:
        rooms[room]["joueurs"].clear()
        rooms[room]["base"].clear()
        rooms[room]["tirage"].clear()
        rooms[room]["questions"] = charger_questions("question.txt")

    socketio.emit('majListe', [], to=room)


# =========================================================
# ======================== CASINO ==========================
# =========================================================

def roulette():
    symboles = ["⭐", "🍋", "💎", "🍒", "💀"]
    poids = [40, 20, 15, 7, 3]

    gains = {
        "⭐": 2,
        "🍋": 4,
        "💎": 5,
        "🍒": 7,
        "💀": 10
    }

    resultat = random.choices(symboles, weights=poids, k=3)

    compteur = Counter(resultat)
    symbole, nb = compteur.most_common(1)[0]

    s1, s2, s3 = resultat
    socketio.emit("symbole", {"s1": s1, "s2": s2, "s3": s3})

    if nb == 3:
        socketio.emit("Resultat", {
            "message": "🎉 JACKPOT ! Gain : ",
            "gain": gains[symbole]
        })

    elif nb == 2:
        gain = math.floor(gains[symbole] / 2)
        socketio.emit("Resultat", {
            "message": "✨ Deux symboles identiques ! Gain : ",
            "gain": gain
        })

    else:
        socketio.emit("Resultat", {
            "message": "❌ Perdu.",
            "gain": 0
        })


@socketio.on('lancerRoulette')
def lancerRoulette(data):
    roulette()


# =========================================================
# ===================== NO ARG MODE =======================
# =========================================================

def charger_questions_noarg(fichier):
    with open(fichier, "r", encoding="utf-8") as f:
        return [ligne.strip() for ligne in f if ligne.strip()]


def tirer_question_noarg(liste_questions):
    if not liste_questions:
        return "PLUS DE QUESTIONS DISPONIBLES"
    q = random.choice(liste_questions)
    liste_questions.remove(q)
    return q


def tirage_noarg(room):
    if not rooms[room]["tirage"]:
        rooms[room]["tirage"] = rooms[room]["base"][:]

    nom = random.choice(rooms[room]["tirage"])

    for j in rooms[room]["base"]:
        if j != nom:
            rooms[room]["tirage"].append(j)

    return nom


# ---------------- NO ARG SOCKET EVENTS ----------------

@socketio.on('NouvJoueurNoArg')
def ajoutJoueur_noarg(data):
    room = get_room("noarg", data['room'])
    pseudo = data['pseudo']

    if room not in rooms:
        rooms[room] = {
            "joueurs": [],
            "questionsNoArg": charger_questions_noarg("questionNoArg.txt"),
            "base": [],
            "tirage": []
        }

    if pseudo not in rooms[room]["joueurs"]:
        rooms[room]["joueurs"].append(pseudo)

    join_room(room)
    socketio.emit('majListeNoArg', rooms[room]["joueurs"], to=room)


@socketio.on('SupprimerJoueurNoArg')
def supprimerJoueur_noarg(data):
    room = get_room("noarg", data['room'])
    pseudo = data['pseudo']

    if room in rooms and pseudo in rooms[room]["joueurs"]:
        rooms[room]["joueurs"].remove(pseudo)

    socketio.emit('majListeNoArg', rooms[room]["joueurs"], to=room)


@socketio.on('lancerRoundNoArg')
def lancerRound_noarg(data):
    room = get_room("noarg", data['room'])

    if room in rooms and rooms[room]["joueurs"]:
        if not rooms[room]["base"]:
            rooms[room]["base"] = rooms[room]["joueurs"][:]
            rooms[room]["tirage"] = rooms[room]["joueurs"][:]

        joueur = tirage_noarg(room)
        socketio.emit('AfficheNomJoueurRNoArg', joueur, to=room)


@socketio.on('demandeQuestionNoArg')
def demanderQuestion_noarg(data):
    room = get_room("noarg", data['room'])

    if room in rooms:
        q = tirer_question_noarg(rooms[room]["questionsNoArg"])
        socketio.emit('AfficherQuestionNoArg', q, to=room)


@socketio.on("envoyerResPileFaceNoArg")
def envoyerRes_noarg(data):
    room = get_room("noarg", data['room'])
    socketio.emit('ResPileFaceNoArg', PileFace(), to=room)


@socketio.on('resetRoomNoArg')
def reset_room_noarg(data):
    room = get_room("noarg", data['room'])

    if room in rooms:
        rooms[room]["joueurs"].clear()
        rooms[room]["base"].clear()
        rooms[room]["tirage"].clear()
        rooms[room]["questionsNoArg"] = charger_questions_noarg("questionNoArg.txt")

    socketio.emit('majListeNoArg', [], to=room)


# =========================================================
# ========================= MAIN ==========================
# =========================================================

if __name__ == '__main__':
    print("Serveur lancé avec rooms isolées (normal / noarg / casino)")
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))