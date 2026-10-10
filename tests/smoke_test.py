#!/usr/bin/env python3
"""Ravens Film Room smoke test (stdlib only). Run: python3 tests/smoke_test.py
1) Cross-checks every game's DRIVE totals against ESPN's BOX SCORE (points, drives, TD drives, FG attempts,
   punts, turnovers, time of possession), for both teams.
2) Checks the compiled data still matches the raw ESPN JSON (no invented plays, stats or scores).
3) Checks the live server (port 4275), the offline snapshot, and the screenshots."""
import json, os, re, subprocess, sys, urllib.request
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(HERE, *a)
fails, passes = [], 0


def check(name, cond, detail=""):
    global passes
    if cond: passes += 1; print(f"  ok   {name}")
    else: fails.append(name); print(f"  FAIL {name} {detail}")


def mmss(s):
    m, x = s.split(":"); return int(m) * 60 + int(x)


D = json.load(open(P("data", "film.json"), encoding="utf-8"))
check("latest game is the most recent completed one in the schedule",
      D["latest"] == max((g for g in D["season"]["games"] if g["completed"]), key=lambda g: g["date"])["id"])

def check_game(gid, G):
    raw = json.load(open(P("data", "raw", f"summary_{gid}.json"), encoding="utf-8"))
    tag = f"[{G['away']}@{G['home']}]"
    print(f"game {gid} {tag}")
    for ab in (G["home"], G["away"]):
        drs = [d for d in G["drives"] if d["team"] == ab]
        S, Pl = G["teamStats"][ab], G["players"][ab]
        tot = lambda cat, i: (Pl.get(cat, {}).get("totals") or [])[i] if len(Pl.get(cat, {}).get("totals") or []) > i else "0"
        pts = sum(d["points"] for d in drs) + sum(d["defPoints"] for d in G["drives"] if d["team"] != ab)
        check(f"{tag} {ab} drive points {pts} == final score {G['teams'][ab]['score']}", pts == G["teams"][ab]["score"])
        check(f"{tag} {ab} drive count == box totalDrives", str(len(drs)) == str(S.get("totalDrives")), f"{len(drs)} vs {S.get('totalDrives')}")
        tdd = sum(1 for d in drs if d["short"] == "TD")
        check(f"{tag} {ab} TD drives == passing TD + rushing TD", tdd == int(tot("passing", 3)) + int(tot("rushing", 3)), f"{tdd}")
        fga = sum(1 for d in drs if "FG" in (d["short"] or ""))
        check(f"{tag} {ab} FG-ending drives == kicking FGA", str(fga) == str(tot("kicking", 0)).split("/")[-1], f"{fga} vs {tot('kicking', 0)}")
        fgm = sum(1 for d in drs if d["short"] == "FG")
        check(f"{tag} {ab} FG-good drives == kicking FGM", str(fgm) == str(tot("kicking", 0)).split("/")[0])
        punts = sum(1 for d in drs if d["short"] == "PUNT")
        check(f"{tag} {ab} punt drives == punting NO", str(punts) == str(tot("punting", 0)), f"{punts} vs {tot('punting', 0)}")
        to = sum(1 for d in drs if re.match(r"^(INT|FUMBLE)", d["short"] or ""))
        check(f"{tag} {ab} INT/FUMBLE drives == box turnovers", str(to) == str(S.get("turnovers")), f"{to} vs {S.get('turnovers')}")
        top = sum(mmss(d["time"]) for d in drs if d["time"])
        check(f"{tag} {ab} sum of drive clocks == time of possession", top == mmss(S["possessionTime"]), f"{top} vs {S['possessionTime']}")
        sc = [s for s in G["scoring"] if s["team"] == ab]
        check(f"{tag} {ab} scoring plays sum to final via last score", (sc[-1]["score"][ab] if sc else 0) == G["teams"][ab]["score"] or not sc)
    # linescores add up
    for ab, T in G["teams"].items():
        check(f"{tag} {ab} quarter linescores sum to final", sum(T["linescores"]) == T["score"])
    # raw fidelity: every compiled play text exists verbatim in the raw summary; scores match header
    raw_txt = {p["id"]: p.get("text", "") for dr in raw["drives"]["previous"] for p in dr["plays"]}
    allp = [p for d in G["drives"] for p in d["playList"]]
    check(f"{tag} every play text is verbatim from ESPN", all(raw_txt.get(p["id"]) == p["text"] for p in allp))
    check(f"{tag} key plays are real plays", all(k["id"] in raw_txt for k in G["keyPlays"]))
    hdr = {c["team"]["abbreviation"]: int(c["score"]) for c in raw["header"]["competitions"][0]["competitors"]}
    check(f"{tag} final score matches ESPN header", all(G["teams"][k]["score"] == v for k, v in hdr.items()))
    wpraw = {w["playId"] for w in raw.get("winprobability", [])}
    check(f"{tag} WP points only where ESPN provides them", all(w["id"] in wpraw for w in G["wp"]) and all(0 <= w["wp"] <= 1 for w in G["wp"]))
    check(f"{tag} drive x positions on the field (0-100)", all(d["x0"] is None or 0 <= d["x0"] <= 100 for d in G["drives"]))
    check(f"{tag} source URL + fetchedAt recorded", G["source"]["url"].startswith("https://site.api.espn.com/") and bool(G["source"]["fetchedAt"]))


