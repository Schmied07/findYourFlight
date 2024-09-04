import requests

url = "http://127.0.0.1:5000/extract_flight_details"
data = {
    "depart": "LOS",
    "arrivee": "CDG",
    "dateDepart": "20240913",
    "dateRetour": "20240930",
    "nbAdultes": 1,
    "nbEnfants": 0,
    "typeVoyage": "aller-retour",
    "classeCabine": "e",
    "prixMax": "1500"
}

response = requests.post(url, json=data)

if response.status_code == 200:
    flight_details = response.json()
    print(flight_details)
else:
    print(f"Request failed with status code {response.status_code}")
