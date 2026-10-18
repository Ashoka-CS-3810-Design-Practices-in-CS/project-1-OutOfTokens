import pytest

from metro.network.loader import load_graph
from metro.routing.planner import Planner

# 30 real trips, answers worked out by hand from each line's station order in edges.csv.
# Placeholder times: minutes = 2 x rides + 5 x changes.
# Row: start, destination, criterion, rides, changes, lines, change stations, minutes.

TRIPS = [
    # --- one line, no change ---------------------------------------------------------------
    ("CHANDNI_CHOWK", "RAJIV_CHOWK", "fastest", 3, 0, ("YELLOW",), (), 6),
    ("RITHALA", "SHAHEED_STHAL", "fastest", 28, 0, ("RED",), (), 56),                  # whole Red line
    ("SAMAYPUR_BADLI", "HUDA_CITY_CENTRE", "fastest", 36, 0, ("YELLOW",), (), 72),     # whole Yellow line
    ("NOIDA_CITY_CENTER", "YAMUNA_BANK", "fastest", 10, 0, ("BLUE",), (), 20),
    ("INDERLOK", "BRIGADIER_HOSHIAR_SINGH", "fastest", 20, 0, ("GREEN",), (), 40),     # whole Green line
    ("SECTOR_55_66", "DLF_PHASE_3", "fastest", 10, 0, ("RAPID",), (), 20),             # whole Rapid Metro
    ("DWARKA", "NAJAFGARH", "fastest", 2, 0, ("GRAY",), (), 4),
    ("NEW_DELHI", "DWARKA_SECTOR_21", "fastest", 5, 0, ("ORANGE",), (), 10),           # Airport Express
    ("JANAK_PURI_WEST", "BOTANICAL_GARDEN", "fastest", 24, 0, ("MAGENTA",), (), 48),   # beats 28 rides on Blue
    ("YAMUNA_BANK", "VAISHALI", "fastest", 7, 0, ("BLUE_BRANCH",), (), 14),
    ("ASHOK_PARK_MAIN", "KIRTI_NAGAR", "fastest", 2, 0, ("GREEN_BRANCH",), (), 4),
    ("NOIDA_SECTOR_52_NOIDA_SECTOR_51", "DEPOT_GREATER_NOIDA", "fastest", 20, 0, ("AQUA",), (), 40),
    ("HAUZ_KHAS", "BOTANICAL_GARDEN", "fastest", 13, 0, ("MAGENTA",), (), 26),
    ("RAJOURI_GARDEN", "MAYUR_VIHAR_PHASE_1", "fastest", 14, 0, ("PINK",), (), 28),    # Pink 14 beats Blue 17
    ("INDERLOK", "KASHMERE_GATE", "fastest", 5, 0, ("RED",), (), 10),
    ("WELCOME", "KASHMERE_GATE", "fastest", 3, 0, ("RED",), (), 6),
    ("LAJPAT_NAGAR", "KALKAJI_MANDIR", "fastest", 4, 0, ("VIOLET",), (), 8),
    ("AZADPUR", "NEW_DELHI", "fastest", 9, 0, ("YELLOW",), (), 18),

    # --- one change ---------------------------------------------------------------------------
    ("NEW_DELHI", "ITO", "fastest", 6, 1, ("YELLOW", "VIOLET"), ("CENTRAL_SECRETARIAT",), 17),
    # via Kashmere Gate (5 rides) beats via Mandi House (6 rides)
    ("RAJIV_CHOWK", "LAL_QUILA", "fastest", 5, 1, ("YELLOW", "VIOLET"), ("KASHMERE_GATE",), 15),
    ("HUDA_CITY_CENTRE", "DLF_PHASE_3", "fastest", 8, 1, ("YELLOW", "RAPID"), ("SIKANDARPUR",), 21),
    ("DWARKA_SECTOR_21", "NAJAFGARH", "fastest", 10, 1, ("BLUE", "GRAY"), ("DWARKA",), 25),
    # Blue branch to Yamuna Bank beats Pink to Mayur Vihar (13 rides)
    ("ANAND_VIHAR", "RAJIV_CHOWK", "fastest", 10, 1, ("BLUE_BRANCH", "BLUE"), ("YAMUNA_BANK",), 25),
    # beats 16 rides and 2 changes via Anand Vihar (42 min)
    ("VAISHALI", "NOIDA_CITY_CENTER", "fastest", 17, 1, ("BLUE_BRANCH", "BLUE"), ("YAMUNA_BANK",), 39),
    ("SAMAYPUR_BADLI", "NOIDA_SECTOR_62", "fastest", 35, 1, ("YELLOW", "BLUE"), ("RAJIV_CHOWK",), 75),

    # --- the three kinds of route disagree -------------------------------------------------------
    # Violet alone is fastest; Yellow then Violet passes one station fewer
    ("KASHMERE_GATE", "RAJA_NAHAR_SINGH", "fastest", 33, 0, ("VIOLET",), (), 66),
    ("KASHMERE_GATE", "RAJA_NAHAR_SINGH", "fewest_stations", 32, 1, ("YELLOW", "VIOLET"), ("CENTRAL_SECRETARIAT",), 69),

    # --- two or more changes ----------------------------------------------------------------------
    ("NAJAFGARH", "TERMINAL_1_IGI_AIRPORT", "fastest", 12, 2, ("GRAY", "BLUE", "MAGENTA"),
     ("DWARKA", "JANAK_PURI_WEST"), 34),

    # adding Blue saves 2 rides but costs a third change; Blue to Mandi House is the only 1-change route
    ("DWARKA_SECTOR_21", "ITO", "fastest", 11, 2, ("ORANGE", "YELLOW", "VIOLET"),
     ("NEW_DELHI", "CENTRAL_SECRETARIAT"), 32),
    ("DWARKA_SECTOR_21", "ITO", "fewest_stations", 9, 3, ("ORANGE", "YELLOW", "BLUE", "VIOLET"),
     ("NEW_DELHI", "RAJIV_CHOWK", "MANDI_HOUSE"), 33),
    ("DWARKA_SECTOR_21", "ITO", "fewest_interchanges", 31, 1, ("BLUE", "VIOLET"), ("MANDI_HOUSE",), 67),

    # Pink is a long U, so cutting across Yellow and Red beats riding it all the way
    ("MAJLIS_PARK", "SHIV_VIHAR", "fastest", 15, 3, ("PINK", "YELLOW", "RED"),
     ("AZADPUR", "KASHMERE_GATE", "WELCOME"), 45),
    ("MAJLIS_PARK", "SHIV_VIHAR", "fewest_stations", 15, 3, ("PINK", "YELLOW", "RED"),
     ("AZADPUR", "KASHMERE_GATE", "WELCOME"), 45),
    ("MAJLIS_PARK", "SHIV_VIHAR", "fewest_interchanges", 37, 0, ("PINK",), (), 74),

    # via Dilli Haat INA (74 min) beats one change at Kashmere Gate (81 min)
    ("RITHALA", "HUDA_CITY_CENTRE", "fastest", 32, 2, ("RED", "PINK", "YELLOW"),
     ("NETAJI_SUBASH_PLACE", "DILLI_HAAT_INA"), 74),
    ("RITHALA", "HUDA_CITY_CENTRE", "fewest_interchanges", 38, 1, ("RED", "YELLOW"), ("KASHMERE_GATE",), 81),
]


@pytest.fixture(scope="module")
def planner() -> Planner:
    return Planner(load_graph())


@pytest.mark.parametrize(
    "source, destination, criterion, rides, changes, lines, interchanges, minutes",
    TRIPS,
    ids=[f"{t[0]}->{t[1]} {t[2]}" for t in TRIPS],
)
def test_trip(planner: Planner, source, destination, criterion, rides, changes, lines, interchanges, minutes):
    routes = planner.plan(source, destination)
    route = next(r for r in routes if criterion in r.criteria)
    assert len(route.stations) - 1 == rides
    assert len(route.interchanges) == changes
    assert route.lines == lines
    assert route.interchanges == interchanges
    assert route.total_time_min == minutes
    assert route.stations[0] == source
    assert route.stations[-1] == destination


def test_thirty_different_trips():
    assert len({(t[0], t[1]) for t in TRIPS}) == 30