for gid, G in D["games"].items():
    check_game(gid, G)

# ======================= Scouting Report =======================
print("scouting report")
SC = json.load(open(P("data", "scout.json"), encoding="utf-8"))
RAWJ = lambda n: json.load(open(P("data", "raw", n), encoding="utf-8"))
man = RAWJ("manifest.json")
bsched = RAWJ("schedule.json")
nxt = next(e for e in bsched["events"] if not e["competitions"][0]["status"]["type"].get("completed"))
check("scout game is the Ravens' next scheduled game", SC["game"]["id"] == nxt["id"], f"{SC['game']['id']} vs {nxt['id']}")
opp_raw = [c["team"]["abbreviation"] for c in nxt["competitions"][0]["competitors"] if c["team"]["abbreviation"] != "BAL"][0]
check(f"scout opponent matches schedule ({opp_raw})", SC["opp"] == opp_raw)
F, O = "BAL", SC["opp"]
pre = RAWJ(f"pregame_{SC['game']['id']}.json")
check("kickoff time matches ESPN header", SC["game"]["date"] == pre["header"]["competitions"][0]["date"])


def pr(v):
    a, b = str(v).split("-"); return int(a), int(b)


def indep_season(ab, sched_file):
    """Independent re-computation from raw box scores (does not import build_scout)."""
    t = dict(g=0, pf=0, pa=0, yds=0, ydsA=0, rush=0, rushA=0, pas=0, pasA=0, sackA=0, give=0, take=0, c3=0, a3=0, c3A=0, a3A=0, rz=0, rza=0, rzA=0, rzaA=0, pen=0, peny=0)
    games = []
    for e in RAWJ(sched_file)["events"]:
        c = e["competitions"][0]
        if not c["status"]["type"].get("completed"):
            continue
        sm = RAWJ(f"summary_{e['id']}.json")
        st = {x["team"]["abbreviation"]: {s["name"]: s["displayValue"] for s in x["statistics"]} for x in sm["boxscore"]["teams"]}
        op = [k for k in st if k != ab][0]
        hdr = {x["team"]["abbreviation"]: int(x["score"]) for x in sm["header"]["competitions"][0]["competitors"]}
        me, oo = st[ab], st[op]
        t["g"] += 1; t["pf"] += hdr[ab]; t["pa"] += hdr[op]
        t["yds"] += int(me["totalYards"]); t["ydsA"] += int(oo["totalYards"]); t["rush"] += int(me["rushingYards"]); t["rushA"] += int(oo["rushingYards"])
        t["pas"] += int(me["netPassingYards"]); t["pasA"] += int(oo["netPassingYards"]); t["sackA"] += pr(oo["sacksYardsLost"])[1]
        t["give"] += int(me["turnovers"]); t["take"] += int(oo["turnovers"])
        x = pr(me["thirdDownEff"]); t["c3"] += x[0]; t["a3"] += x[1]; x = pr(oo["thirdDownEff"]); t["c3A"] += x[0]; t["a3A"] += x[1]
        x = pr(me["redZoneAttempts"]); t["rz"] += x[0]; t["rza"] += x[1]; x = pr(oo["redZoneAttempts"]); t["rzA"] += x[0]; t["rzaA"] += x[1]
        x = pr(me["totalPenaltiesYards"]); t["pen"] += x[0]; t["peny"] += x[1]
        games.append((e["id"], hdr[ab], hdr[op]))
    return t, games


def core(ab):
    out = {}
    for cat in RAWJ(f"teamstats_{ab.lower()}.json")["splits"]["categories"]:
        for s_ in cat["stats"]:
            out.setdefault(s_["name"], s_.get("value"))
    return out


