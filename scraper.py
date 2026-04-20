import sys
import json
import logging
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

URL = "https://www.supercars.com/standings/2026/supercars"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Mapping teams to car manufacturers based on the user's provided manual sample.
TEAMS_CAR_MAP = {
    "Red Bull Ampol Racing": "Ford Mustang GT",
    "Penrite Racing": "Ford Mustang GT",
    "Monster Castrol Racing": "Ford Mustang GT",
    "DEWALT Racing": "Chev Camaro ZL1",
    "Shell V-Power Racing Team": "Ford Mustang GT",
    "Mobil1 Truck Assist Racing": "Toyota GR Supra",
    "Sherrin Rentals Racing": "Chev Camaro ZL1",
    "Snowy River Caravans Racing": "Chev Camaro ZL1",
    "Brad Jones Racing": "Toyota GR Supra",
    "Blanchard Racing Team": "Ford Mustang GT",
    "Mobil1 Optus Racing": "Toyota GR Supra",
    "Bendix Racing": "Chev Camaro ZL1",
    "R&J Batteries Racing": "Toyota GR Supra",
    "PremiAir Racing": "Chev Camaro ZL1",
    "Objective Racing": "Ford Mustang GT",
    "Erebus Motorsport": "Chev Camaro ZL1",
    "LIQUI MOLY BLAHST Racing": "Ford Mustang GT",
    "CoolDrive Racing": "Ford Mustang GT",
}

def clean_int(text):
    if not text:
        return 0
    clean_text = "".join(c for c in text if c.isdigit())
    if not clean_text:
        return 0
    return int(clean_text)

def scrape_standings():
    logging.info(f"Fetching standings from {URL}")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to fetch standings: {e}")
        return None

    soup = BeautifulSoup(response.text, "lxml")
    table = soup.find("table")
    if not table:
        logging.error("Could not find standings table on the page.")
        return None

    tbody = table.find("tbody")
    if not tbody:
        logging.error("Could not find tbody inside the table.")
        return None

    standings = []
    
    # Iterate over each row
    for row in tbody.find_all("tr"):
        cells = row.find_all(["th", "td"])
        if len(cells) < 4:
            continue
            
        # Determine format based on number of columns
        # In 2026: 4 columns (Pos+Driver, Wins, Poles, Pts)
        # In 2025 Finals/Enduros: 5 columns (Pos, Driver, Wins, Poles, Pts)
        if len(cells) == 5:
            pos_cell = cells[0]
            driver_cell = cells[1]
            wins_cell = cells[2]
            poles_cell = cells[3]
            pts_cell = cells[4]
        else:
            pos_cell = cells[0]
            driver_cell = cells[0]
            wins_cell = cells[1]
            poles_cell = cells[2]
            pts_cell = cells[3]
        
        # Place is in a div with text containing the number
        place_elem = pos_cell.find("div", class_=lambda x: x and "font-medium" in x and "text-sm" in x)
        place = int(place_elem.text.strip()) if place_elem else 0
        
        # Number is in a span with text-white
        number_span = driver_cell.find("span", class_=lambda x: x and "text-white" in x)
        number = int(number_span.text.strip()) if number_span else 0
        
        # Name is in a div with aria-label
        name_div = driver_cell.find("div", attrs={"aria-label": True})
        name = name_div.text.strip() if name_div else ""
        
        # Team is in a div with text-light-grey-4
        team_div = driver_cell.find("div", class_=lambda x: x and "text-light-grey-4" in x)
        team = team_div.text.strip() if team_div else ""
        
        # Parse wins, poles, points
        wins = clean_int(wins_cell.text.strip())
        poles = clean_int(poles_cell.text.strip())
        points = clean_int(pts_cell.text.strip())
        
        car = TEAMS_CAR_MAP.get(team, "Unknown Car")
        
        driver_data = {
            "place": place,
            "number": number,
            "team": team,
            "name": name,
            "car": car,
            "poles": poles,
            "wins": wins,
            "points": points,
            "odds": { "bet365": "0", "sportsbet": "0", "dabble": "0" }
        }
        standings.append(driver_data)
        
    return standings

def save_data(data):
    # Save as pure JSON file
    json_path = "sc_championship_standing.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logging.info(f"Saved to {json_path}")
    
    # Save as PHP file that outputs JSON
    php_path = "sc_championship_standing.php"
    php_content = "<?php\nheader('Content-Type: application/json');\n?>\n" + json.dumps(data, indent=2) + "\n"
    with open(php_path, "w", encoding="utf-8") as f:
        f.write(php_content)
    logging.info(f"Saved to {php_path}")

if __name__ == "__main__":
    data = scrape_standings()
    if data:
        logging.info(f"Successfully parsed {len(data)} drivers.")
        save_data(data)
    else:
        logging.error("Failed to parse standings.")
        sys.exit(1)
