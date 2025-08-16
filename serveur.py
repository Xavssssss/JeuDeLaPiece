from flask import Flask, send_from_directory , render_template
from flask_socketio import SocketIO
import random
app = Flask(__name__)
socketio = SocketIO(app)

listeJoueur = []
listePseudo = []
Questions = []

def tirage(listePseudo):
    global listeJoueur
    nomSortie = random.choice(listeJoueur)
    listeF = [i for i in listePseudo if i !=nomSortie]
    listeJoueur.extend(listeF)
    return nomSortie

def PileFace():
    nb=random.randint(0,1)
    if nb==0:
        return 'pile'
    else:
        return 'face'

def charger_questions(fichier):
    """Retourne une liste contenant toutes les questions du fichier."""
    global Questions
    with open(fichier, "r", encoding="utf-8") as f:
        Questions = [ligne.strip() for ligne in f]

def tirer_question(liste_questions):
    """Retourne une question aléatoire et la retire de la liste."""
    if not liste_questions:
        return None  # plus de questions disponibles
    question = random.choice(liste_questions)
    liste_questions.remove(question)
    return question

@app.route('/')
def index():
    return render_template('client.html')

@socketio.on('NouvJoueur')
def ajoutJoueur(pseudo):
    global listeJoueur
    global listePseudo
    if pseudo not in listeJoueur:
        listeJoueur.append(pseudo)
        listePseudo.append(pseudo)
        print(pseudo, "ajouté")
    socketio.emit('majListe', listeJoueur)  # on renvoie la liste complète
    print(listeJoueur)

@socketio.on('SupprimerJoueur')
def supprimerJoueur(pseudo):
    global listeJoueur
    if pseudo in listeJoueur:
        listeJoueur.remove(pseudo)
        listePseudo.remove(pseudo)
        print(pseudo, "supprimé")
    socketio.emit('majListe', listeJoueur)  # on renvoie la liste complète
    print(listeJoueur)

@socketio.on('chargerQuestion')
def charger(data):
    print("on charge les question")
    charger_questions('question.txt')

@socketio.on('lancerRound')
def lancerRound(data):
    global listeJoueur
    print("Round Lancer")
    joueurEnCours = tirage(listePseudo)
    print("Le joueur choisie est "+joueurEnCours)
    socketio.emit('AfficheNomJoueurR',joueurEnCours)

@socketio.on('demandeQuestion')
def demanderQuestion(data):
    global Questions
    question = tirer_question(Questions)
    socketio.emit('AfficherQuestion',question)
    print("question envoyé " + question)
    

@socketio.on("envoyerResPileFace")
def envoyerRes(data):
    res=PileFace()
    socketio.emit('ResPileFace',res)
   
if __name__ == '__main__':
    print("Serveur lancé sur http://127.0.0.1:8080")
    socketio.run(app, host='127.0.0.1', port=8080)
