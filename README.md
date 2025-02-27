`README.md`  projet Flask API qui utilise Playwright pour extraire des détails de vol depuis Skyscanner :

---

# Skyscanner Flight Details API

This is a Flask-based API that scrapes flight details from Skyscanner based on user-provided parameters. The API uses Playwright to automate the scraping process and return flight information.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoint](#api-endpoint)
- [Example Request](#example-request)
- [Example Response](#example-response)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features

- Scrapes flight details from Skyscanner based on departure, destination, travel dates, number of passengers, and more.
- Filters flights based on a maximum price specified by the user.
- Returns comprehensive flight information, including airline, price, duration, and more.

## Requirements

- Python 3.7 or higher
- Flask
- Playwright
- Other dependencies listed in `requirements.txt`

## Installation

1. **Clone the repository**:
    ```bash
    git clone https://github.com/Schmied07/findYourFlight.git
    cd findYourFlight
    ```

2. **Set up a virtual environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Install Playwright and its dependencies**:
    ```bash
    playwright install
    ```

## Usage

1. **Run the Flask server**:
    ```bash
    flask run
    ```

2. **Send a POST request** to the `/extract_flight_details` endpoint with the required parameters to get flight details.

## API Endpoint

### `POST /extract_flight_details`

Extracts flight details from Skyscanner based on the input parameters.

#### Request Parameters

- `depart` (string): Departure airport code (e.g., `LOS` for Lagos).
- `arrivee` (string): Arrival airport code (e.g., `CDG` for Paris).
- `dateDepart` (string): Departure date in `YYYYMMDD` format.
- `dateRetour` (string): Return date in `YYYYMMDD` format (optional for one-way trips).
- `nbAdultes` (integer): Number of adult passengers (default: 1).
- `nbEnfants` (integer): Number of child passengers (default: 0).
- `typeVoyage` (string): Type of trip (`aller-simple` for one-way, `aller-retour` for round-trip).
- `classeCabine` (string): Cabin class (`e` for economy, `b` for business, etc.).
- `prixMax` (integer): Maximum allowed price for flights.

#### Example Request

```json
{
    "depart": "LOS",
    "arrivee": "CDG",
    "dateDepart": "20240913",
    "dateRetour": "20240930",
    "nbAdultes": 1,
    "nbEnfants": 0,
    "typeVoyage": "aller-retour",
    "classeCabine": "e",
    "prixMax": "1000"
}
```

#### Example Response

```json
{
    "flights": [
        {
            "airline_info": "Air France",
            "price": 950,
            "departure_time": "08:30",
            "departure_airport": "LOS",
            "arrival_time": "14:10",
            "arrival_airport": "CDG",
            "duration": "6h 40m",
            "stop_info": "Non-stop",
            "return_departure_time": "16:00",
            "return_departure_airport": "CDG",
            "return_arrival_time": "21:40",
            "return_arrival_airport": "LOS",
            "return_duration": "6h 40m",
            "return_stop_info": "Non-stop",
            "booking_link": "https://www.skyscanner.fr/path/to/booking"
        },
        ...
    ]
}
```

## Troubleshooting

- **Playwright not launching the browser**: Ensure that you have installed Playwright and its dependencies correctly by running `playwright install`.
- **Timeout errors**: If scraping takes too long, consider increasing the timeout or ensuring your internet connection is stable.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

This `README.md` file provides a clear and concise overview of your project, explaining how to set it up, use it, and what to expect from the API. You can modify this template to suit your specific project details.