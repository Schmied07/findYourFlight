from flask import Flask, request, jsonify
from playwright.sync_api import sync_playwright
import re

app = Flask(__name__)

def extract_flight_details(data):
    # Récupérer les paramètres depuis le dictionnaire data
    depart = data.get("depart", "")
    arrivee = data.get("arrivee", "")
    date_depart = data.get("dateDepart", "")
    date_retour = data.get("dateRetour", "")
    nb_adultes = data.get("nbAdultes", 1)
    nb_enfants = data.get("nbEnfants", 0)
    type_voyage = data.get("typeVoyage", "aller-simple")
    classe_cabine = data.get("classeCabine", "e")
    prix_max = int(data.get("prixMax", 1000)) 
    
    # Construire l'URL en fonction des paramètres
    if type_voyage == "aller-simple":
        url = f"https://www.skyscanner.fr/transport/vols/{depart}/{arrivee}/{date_depart}/?adults={nb_adultes}&adultsv2={nb_adultes}&cabinclass={classe_cabine}&children={nb_enfants}&childrenv2=&inboundaltsenabled=false&infants=0&outboundaltsenabled=false&preferdirects=false&ref=home&rtn=0"
    else:
        url = f"https://www.skyscanner.fr/transport/vols/{depart}/{arrivee}/{date_depart}/{date_retour}/?adults={nb_adultes}&adultsv2={nb_adultes}&cabinclass={classe_cabine}&children={nb_enfants}&childrenv2=&inboundaltsenabled=false&infants=0&outboundaltsenabled=false&preferdirects=false&ref=home&rtn=1"

    flight_details = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url, timeout=60000)

        # Attendre que la page soit complètement chargée
        page.wait_for_load_state('networkidle')

        # Récupérer tous les blocs contenant les informations de vol
        flights = page.query_selector_all("div.FlightsResults_dayViewItems__ZmU3Z > div")

        if not flights:
            flight_details.append("No flight data found. Check your selectors or page load timing.")
        else:
            for flight in flights:
                # Extraction des informations spécifiques pour le vol aller
                airline_info = flight.query_selector("div.LogoImage_container__ZjFjY").inner_text().strip() if flight.query_selector("div.LogoImage_container__ZjFjY") else "N/A"
                price_info = flight.query_selector("div.Price_mainPriceContainer__YTcwM").inner_text().strip() if flight.query_selector("div.Price_mainPriceContainer__YTcwM") else "N/A"
                
                if price_info != "N/A":
                    price_info_cleaned = re.sub(r'[^\d]', '', price_info)
                    if price_info_cleaned:
                        price_info = int(price_info_cleaned)

                if price_info != "N/A" and price_info > prix_max:
                    continue  # Ignorer ce vol s'il dépasse le prix maximum

                price_total_info = flight.query_selector("span.Price_totalPrice__NTE2Z").inner_text().strip() if flight.query_selector("span.Price_totalPrice__NTE2Z") else "N/A"
                departure_time = flight.query_selector("div.LegInfo_routePartialDepart__MDFkN span span").inner_text().strip() if flight.query_selector("div.LegInfo_routePartialDepart__MDFkN span span") else "N/A"
                departure_airport = flight.query_selector("span.LegInfo_routePartialCityTooltip__YzAzY").inner_text().strip() if flight.query_selector("span.LegInfo_routePartialCityTooltip__YzAzY") else "N/A"
                duration = flight.query_selector("span.Duration_duration__ZjQ0Z").inner_text().strip() if flight.query_selector("span.Duration_duration__ZjQ0Z") else "N/A"
                # Nettoyer la durée pour enlever les espaces insécables
                duration = duration.replace('\xa0', ' ')
                stop_info = flight.query_selector("span.LegInfo_stopsLabelRed__MWRmM").inner_text().strip() if flight.query_selector("span.LegInfo_stopsLabelRed__MWRmM") else "N/A"

                arrival_time = flight.query_selector_all("div.LegInfo_routePartialArrive__ZmRjO span")[1].inner_text().strip() if len(flight.query_selector_all("div.LegInfo_routePartialArrive__ZmRjO span")) > 1 else "N/A"
                arrival_airport = flight.query_selector_all("span.LegInfo_routePartialCityTooltip__YzAzY")[1].inner_text().strip() if len(flight.query_selector_all("span.LegInfo_routePartialCityTooltip__YzAzY")) > 1 else "N/A"

                back_leg = flight.query_selector("div.UpperTicketBody_legsContainer__ZGJkZ")
                if back_leg:
                    return_legs = back_leg.query_selector_all("div.LegDetails_container__ZjJhN")
                    if len(return_legs) > 1:
                        back_leg = return_legs[1]

                        departure_back_time = back_leg.query_selector("div.LegInfo_routePartialDepart__MDFkN span span").inner_text().strip() if back_leg.query_selector("div.LegInfo_routePartialDepart__MDFkN span span") else "N/A"
                        departure_back_airport = back_leg.query_selector("span.LegInfo_routePartialCityTooltip__YzAzY").inner_text().strip() if back_leg.query_selector("span.LegInfo_routePartialCityTooltip__YzAzY") else "N/A"
                        duration_back = back_leg.query_selector("span.Duration_duration__ZjQ0Z").inner_text().strip() if back_leg.query_selector("span.Duration_duration__ZjQ0Z") else "N/A"
                        # Nettoyer la durée de retour pour enlever les espaces insécables
                        duration_back = duration_back.replace('\xa0', ' ')
                        stop_info_back = back_leg.query_selector("span.LegInfo_stopsLabelRed__MWRmM").inner_text().strip() if back_leg.query_selector("span.LegInfo_stopsLabelRed__MWRmM") else "N/A"

                        arrival_back_time = back_leg.query_selector_all("div.LegInfo_routePartialArrive__ZmRjO span")[1].inner_text().strip() if len(back_leg.query_selector_all("div.LegInfo_routePartialArrive__ZmRjO span")) > 1 else "N/A"
                        arrival_back_airport = back_leg.query_selector_all("span.LegInfo_routePartialCityTooltip__YzAzY")[1].inner_text().strip() if len(back_leg.query_selector_all("span.LegInfo_routePartialCityTooltip__YzAzY")) > 1 else "N/A"
                    else:
                        departure_back_time = departure_back_airport = duration_back = stop_info_back = arrival_back_time = arrival_back_airport = "N/A"
                else:
                    departure_back_time = departure_back_airport = duration_back = stop_info_back = arrival_back_time = arrival_back_airport = "N/A"

                booking_link = flight.query_selector("a")
                if booking_link:
                    link_url = booking_link.get_attribute('href')
                    full_booking_link = f"https://www.skyscanner.fr{link_url}" if link_url.startswith("/") else link_url
                else:
                    full_booking_link = "N/A"

                if airline_info != "N/A":
                    flight_details.append({
                        "airline_info": airline_info,
                        "price": price_info,
                        "total_price": price_total_info,
                        "departure_time": departure_time,
                        "departure_airport": departure_airport,
                        "arrival_time": arrival_time,
                        "arrival_airport": arrival_airport,
                        "duration": duration,
                        "stop_info": stop_info,
                        "return_departure_time": departure_back_time,
                        "return_departure_airport": departure_back_airport,
                        "return_duration": duration_back,
                        "return_stop_info": stop_info_back,
                        "return_arrival_time": arrival_back_time,
                        "return_arrival_airport": arrival_back_airport,
                        "booking_link": full_booking_link
                    })

        browser.close()
    return flight_details

