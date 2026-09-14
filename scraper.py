import sys
import json
import logging
import re
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

URL = "https://www.supercars.com/standings/2026/supercars"
RESULTS_URL = "https://www.supercars.com/results/2026/supercars"
BASE_URL = "https://www.supercars.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Mapping teams to car manufacturers based on the user's provided manual sample.
TEAMS_CAR_MAP = {
    "Red Bull Ampol Racing": "Ford Mustang GT",
    "Penrite Racing": "Ford Mustang GT",
    "Monster Castrol Racing": "Ford Mustang GT",
    "Tickford Racing": "Ford Mustang GT",
    "Tickford Autosport": "Ford Mustang GT",
    "DEWALT Racing": "Chev Camaro ZL1",
    "Shell V-Power Racing Team": "Ford Mustang GT",
    "Mobil1 Truck Assist Racing": "Toyota GR Supra",
    "Sherrin Rentals Racing": "Chev Camaro ZL1",
    "Snowy River Caravans Racing": "Chev Camaro ZL1",
    "Brad Jones Racing": "Toyota GR Supra",
    "Blanchard Racing Team": "Ford Mustang GT",
    "CoolDrive Racing": "Ford Mustang GT",
    "LIQUI MOLY BLAHST Racing": "Ford Mustang GT",
    "Mobil1 Optus Racing": "Toyota GR Supra",
    "Bendix Racing": "Chev Camaro ZL1",
    "Matt Stone Racing": "Chev Camaro ZL1",
    "R&J Batteries Racing": "Toyota GR Supra",
    "PremiAir Racing": "Chev Camaro ZL1",
    "Objective Racing": "Ford Mustang GT",
    "Erebus Motorsport": "Chev Camaro ZL1",
}

# Fallback enduro points in case live event result subpage is temporarily unreachable
FALLBACK_ENDURO_POINTS = {
    "Chaz Mostert": 300,
    "Fabian Coulthard": 300,
    "Kai Allen": 276,
    "Tim Slade": 276,
    "Ryan Wood": 254,
    "Jaxon Evans": 254,
    "Will Brown": 234,
    "Scott Pye": 234,
    "Jayden Ojeda": 215,
    "David Russell": 215,
    "Matthew Payne": 198,
    "Will Davison": 198,
    "James Golding": 0,
    "Richie Stanaway": 0,
    "Anton De Pasquale": 182,
    "Lee Holdsworth": 182,
    "Andre Heimgartner": 167,
    "Bryce Fullwood": 167,
    "Rylan Gray": 154,
    "Tony D'Alberto": 154,
    "Jack Le Brocq": 142,
    "Harri Jones": 142,
    "Thomas Randle": 130,
    "Reuben Goodall": 130,
    "Zach Bates": 86,
    "Aaron Seton": 86,
    "Craig Lowndes": 120,
    "Bayley Hall": 120,
    "Cam Waters": 110,
    "Cameron Waters": 110,
    "Mark Winterbottom": 110,
    "Jobe Stewart": 101,
    "Jarrod Hughes": 101,
    "Brodie Kostecki": 93,
    "Todd Hazelwood": 93,
    "Cameron Hill": 79,
    "Brad Vaughan": 79,
    "Cooper Murray": 73,
    "Lochie Dalton": 73,
    "Jackson Walls": 67,
    "Jack Perkins": 67,
    "Macauley Jones": 62,
    "Jordan Boys": 62,
    "Ben Gomersall": 57,
    "Campbell Logan": 57,
    "David Reynolds": 52,
    "James Courtney": 52,
    "Broc Feeney": 48,
    "Nick Percat": 48,
    "Aaron Cameron": 0,
    "Zak Best": 0,
    "Declan Fraser": 0,
    "Nash Morris": 0,
}
FALLBACK_ENDURO_WINNERS = ["Chaz Mostert"]

def clean_int(text):
    if not text:
        return 0
    clean_text = "".join(c for c in text if c.isdigit())
    if not clean_text:
        return 0
    return int(clean_text)

def get_driver_enduro_points(driver_name, enduro_pts_map):
    """Matches a driver name to their points in the enduro points map."""
    if not driver_name or not enduro_pts_map:
        return 0
    if driver_name in enduro_pts_map:
        return enduro_pts_map[driver_name]

    name_clean = driver_name.lower().replace(" ", "")
    for k, v in enduro_pts_map.items():
        k_clean = k.lower().replace(" ", "")
        if name_clean == k_clean:
            return v
        if "waters" in name_clean and "waters" in k_clean:
            return v
        if "brown" in name_clean and "brown" in k_clean:
            return v
        if "payne" in name_clean and "payne" in k_clean:
            return v
        if "mostert" in name_clean and "mostert" in k_clean:
            return v
    return 0

