from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import re
import random
import time

app = Flask(__name__)

# Liste de différents user-agents populaires pour éviter le blocage par le site
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Mobile Safari/537.36",
]

def extract_flight_details(data):
    # Choisir un user-agent aléatoire
    random_user_agent = random.choice(USER_AGENTS)
    
    # Récupérer les détails du vol à partir des données JSON
    depart = data.get("depart", "")
    arrivee = data.get("arrivee", "")
    date_depart = data.get("dateDepart", "")
    date_retour = data.get("dateRetour", "")
    nb_adultes = data.get("nbAdultes", 1)
    nb_enfants = data.get("nbEnfants", 0)
    type_voyage = data.get("typeVoyage", "aller-simple")
    classe_cabine = data.get("classeCabine", "e")
    prix_max = int(data.get("prixMax", 1000)) 

    # Construire l'URL de Skyscanner en fonction des détails du vol
    if type_voyage == "aller-simple":
        url = f"https://www.skyscanner.fr/transport/vols/{depart}/{arrivee}/{date_depart}/?adults={nb_adultes}&adultsv2={nb_adultes}&cabinclass={classe_cabine}&children={nb_enfants}&childrenv2=&inboundaltsenabled=false&infants=0&outboundaltsenabled=false&preferdirects=false&ref=home&rtn=0"
    else:
        url = f"https://www.skyscanner.fr/transport/vols/{depart}/{arrivee}/{date_depart}/{date_retour}/?adults={nb_adultes}&adultsv2={nb_adultes}&cabinclass={classe_cabine}&children={nb_enfants}&childrenv2=&inboundaltsenabled=false&infants=0&outboundaltsenabled=false&preferdirects=false&ref=home&rtn=1"

    flight_details = []  # Liste pour stocker les détails des vols
    max_retries = 3  # Nombre maximum de tentatives en cas d'échec
    retry_delay = 180  # Délai entre les tentatives (en secondes)

    with sync_playwright() as p:
        # Lancer le navigateur en mode headless pour une meilleure performance
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(user_agent=random_user_agent)  # Créer un contexte avec un user-agent personnalisé
        page = context.new_page()  # Créer une nouvelle page

        # Essayer de récupérer les détails des vols avec un nombre maximum de tentatives
        for attempt in range(max_retries):
            try:
                page.goto(url, timeout=60000)  # Accéder à l'URL et attendre 60 secondes maximum
                page.wait_for_load_state('networkidle')  # Attendre que le réseau soit inactif

                # Récupérer tous les blocs contenant les informations de vol
                flights = page.query_selector_all("div.FlightsResults_dayViewItems__ZmU3Z > div")
                if not flights:
                    print(f"Tentative {attempt + 1}/{max_retries}: No flight data found. Retrying in 3 minutes...")
                    time.sleep(retry_delay)  # Attendre avant de réessayer
                    continue  # Passer à la prochaine tentative

                # Extraire les informations de chaque vol
                for flight in flights:
                    airline_info = flight.query_selector("div.LogoImage_container__ZjFjY").inner_text().strip() if flight.query_selector("div.LogoImage_container__ZjFjY") else "N/A"
                    price_info = flight.query_selector("div.Price_mainPriceContainer__YTcwM").inner_text().strip() if flight.query_selector("div.Price_mainPriceContainer__YTcwM") else "N/A"
                    
                    if price_info != "N/A":
                        price_info_cleaned = re.sub(r'[^\d]', '', price_info)  # Nettoyer le prix pour garder seulement les chiffres
                        if price_info_cleaned:
                            price_info = int(price_info_cleaned)  # Conversion en entier

                    # Ignorer le vol si le prix dépasse le prix maximum spécifié
                    if isinstance(price_info, int) and price_info > prix_max:
                        continue

                    # Extraire d'autres informations sur le vol
                    total_price_info = flight.query_selector("span.Price_totalPrice__NTE2Z").inner_text().strip() if flight.query_selector("span.Price_totalPrice__NTE2Z") else "N/A"
                    departure_time = flight.query_selector("div.LegInfo_routePartialDepart__MDFkN span span").inner_text().strip() if flight.query_selector("div.LegInfo_routePartialDepart__MDFkN span span") else "N/A"
                    departure_airport = flight.query_selector("span.LegInfo_routePartialCityTooltip__YzAzY").inner_text().strip() if flight.query_selector("span.LegInfo_routePartialCityTooltip__YzAzY") else "N/A"
                    duration = flight.query_selector("span.Duration_duration__ZjQ0Z").inner_text().strip() if flight.query_selector("span.Duration_duration__ZjQ0Z") else "N/A"
                    duration = duration.replace('\xa0', ' ')  # Nettoyer la durée pour enlever les espaces insécables
                    stop_info = flight.query_selector("span.LegInfo_stopsLabelRed__MWRmM").inner_text().strip() if flight.query_selector("span.LegInfo_stopsLabelRed__MWRmM") else "N/A"

                    arrival_time = flight.query_selector_all("div.LegInfo_routePartialArrive__ZmRjO span")[1].inner_text().strip() if len(flight.query_selector_all("div.LegInfo_routePartialArrive__ZmRjO span")) > 1 else "N/A"
                    arrival_airport = flight.query_selector_all("span.LegInfo_routePartialCityTooltip__YzAzY")[1].inner_text().strip() if len(flight.query_selector_all("span.LegInfo_routePartialCityTooltip__YzAzY")) > 1 else "N/A"

                    # Vérification des informations de vol de retour
                    back_leg = flight.query_selector("div.UpperTicketBody_legsContainer__ZGJkZ")
                    if back_leg:
                        return_legs = back_leg.query_selector_all("div.LegDetails_container__ZjJhN")
                        if len(return_legs) > 1:
                            back_leg = return_legs[1]

                            departure_back_time = back_leg.query_selector("div.LegInfo_routePartialDepart__MDFkN span span").inner_text().strip() if back_leg.query_selector("div.LegInfo_routePartialDepart__MDFkN span span") else "N/A"
                            departure_back_airport = back_leg.query_selector("span.LegInfo_routePartialCityTooltip__YzAzY").inner_text().strip() if back_leg.query_selector("span.LegInfo_routePartialCityTooltip__YzAzY") else "N/A"
                            duration_back = back_leg.query_selector("span.Duration_duration__ZjQ0Z").inner_text().strip() if back_leg.query_selector("span.Duration_duration__ZjQ0Z") else "N/A"
                            duration_back = duration_back.replace('\xa0', ' ')  # Nettoyer la durée de retour
                            stop_info_back = back_leg.query_selector("span.LegInfo_stopsLabelRed__MWRmM").inner_text().strip() if back_leg.query_selector("span.LegInfo_stopsLabelRed__MWRmM") else "N/A"

                            arrival_back_time = back_leg.query_selector_all("div.LegInfo_routePartialArrive__ZmRjO span")[1].inner_text().strip() if len(back_leg.query_selector_all("div.LegInfo_routePartialArrive__ZmRjO span")) > 1 else "N/A"
                            arrival_back_airport = back_leg.query_selector_all("span.LegInfo_routePartialCityTooltip__YzAzY")[1].inner_text().strip() if len(back_leg.query_selector_all("span.LegInfo_routePartialCityTooltip__YzAzY")) > 1 else "N/A"
                        else:
                            # Initialiser les valeurs de retour à "N/A" si aucune information n'est trouvée
                            departure_back_time = departure_back_airport = duration_back = stop_info_back = arrival_back_time = arrival_back_airport = "N/A"
                    else:
                        # Initialiser les valeurs de retour à "N/A" si aucune information n'est trouvée
                        departure_back_time = departure_back_airport = duration_back = stop_info_back = arrival_back_time = arrival_back_airport = "N/A"

                    # Ajouter les détails du vol à la liste
                    if airline_info != "N/A":
                        flight_details.append({
                            "airline": airline_info,
                            "price": price_info,
                            "total_price": total_price_info,
                            "departure_time": departure_time,
                            "departure_airport": departure_airport,
                            "arrival_time": arrival_time,
                            "arrival_airport": arrival_airport,
                            "duration": duration,
                            "stops": stop_info,
                            "return_departure_time": departure_back_time,
                            "return_departure_airport": departure_back_airport,
                            "return_arrival_time": arrival_back_time,
                            "return_arrival_airport": arrival_back_airport,
                            "return_duration": duration_back,
                            "return_stops": stop_info_back,
                        })

                break  # Sortir de la boucle de réessai si le succès
            except Exception as e:
                print(f"An error occurred: {e}")  # Afficher l'erreur
                if attempt < max_retries - 1:
                    print(f"Tentative {attempt + 1}/{max_retries} failed. Retrying in 3 minutes...")
                    time.sleep(retry_delay)  # Attendre avant de réessayer

        browser.close()  # Fermer le navigateur
    return flight_details  # Retourner les détails des vols

@app.route('/extract_flight_details', methods=['POST'])
def extract_flight_details_api():
    data = request.json  # Récupérer les données JSON de la requête
    flight_details = extract_flight_details(data)  # Extraire les détails des vols
    return jsonify(flight_details)  # Retourner les détails au format JSON

if __name__ == "__main__":
    app.run(debug=True)  # Lancer l'application Flask en mode debug
