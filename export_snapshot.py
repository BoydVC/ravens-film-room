#!/usr/bin/env python3
"""Build offline snapshots (CSS, JS, fonts, data inlined; file:// safe):
  dist/ravens-film-room-snapshot.html  (War Room hub: film + scout + research)
  dist/ravens-scouting-snapshot.html   (standalone scout page)
"""
import base64, json, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, "web")
FILM, SCOUT = "ravens-film-room-snapshot.html", "ravens-scouting-snapshot.html"


def rd(name):
    return open(os.path.join(W, name), encoding="utf-8").read()


def inline_css(css):
    def font(m):
        path = os.path.join(W, m.group(1))
        return 'url("data:font/ttf;base64,' + base64.b64encode(open(path, "rb").read()).decode() + '")'
    return re.sub(r'url\("(fonts/[^"]+)"\)', font, css)


def payload(name):
    data = json.load(open(os.path.join(HERE, "data", name), encoding="utf-8"))
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def inline_js(name):
    return "<script>\n" + rd(name).replace("</script", "<\\/script") + "\n</script>"


def build_hub():
    html, css = rd("index.html"), inline_css(rd("style.css"))
    html = html.replace('<link rel="stylesheet" href="style.css">', "<style>\n" + css + "\n</style>")
    html = html.replace("<!--FILMDATA-->", f"<script>window.__FILM__={payload('film.json')};</script>")
    html = html.replace("<!--SCOUTDATA-->", f"<script>window.__SCOUT__={payload('scout.json')};</script>")
    html = html.replace("<!--RESEARCHDATA-->", f"<script>window.__RESEARCH__={payload('research.json')};</script>")
    html = html.replace('<script src="common.js"></script>', inline_js("common.js"))
    html = html.replace('<script src="hub.js"></script>', inline_js("hub.js"))
    html = html.replace('<script src="app.js"></script>', inline_js("app.js"))
    html = html.replace('<script src="scout.js"></script>', inline_js("scout.js"))
    # still=1 for screenshot stability optional via query; leave as-is
    os.makedirs(os.path.join(HERE, "dist"), exist_ok=True)
    out = os.path.join(HERE, "dist", FILM)
    open(out, "w", encoding="utf-8").write(html)
    print(f"{out} ({os.path.getsize(out)//1024} KB)")


def build_scout():
    if not os.path.exists(os.path.join(HERE, "data", "scout.json")):
        return
    html, css = rd("scout.html"), inline_css(rd("style.css"))
    html = html.replace('<link rel="stylesheet" href="style.css">', "<style>\n" + css + "\n</style>")
    html = html.replace("<!--SCOUTDATA-->", f"<script>window.__SCOUT__={payload('scout.json')};</script>")
    html = html.replace('<script src="common.js"></script>', inline_js("common.js"))
    html = html.replace('<script src="scout.js"></script>', inline_js("scout.js"))
    html = html.replace('href="index.html', f'href="{FILM}')
    out = os.path.join(HERE, "dist", SCOUT)
    open(out, "w", encoding="utf-8").write(html)
    print(f"{out} ({os.path.getsize(out)//1024} KB)")


if __name__ == "__main__":
    build_hub()
    build_scout()