near = lambda a, b, tol=0.051: a is not None and b is not None and abs(float(a) - float(b)) < tol
pre_avg = {x["team"]["abbreviation"]: {s_["name"]: s_["displayValue"] for s_ in x.get("statistics", [])} for x in pre["boxscore"]["teams"]}
for ab, sf in ((F, "schedule.json"), (O, f"schedule_{O.lower()}.json")):
    t, games = indep_season(ab, sf)
    ss, cr, pa = SC["season"][ab], core(ab), pre_avg.get(ab, {})
    g = t["g"]
    # compiled scout.json == independent sums
    for k_s, k_t in [("games", "g"), ("pf", "pf"), ("pa", "pa"), ("yds", "yds"), ("ydsA", "ydsA"), ("rush", "rush"), ("rushA", "rushA"), ("pass", "pas"), ("passA", "pasA"),
                     ("give", "give"), ("take", "take"), ("c3", "c3"), ("a3", "a3"), ("c3A", "c3A"), ("a3A", "a3A"), ("rzTD", "rz"), ("rzAtt", "rza"), ("rzTDA", "rzA"), ("rzAttA", "rzaA"), ("pen", "pen"), ("penYds", "peny")]:
        check(f"[{ab}] scout.{k_s} == independent box-score sum ({t[k_t]})", ss[k_s] == t[k_t], f"{ss[k_s]}")
    # independent sums == ESPN's own season team statistics
    for lab, ours, theirs in [("points", t["pf"], cr.get("totalPoints")), ("net total yards", t["yds"], cr.get("netTotalYards")), ("rushing yards", t["rush"], cr.get("rushingYards")),
                              ("net passing yards", t["pas"], cr.get("netPassingYards")), ("3rd-down conversions", t["c3"], cr.get("thirdDownConvs")), ("3rd-down attempts", t["a3"], cr.get("thirdDownAttempts")),
                              ("red-zone TD %", round(100 * t["rz"] / t["rza"], 2) if t["rza"] else 0, cr.get("redzoneTouchdownPct")), ("giveaways", t["give"], cr.get("totalGiveaways")),
                              ("takeaways", t["take"], cr.get("totalTakeaways")), ("turnover margin", t["take"] - t["give"], cr.get("turnOverDifferential")),
                              ("penalties", t["pen"], cr.get("totalPenalties")), ("penalty yards", t["peny"], cr.get("totalPenaltyYards"))]:
        check(f"[{ab}] {lab}: box sum {ours} == ESPN season stats {theirs}", near(ours, theirs))
    # ...and == the per-game averages in ESPN's pre-game summary (rounded half-up like ESPN)
    from decimal import Decimal, ROUND_HALF_UP
    q = lambda n, d: float((Decimal(n) / Decimal(d)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    for lab, ours, key in [("PPG", q(t["pf"], g), "totalPointsPerGame"), ("PA/G", q(t["pa"], g), "totalPointsPerGameAllowed"),
                           ("rush yds allowed/G", q(t["rushA"], g), "rushingYardsPerGameAllowed"), ("gross pass yds allowed/G", q(t["pasA"] + t["sackA"], g), "passingYardsPerGameAllowed")]:
        check(f"[{ab}] {lab}: {ours} == ESPN pre-game {pa.get(key)}", near(ours, pa.get(key)))
    # derived per-game numbers shown on the page
    for k, v in [("ppg", q(t["pf"], g)), ("papg", q(t["pa"], g)), ("rpg", q(t["rush"], g)), ("rpgA", q(t["rushA"], g)), ("ppgPass", q(t["pas"], g)), ("ppgPassA", q(t["pasA"], g)),
                 ("ypg", q(t["yds"], g)), ("ypgA", q(t["ydsA"], g)), ("p3", q(100 * t["c3"], t["a3"])), ("p3A", q(100 * t["c3A"], t["a3A"])), ("rz", q(100 * t["rz"], t["rza"])),
                 ("rzA", q(100 * t["rzA"], t["rzaA"])), ("margin", t["take"] - t["give"]), ("penYdspg", q(t["peny"], g))]:
        check(f"[{ab}] displayed {k} = {v}", ss[k] == v, f"{ss[k]}")
    # game-by-game results == schedule scores (and ESPN's lastFiveGames where it overlaps)
    rows = {r["id"]: r for r in SC["results"][ab] if r["completed"]}
    check(f"[{ab}] game-by-game rows == completed schedule games ({len(games)})", set(rows) == {x[0] for x in games})
    check(f"[{ab}] every result score matches the ESPN game header", all(rows[i]["us"] == u and rows[i]["them"] == th for i, u, th in games))
    l5 = next((x for x in pre.get("lastFiveGames", []) if x["team"]["abbreviation"] == ab), None)
    if l5:
        ov = [e for e in l5["events"] if e["id"] in rows]
        check(f"[{ab}] W/L agrees with ESPN lastFiveGames ({len(ov)} overlapping)", ov and all(rows[e["id"]]["result"] == e["gameResult"] for e in ov))
check("all on-page season audit rows match", SC["checks"] and all(c["ok"] for c in SC["checks"]), str([c for c in SC["checks"] if not c["ok"]]))
# keys to the game: every cited number is a real stat, every gap is arithmetic on those numbers
vals = set()
for ab in (F, O):
    for k, v in SC["season"][ab].items():
        if isinstance(v, (int, float)): vals.add(round(abs(float(v)), 1))
ok_nums = ok_gap = ok_text = True
for k in SC["keys"]:
    ns = [v for _, v in k["nums"]]
    ok_nums &= all(round(abs(float(v)), 1) in vals for v in ns)
    ok_gap &= near(k["gap"], abs(ns[0] - ns[1]), 0.051)
    allowed = vals | {round(float(k["gap"]), 1)}
    toks = [round(abs(float(x)), 1) for x in re.findall(r"\d+(?:\.\d+)?", re.sub(r"\(\d+/\d+\)", "", k["text"]))]
    ok_text &= all(x in allowed for x in toks)
    for a_, b_ in re.findall(r"\((\d+)/(\d+)\)", k["text"]):
        ok_text &= int(a_) in vals and int(b_) in vals
check(f"keys to the game: {len(SC['keys'])} keys, each with 2 cited numbers", 3 <= len(SC["keys"]) <= 6 and all(len(k["nums"]) == 2 for k in SC["keys"]))
check("keys: every cited number is a computed season stat", ok_nums)
check("keys: every gap = |a − b| of its cited numbers", ok_gap)
check("keys: every number in the bullet text traces to the stats", ok_text)
# betting line: only if ESPN has it; must carry source + fetched time
pcs = pre.get("pickcenter") or []
if pcs:
    o = SC["odds"] or {}
    check(f"line matches ESPN pickcenter ({pcs[0].get('details')}, O/U {pcs[0].get('overUnder')})", o.get("details") == pcs[0].get("details") and o.get("overUnder") == pcs[0].get("overUnder")
          and o.get("homeML") == pcs[0]["homeTeamOdds"].get("moneyLine") and o.get("awayML") == pcs[0]["awayTeamOdds"].get("moneyLine"))
    check("line is labelled with source + fetched-at", bool(o.get("source")) and o.get("url") == man["scout"]["pregame"]["url"] and o.get("fetchedAt") == man["scout"]["pregame"]["fetchedAt"])
else:
    check("no line in ESPN data -> none shown", SC["odds"] is None)
# injuries: only if ESPN has them; every row verbatim
raw_inj = {t_["team"]["abbreviation"]: [(i["athlete"]["displayName"], i.get("status")) for i in t_.get("injuries", [])] for t_ in pre.get("injuries") or []}
ours_inj = {ab: [(i["name"], i.get("status")) for i in v] for ab, v in (SC["injuries"] or {}).items()}
check(f"injury report == ESPN pre-game injuries ({sum(len(v) for v in raw_inj.values())} rows)", raw_inj == ours_inj)
# opponent's last game: right game, and its drives reconcile with the box score like every Ravens game
og = SC["oppLastGame"]
last = max((r for r in SC["results"][O] if r["completed"]), key=lambda r: r["date"])
check(f"{O} drive chart is {O}'s most recent completed game ({last['id']})", og["id"] == last["id"] and og["focus"] == O)
check_game(og["id"], og)
import importlib.util
spec = importlib.util.spec_from_file_location("bd", P("build_data.py")); bd = importlib.util.module_from_spec(spec); spec.loader.exec_module(bd)
for r in SC["results"][O]:
    if r["completed"] and r["id"] != og["id"]:
        check_game(r["id"], bd.build_game(r["id"], man, focus=O))

print("live server")
try:
    with urllib.request.urlopen("http://127.0.0.1:4275/api/film", timeout=3) as r:
        live = json.load(r)
    check("/api/film serves film.json", live["latest"] == D["latest"])
    with urllib.request.urlopen("http://127.0.0.1:4275/", timeout=3) as r:
        check("/ serves index.html", b"Film Room" in r.read())
    with urllib.request.urlopen("http://127.0.0.1:4275/api/scout", timeout=3) as r:
        check("/api/scout serves scout.json", json.load(r)["game"]["id"] == SC["game"]["id"])
    with urllib.request.urlopen("http://127.0.0.1:4275/api/research", timeout=3) as r:
        rr = json.load(r)
        check("/api/research has Jurgens trade", "Jurgens" in rr.get("headlineTrade", {}).get("title", ""))
    for path_ in ("/scout.html", "/common.js", "/scout.js", "/hub.js"):
        with urllib.request.urlopen("http://127.0.0.1:4275" + path_, timeout=3) as r:
            check(f"{path_} served", r.status == 200)
except Exception as e:
    check("server reachable on 127.0.0.1:4275", False, str(e))

print("deliverables")
snap = P("dist", "ravens-film-room-snapshot.html")
check("snapshot exists", os.path.exists(snap))
if os.path.exists(snap):
    h = open(snap, encoding="utf-8").read()
    check("snapshot inlines data", "window.__FILM__=" in h and "window.__SCOUT__=" in h and "window.__RESEARCH__=" in h)
    check("snapshot has no external script/css/font refs", not re.search(r'<script[^>]+src=|<link[^>]+stylesheet|url\("fonts/', h))
    try:
        dom = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=4000", "--dump-dom", "file://" + snap + "?still=1&screen=film"],
                             capture_output=True, text=True, timeout=90).stdout
        dom = re.sub(r"<script\b.*?</script>", "", dom, flags=re.S)  # judge rendered DOM only, not inline JS source
        check("snapshot renders (data-ready=1)", 'data-ready="1"' in dom)
        g = D["games"][D["latest"]]
        # Hub snapshot also renders the scout opp-drive chart into a hidden screen; count film rows via screen-film.
        film_dom = dom
        if 'id="screen-film"' in dom:
            import re as _re
            m = _re.search(r'id="screen-film"[^>]*>(.*)id="screen-next"', dom, _re.S)
            if m: film_dom = m.group(1)
        n_drow = film_dom.count('class="drow')
        check("rendered drive chart has one row per drive", n_drow == len(g["drives"]), f"{n_drow} vs {len(g['drives'])}")
        check("rendered audit shows no mismatches", "✕ mismatch" not in dom and dom.count("✓ match") >= 14)
    except Exception as e:
        check("headless render", False, str(e))
snap2 = P("dist", "ravens-scouting-snapshot.html")
check("scouting snapshot exists", os.path.exists(snap2))
if os.path.exists(snap2):
    h = open(snap2, encoding="utf-8").read()
    check("scouting snapshot inlines data + shared renderer", "window.__SCOUT__=" in h and "driveChart" in h)
    check("scouting snapshot has no external script/css/font refs", not re.search(r'<script[^>]+src=|<link[^>]+stylesheet|url\("fonts/', h))
    check("tabs link back to hub snapshot", "ravens-film-room-snapshot.html" in h)
    try:
        dom = subprocess.run(["google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu", "--virtual-time-budget=4000", "--dump-dom", "file://" + snap2 + "?still=1"],
                             capture_output=True, text=True, timeout=90).stdout
        dom = re.sub(r"<script\b.*?</script>", "", dom, flags=re.S)
        check("scouting snapshot renders (data-ready=1)", 'data-ready="1"' in dom)
        check(f"rendered {O} drive chart has one row per drive ({len(og['drives'])})", len(re.findall(r'class="drow[^"]*" data-i="\d+"', dom)) == len(og["drives"]))
        check(f"rendered keys ({len(SC['keys'])}) and stat audit (no mismatches)", dom.count('class="key"') == len(SC["keys"]) and "✕ mismatch" not in dom and dom.count("✓ match") == len(SC["checks"]))
        if SC["odds"]: check("rendered line shows source + fetched time", SC["odds"]["details"] in dom and "pickcenter" in dom)
    except Exception as e:
        check("scouting headless render", False, str(e))
for s in ["00-best-home", "01-injury-board", "02-depth-chart", "03-film-notes", "04-film-room", "05-next-game"]:
    p = P("screenshots", s + ".png")
    check(f"screenshot {s}.png", os.path.exists(p) and os.path.getsize(p) > 20_000)

print(f"\n{passes} passed, {len(fails)} failed")
sys.exit(1 if fails else 0)