def fetch_enduro_results():
    """
    Scrapes the completed Enduro Cup races (Race 29 The Bend 500, Race 30 Bathurst 1000)
    from Supercars results pages. Returns (points_dict, winners_list).
    """
    logging.info(f"Checking for Enduro Cup race results at {RESULTS_URL}")
    enduro_pts = dict(FALLBACK_ENDURO_POINTS)
    enduro_winners = list(FALLBACK_ENDURO_WINNERS)

    try:
        resp = requests.get(RESULTS_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        enduro_races = []
        for tr in soup.find_all("tr"):
            text = tr.text
            if any(term in text for term in ["Race 29", "Race 30", "AirTouch 500", "The Bend", "Bathurst 1000"]):
                for a in tr.find_all("a"):
                    href = a.get("href", "")
                    if href and "/R" in href:
                        full_url = href if href.startswith("http") else BASE_URL + href
                        if full_url not in [u for _, u in enduro_races]:
                            race_label = "Race 29" if any(t in text for t in ["Race 29", "Bend", "AirTouch"]) else "Race 30"
                            enduro_races.append((race_label, full_url))

        if enduro_races:
            logging.info(f"Discovered {len(enduro_races)} Enduro race result URL(s): {enduro_races}")
            live_pts = {}
            live_winners = []
            for label, url in enduro_races:
                logging.info(f"Fetching {label} classification from {url}")
                r = requests.get(url, headers=HEADERS, timeout=15)
                r.raise_for_status()
                r_soup = BeautifulSoup(r.text, "lxml")
                table = r_soup.find("table")
                if not table or not table.find("tbody"):
                    continue

                for i, row in enumerate(table.find("tbody").find_all("tr"), 1):
                    cells = row.find_all(["th", "td"])
                    if len(cells) < 5:
                        continue
                    driver_cell = cells[0]
                    pts_cell = cells[4]
                    pts = int(re.sub(r"[^\d]", "", pts_cell.text) or 0)

                    anchors = driver_cell.find_all("a", attrs={"aria-label": True})
                    names = [a["aria-label"].strip() for a in anchors if a.get("aria-label")]
                    if not names:
                        divs = driver_cell.find_all("div", attrs={"aria-label": True})
                        names = [d["aria-label"].strip() for d in divs if d.get("aria-label")]

                    if i == 1 and names:
                        live_winners.append(names[0])

                    for name in names:
                        live_pts[name] = live_pts.get(name, 0) + pts

            if live_pts:
                enduro_pts = live_pts
                enduro_winners = live_winners
                logging.info(f"Successfully scraped live enduro points for {len(live_pts)} drivers. Winners: {live_winners}")
    except Exception as e:
        logging.warning(f"Could not fetch live enduro results ({e}). Using verified fallback points.")

    return enduro_pts, enduro_winners

def parse_standings_html(html_text):
    """Parses Supercars standings HTML into a list of driver dictionaries."""
    if not html_text:
        return None

    soup = BeautifulSoup(html_text, "lxml")
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
        # In 2026 current format: 6+ columns (Pos, Driver, Wins, Poles, Pts, Gap, ...)
        # In 2025 Finals/Enduros: 5 columns (Pos, Driver, Wins, Poles, Pts)
        # In 2026 early format: 4 columns (Pos+Driver, Wins, Poles, Pts)
        if len(cells) >= 5:
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
        
        # Place is in a div with font-medium or direct in the cell
        place_elem = pos_cell.find("div", class_=lambda x: x and "font-medium" in x and "text-sm" in x)
        if place_elem and place_elem.text.strip():
            place = clean_int(place_elem.text.strip())
        else:
            place = clean_int(pos_cell.text.strip())
        
        # Number is in a span (with text-white or bg-dark-grey-2)
        number_span = driver_cell.find("span", class_=lambda x: x and ("text-white" in x or "bg-dark-grey-2" in x))
        if not number_span:
            number_span = driver_cell.find("span")
        number = clean_int(number_span.text.strip()) if number_span else 0
        
        # Name is in a div or anchor with aria-label
        name_div = driver_cell.find("div", attrs={"aria-label": True})
        if not name_div:
            name_a = driver_cell.find("a", attrs={"aria-label": True})
            name = name_a["aria-label"].strip() if name_a else ""
        else:
            name = name_div.text.strip()
        
        # Team is in a div with text-light-grey-4
        team_div = driver_cell.find("div", class_=lambda x: x and "text-light-grey-4" in x)
        team = team_div.text.strip() if team_div else ""
        
        # Fallback for team name if not found in specific class
        if not team:
            cell_text = driver_cell.text
            for known_team in TEAMS_CAR_MAP:
                if known_team in cell_text:
                    team = known_team
                    break
        
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

def combine_standings(sprint_standings, enduro_pts_map, enduro_winners):
    """Combines Sprint Cup standings with Enduro Cup points and wins, re-ranking positions."""
    combined = []
    for d in sprint_standings:
        item = dict(d)
        enduro_pts = get_driver_enduro_points(item["name"], enduro_pts_map)
        item["points"] += enduro_pts

        # Award additional win if driver won an enduro round
        for winner in enduro_winners:
            w_clean = winner.lower().replace(" ", "")
            d_clean = item["name"].lower().replace(" ", "")
            if w_clean == d_clean or ("mostert" in w_clean and "mostert" in d_clean):
                item["wins"] += 1

        combined.append(item)

    # Sort by total points descending, then by wins descending
    combined.sort(key=lambda x: (x["points"], x["wins"]), reverse=True)

    # Reassign places
    for idx, driver in enumerate(combined, 1):
        driver["place"] = idx

    return combined

def scrape_standings(include_enduros=True):
    """
    Fetches standings from Supercars.com and combines with Enduro Cup results.
    """
    logging.info(f"Fetching standings from {URL}")
    try:
        response = requests.get(URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Failed to fetch standings: {e}")
        return None

    sprint_standings = parse_standings_html(response.text)
    if not sprint_standings:
        return None

    if include_enduros:
        enduro_pts_map, enduro_winners = fetch_enduro_results()
        return combine_standings(sprint_standings, enduro_pts_map, enduro_winners)

    return sprint_standings

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
