import requests

ville = input("Entrez une ville : ")
url = f"https://wttr.in/{ville}?format=3"

try:
    reponse = requests.get(url)
    if reponse.status_code == 200:
        print("Météo :", reponse.text)
    else:
        print("Erreur de récupération de la météo.")
except Exception as e:
    print("Erreur :", e)
