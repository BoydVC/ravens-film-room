# Ravens Film Room

Interactive Ravens war room for Boyd: ESPN drive-chart film breakdown, Week 5 scouting, plus a research-backed **Injury Board**, **Depth Chart**, and **Film Notes** (Jim Interest Journal facts only — cited on-page, gaps labeled).

**Current game (latest completed):** Week 4, Sun Oct 4, 2026 — TEN @ BAL, **BAL 24, TEN 18**.
**Next:** Week 5, Sun Oct 11, 8:20 PM ET — BAL @ ATL (Mercedes-Benz Stadium).

## What's new (Sat Oct 10 afternoon remaster)
- **Multi-screen War Room** on one hub (`index.html`): War Room · Film · Next Game · Injury Board · Depth Chart · Film Notes.
- **Darker film-room aesthetic** — deeper blacks/purples, grain + scanlines, pulse/glow accents, sticky screen nav, purple/gold CTAs.
- **Oct 2026 research layer** from Jim journals already on disk (`ij_2026-10-0*_research.md`, plus late-Sep OL notes): Cam Jurgens trade card, Lamar ankle timeline (Oct 4–7), Wednesday DNP/Limited board, OL plan (Ioane→RG / Simpson LG), Titans film-note reel. Every bullet cites its `ij_*.md` file + source URLs.
- **Dual-source Injury Board** — journal Wed practice report beside ESPN pre-game list (scout.json); mismatches called out, never silently merged.
- **Depth chart** is a research projection only; RT and several defense spots marked **GAP** when journals don't name them.
- Port moved to **4275**. Fresh `dist/ravens-film-room-snapshot.html` (film+scout+research inlined) and `screenshots/00-best-home.png`.
- `build_research.py` → `data/research.json`. `./screenshot.sh` ships the hero + per-screen shots.

## Open it
- Live: http://127.0.0.1:4275 (War Room hub). Start with `./run.sh start`.
- Deep screens: `?screen=war|film|next|injuries|depth|notes` (add `&still=1` to freeze animations).
- Standalone scouting page still at `/scout.html`.
- Offline: `dist/ravens-film-room-snapshot.html` (self-contained hub) and `dist/ravens-scouting-snapshot.html`.
- Best screenshot: `screenshots/00-best-home.png` (War Room). Also `01-injury-board.png`, `02-depth-chart.png`, `03-film-notes.png`, `04-film-room.png`, `05-next-game.png`.

## Scouting Report (Week 5: Ravens @ Falcons, Sun Oct 11, 8:20 PM ET, Mercedes-Benz Stadium)
Built automatically for the Ravens' next scheduled game (`build_scout.py` → `data/scout.json`).

| Through 4 games | BAL | ATL |
|---|---|---|
| Points / game (for–against) | 29.0 – 24.0 | 24.0 – 23.0 |
| Net yards / game (off – def) | 395.0 – 315.3 | 360.5 – 313.0 |
| Rushing / game (off – allowed) | 153.5 – 100.0 | 181.0 – 48.3 |
| Net passing / game (off – allowed) | 241.5 – 215.3 | 179.5 – 264.8 |
| Turnover margin | +3 (5 take, 2 give) | −5 (3 take, 8 give) |
| 3rd down (off – allowed) | 32.4% (12/37) – 37.5% (18/48) | 37.2% (16/43) – 36.8% (21/57) |
| Red-zone TD (off – allowed) | 73.3% (11/15) – 64.3% (9/14) | 80.0% (8/10) – 56.3% (9/16) |
| Penalties | 39 for 329 (82.3 yds/g) | 29 for 288 (72.0 yds/g) |

Line (ESPN pickcenter, provider DraftKings, fetched Oct 7, 5:33 PM ET): **ATL −3.5, O/U 43.5**, BAL ML +150, ATL ML −180. ESPN Matchup Predictor: ATL 54.5%, BAL 45.1%, shown as ESPN published them. (The table above reflects the Oct 7 fetch; the page always shows the latest build.)

What's on the page:
- **Matchup header.** The betting line and ESPN's predictor appear only when ESPN's public pre-game summary has them, always labelled with source and fetch time. Sportsbook links are deliberately left out.
- **Keys to the game.** Fixed rules compare each offense with the opposing defense: rushing, net passing, 3rd-down rate and red-zone TD rate. They also compare turnover margin and penalty yards. Every comparison is ranked by its relative gap, and the 6 biggest are shown. Each bullet cites both numbers and states the gap. No predictions, no adjectives beyond the arithmetic.
- **Season stats side by side** (offense, defense allowed, ball & discipline). Each is summed from ESPN's per-game box scores and shown with its raw totals (e.g. 12/37).
- **Game by game** for both teams (score, yards, yards allowed, giveaways). Ravens results link to that game in the Film Room.
- **Atlanta's last game drive chart** (Week 4, ATL 45 @ NO 24), drawn by the same renderer as the Film Room (`web/common.js`), with ATL attacking right. Click any drive to see its play-by-play.
- **Injury report.** ESPN's pre-game injury list for both teams: name, position, status and injury, verbatim. If ESPN publishes none, the section says so.
- **Stat audit.** 34 checks comparing our box-score sums with ESPN's own season team statistics (`sports.core.api.espn.com`) and the per-game averages in ESPN's pre-game summary. All 34 match. ESPN's pre-game "pass yards allowed" is gross (opponents' net passing plus sack yards), so the audit adds the sack yards back before comparing.

