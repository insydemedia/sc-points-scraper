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
from scraper import TEAMS_CAR_MAP, clean_int, parse_standings_html, scrape_standings, save_data

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
print("\n=== TEST 1: Current 2026 Live Format (6-column table, 28 drivers) ===")
html_file = "supercars_2026_current.html" if os.path.exists("supercars_2026_current.html") else "supercars.html"
with open(html_file, "r", encoding="utf-8") as f:
    data_current = parse_standings_html(f.read())

check(data_current is not None, "Current table parsed without errors")
check(data_current is not None and len(data_current) == 28, f"Expected 28 drivers, got {len(data_current) if data_current else 0}")

if data_current:
    first = data_current[0]
    check(first["place"] == 1,                         f"P1 place=1, got {first['place']}")
    check(first["name"] == "Matthew Payne",            f"P1 name='Matthew Payne', got '{first['name']}'")
    check(first["number"] == 19,                       f"P1 number=19, got {first['number']}")
    check(first["team"] == "Penrite Racing",           f"P1 team correct: '{first['team']}'")
    check(first["car"] == "Ford Mustang GT",           f"P1 car='Ford Mustang GT', got '{first['car']}'")
    check(first["wins"] == 5,                          f"P1 wins=5, got {first['wins']}")
    check(first["poles"] == 5,                         f"P1 poles=5, got {first['poles']}")
    check(first["points"] == 1950,                     f"P1 points=1950, got {first['points']}")

    # standings should be in ascending place order
    places = [d["place"] for d in data_current]
    check(places == list(range(1, 29)),                f"All places 1-28 sequential: {places[:5]}...")

    # No unknown cars
    unknown = [d["team"] for d in data_current if d["car"] == "Unknown Car"]
    check(len(unknown) == 0,                           f"No unknown car mappings (unknown: {unknown})")

    # Check specific 2026 wildcard/entrant cars
    golding = next((d for d in data_current if d["name"] == "James Golding"), None)
    check(golding is not None and golding["car"] == "Ford Mustang GT", "James Golding car mapped to Ford Mustang GT")

    cameron = next((d for d in data_current if d["name"] == "Aaron Cameron"), None)
    check(cameron is not None and cameron["car"] == "Ford Mustang GT", "Aaron Cameron car mapped to Ford Mustang GT")

    seton = next((d for d in data_current if d["name"] == "Aaron Seton"), None)
    check(seton is not None and seton["car"] == "Chev Camaro ZL1", "Aaron Seton car mapped to Chev Camaro ZL1")

    goodall = next((d for d in data_current if d["name"] == "Reuben Goodall"), None)
    check(goodall is not None and goodall["car"] == "Ford Mustang GT", "Reuben Goodall car mapped to Ford Mustang GT")

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
print("\n=== TEST 4: Scraper Execution & Output Files ===")
if data_current:
    save_data(data_current)

# Verify sc_championship_standing.php
try:
    php_content = open("sc_championship_standing.php").read()
    check(php_content.startswith("<?php"),             "PHP file starts with <?php")
    check("Content-Type: application/json" in php_content, "PHP sets Content-Type header")
    json_part = php_content.split("?>\n", 1)[1] if "?>\n" in php_content else ""
    try:
        parsed_php = json.loads(json_part)
        check(isinstance(parsed_php, list),            "PHP payload is a JSON array")
        check(len(parsed_php) == 28,                   f"PHP payload has 28 entries, got {len(parsed_php)}")
        check(parsed_php[0]["name"] == "Matthew Payne", f"PHP P1 name correct: '{parsed_php[0]['name']}'")
    except Exception as e:
        check(False,                                   f"PHP JSON is valid: {e}")
except Exception as e:
    check(False,                                       f"PHP file readable: {e}")

# Verify sc_championship_standing.json
try:
    with open("sc_championship_standing.json") as f:
        parsed_json = json.load(f)
    check(isinstance(parsed_json, list),               "JSON file is an array")
    check(len(parsed_json) == 28,                      f"JSON has 28 entries, got {len(parsed_json)}")

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

