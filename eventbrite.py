from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import calendar
import json

app = Flask(__name__)

# Configurer les headers pour imiter un navigateur
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

session = requests.Session()
session.headers.update(headers)

def fetch_page(url):
    try:
        response = session.get(url)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None

def parse_events(soup):
    events = soup.find_all('section', class_='DiscoverHorizontalEventCard-module__cardWrapper___2_FKN')
    
    if not events:
        return []

    current_week_start = datetime.now() - timedelta(days=datetime.now().weekday())
    current_week_end = current_week_start + timedelta(days=6)
    event_list = []

    for event in events:
        title_element = event.find('h3', class_='Typography_root__487rx #3a3247 Typography_body-lg__487rx event-card__clamp-line--two Typography_align-match-parent__487rx')
        title = title_element.get_text(strip=True) if title_element else 'No title found'

        date_element = event.find('p', class_='Typography_root__487rx #585163 Typography_body-md__487rx event-card__clamp-line--one Typography_align-match-parent__487rx')
        date_text = date_element.get_text(strip=True) if date_element else 'No date found'

        event_date = None
        for fmt in ('%A at %I:%M %p', '%a, %b %d, %I:%M %p'):
            try:
                event_date = datetime.strptime(date_text, fmt)
                day_index = list(calendar.day_name).index(event_date.strftime('%A'))
                event_date = current_week_start + timedelta(days=day_index)
                event_date = event_date.replace(hour=event_date.hour, minute=event_date.minute)
                break
            except ValueError:
                continue
        
        if not event_date or not (current_week_start <= event_date <= current_week_end):
            continue

        link_element = event.find('a', class_='event-card-link')
        link = link_element['href'] if link_element else 'No link found'

        image_element = event.find('img', class_='event-card-image')
        image_url = image_element['src'] if image_element else 'No image found'

        event_list.append({
            'title': title,
            'date': event_date.strftime('%A, %B %d, %Y at %I:%M %p'),
            'link': link,
            'image_url': image_url
        })
    
    return event_list

def scrape_all_pages(base_url):
    page = 1
    all_events = []
    while True:
        url = f'{base_url}?page={page}'
        response = fetch_page(url)
        if response and response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            events = parse_events(soup)
            all_events.extend(events)
            
            next_button = soup.find('a', {'aria-label': 'Next'})
            if not next_button or 'disabled' in next_button.get('class', []):
                break
            page += 1
        else:
            break
    return all_events

@app.route('/events', methods=['GET'])
def get_events():
    country = request.args.get('country', 'france')
    city = request.args.get('city', 'paris')
    category = request.args.get('category', 'music')

    base_url = f'https://www.eventbrite.fr/d/{country}--{city}/{category}--events/'
    events = scrape_all_pages(base_url)
    
    # Utilisation de json.dumps avec ensure_ascii=False pour éviter le ré-encodage
    return app.response_class(
        response=json.dumps(events, ensure_ascii=False),
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(debug=True)
