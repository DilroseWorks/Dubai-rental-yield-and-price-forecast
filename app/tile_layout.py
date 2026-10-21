"""Where each community sits on the schematic tile map, and its short tile label.

The map is 11 columns (west -> east: Jebel Ali to Deira) by 5 rows (row 0 = the Gulf,
row 4 = furthest inland). Positions are approximate on purpose: the page says "not to scale".
Keys are (segment, DLD area name) so the map follows the data, not the display names.
A community in the data but missing here is listed under the map instead of being dropped.
"""

COLS, ROWS = 11, 5

# (segment, area): (column, row, tile label)
TILES = {
    # ---- flats
    ("Flat", "PALM JUMEIRAH"): (3, 0, "Palm Jumeirah"),
    ("Flat", "AL KHAIRAN FIRST"): (10, 0, "Creek Harbour"),
    ("Flat", "MARSA DUBAI"): (1, 1, "Dubai Marina"),
    ("Flat", "AL THANYAH FIFTH"): (2, 1, "JLT"),
    ("Flat", "AL SAFOUH FIRST"): (3, 1, "Al Sufouh"),
    ("Flat", "UM SUQAIM THIRD"): (4, 1, "Madinat Jumeirah Living"),
    ("Flat", "JUMEIRAH FIRST"): (5, 1, "La Mer"),
    ("Flat", "AL WASL"): (6, 1, "City Walk"),
    ("Flat", "BURJ KHALIFA"): (7, 1, "Downtown"),
    ("Flat", "BUSINESS BAY"): (8, 1, "Business Bay"),
    ("Flat", "ZAABEEL SECOND"): (9, 1, "d3 / Za'abeel\u00a02"),
    ("Flat", "AL JADAF"): (10, 1, "Al Jaddaf"),
    ("Flat", "JABAL ALI FIRST"): (0, 2, "Jebel Ali 1"),
    ("Flat", "AL BARSHA SOUTH FIFTH"): (1, 2, "JVT"),
    ("Flat", "AL BARSHA SOUTH FOURTH"): (2, 2, "JVC"),
    ("Flat", "AL THANYAH THIRD"): (3, 2, "The Views"),
    ("Flat", "AL GOZE FOURTH"): (4, 2, "Al Quoz 4"),
    ("Flat", "HADAEQ SHEIKH MOHAMMED BIN RASHID"): (5, 2, "Dubai Hills"),
    ("Flat", "AL BARSHAA SOUTH SECOND"): (6, 2, "Science Park"),
    ("Flat", "AL MERKADH"): (7, 2, "Sobha Hartland"),
    ("Flat", "NAD AL SHIBA FIRST"): (8, 2, "Meydan"),
    ("Flat", "NADD HESSA"): (9, 2, "Silicon Oasis"),
    ("Flat", "AL WARSAN FIRST"): (10, 2, "International City"),
    ("Flat", "JABAL ALI INDUSTRIAL SECOND"): (0, 3, "Downtown Jebel Ali"),
    ("Flat", "ME'AISEM FIRST"): (1, 3, "Production City"),
    ("Flat", "AL HEBIAH FOURTH"): (2, 3, "Sports City"),
    ("Flat", "AL HEBIAH FIRST"): (3, 3, "Motor City"),
    ("Flat", "AL HEBIAH SECOND"): (4, 3, "Studio City"),
    ("Flat", "AL BARSHAA SOUTH THIRD"): (5, 3, "Arjan"),
    ("Flat", "WADI AL SAFA 3"): (6, 3, "Majan"),
    ("Flat", "WADI AL SAFA 2"): (7, 3, "Liwan / Falcon City"),
    ("Flat", "WADI AL SAFA 5"): (8, 3, "Residence Complex"),
    ("Flat", "WARSAN FOURTH"): (10, 3, "Intl City Phase 2"),
    ("Flat", "MADINAT AL MATAAR"): (0, 4, "Dubai South"),
    ("Flat", "AL HEBIAH THIRD"): (2, 4, "Damac Hills"),
    ("Flat", "AL HEBIAH FIFTH"): (3, 4, "Damac Lagoons"),
    ("Flat", "AL YELAYISS 2"): (4, 4, "Town Square"),
    # ---- villas
    ("Villa", "JABAL ALI FIRST"): (0, 2, "Jebel Ali 1"),
    ("Villa", "AL BARSHA SOUTH FOURTH"): (2, 2, "JVC"),
    ("Villa", "AL THANAYAH FOURTH"): (3, 2, "The Springs"),
    ("Villa", "HADAEQ SHEIKH MOHAMMED BIN RASHID"): (5, 2, "Dubai Hills"),
    ("Villa", "NAD AL SHIBA FIRST"): (8, 2, "Meydan"),
    ("Villa", "AL HEBIAH FOURTH"): (2, 3, "Sports City"),
    ("Villa", "WADI AL SAFA 6"): (4, 3, "Arabian Ranches"),
    ("Villa", "WADI AL SAFA 3"): (6, 3, "Wadi Al Safa\u00a03"),
    ("Villa", "WADI AL SAFA 5"): (8, 3, "Wadi Al Safa\u00a05"),
    ("Villa", "WADI AL SAFA 7"): (9, 3, "Wadi Al Safa\u00a07"),
    ("Villa", "MADINAT AL MATAAR"): (0, 4, "Dubai South"),
    ("Villa", "AL YELAYISS 2"): (4, 4, "Town Square"),
    ("Villa", "AL HEBIAH SIXTH"): (5, 4, "Mudon"),
    ("Villa", "AL YELAYISS 1"): (6, 4, "Damac Islands"),
    ("Villa", "AL YUFRAH 1"): (10, 4, "The Valley"),
}

# Points named on the scatter (the rest show their name on hover).
# value: where the label goes relative to the dot: "right", "left" or "below".
SCATTER_LABELS = {
    "Flat": {
        "ME'AISEM FIRST": "left", "AL WARSAN FIRST": "right", "WADI AL SAFA 5": "left",
        "JABAL ALI INDUSTRIAL SECOND": "below", "WADI AL SAFA 3": "right", "AL BARSHA SOUTH FIFTH": "right",
        "AL HEBIAH SECOND": "left", "HADAEQ SHEIKH MOHAMMED BIN RASHID": "below", "BUSINESS BAY": "right",
        "BURJ KHALIFA": "right", "MARSA DUBAI": "left", "PALM JUMEIRAH": "right",
    },
    "Villa": {
        "WADI AL SAFA 7": "left", "AL YELAYISS 2": "right", "WADI AL SAFA 5": "right",
        "AL YELAYISS 1": "left", "HADAEQ SHEIKH MOHAMMED BIN RASHID": "right", "AL YUFRAH 1": "right",
        "MADINAT AL MATAAR": "right", "AL THANAYAH FOURTH": "right",
    },
}


def tile_for(segment: str, area: str):
    return TILES.get((segment, area))
