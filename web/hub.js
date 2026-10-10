/* Ravens Film Room · War Room hub: screen switching + research screens.
   Research facts only from data/research.json (Jim journals). ESPN via film/scout. */
(function () {
  "use strict";
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const qs = new URLSearchParams(location.search);
  const STILL = qs.has("still");

  let RESEARCH = null;

  function showScreen(name) {
    $$(".screen").forEach((el) => {
      const on = el.id === "screen-" + name;
      el.classList.toggle("on", on);
      el.hidden = !on;
    });
    $$(".sn").forEach((b) => {
      const on = b.dataset.screen === name;
      b.classList.toggle("on", on);
      b.setAttribute("aria-selected", on ? "true" : "false");
    });
    const titles = {
      war: "War Room",
      film: "Film Room",
      next: "Next Game",
      injuries: "Injury Board",
      depth: "Depth Chart",
      notes: "Film Notes",
    };
    const t = $(".title");
    if (t) t.textContent = titles[name] || "Film Room";
    document.body.dataset.screen = name;
    const u = new URL(location);
    u.searchParams.set("screen", name);
    history.replaceState(null, "", u);
    // reflow drive charts when film/next become visible
    if (name === "film" || name === "next") {
      requestAnimationFrame(() => window.dispatchEvent(new Event("resize")));
    }
  }

  function cite(file, urls) {
    const links = (urls || []).map((u) => `<a href="${esc(u)}" target="_blank" rel="noopener">${esc(u.replace(/^https?:\/\//, "").slice(0, 48))}…</a>`).join(" · ");
    return `<div class="cite"><span class="cite-file">${esc(file || "")}</span>${links ? " · " + links : ""}</div>`;
  }

  function renderWar(R) {
    const trade = R.headlineTrade;
    const ng = R.nextGame;
    const lam = R.lamarTimeline[R.lamarTimeline.length - 1];
    const film = R.filmNotesLastGame;
    const line = R.lineContext;
    $("#rec-pill").innerHTML = `<span class="rp-k">BAL</span><span class="rp-v">${esc(R.record)}</span><span class="rp-s">into ${esc(ng.label)}</span>`;

    $("#war-root").innerHTML = `
      <div class="war-hero card glow-pulse">
        <div class="wh-kicker"><span class="reel"></span> NEXT UP · ${esc(ng.label)}</div>
        <div class="wh-title">BAL <span class="at">@</span> ATL</div>
        <div class="wh-when">${esc(ng.whenEt)} · ${esc(ng.venue)}</div>
        <div class="wh-actions">
          <button type="button" class="gold-btn" data-go="next">Open scouting</button>
          <button type="button" class="ghost-btn" data-go="injuries">Injury board</button>
          <button type="button" class="ghost-btn" data-go="depth">Depth chart</button>
        </div>
        <div class="as-of">${esc(R.asOfLabel)}</div>
      </div>

      <div class="war-grid">
        <article class="card trade-card">
          <h2><span class="badge-new">OCT 7</span> Cam Jurgens trade</h2>
          <p class="lead">${esc(trade.title)}</p>
          <div class="swap">
            <div><em>Give</em><ul>${trade.give.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>
            <div class="swap-arrow">⟷</div>
            <div><em>Get</em><ul>${trade.get.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>
          </div>
          <p>${esc(trade.profile)}</p>
          <p class="hi">${esc(trade.status)}</p>
          <p>${esc(trade.olPlan)}</p>
          <p class="dim">${esc(trade.note)}</p>
          ${cite(trade.sources[0].file, trade.sources[0].urls)}
        </article>

        <article class="card lamar-card">
          <h2>Lamar · ankle timeline</h2>
          <ol class="tl">${R.lamarTimeline.map((e) => `
            <li>
              <div class="tl-d">${esc(e.date)}</div>
              <div class="tl-t">${esc(e.title)}</div>
              <div class="tl-x">${esc(e.text)}</div>
              ${cite(e.file, e.urls)}
            </li>`).join("")}</ol>
          <p class="dim">Latest: ${esc(lam.title)} (${esc(lam.date)}).</p>
        </article>
      </div>

      <div class="war-grid three">
        <article class="card">
          <h2>Line context <span class="aside">info only</span></h2>
          <div class="line-big">${esc(line.espnSnapshot.details)} · O/U ${esc(line.espnSnapshot.ou)}</div>
          <div class="dim">ESPN/DraftKings snapshot ${esc(line.espnSnapshot.fetchedAt)} · BAL ML ${line.espnSnapshot.balML > 0 ? "+" : ""}${line.espnSnapshot.balML}</div>
          <ul class="move-list">${line.journalMoves.map((m) => `<li><code>${esc(m.file)}</code> — ${esc(m.text)}</li>`).join("")}</ul>
          <p class="dim">${esc(line.disclaimer)}</p>
        </article>
        <article class="card">
          <h2>Last film · vs TEN</h2>
          <p class="lead">${esc(film.game)}</p>
          <ul class="bullet-tight">${film.bullets.slice(0, 5).map((b) => `<li>${esc(b)}</li>`).join("")}</ul>
          <button type="button" class="ghost-btn" data-go="notes">All film notes</button>
          <button type="button" class="ghost-btn" data-go="film">Open drive chart</button>
          ${cite(film.file, film.urls)}
        </article>
        <article class="card gap-card">
          <h2>Honest gaps</h2>
          <ul class="gap-list">${R.gaps.map((g) => `<li>${esc(g)}</li>`).join("")}</ul>
          <p class="dim">Nothing here is invented. Thin spots stay labeled.</p>
        </article>
      </div>
    `;
    $$("#war-root [data-go]").forEach((b) => b.addEventListener("click", () => showScreen(b.dataset.go)));
  }

  function renderInjuries(R, scout) {
    const wed = R.wedInjuryReport;
    const espnBal = (scout && scout.injuries && scout.injuries.BAL) || [];
    const espnAtl = (scout && scout.injuries && scout.injuries.ATL) || [];
    const row = (p, cls) => `<div class="inj-row ${cls || ""}">
      <div class="inj-name"><b>${esc(p.name)}</b> <span class="pos">${esc(p.pos || "")}</span></div>
      <div class="inj-note">${esc(p.note || p.injury || "")}</div>
      <div class="inj-st ${statusClass(p.status || p.note)}">${esc(p.status || (cls === "dnp" ? "DNP" : cls === "lim" ? "Limited" : "") || "—")}</div>
    </div>`;
    function statusClass(s) {
      s = (s || "").toLowerCase();
      if (/ir|season|out|dnp|torn|long-term/.test(s)) return "bad";
      if (/limited|question|chance|sprain|foot|ankle|groin|shoulder|calf|finger|toe/.test(s)) return "warn";
      return "";
    }
    const espnRow = (p) => `<div class="inj-row">
      <div class="inj-name"><b>${esc(p.name)}</b> <span class="pos">${esc(p.pos)}</span></div>
      <div class="inj-note">${esc(p.injury)}</div>
      <div class="inj-st ${statusClass(p.status)}">${esc(p.status)}</div>
    </div>`;

    $("#injuries-root").innerHTML = `
      <div class="card glow-soft">
        <h2>Injury board <span class="aside">dual source · never merged silently</span></h2>
        <p class="lead">Jim journal Wednesday practice report (Oct 7) sits beside ESPN's pre-game injury list from scout.json. They do not match — both are shown, labeled.</p>
        <p class="dim">${esc(wed.gap)}</p>
      </div>
      <div class="war-grid">
        <article class="card">
          <h2><span class="badge-src">JOURNAL</span> Wed practice · ${esc(wed.asOfEt)}</h2>
          <h3 class="inj-h">Did not practice</h3>
          ${wed.didNotPractice.map((p) => row(p, "dnp")).join("")}
          <h3 class="inj-h">Limited</h3>
          ${wed.limited.map((p) => row(p, "lim")).join("")}
          ${cite(wed.file, [wed.url])}
        </article>
        <article class="card">
          <h2><span class="badge-src espn">ESPN</span> Pre-game list (BAL)</h2>
          ${espnBal.length ? espnBal.map(espnRow).join("") : '<p class="dim">No BAL injuries in ESPN pre-game payload.</p>'}
          <h3 class="inj-h">ATL (ESPN)</h3>
          ${espnAtl.length ? espnAtl.map(espnRow).join("") : '<p class="dim">None listed.</p>'}
          <div class="cite">Source: data/scout.json · ESPN pre-game summary fetched with the Oct 7 scout build</div>
        </article>
      </div>
      <div class="card">
        <h2>Season-ending / long-term (journals)</h2>
        ${R.otherInjuries.map((p) => `
          <div class="inj-row bad">
            <div class="inj-name"><b>${esc(p.name)}</b> <span class="pos">${esc(p.pos)}</span></div>
            <div class="inj-note">${esc(p.status)}${p.depthNote ? " — " + esc(p.depthNote) : ""}</div>
          </div>
          ${cite(p.file, p.urls)}
        `).join("")}
      </div>
    `;
  }

  function renderDepth(R) {
    const d = R.depthChart;
    const cell = (p) => `<div class="dc-row ${p.gap ? "gap" : ""}">
      <div class="dc-pos">${esc(p.pos)}</div>
      <div class="dc-main">
        <div class="dc-starter">${p.gap && p.starter === "—" ? `<span class="gap-tag">GAP</span> ${esc(p.gapLabel || "not in research")}` : esc(p.starter)}</div>
        ${p.note ? `<div class="dc-note">${esc(p.note)}</div>` : ""}
        ${p.backup && p.backup !== "—" ? `<div class="dc-back">Next: ${esc(p.backup)}</div>` : ""}
        ${p.gap && p.starter !== "—" && p.gapLabel ? `<div class="gap-tag soft">${esc(p.gapLabel)}</div>` : ""}
      </div>
    </div>`;
    $("#depth-root").innerHTML = `
      <div class="card glow-soft">
        <h2>Depth chart <span class="aside">research projection</span></h2>
        <p class="lead">${esc(d.disclaimer)}</p>
        <p class="dim">Grounded in ${esc(d.asOfFile)}.</p>
      </div>
      <div class="war-grid">
        <article class="card dc-card">
          <h2>Offense</h2>
          ${d.offense.map(cell).join("")}
        </article>
        <article class="card dc-card">
          <h2>Defense <span class="aside">named standouts only</span></h2>
          ${d.defense.map(cell).join("")}
        </article>
      </div>
      <div class="card trade-card">
        <h2>OL plan after Jurgens</h2>
        <p>${esc(R.headlineTrade.olPlan)}</p>
        <p class="hi">${esc(R.headlineTrade.status)}</p>
        ${cite(R.headlineTrade.sources[0].file, R.headlineTrade.sources[0].urls)}
      </div>
    `;
  }

  function renderNotes(R) {
    const film = R.filmNotesLastGame;
    $("#notes-root").innerHTML = `
      <div class="card glow-pulse">
        <h2>Film notes · Week 4 vs Titans</h2>
        <p class="lead">${esc(film.game)}</p>
        <p class="dim">${esc(film.venue)} · from ${esc(film.file)}</p>
        <ul class="film-bullets">${film.bullets.map((b) => `<li><span class="tick"></span><span>${esc(b)}</span></li>`).join("")}</ul>
        ${cite(film.file, film.urls)}
        <button type="button" class="gold-btn" data-go="film" style="margin-top:12px">Open ESPN drive chart</button>
      </div>
      <div class="card">
        <h2>Lamar &amp; line · research reel</h2>
        <div class="reel-strip">
          ${R.lamarTimeline.map((e) => `<div class="reel-frame"><div class="rf-d">${esc(e.date)}</div><div class="rf-t">${esc(e.title)}</div><div class="rf-x">${esc(e.text)}</div>${cite(e.file, e.urls)}</div>`).join("")}
        </div>
      </div>
      <div class="card">
        <h2>Cam Jurgens · trade card</h2>
        <p class="lead">${esc(R.headlineTrade.title)} · ${esc(R.headlineTrade.whenEt)}</p>
        <p>${esc(R.headlineTrade.profile)} ${esc(R.headlineTrade.note)}</p>
        <p class="hi">${esc(R.headlineTrade.status)}</p>
        ${cite(R.headlineTrade.sources[0].file, R.headlineTrade.sources[0].urls)}
      </div>
      <div class="card gap-card">
        <h2>Gaps on the board</h2>
        <ul class="gap-list">${R.gaps.map((g) => `<li>${esc(g)}</li>`).join("")}</ul>
      </div>
    `;
    $$("#notes-root [data-go]").forEach((b) => b.addEventListener("click", () => showScreen(b.dataset.go)));
  }

  function nextBanner(R) {
    const el = $("#next-research-banner");
    if (!el || !R) return;
    el.innerHTML = `<div class="card research-strip">
      <h2><span class="badge-new">RESEARCH</span> Oct 7 context on top of ESPN scouting</h2>
      <div class="rs-grid">
        <div><b>Jurgens:</b> ${esc(R.headlineTrade.status)}</div>
        <div><b>Lamar:</b> ${esc(R.lamarTimeline[R.lamarTimeline.length - 1].title)} — ${esc(R.lamarTimeline[R.lamarTimeline.length - 1].text.slice(0, 140))}…</div>
        <div><b>Line journal:</b> ${esc(R.lineContext.journalMoves[R.lineContext.journalMoves.length - 1].text)}</div>
      </div>
      <p class="dim">ESPN blocks below are unchanged public data. Research strip cites Jim journals only.</p>
    </div>`;
  }

  function boot(research, scout) {
    RESEARCH = research;
    renderWar(research);
    renderInjuries(research, scout);
    renderDepth(research);
    renderNotes(research);
    nextBanner(research);
    $$("#screen-nav .sn").forEach((b) => b.addEventListener("click", () => showScreen(b.dataset.screen)));
    const want = qs.get("screen") || "war";
    showScreen(["war", "film", "next", "injuries", "depth", "notes"].includes(want) ? want : "war");
    if (!STILL) document.body.classList.add("anim-on");
    document.body.dataset.hub = "1";
  }

  function fail(m) {
    const root = $("#war-root");
    if (root) root.innerHTML = `<div class="card" style="border-color:var(--to)"><b>Research unavailable.</b> ${esc(m)}</div>`;
  }

  function load() {
    const gotR = window.__RESEARCH__
      ? Promise.resolve(window.__RESEARCH__)
      : fetch("/api/research").then((r) => (r.ok ? r.json() : Promise.reject(new Error("HTTP " + r.status))));
    const gotS = window.__SCOUT__
      ? Promise.resolve(window.__SCOUT__)
      : fetch("/api/scout").then((r) => (r.ok ? r.json() : null)).catch(() => null);
    Promise.all([gotR, gotS]).then(([r, s]) => boot(r, s)).catch((e) => fail(e.message));
  }

  window.RFRHub = { showScreen, boot };
  load();
})();
