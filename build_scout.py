#!/usr/bin/env python3
"""Compile data/scout.json: the Scouting Report for the Ravens' next scheduled game (no network; reads data/raw).
Season stats are summed from ESPN's per-game box scores, then cross-checked against ESPN's own season team statistics
(sports.core.api) and the per-game averages in ESPN's pre-game summary. Injuries and the betting line appear only if
ESPN's public pre-game summary carries them. Keys to the game are generated from the stat gaps by fixed rules.
Nothing is invented: missing fields are left out."""
import json, os
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from zoneinfo import ZoneInfo
import build_data as BD

HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "data", "raw")
ET = ZoneInfo("America/New_York")
J = lambda name: json.load(open(os.path.join(RAW, name), encoding="utf-8"))


def r1(num, den=1):  # exact ratio, rounded half-up to 0.1 (ESPN's convention: 193/4 = 48.25 -> 48.3)
    return float((Decimal(num) / Decimal(den)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def pair(v):  # "5-12" -> (5, 12)
    a, b = str(v).split("-"); return int(a), int(b)


def schedule_rows(sched, ab):
    rows = []
    for e in sched["events"]:
        c = e["competitions"][0]; st = c["status"]["type"]
        cs = {x["team"]["abbreviation"]: x for x in c["competitors"]}
        me = cs[ab]; opp = [k for k in cs if k != ab][0]
        sc = lambda x: (x.get("score") or {}).get("displayValue") if isinstance(x.get("score"), dict) else x.get("score")
        r = {"id": e["id"], "week": e.get("week", {}).get("number"), "date": e["date"], "opp": opp, "home": me["homeAway"] == "home",
             "completed": bool(st.get("completed")), "status": st.get("shortDetail") or st.get("detail")}
        if r["completed"]:
            r["us"], r["them"] = int(sc(me)), int(sc(cs[opp]))
            r["result"] = "W" if me.get("winner") else ("L" if cs[opp].get("winner") else "T")
        rows.append(r)
    return rows


def team_season(ab, rows):
    """Sum ESPN per-game box scores for every completed game. Offense = this team's box; defense = opponent's box."""
    T = {k: 0 for k in ["pf", "pa", "yds", "ydsA", "rush", "rushA", "pass", "passA", "sackYdsA", "give", "take",
                        "c3", "a3", "c3A", "a3A", "rzTD", "rzAtt", "rzTDA", "rzAttA", "pen", "penYds"]}
    T["games"] = 0
    for r in rows:
        if not r["completed"]:
            continue
        d = J(f"summary_{r['id']}.json")
        S = {t["team"]["abbreviation"]: BD.stat_map(t) for t in d["boxscore"]["teams"]}
        me, op = S[ab], S[r["opp"]]
        T["games"] += 1; T["pf"] += r["us"]; T["pa"] += r["them"]
        T["yds"] += int(me["totalYards"]); T["ydsA"] += int(op["totalYards"])
        T["rush"] += int(me["rushingYards"]); T["rushA"] += int(op["rushingYards"])
        T["pass"] += int(me["netPassingYards"]); T["passA"] += int(op["netPassingYards"])
        T["sackYdsA"] += pair(op["sacksYardsLost"])[1]
        T["give"] += int(me["turnovers"]); T["take"] += int(op["turnovers"])
        c, a = pair(me["thirdDownEff"]); T["c3"] += c; T["a3"] += a
        c, a = pair(op["thirdDownEff"]); T["c3A"] += c; T["a3A"] += a
        c, a = pair(me["redZoneAttempts"]); T["rzTD"] += c; T["rzAtt"] += a
        c, a = pair(op["redZoneAttempts"]); T["rzTDA"] += c; T["rzAttA"] += a
        n, y = pair(me["totalPenaltiesYards"]); T["pen"] += n; T["penYds"] += y
        r["box"] = {"yds": int(me["totalYards"]), "ydsA": int(op["totalYards"]), "give": int(me["turnovers"]), "take": int(op["turnovers"]),
                    "third": me["thirdDownEff"], "rz": me["redZoneAttempts"], "pen": me["totalPenaltiesYards"]}
    g = T["games"] or 1
    pct = lambda a, b: r1(100 * a, b) if b else None
    T.update({"ppg": r1(T["pf"], g), "papg": r1(T["pa"], g), "ypg": r1(T["yds"], g), "ypgA": r1(T["ydsA"], g),
              "rpg": r1(T["rush"], g), "rpgA": r1(T["rushA"], g), "ppgPass": r1(T["pass"], g), "ppgPassA": r1(T["passA"], g),
              "margin": T["take"] - T["give"], "p3": pct(T["c3"], T["a3"]), "p3A": pct(T["c3A"], T["a3A"]),
              "rz": pct(T["rzTD"], T["rzAtt"]), "rzA": pct(T["rzTDA"], T["rzAttA"]), "penpg": r1(T["pen"], g), "penYdspg": r1(T["penYds"], g)})
    return T


def core_stats(path):
    out = {}
    for cat in J(path)["splits"]["categories"]:
        for s in cat["stats"]:
            out.setdefault(s["name"], s.get("value"))
    return out


def checks_for(ab, T, core, pre):
    """Our box-score sums vs ESPN's season numbers. Every row is a hard check."""
    C = []
    add = lambda label, ours, espn, src: C.append({"team": ab, "label": label, "ours": ours, "espn": espn, "source": src,
                                                    "ok": espn is not None and abs(float(ours) - float(espn)) < 0.051})
    add("Games played", T["games"], core.get("teamGamesPlayed") or core.get("gamesPlayed"), "season stats")
    add("Points scored", T["pf"], core.get("totalPoints"), "season stats")
    add("Net total yards", T["yds"], core.get("netTotalYards"), "season stats")
    add("Rushing yards", T["rush"], core.get("rushingYards"), "season stats")
    add("Net passing yards", T["pass"], core.get("netPassingYards"), "season stats")
    add("3rd-down conversions", T["c3"], core.get("thirdDownConvs"), "season stats")
    add("3rd-down attempts", T["a3"], core.get("thirdDownAttempts"), "season stats")
    add("Red-zone TD %", round(100 * T["rzTD"] / T["rzAtt"], 2) if T["rzAtt"] else 0, core.get("redzoneTouchdownPct"), "season stats")
    add("Giveaways", T["give"], core.get("totalGiveaways"), "season stats")
    add("Takeaways", T["take"], core.get("totalTakeaways"), "season stats")
    add("Turnover margin", T["margin"], core.get("turnOverDifferential"), "season stats")
    add("Penalties", T["pen"], core.get("totalPenalties"), "season stats")
    add("Penalty yards", T["penYds"], core.get("totalPenaltyYards"), "season stats")
    g = T["games"] or 1
    add("Points per game", T["ppg"], pre.get("totalPointsPerGame"), "pre-game summary")
    add("Points allowed per game", T["papg"], pre.get("totalPointsPerGameAllowed"), "pre-game summary")
    add("Rush yards allowed per game", T["rpgA"], pre.get("rushingYardsPerGameAllowed"), "pre-game summary")
    # ESPN's pre-game "pass yards allowed" is gross: opponents' net passing + yards they lost to sacks
    add("Pass yards allowed per game (gross)", r1(T["passA"] + T["sackYdsA"], g), pre.get("passingYardsPerGameAllowed"), "pre-game summary")
    return C


def keys_to_game(F, O, s):
    """Rule-based keys from the stat gaps. Each key cites its numbers. Ranked by relative gap; strongest 6 kept."""
    a, b = s[F], s[O]
    K = []
    def unit(title, x, xl, y, yl, kind, noun, off, de):
        gap = abs(x - y); rel = gap / max(abs(x), abs(y), 1)
        fmt = (lambda v: f"{v:g}%") if kind == "pct" else (lambda v: f"{v:g} yds/g")
        gtxt = f"{gap:.1f} pts" if kind == "pct" else f"{gap:.1f}"
        if kind == "pct":
            verdict = (f"{de}'s rate allowed is {gtxt} {'lower' if y < x else 'higher'} than {off}'s rate." if y != x else f"Even: {de} allows exactly {off}'s rate.")
        else:
            verdict = (f"{de} has allowed {gtxt} {'fewer' if y < x else 'more'} {noun} per game than {off} has gained." if y != x else f"Even: {de} allows exactly what {off} gains.")
        K.append({"title": title, "rel": round(rel, 3), "nums": [[xl, x], [yl, y]], "gap": round(gap, 1),
                  "text": f"{xl}: {fmt(x)}. {yl}: {fmt(y)}. {verdict}"})
    unit(f"{F} run game vs. {O} run defense", a["rpg"], f"{F} rushing", b["rpgA"], f"{O} rushing allowed", "yds", "rushing yds", F, O)
    unit(f"{F} passing vs. {O} pass defense", a["ppgPass"], f"{F} net passing", b["ppgPassA"], f"{O} net passing allowed", "yds", "net passing yds", F, O)
    unit(f"{O} run game vs. {F} run defense", b["rpg"], f"{O} rushing", a["rpgA"], f"{F} rushing allowed", "yds", "rushing yds", O, F)
    unit(f"{O} passing vs. {F} pass defense", b["ppgPass"], f"{O} net passing", a["ppgPassA"], f"{F} net passing allowed", "yds", "net passing yds", O, F)
    if a["p3"] is not None and b["p3A"] is not None:
        unit(f"{F} 3rd downs vs. {O} 3rd-down defense", a["p3"], f"{F} 3rd-down rate ({a['c3']}/{a['a3']})", b["p3A"], f"{O} 3rd-down rate allowed ({b['c3A']}/{b['a3A']})", "pct", "3rd-down rate", F, O)
    if b["p3"] is not None and a["p3A"] is not None:
        unit(f"{O} 3rd downs vs. {F} 3rd-down defense", b["p3"], f"{O} 3rd-down rate ({b['c3']}/{b['a3']})", a["p3A"], f"{F} 3rd-down rate allowed ({a['c3A']}/{a['a3A']})", "pct", "3rd-down rate", O, F)
    if a["rz"] is not None and b["rzA"] is not None:
        unit(f"{F} red zone vs. {O} red-zone defense", a["rz"], f"{F} red-zone TD rate ({a['rzTD']}/{a['rzAtt']})", b["rzA"], f"{O} red-zone TD rate allowed ({b['rzTDA']}/{b['rzAttA']})", "pct", "red-zone TD rate", F, O)
    if b["rz"] is not None and a["rzA"] is not None:
        unit(f"{O} red zone vs. {F} red-zone defense", b["rz"], f"{O} red-zone TD rate ({b['rzTD']}/{b['rzAtt']})", a["rzA"], f"{F} red-zone TD rate allowed ({a['rzTDA']}/{a['rzAttA']})", "pct", "red-zone TD rate", O, F)
    # turnovers and penalties: team vs team
    d = a["margin"] - b["margin"]
    K.append({"title": "Turnover margin", "rel": round(min(1, abs(d) / 8), 3), "nums": [[f"{F} margin", a["margin"]], [f"{O} margin", b["margin"]]],
              "text": f"{F}: {a['margin']:+d} ({a['take']} takeaways, {a['give']} giveaways). {O}: {b['margin']:+d} ({b['take']} takeaways, {b['give']} giveaways). "
                      f"Gap: {abs(d)}, in {F if d > 0 else O}'s favor.", "gap": abs(d)})
    pf, po = a["penYdspg"], b["penYdspg"]
    K.append({"title": "Penalty yards", "rel": round(abs(pf - po) / max(pf, po, 1), 3), "nums": [[f"{F} penalty yds/g", pf], [f"{O} penalty yds/g", po]],
              "gap": round(abs(pf - po), 1),
              "text": f"{F}: {a['pen']} penalties for {a['penYds']} yds ({pf:g} yds/g). {O}: {b['pen']} for {b['penYds']} yds ({po:g} yds/g). "
                      f"{F if pf > po else O} has been flagged for {abs(pf - po):.1f} more penalty yds/g."})
    K.sort(key=lambda k: -k["rel"])
    return K[:6], K


def odds(pre, man):
    pcs = pre.get("pickcenter") or []
    if not pcs:
        return None
    p = pcs[0]
    comp = pre["header"]["competitions"][0]
    ha = {c["homeAway"]: c["team"]["abbreviation"] for c in comp["competitors"]}
    out = {"provider": (p.get("provider") or {}).get("name"), "details": p.get("details"), "overUnder": p.get("overUnder"),
           "spread": p.get("spread"), "overOdds": p.get("overOdds"), "underOdds": p.get("underOdds"),
           "home": ha["home"], "away": ha["away"],
           "homeML": (p.get("homeTeamOdds") or {}).get("moneyLine"), "awayML": (p.get("awayTeamOdds") or {}).get("moneyLine"),
           "homeSpreadOdds": (p.get("homeTeamOdds") or {}).get("spreadOdds"), "awaySpreadOdds": (p.get("awayTeamOdds") or {}).get("spreadOdds"),
           "source": "ESPN pre-game summary (pickcenter)", "url": man["pregame"]["url"], "fetchedAt": man["pregame"]["fetchedAt"]}
    return {k: v for k, v in out.items() if v is not None}


def injuries(pre):
    out = {}
    for t in pre.get("injuries") or []:
        ab = t["team"]["abbreviation"]; out[ab] = []
        for i in t.get("injuries", []):
            a = i.get("athlete", {}); det = i.get("details") or {}
            row = {"name": a.get("displayName"), "pos": (a.get("position") or {}).get("abbreviation"), "status": i.get("status"),
                   "injury": det.get("type"), "date": i.get("date")}
            out[ab].append({k: v for k, v in row.items() if v})
    return out


def main():
    man = json.load(open(os.path.join(RAW, "manifest.json")))
    sm = man.get("scout")
    if not sm:
        raise SystemExit("no scout data in manifest; run ./run.sh fetch")
    F, O, eid = "BAL", sm["opp"], sm["event"]
    pre = J(f"pregame_{eid}.json")
    comp = pre["header"]["competitions"][0]
    cs = {c["homeAway"]: c for c in comp["competitors"]}
    rows = {F: schedule_rows(J("schedule.json"), F), O: schedule_rows(J(f"schedule_{O.lower()}.json"), O)}
    season = {ab: team_season(ab, rows[ab]) for ab in (F, O)}
    pregame_avgs = {t["team"]["abbreviation"]: {s["name"]: s.get("displayValue") for s in t.get("statistics", [])} for t in pre.get("boxscore", {}).get("teams", [])}
    core = {ab: core_stats(f"teamstats_{ab.lower()}.json") for ab in (F, O)}
    checks = checks_for(F, season[F], core[F], pregame_avgs.get(F, {})) + checks_for(O, season[O], core[O], pregame_avgs.get(O, {}))
    keys, allkeys = keys_to_game(F, O, season)
    teams = {}
    for ha, c in cs.items():
        t = c["team"]
        teams[t["abbreviation"]] = {"abbr": t["abbreviation"], "name": t.get("displayName"), "short": t.get("name"), "color": "#" + t.get("color", "777777"),
                                    "alt": "#" + t.get("alternateColor", "333333"), "homeAway": ha,
                                    "record": next((r.get("summary") or r.get("displayValue") for r in c.get("record", []) if r.get("type") == "total"), None)}
    # opponent's most recent completed game, built by the Film Room's own drive builder (opponent attacks right)
    last = max((r for r in rows[O] if r["completed"]), key=lambda r: r["date"])
    oppGame = BD.build_game(last["id"], man, focus=O)
    pred = pre.get("predictor") or {}
    predictor = None
    if pred.get("homeTeam") and pred.get("awayTeam"):
        predictor = {"home": cs["home"]["team"]["abbreviation"], "away": cs["away"]["team"]["abbreviation"],
                     "homePct": pred["homeTeam"].get("gameProjection"), "awayPct": pred["awayTeam"].get("gameProjection"), "label": pred.get("header")}
    gi = pre.get("gameInfo", {})
    out = {"generatedAt": datetime.now(ET).isoformat(timespec="seconds"), "focus": F, "opp": O,
           "game": {"id": eid, "date": comp.get("date"), "week": pre["header"].get("week"), "home": cs["home"]["team"]["abbreviation"],
                    "away": cs["away"]["team"]["abbreviation"], "venue": gi.get("venue", {}).get("fullName"),
                    "city": ", ".join(x for x in [gi.get("venue", {}).get("address", {}).get("city"), gi.get("venue", {}).get("address", {}).get("state")] if x),
                    "status": comp["status"]["type"].get("detail"), "espnPage": f"https://www.espn.com/nfl/game/_/gameId/{eid}"},
           "teams": teams, "season": season, "results": rows, "checks": checks, "keys": keys, "allKeys": allkeys,
           "injuries": injuries(pre), "odds": odds(pre, sm), "predictor": predictor, "oppLastGame": oppGame,
           "sources": {"pregame": sm["pregame"], "oppSchedule": sm["oppSchedule"], "schedule": man["schedule"], "teamStats": sm["teamStats"],
                       "summaries": {r["id"]: man["summaries"].get(r["id"]) for ab in rows for r in rows[ab] if r["completed"]}}}
    tmp = os.path.join(HERE, "data", "scout.json.tmp")
    json.dump(out, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, os.path.join(HERE, "data", "scout.json"))
    bad = [c for c in checks if not c["ok"]]
    print(f"scout.json: {F} @ {O} wk{out['game']['week']}; {len(checks)} season checks, {len(bad)} mismatches; {len(keys)} keys; "
          f"injuries {sum(len(v) for v in out['injuries'].values())}; odds {'yes' if out['odds'] else 'no'}; "
          f"opp last game {oppGame['away']}@{oppGame['home']} {len(oppGame['drives'])} drives; {os.path.getsize(os.path.join(HERE,'data','scout.json'))//1024} KB")
    for c in bad:
        print("  MISMATCH", c)


if __name__ == "__main__":
    main()