## Features
- **Season strip:** every 2026 game from the schedule. Completed games are clickable and switch the whole page (`?game=<espn event id>`).
- **Scoreboard** with quarter linescores and records.
- **Animated drive chart:** every drive drawn on a field from start to end spot, colored by result (TD / FG / punt / turnover / missed FG / end of half or game). The Ravens always attack to the right. REPLAY button. Click a drive for a mini play tracker plus play-by-play with ESPN's win probability after each play (`?drive=<index>`).
- **Scoring timeline:** step chart plus a list of ESPN scoring plays.
- **Win-probability graph** (ESPN model, one point per play, hover to scrub, key-play dots). If ESPN publishes no WP for a game, the chart is left out and the page says so.
- **Key plays:** scores, turnovers, 4th-down stops, the top WP swings, big gains (25+ yd rush or pass), long FGs (50+). All play text is ESPN's own text, verbatim.
- **Box-score leaders** plus team-stat comparison bars.
- **Film-room audit:** drive-chart totals reconciled against ESPN's box score on the page.
- `?still=1` skips the animations (used for screenshots).

## Data
| What | URL |
|---|---|
| Schedule | https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/bal/schedule |
| Game summary (drives, plays, WP, box score) | https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={id} |
| Opponent schedule | https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{abbr}/schedule |
| Pre-game summary (injuries, pickcenter line, predictor, per-game averages) | same summary URL, for the upcoming event (saved as `pregame_{id}.json`) |
| Season team statistics (cross-check) | https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/2026/types/2/teams/{teamId}/statistics |

Fetched Oct 7, 2026, 5:33–5:34 PM ET. Each URL and fetch time is listed in `data/raw/manifest.json` and shown in the page footer. Raw responses are kept in `data/raw/`. Nothing is invented: a field ESPN doesn't provide is left out.

**Field orientation:** ESPN's `yardLine` is the distance from the **home** team's goal line (checked against the `downDistanceText` spot on every play of all 4 games, 0 mismatches). The chart uses x = yardLine when BAL is home, otherwise 100 − yardLine, so the Ravens always attack right.

**Audit / cross-checks:** for every game and both teams, these match the box score exactly:
- drive points vs. final score
- drive count vs. `totalDrives`
- TD drives vs. passing TD + rushing TD
- FG drives vs. kicking made/attempted
- punt drives vs. punts
- INT/fumble drives vs. turnovers
- summed drive clocks vs. time of possession

Drive yards and play counts are shown as *info* only. ESPN's drive yards include penalty yards, and its drive play counts include plays wiped out by penalties, so they don't equal box-score total yards or offensive plays.

## Commands
```
./run.sh start|stop|restart|status|shot   # server on 127.0.0.1:4275 (nohup; pid in data/server.pid, log in data/server.log)
./run.sh fetch                       # re-pull ESPN, then rebuild
./run.sh build                       # build_research.py -> build_data.py -> build_scout.py -> export_snapshot.py -> screenshot.sh
./run.sh test                        # python3 tests/smoke_test.py
```
After a new game finishes: `./run.sh fetch` (which also rebuilds). The Film Room picks the latest completed game, and the Scouting Report moves to the next scheduled game, automatically.

### What the smoke test checks
- **Film Room:** for every Ravens game, the drive chart reconciles with the box score (points, drives, TDs, FGs, punts, turnovers, time of possession). Play text is verbatim from ESPN, scores match ESPN's header, and WP values lie between 0 and 1.
- **Scouting:** an independent re-sum of every box score (it doesn't import the builder) must equal `scout.json`, ESPN's season team statistics and ESPN's pre-game per-game averages. That covers points, yards, rushing, net passing, 3rd downs, red zone, giveaways, takeaways, margin and penalties.
- **Displayed numbers:** every per-game average and percentage shown is re-derived.
- **Results:** game-by-game rows match the schedule, ESPN game headers, and ESPN's lastFiveGames W/L.
- **Keys:** every number in every key traces to a computed stat, and every gap is the arithmetic difference.
- **Line and injuries:** the line matches ESPN pickcenter and carries a source and fetch time. The injury list equals ESPN's.
- **Atlanta drives:** Atlanta's drive charts (all 4 games) reconcile with their box scores.
- **Pages and files:** the live server routes respond, both snapshots are self-contained and render in headless Chrome with no audit mismatches, and all screenshots exist.

## Files
`build_research.py` → `data/research.json`, `fetch.py`, `build_data.py` → `data/film.json`, `build_scout.py` → `data/scout.json`, `web/` (index.html hub + hub.js / app.js / scout.js / common.js, scout.html, style.css, fonts), `server.py` (`/api/film`, `/api/scout`, `/api/research` on **4275**), `export_snapshot.py` → `dist/`, `screenshot.sh` → `screenshots/00-best-home.png` (+ per-screen), `tests/smoke_test.py`.

## Privacy
Public ESPN data only. No accounts, no keys, nothing sent anywhere. The server binds to 127.0.0.1 only. Betting lines are shown for information only. Not affiliated with the NFL, ESPN, DraftKings, the Baltimore Ravens or the Atlanta Falcons.


---
## Repo notes
- **Built:** Oct 4, 2026, by TokenMax (Boyd's Grok Bot) on the Grok Bot box.
- **Run:** `./run.sh` (then open the localhost URL it prints).
- Imported from `/workspace/tokenmax/ravens-film-room` on Oct 23, 2026. node_modules, virtualenvs, logs and files over 20 MB were left out.
- Personal details (emails, phone numbers, home street address) were replaced with `[redacted-…]` placeholders.
