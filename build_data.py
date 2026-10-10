#!/usr/bin/env python3
"""Compile data/film.json from the raw ESPN JSON in data/raw (no network).
Nothing is invented. Fields ESPN doesn't provide are left out (None/absent), never guessed."""
import json, os, re
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "data", "raw")
ET = ZoneInfo("America/New_York")
TEAM = "BAL"
NONPLAY = {"Official Timeout", "Timeout", "End Period", "End of Half", "End of Game", "Two-minute warning", "End of Regulation"}


def secs(clock):
    try:
        m, s = clock.split(":"); return int(m) * 60 + int(float(s))
    except Exception:
        return None


def elapsed(period, clock):
    c = secs(clock)
    if c is None or period is None:
        return None
    if period <= 4:
        return (period - 1) * 900 + (900 - c)
    return 3600 + (period - 5) * 600 + (600 - c)


def result_class(r):
    r = (r or "").upper()
    if r in ("TD",): return "td"
    if r == "FG": return "fg"
    if r in ("PUNT",): return "punt"
    if r in ("INT", "FUMBLE", "DOWNS", "FUMBLE RETURN TD", "INT TD", "FUMBLE TD", "SF", "SAFETY"): return "to"
    if "MISSED" in r or "BLOCKED" in r: return "miss"
    return "end"


def stat_map(team_box):
    out = {}
    for s in team_box.get("statistics", []):
        out.setdefault(s["name"], s.get("displayValue"))
    return out


