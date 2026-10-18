# Testing

How the Delhi Metro Route Planner is tested, what each set of checks proves, and what testing has found.

Last updated: 18 Oct 2026.

## Summary

| Layer | Checks | Result | Command |
|---|---|---|---|
| Backend (Python) | 147 | All pass, 100% of backend lines run | `cd backend && uv run pytest` |
| Website logic (TypeScript) | 41 | All pass | `cd frontend && npm test` |
| Whole app in Chrome | 11 | All pass | `cd frontend && npm run test:e2e` |

## How to run

```bash
# backend checks, from backend/
uv sync
uv run pytest                                      # all 147
uv run pytest --cov=metro --cov-report=term-missing   # with coverage: which lines were run

# website checks, from frontend/
npm install
npm test                                           # logic checks (Vitest)
npx playwright test                                # whole app in Chrome; starts both servers if they aren't running
```

The Chrome tests use the Chrome already installed on the computer, so nothing extra is downloaded.

## What each set of checks proves

### Backend

| File | Checks | What it proves |
|---|---|---|
| `test_graph.py` | 9 | The network structure stores stations, lines, platforms and track pieces, and every track piece works in both directions. |
| `test_loader.py` | 11 | The four CSV files are read correctly, and a missing file, a missing column, a bad number or a duplicate is reported with the file and line. |
| `test_bad_data.py` | 15 | Every check that refuses broken data actually fires: duplicates, references to things that don't exist, a ride joining two lines, a line change joining two stations, zero or negative times, an empty name. |
| `test_validator.py` | 8 | The start-up data check (`network/validator.py`) passes the real data and reports, all at once: a line change with a distance, an interchange missing one of its line changes (including a real one at Kashmere Gate), and platforms cut off from the rest of the network. |
| `test_dijkstra.py` | 13 | The fastest and fewest-changes searches, on a small hand-built map and on the real one. |
| `test_zero_one_bfs.py` | 10 | The fewest-stations search, including the case that line changes must not count as stations. |
| `test_route_builder.py` | 11 | A search result becomes the right stations, lines, change stations and totals, including when the track pieces are listed against the direction of travel. |
| `test_planner.py` | 8 | All three searches run, identical routes are merged with both labels, and "no route" gives an empty list. |
| `test_route_service.py` | 13 | Unknown and identical stations are refused with the right code, and both replies convert to JSON. |
| `test_api.py` | 9 | The two web addresses answer correctly, bad requests get 400 or 422, and the website's address is allowed by CORS. |
| `test_hand_verified.py` | 37 | 30 real trips whose answers were worked out by hand (see below). |
| `test_against_brute_force.py` | 1 (400 random maps) | All three searches always find a route as good as the best one found by trying every route (see below). |
| `test_performance.py` | 2 | Loading the network and answering requests stay fast (see below). |

### Coverage

Coverage measures which lines of backend code the checks actually run.

- **Before this round:** 96%. The untested 4% was almost all the safety checks that refuse broken data. Most had never been tried.
- **After adding `test_bad_data.py`:** 100% of the 434 lines in `backend/metro/`.
- **After adding the start-up data check and `test_validator.py`:** still 100%, now of 467 lines.

100% means every line runs at least once during the checks. It does not prove every line is right, which is what the hand-checked trips and the random maps are for.

### 30 trips checked by hand

`test_hand_verified.py` checks 30 real station pairs against answers worked out by hand, not by running the code.

**Method.** Each line's stations were listed in order from `data/edges.csv`. Each trip was then reasoned out from those lists, including the obvious detours that might beat it. With today's placeholder times (every ride 2 minutes, every line change 5), time = 2 × rides + 5 × changes.

| Kind of trip | Trips | Examples |
|---|---|---|
| One line, no change | 18 | Every line end to end at least once: Rithala → Shaheed Sthal (28 rides), Samaypur Badli → Huda City Centre (36 rides) |
| One change | 7 | New Delhi → ITO via Central Secretariat; Rajiv Chowk → Lal Quila via Kashmere Gate (beats Mandi House by one stop) |
| The three kinds of route disagree, fastest has no change | 1 | Kashmere Gate → Raja Nahar Singh (Violet all the way is fastest; Yellow then Violet passes one station fewer) |
| Two or more changes | 4 | Najafgarh → Terminal 1 IGI Airport; Dwarka Sector 21 → ITO (three different routes); Majlis Park → Shiv Vihar (3 changes beat 37 rides on Pink); Rithala → Huda City Centre |

Four trips are checked for more than one kind of route: Kashmere Gate → Raja Nahar Singh, Dwarka Sector 21 → ITO, Majlis Park → Shiv Vihar and Rithala → Huda City Centre. So the 30 trips give 36 checks, plus one check that there really are 30 different trips.

**Result:** every hand-worked answer matched the route finder on the first run.

### Random maps against a brute-force referee

`test_against_brute_force.py` uses the `hypothesis` library to build 400 random small metro maps per run. Each follows the real map's rules: lines are chains of stations, one platform per line, and line changes between every pair of lines at a station. On each map it picks a start and a destination, and checks:

