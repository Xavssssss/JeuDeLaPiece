

import random
def charger_questions(fichier):
    """Retourne une liste contenant toutes les questions du fichier."""
    with open(fichier, "r", encoding="utf-8") as f:
        return [ligne.strip() for ligne in f]

# --- Fonction 2 : Piocher une question aléatoire et la retirer ---
def tirer_question(liste_questions):
    """Retourne une question aléatoire et la retire de la liste."""
    if not liste_questions:
        return None  # plus de questions disponibles
    question = random.choice(liste_questions)
    liste_questions.remove(question)
    return question
liste = ['xavy','alex','theo']

def tirage(listePseudo):
    global liste
    nomSortie = random.choice(liste)
    listeF = [i for i in listePseudo if i !=nomSortie]
    liste.extend(listeF)
    return nomSortie
    
liste = charger_questions("question.txt")

# Tirer 5 questions aléatoires
for _ in range(5):
    q = tirer_question(liste)
    if q:
        print("Question tirée :", q)
    else:
        print("Plus de questions disponibles !")