def build_game(eid, man, focus=TEAM):
    d = json.load(open(os.path.join(RAW, f"summary_{eid}.json"), encoding="utf-8"))
    comp = d["header"]["competitions"][0]
    cs = {c["homeAway"]: c for c in comp["competitors"]}
    home, away = cs["home"]["team"]["abbreviation"], cs["away"]["team"]["abbreviation"]
    f_home = home == focus
    opp = away if f_home else home
    X = (lambda y: y) if f_home else (lambda y: None if y is None else 100 - y)  # focus team always attacks right
    teams = {}
    for ha, c in cs.items():
        t = c["team"]
        teams[t["abbreviation"]] = {"abbr": t["abbreviation"], "name": t.get("displayName"), "short": t.get("name"), "color": "#" + t.get("color", "777777"),
                                    "alt": "#" + t.get("alternateColor", "333333"), "homeAway": ha, "score": int(c["score"]) if c.get("score") not in (None, "") else None,
                                    "linescores": [int(float(l["displayValue"])) for l in c.get("linescores", []) if l.get("displayValue") not in (None, "")],
                                    "record": next((r["displayValue"] for r in c.get("record", []) if r.get("type") == "total"), None), "winner": c.get("winner")}
    wp = {w["playId"]: w["homeWinPercentage"] for w in d.get("winprobability", [])}
    drives, plays_all = [], []
    run = {home: 0, away: 0}
    for i, dr in enumerate(d.get("drives", {}).get("previous", [])):
        off = dr["team"]["abbreviation"]
        before = dict(run)
        plays = []
        for p in dr.get("plays", []):
            per = p.get("period", {}).get("number"); clk = p.get("clock", {}).get("displayValue")
            hs, as_ = p.get("homeScore"), p.get("awayScore")
            if hs is not None and as_ is not None:
                run = {home: hs, away: as_}
            typ = p.get("type", {}).get("text", "")
            st, en = p.get("start", {}), p.get("end", {})
            pl = {"id": p["id"], "drive": i, "type": typ, "text": p.get("text", ""), "period": per, "clock": clk, "t": elapsed(per, clk),
                  "off": off, "x0": X(st.get("yardLine")), "x1": X(en.get("yardLine")), "yds": p.get("statYardage"),
                  "dd": st.get("downDistanceText"), "down": st.get("down"), "scoring": bool(p.get("scoringPlay")),
                  "penalty": bool(p.get("isPenalty")), "turnover": bool(p.get("isTurnover")), "nonplay": typ in NONPLAY,
                  "score": {focus: run[focus], opp: run[opp]}}
            if p["id"] in wp:
                h = wp[p["id"]]; pl["wpF"] = round(h if f_home else 1 - h, 4)
            plays.append(pl)
        pts = {focus: run[focus] - before[focus], opp: run[opp] - before[opp]}
        s, e = dr.get("start", {}), dr.get("end", {})
        drives.append({"i": i, "id": dr["id"], "team": off, "result": dr.get("displayResult"), "short": dr.get("shortDisplayResult"),
                       "cls": result_class(dr.get("shortDisplayResult") or dr.get("result")), "desc": dr.get("description"),
                       "yards": dr.get("yards"), "plays": dr.get("offensivePlays"), "time": dr.get("timeElapsed", {}).get("displayValue"),
                       "isScore": dr.get("isScore"), "points": pts[off], "defPoints": pts[[t for t in pts if t != off][0]],
                       "startText": s.get("text"), "endText": e.get("text"), "x0": X(s.get("yardLine")), "x1": X(e.get("yardLine")),
                       "period": s.get("period", {}).get("number"), "clock": s.get("clock", {}).get("displayValue"),
                       "t0": elapsed(s.get("period", {}).get("number"), s.get("clock", {}).get("displayValue")),
                       "scoreAfter": {focus: run[focus], opp: run[opp]}, "playList": plays})
        plays_all.extend(plays)
    # scoring timeline
    scoring = []
    for s in d.get("scoringPlays", []):
        per = s["period"]["number"]; clk = s["clock"]["displayValue"]
        bal = s["homeScore"] if f_home else s["awayScore"]; op = s["awayScore"] if f_home else s["homeScore"]
        scoring.append({"team": s["team"]["abbreviation"], "type": s["type"]["text"], "text": s["text"], "period": per, "clock": clk,
                        "t": elapsed(per, clk), "score": {focus: bal, opp: op}})
    # win probability series (only plays that carry a WP value)
    wps = [{"t": p["t"], "wp": p["wpF"], "id": p["id"]} for p in plays_all if "wpF" in p and p["t"] is not None]
    # key plays: scoring, turnovers/downs, biggest WP swings, long gains. Text is ESPN's, verbatim.
    real = [p for p in plays_all if not p["nonplay"] and p["type"] != "Kickoff"]
    key = {}
    def addk(p, tag):
        k = key.setdefault(p["id"], dict(p, tags=[])); k.pop("score", None); k["score"] = p["score"]
        if tag not in k["tags"]: k["tags"].append(tag)
    for p in plays_all:
        if p["scoring"]: addk(p, "Score")
        if p["turnover"] or "Interception" in p["type"] or "Fumble Recovery (Opponent)" in p["type"]: addk(p, "Turnover")
    for dr in drives:
        if dr["short"] == "DOWNS":
            last = [p for p in dr["playList"] if not p["nonplay"]]
            if last: addk(last[-1], "4th-down stop")
    prev = None; swings = []
    for p in plays_all:
        if "wpF" in p:
            if prev is not None and not p["nonplay"]:
                swings.append((abs(p["wpF"] - prev), p["wpF"] - prev, p))
            prev = p["wpF"]
    for mag, delta, p in sorted(swings, key=lambda z: -z[0])[:5]:
        if mag >= 0.04:
            addk(p, "WP swing"); key[p["id"]]["wpDelta"] = round(delta, 4)
    GAIN = {"Rush", "Pass Reception", "Passing Touchdown", "Rushing Touchdown"}
    for p in sorted([p for p in real if p["type"] in GAIN and not p["penalty"]], key=lambda z: -(z["yds"] or 0))[:4]:
        if (p["yds"] or 0) >= 25: addk(p, "Big play")
    for p in real:
        m = re.search(r"(\d+) yard field goal is GOOD", p["text"])
        if m and int(m.group(1)) >= 50:
            addk(p, "Long FG"); key[p["id"]]["fgYards"] = int(m.group(1))
    keyplays = sorted(key.values(), key=lambda z: (z["t"] if z["t"] is not None else 0))
    # box score
    tstats = {t["team"]["abbreviation"]: stat_map(t) for t in d["boxscore"]["teams"]}
    players = {}
    for t in d["boxscore"]["players"]:
        ab = t["team"]["abbreviation"]; players[ab] = {}
        for g in t["statistics"]:
            players[ab][g["name"]] = {"labels": g.get("labels", []), "totals": g.get("totals", []),
                                      "athletes": [{"name": a["athlete"]["displayName"], "pos": a["athlete"].get("position", {}).get("abbreviation"), "stats": a["stats"]} for a in g.get("athletes", [])]}
    leaders = {}
    for L in d.get("leaders", []):
        ab = L["team"]["abbreviation"]; leaders[ab] = []
        for cat in L["leaders"]:
            if cat.get("leaders"):
                x = cat["leaders"][0]
                leaders[ab].append({"cat": cat.get("displayName"), "name": x["athlete"].get("displayName"), "pos": x["athlete"].get("position", {}).get("abbreviation"), "value": x.get("displayValue")})
    gi = d.get("gameInfo", {})
    m = man["summaries"].get(eid, {})
    return {"id": eid, "date": comp.get("date"), "week": d["header"].get("week"), "status": comp["status"]["type"].get("detail"),
            "home": home, "away": away, "focus": focus, "focusHome": f_home, "opp": opp, "teams": teams,
            "venue": gi.get("venue", {}).get("fullName"), "city": ", ".join(x for x in [gi.get("venue", {}).get("address", {}).get("city"), gi.get("venue", {}).get("address", {}).get("state")] if x),
            "attendance": gi.get("attendance"), "drives": drives, "scoring": scoring, "wp": wps, "keyPlays": keyplays,
            "teamStats": tstats, "players": players, "leaders": leaders,
            "source": {"url": m.get("url"), "fetchedAt": m.get("fetchedAt"), "espnPage": f"https://www.espn.com/nfl/game/_/gameId/{eid}"}}


