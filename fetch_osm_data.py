"""
Télécharge les données écoles et stations de transport depuis OpenStreetMap
via l'API Overpass pour le département 44 (Loire-Atlantique).

Génère les fichiers CSV attendus par create_duckdb.py :
  - data/ecoles/ecoles-44.csv
  - data/transport/stations-44.csv
"""

import csv
import os
import time
import urllib.request
import urllib.parse
import json

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
DATA_DIR = "data"

# -- Overpass queries --------------------------------------------------------

# Écoles : amenity = school | kindergarten | university | college
ECOLES_QUERY = """
[out:json][timeout:120];
area["name"="Loire-Atlantique"]["admin_level"="6"]->.searchArea;
(
  nwr["amenity"~"^(school|kindergarten|university|college)$"](area.searchArea);
);
out center;
"""

# Stations de transport : railway = station | halt | tram_stop
#   + public_transport = station (pour les arrêts de bus/tram TAN)
STATIONS_QUERY = """
[out:json][timeout:120];
area["name"="Loire-Atlantique"]["admin_level"="6"]->.searchArea;
(
  nwr["railway"~"^(station|halt|tram_stop)$"](area.searchArea);
);
out center;
"""


def overpass_fetch(query: str) -> list[dict]:
    """Envoie une requête Overpass et retourne la liste des éléments."""
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(
        OVERPASS_URL,
        data=data,
        headers={"User-Agent": "SAE601-Nantes-DataLoader/1.0"},
    )
    print(f"   -> Envoi de la requete Overpass...")
    with urllib.request.urlopen(req, timeout=180) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    elements = body.get("elements", [])
    print(f"   -> {len(elements)} elements recus.")
    return elements


def extract_lat_lon(elem: dict) -> tuple:
    """Extrait lat/lon d'un élément (node, way center, relation center)."""
    if elem["type"] == "node":
        return elem.get("lat"), elem.get("lon")
    # Pour way/relation, Overpass renvoie 'center' avec out center;
    center = elem.get("center", {})
    return center.get("lat"), center.get("lon")


# -- Ecoles ------------------------------------------------------------------

def fetch_ecoles():
    print("=" * 60)
    print("Telechargement des ecoles (OpenStreetMap - Overpass)")
    print("=" * 60)

    elements = overpass_fetch(ECOLES_QUERY)

    csv_path = os.path.join(DATA_DIR, "ecoles", "ecoles-44.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    fieldnames = ["osm_id", "type", "lat", "lon", "name", "city", "postcode", "amenity"]
    count = 0

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for elem in elements:
            tags = elem.get("tags", {})
            lat, lon = extract_lat_lon(elem)
            if lat is None or lon is None:
                continue

            row = {
                "osm_id": elem.get("id"),
                "type": elem.get("type", ""),
                "lat": lat,
                "lon": lon,
                "name": tags.get("name", ""),
                "city": tags.get("addr:city", ""),
                "postcode": tags.get("addr:postcode", ""),
                "amenity": tags.get("amenity", ""),
            }
            writer.writerow(row)
            count += 1

    print(f"   [OK] {count} ecoles ecrites dans {csv_path}\n")
    return count


# -- Stations transport ------------------------------------------------------

def fetch_stations():
    print("=" * 60)
    print("Telechargement des stations de transport (OpenStreetMap - Overpass)")
    print("=" * 60)

    elements = overpass_fetch(STATIONS_QUERY)

    csv_path = os.path.join(DATA_DIR, "transport", "stations-44.csv")
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    fieldnames = ["osm_id", "lat", "lon", "name", "railway_type", "operator", "network", "uic_ref"]
    count = 0

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for elem in elements:
            tags = elem.get("tags", {})
            lat, lon = extract_lat_lon(elem)
            if lat is None or lon is None:
                continue

            row = {
                "osm_id": elem.get("id"),
                "lat": lat,
                "lon": lon,
                "name": tags.get("name", ""),
                "railway_type": tags.get("railway", ""),
                "operator": tags.get("operator", ""),
                "network": tags.get("network", ""),
                "uic_ref": tags.get("uic_ref", ""),
            }
            writer.writerow(row)
            count += 1

    print(f"   [OK] {count} stations ecrites dans {csv_path}\n")
    return count


# -- Main --------------------------------------------------------------------

if __name__ == "__main__":
    n_ecoles = fetch_ecoles()
    # Pause de courtoisie envers l'API Overpass
    if n_ecoles > 0:
        print("   (pause 5 s avant la requete suivante...)")
        time.sleep(5)
    n_stations = fetch_stations()

    print("=" * 60)
    print("RESUME")
    print("=" * 60)
    print(f"  Ecoles :   {n_ecoles:>6}")
    print(f"  Stations : {n_stations:>6}")
    print("\nVous pouvez maintenant relancer create_duckdb.py !")