- **Fastest:** the least total time equals the best time over every possible route.
- **Fewest changes:** the fewest changes, then the least time among those, equals the best over every possible route.
- **Fewest stations:** the fewest rides equals the best over every possible route.
- **No route:** if no route exists, all three searches say so.
- **Totals:** every answer is a joined-up route from start to destination, and the route builder's totals agree with it.

The brute-force referee tries every route that never visits the same platform twice. It's slow but obviously right. Revisiting a platform can never make a route better, since no time is negative.

### Speed

Measured on 10 Oct 2026 across all 65,792 station pairs (Apple M5): about 0.04 ms per search, so about 0.12 ms for a request that runs all three. Loading the network takes about 1.5 ms.

`test_performance.py` checks that loading stays under 200 ms and that 500 requests average under 5 ms each. The limits are over 40 times looser than measured, so the check only fails if something has gone badly wrong, not because a laptop is busy.

### Website logic

| File | Checks | What it proves |
|---|---|---|
| `src/stationIndex.test.ts` | 9 | Station search: nothing until something is typed; case, spaces and accents ignored; names that start with the text come first; at most 8 suggestions; only the first 100 characters are read. |
| `src/mapGeometry.test.ts` | 7 | North is up, east is right, the whole network fits in the drawing area, and the starting view keeps the 4:3 shape with a margin around every station. |
| `src/apiClient.test.ts` | 8 | Requests go to the right address with the right body, and each kind of failure is reported correctly: the backend's own reason, a bad request, a server error, an unreachable server, a 5-second timeout, and a cancelled request. |
| `src/routeStore.test.ts` | 17 | The page's memory: loading the network once, refusing the same station twice, only asking for a route when both stations are chosen, turning each failure into the right message, ignoring a late answer after Reset, cancelling the request in flight, and switching tabs without asking the backend again. |

In these checks the backend is replaced with a stand-in, so every kind of answer and failure can be tried without a server.

### Whole app in Chrome

`frontend/e2e/app.e2e.ts` drives the real website and the real backend in Chrome, clicking and typing like a person.

| Test | Result |
|---|---|
| The map shows all 257 stations and 272 track pieces, and the boxes can be used | Pass |
| Clicking a station box opens the search before anything is typed (the B1 fix) | Pass |
| Find route stays disabled until both stations are chosen | Pass |
| New Delhi → ITO shows 17 min / 6.8 km, 18 min / 3.6 km and 17 min on the three tabs | Pass |
| A name with no match shows "No matching station found." | Pass |
| Typing a name without picking it shows "Please choose a station from the list" | Pass (failed until the B2 fix) |
| The same station twice shows "Source and destination must be different." | Pass (failed until the B2 fix) |
| Reset clears the stations and the route | Pass |
| Clicking a station on the map shows its details, and Escape closes them | Pass |
| If the map data can't be loaded, the page says so and Reload works | Pass |
| If a route request fails, the page says so and Retry works | Pass |

## Bugs found by testing

| # | Found | Bug | Status |
|---|---|---|---|
| B1 | 15 Oct, by hand | The From and To boxes did nothing when clicked. The list was empty until something was typed, and the component library refuses to open an empty list, so the typing box inside it could never be reached. | Fixed: `allowsEmptyCollection` on the box (commit 0568553). Now covered by a Chrome test. |
| B2 | 18 Oct, by the Chrome tests | The station box warnings are invisible. "Please choose a station from the list" and "Source and destination must be different." are on the page but have zero height and are fully transparent. The cause: the component library has its own style called `field-error` (hidden unless switched on), and our warning uses the same name, so the library's style hides it. | Fixed on 18 Oct: our style renamed to `station-field-error` in `StationSearch.tsx` and `index.css`. Both Chrome tests now pass. |

## Still checked by hand

These are hard to automate well, so they're checked by eye before a demo.

- [ ] The map looks right: line colours, station dots, interchange rings, labels readable.
- [ ] Dragging, scrolling and the + / − buttons move and zoom the map; Reset view returns it.
- [ ] Hovering a station shows its name.
- [ ] On a narrow window (under 700 px wide) the panel and map stack instead of sitting side by side.
- [ ] Keyboard only: Tab reaches the boxes, the buttons and the stations on the map; Enter opens a station's details.
- [ ] The route's stations are listed under the map panel, grouped by line, with the right colours.

## Known limits of this testing

- **Placeholder times.** All expected times assume every ride takes 2 minutes and every line change 5. When real times go into `edges.csv`, the minutes in `test_hand_verified.py` and the other real-data checks must be updated; the stations and lines should stay the same unless the real times change which route is fastest.
- **The hand-checked answers come from our own data file.** They prove the route finder gives the right answer for the network as we recorded it, not that `edges.csv` matches the real Delhi Metro.
- **The Chrome tests check the page's content, not how it looks.** That's what the hand-checked list above is for.
- **No tests for very large maps.** The real network is small (285 platforms), and the random maps are smaller still so the brute-force referee stays fast.