def season(man):
    s = json.load(open(os.path.join(RAW, "schedule.json"), encoding="utf-8"))
    out = []
    for e in s["events"]:
        c = e["competitions"][0]; st = c["status"]["type"]
        cs = {x["team"]["abbreviation"]: x for x in c["competitors"]}
        me = cs.get(TEAM); opp = [k for k in cs if k != TEAM][0]
        sc = lambda x: (x.get("score", {}) or {}).get("displayValue") if isinstance(x.get("score"), dict) else x.get("score")
        row = {"id": e["id"], "week": e.get("week", {}).get("number"), "date": e["date"], "opp": opp, "home": me["homeAway"] == "home",
               "completed": bool(st.get("completed")), "status": st.get("shortDetail") or st.get("detail")}
        if row["completed"]:
            row["us"] = int(sc(me)); row["them"] = int(sc(cs[opp])); row["result"] = "W" if me.get("winner") else ("L" if cs[opp].get("winner") else "T")
        out.append(row)
    return {"season": s.get("season", {}).get("displayName"), "games": out, "source": {"url": man["schedule"]["url"], "fetchedAt": man["schedule"]["fetchedAt"]}}


def main():
    man = json.load(open(os.path.join(RAW, "manifest.json")))
    sea = season(man)
    done = [g for g in sea["games"] if g["completed"]]
    games = {g["id"]: build_game(g["id"], man) for g in done if os.path.exists(os.path.join(RAW, f"summary_{g['id']}.json"))}
    latest = max(done, key=lambda g: g["date"])["id"]
    out = {"generatedAt": datetime.now(ET).isoformat(timespec="seconds"), "team": TEAM, "latest": latest, "season": sea, "games": games}
    tmp = os.path.join(HERE, "data", "film.json.tmp")
    json.dump(out, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, os.path.join(HERE, "data", "film.json"))
    g = games[latest]
    print(f"film.json: {len(games)} games; latest {g['away']} @ {g['home']} {g['teams'][g['away']]['score']}-{g['teams'][g['home']]['score']}, "
          f"{len(g['drives'])} drives, {len(g['keyPlays'])} key plays, {len(g['wp'])} WP points; {os.path.getsize(os.path.join(HERE,'data','film.json'))//1024} KB")


if __name__ == "__main__":
    main()
