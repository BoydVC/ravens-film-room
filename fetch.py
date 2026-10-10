#!/usr/bin/env python3
"""Fetch PUBLIC ESPN JSON for the Ravens (schedule + every completed game's summary). Read-only, no auth.
Writes data/raw/*.json and data/raw/manifest.json (URL + fetched-at for each file)."""
import json, os, urllib.request
from datetime import datetime
from zoneinfo import ZoneInfo
HERE = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(HERE, "data", "raw")
ET = ZoneInfo("America/New_York")
SCHED = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/bal/schedule"
SUMM = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/summary?event={}"
TSCHED = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/teams/{}/schedule"
CORE = "https://sports.core.api.espn.com/v2/sports/football/leagues/nfl/seasons/{}/types/2/teams/{}/statistics"


def get(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (TokenMax ravens-film-room; local)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
    json.loads(body)
    tmp = path + ".tmp"; open(tmp, "wb").write(body); os.replace(tmp, path)
    return datetime.now(ET).isoformat(timespec="seconds")


def main():
    os.makedirs(RAW, exist_ok=True)
    man = {"schedule": {"url": SCHED, "fetchedAt": get(SCHED, os.path.join(RAW, "schedule.json"))}, "summaries": {}}
    sched = json.load(open(os.path.join(RAW, "schedule.json")))
    for e in sched["events"]:
        if e["competitions"][0]["status"]["type"].get("completed"):
            url = SUMM.format(e["id"])
            man["summaries"][e["id"]] = {"url": url, "fetchedAt": get(url, os.path.join(RAW, f"summary_{e['id']}.json"))}
            print("fetched", e["id"])
    # ---- scouting: next scheduled BAL game (pre-game summary = injuries + odds), the opponent's schedule and
    # completed-game summaries, and ESPN's season team statistics for both teams.
    nxt = next((e for e in sched["events"] if not e["competitions"][0]["status"]["type"].get("completed")), None)
    if nxt:
        comp = nxt["competitions"][0]
        teams = {c["team"]["abbreviation"]: c["team"]["id"] for c in comp["competitors"]}
        opp = [k for k in teams if k != "BAL"][0]
        url = SUMM.format(nxt["id"])
        sc = {"event": nxt["id"], "opp": opp, "teamIds": teams,
              "pregame": {"url": url, "fetchedAt": get(url, os.path.join(RAW, f"pregame_{nxt['id']}.json"))}, "oppSchedule": {}, "teamStats": {}}
        u = TSCHED.format(opp.lower())
        sc["oppSchedule"] = {"url": u, "fetchedAt": get(u, os.path.join(RAW, f"schedule_{opp.lower()}.json"))}
        osched = json.load(open(os.path.join(RAW, f"schedule_{opp.lower()}.json")))
        for e in osched["events"]:
            if e["competitions"][0]["status"]["type"].get("completed") and e["id"] not in man["summaries"]:
                u = SUMM.format(e["id"])
                man["summaries"][e["id"]] = {"url": u, "fetchedAt": get(u, os.path.join(RAW, f"summary_{e['id']}.json"))}
                print("fetched", opp, e["id"])
        year = sched.get("season", {}).get("year") or 2026
        for ab, tid in teams.items():
            u = CORE.format(year, tid)
            sc["teamStats"][ab] = {"url": u, "fetchedAt": get(u, os.path.join(RAW, f"teamstats_{ab.lower()}.json"))}
        man["scout"] = sc
        print("scout:", nxt["id"], "BAL vs", opp)
    json.dump(man, open(os.path.join(RAW, "manifest.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