@app.route('/extract_flight_details', methods=['POST'])
def extract_flight_details_api():
    data = request.json
    flight_details = extract_flight_details(data)
    return jsonify(flight_details)

if __name__ == "__main__":
    app.run(debug=True)



# from requests_html import HTMLSession

# session = HTMLSession()
# response = session.get('https://www.kayak.fr/flights/PAR-NYC/2024-10-02/2024-10-08?fs=bfc=2&sort=bestflight_a')

# # Attendre que le JavaScript soit exécuté
# response.html.render()

# # Extraire le titre de la page
# title = response.html.find('title', first=True).text
# print(f'Title of the page is: {title}')


# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager

# def scrape_with_chrome(url):
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")  # Exécute le navigateur en arrière-plan
#     chrome_options.add_argument("--ignore-certificate-errors")
#     chrome_options.add_argument("--no-sandbox")
#     chrome_options.add_argument("--disable-dev-shm-usage")

#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=chrome_options)

#     try:
#         driver.get(url)
#         print(driver.title)  # Test simple pour vérifier que le site se charge
#     finally:
#         driver.quit()

# url = 'https://www.esky.fr/flights/search/ap/DLA/ap/LOS?departureDate=2024-09-10&returnDate=2024-09-19&pa=1&py=0&pc=0&pi=0&sc=economy'
# scrape_with_chrome(url)

