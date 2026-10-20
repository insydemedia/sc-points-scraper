"""
Comprehensive verification for scraper.py.
Tests the actual scraper logic against current 2026 HTML, 2026 early format,
and 2025 Finals format, validates output files and all edge cases.
"""
import sys
import json
import os

# ── Import the real scraper functions ─────────────────────────────────────────
sys.path.insert(0, ".")
from scraper import (
    TEAMS_CAR_MAP,
    clean_int,
    parse_standings_html,
    parse_standings_json,
    parse_standings,
    scrape_standings,
    save_data
)

PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"
errors = []

def check(condition, message):
    if condition:
        print(f"  {PASS}  {message}")
    else:
        print(f"  {FAIL}  {message}")
        errors.append(message)


# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TEST 1: Current 2026 Finals Format (Official Next.js Stream, 24 drivers) ===")
html_file = "supercars_2026_current.html" if os.path.exists("supercars_2026_current.html") else "supercars.html"
with open(html_file, "r", encoding="utf-8") as f:
    html_content = f.read()
    data_current = parse_standings(html_content)

check(data_current is not None, "Current standings parsed without errors")
check(data_current is not None and len(data_current) == 24, f"Expected 24 drivers, got {len(data_current) if data_current else 0}")

if data_current:
    first = data_current[0]
    check(first["place"] == 1,                         f"P1 place=1, got {first['place']}")
    check(first["name"] == "Matthew Payne",            f"P1 name='Matthew Payne', got '{first['name']}'")
    check(first["number"] == 19,                       f"P1 number=19, got {first['number']}")
    check(first["team"] == "Penrite Racing",           f"P1 team correct: '{first['team']}'")
    check(first["car"] == "Ford Mustang GT",           f"P1 car='Ford Mustang GT', got '{first['car']}'")
    check(first["wins"] == 5,                          f"P1 wins=5, got {first['wins']}")
    check(first["poles"] == 7,                         f"P1 poles=7, got {first['poles']}")
    check(first["points"] == 3150,                     f"P1 points=3150, got {first['points']}")

    second = data_current[1]
    check(second["place"] == 2,                        f"P2 place=2, got {second['place']}")
    check(second["name"] == "Broc Feeney",             f"P2 name='Broc Feeney', got '{second['name']}'")
    check(second["points"] == 3145,                    f"P2 points=3145, got {second['points']}")

    third = data_current[2]
    check(third["place"] == 3,                         f"P3 place=3, got {third['place']}")
    check(third["name"] == "Will Brown",               f"P3 name='Will Brown', got '{third['name']}'")
    check(third["points"] == 3103,                     f"P3 points=3103, got {third['points']}")

    # standings should be in ascending place order
    places = [d["place"] for d in data_current]
    check(places == list(range(1, 25)),                f"All places 1-24 sequential: {places[:5]}...")

    # No unknown cars
    unknown = [d["team"] for d in data_current if d["car"] == "Unknown Car"]
    check(len(unknown) == 0,                           f"No unknown car mappings (unknown: {unknown})")

    # Check specific 2026 entrant cars
    golding = next((d for d in data_current if d["name"] == "James Golding"), None)
    check(golding is not None and golding["car"] == "Ford Mustang GT", "James Golding car mapped to Ford Mustang GT")

    cameron = next((d for d in data_current if d["name"] == "Aaron Cameron"), None)
    check(cameron is not None and cameron["car"] == "Ford Mustang GT", "Aaron Cameron car mapped to Ford Mustang GT")

    mostert = next((d for d in data_current if d["name"] == "Chaz Mostert"), None)
    check(mostert is not None and mostert["car"] == "Toyota GR Supra", "Chaz Mostert car mapped to Toyota GR Supra")

    # All drivers have the odds structure
    odds_ok = all(
        isinstance(d.get("odds"), dict) and
        set(d["odds"].keys()) == {"bet365", "sportsbet", "dabble"}
        for d in data_current
    )
    check(odds_ok, "All drivers have correct odds keys")


# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TEST 2: Earlier 2026 Format (4-column table, 24 drivers) ===")
with open("supercars.html", "r", encoding="utf-8") as f:
    data_2026_early = parse_standings_html(f.read())

check(data_2026_early is not None, "Table parsed without errors")
check(data_2026_early is not None and len(data_2026_early) == 24, f"Expected 24 drivers, got {len(data_2026_early) if data_2026_early else 0}")

if data_2026_early:
    first = data_2026_early[0]
    check(first["place"] == 1,                         f"P1 place=1, got {first['place']}")
    check(first["name"] == "Broc Feeney",              f"P1 name='Broc Feeney', got '{first['name']}'")
    check(first["number"] == 88,                       f"P1 number=88, got {first['number']}")
    check(first["team"] == "Red Bull Ampol Racing",    f"P1 team correct")
    check(first["car"] == "Ford Mustang GT",           f"P1 car='Ford Mustang GT', got '{first['car']}'")
    check(first["wins"] == 2,                          f"P1 wins=2, got {first['wins']}")
    check(first["poles"] == 1,                         f"P1 poles=1, got {first['poles']}")
    check(first["points"] == 259,                      f"P1 points=259, got {first['points']}")


# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TEST 3: 2025 Finals Format (5-column table) ===")
with open("supercars_2025.html", "r", encoding="utf-8") as f:
    data_2025 = parse_standings_html(f.read())

check(data_2025 is not None, "Table parsed without errors")
check(data_2025 is not None and len(data_2025) >= 24, f"At least 24 drivers, got {len(data_2025) if data_2025 else 0}")

if data_2025:
    first = data_2025[0]
    check(first["place"] == 1,                         f"P1 place=1, got {first['place']}")
    check(first["name"] == "Broc Feeney",              f"P1 name='Broc Feeney', got '{first['name']}'")
    check(first["number"] == 88,                       f"P1 number=88, got {first['number']}")
    check(first["team"] != "",                         f"P1 team found: '{first['team']}'")
    check(first["points"] > 0,                         f"P1 points > 0, got {first['points']}")
    check(first["wins"] > 0,                           f"P1 wins > 0, got {first['wins']}")

    # Check no one has place=0
    zero_place = [d["name"] for d in data_2025 if d["place"] == 0]
    check(len(zero_place) == 0,                        f"No drivers with place=0 (found: {zero_place})")

    # Check no one has name=""
    empty_name = [d["number"] for d in data_2025 if d["name"] == ""]
    check(len(empty_name) == 0,                        f"No drivers with empty name (numbers: {empty_name})")


# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TEST 4: Enduro Cup Combination Logic ===")
from scraper import combine_standings, FALLBACK_ENDURO_POINTS, FALLBACK_ENDURO_WINNERS

if data_current:
    combined_test = combine_standings(data_current, FALLBACK_ENDURO_POINTS, FALLBACK_ENDURO_WINNERS)
    check(combined_test is not None, "Combined standings generated")
    check(len(combined_test) == len(data_current), f"Combined standings driver count ({len(combined_test)}) matches input")
    
    # Check that places are 1..N
    c_places = [d["place"] for d in combined_test]
    check(c_places == list(range(1, len(combined_test) + 1)), "Combined standings have sequential places 1..N")
    
    # Check Chaz Mostert has extra win
    mostert = next((d for d in combined_test if "Mostert" in d["name"]), None)
    check(mostert is not None and mostert["wins"] >= 2, f"Chaz Mostert awarded extra win for Enduro round (wins: {mostert['wins'] if mostert else 0})")
    check(mostert is not None and mostert["points"] > 1413, f"Chaz Mostert enduro points added (total: {mostert['points'] if mostert else 0})")


# ─────────────────────────────────────────────────────────────────────────────
print("\n=== TEST 5: Scraper Execution & Output Files ===")
live_data = scrape_standings()
check(live_data is not None and len(live_data) == 24, f"Live scrape succeeded with {len(live_data) if live_data else 0} drivers")

if live_data:
    save_data(live_data)

    p1 = live_data[0]
    check(p1["place"] == 1, f"P1 place=1, got {p1['place']}")
    check(p1["name"] == "Matthew Payne", f"P1 name='Matthew Payne', got '{p1['name']}'")
    check(p1["points"] == 3150, f"P1 points=3150, got {p1['points']}")

# Verify sc_championship_standing.php
try:
    php_content = open("sc_championship_standing.php").read()
    check(php_content.startswith("<?php"),             "PHP file starts with <?php")
    check("Content-Type: application/json" in php_content, "PHP sets Content-Type header")
    json_part = php_content.split("?>\n", 1)[1] if "?>\n" in php_content else ""
    try:
        parsed_php = json.loads(json_part)
        check(isinstance(parsed_php, list),            "PHP payload is a JSON array")
        check(len(parsed_php) == 24,                   f"PHP payload has 24 entries, got {len(parsed_php)}")
        check(parsed_php[0]["name"] == "Matthew Payne", f"PHP P1 name correct: '{parsed_php[0]['name']}'")
        check(parsed_php[0]["points"] == 3150,         f"PHP P1 points=3150, got {parsed_php[0]['points']}")
    except Exception as e:
        check(False,                                   f"PHP JSON is valid: {e}")
except Exception as e:
    check(False,                                       f"PHP file readable: {e}")

# Verify sc_championship_standing.json
try:
    with open("sc_championship_standing.json") as f:
        parsed_json = json.load(f)
    check(isinstance(parsed_json, list),               "JSON file is an array")
    check(len(parsed_json) == 24,                      f"JSON has 24 entries, got {len(parsed_json)}")

    required_keys = {"place", "number", "team", "name", "car", "poles", "wins", "points", "odds"}
    for d in parsed_json:
        missing = required_keys - d.keys()
        if missing:
            check(False, f"Driver '{d.get('name','?')}' missing keys: {missing}")
            break
    else:
        check(True, f"All {len(parsed_json)} drivers have required keys")
except Exception as e:
    check(False, f"JSON file parseable: {e}")


# ─────────────────────────────────────────────────────────────────────────────
print()
if errors:
    print(f"\033[91m{len(errors)} test(s) FAILED:\033[0m")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\033[92mAll tests passed! ✓\033[0m")


