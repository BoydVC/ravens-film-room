/* Ravens Film Room: renders data/film.json (live via /api/film, or inlined in the offline snapshot). ESPN data only.
   Shared helpers + the drive-chart renderer live in common.js (window.FR). */
(function () {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const { esc, qs, RAV, fmtET, qLabel, showTip, hideTip, tcol } = window.FR;

  let D, G, selDrive = null;

  function render(data) {
    D = data;
    const want = qs.get("game");
    const id = want && D.games[want] ? want : D.latest;
    $("#season-name").textContent = (D.season.season || "") + " SEASON";
    showGame(id);
    document.body.dataset.ready = "1";
  }

  function showGame(id) {
    G = D.games[id]; selDrive = null;
    document.documentElement.style.setProperty("--opp", tcol(G, G.opp));
    strip(); scoreboard(); notes(); drives(); scoring(); wp(); keyplays(); leaders(); audit(); sources();
  }

  // ---------------- season strip
  function strip() {
    $("#strip").innerHTML = D.season.games.map((g) => {
      const cls = g.completed ? `done ${g.result}` : "future";
      const r = g.completed ? `${g.result} ${g.us}-${g.them}` : fmtET(g.date, { month: "numeric", day: "numeric" });
      return `<button class="gm ${cls} ${G.id === g.id ? "sel" : ""}" data-id="${g.id}" ${g.completed && D.games[g.id] ? "" : "disabled"} title="${esc(g.status || "")}"><div class="w">WK ${g.week}</div><div class="o">${g.home ? "vs" : "@"} ${esc(g.opp)}</div><div class="r">${r}</div></button>`;
    }).join("");
    document.querySelectorAll(".gm.done").forEach((b) => b.addEventListener("click", () => { const u = new URL(location); u.searchParams.set("game", b.dataset.id); history.replaceState(null, "", u); showGame(b.dataset.id); }));
  }

  // ---------------- scoreboard
  function scoreboard() {
    const A = G.teams[G.away], H = G.teams[G.home];
    const el = $("#scoreboard");
    el.style.setProperty("--awayc", tcol(G, G.away)); el.style.setProperty("--homec", tcol(G, G.home));
    const side = (T, right) => `<div class="tm ${right ? "r" : ""} ${T.winner ? "win" : "lose"}">
      ${right ? `<div class="pts">${T.score}</div>` : ""}<div><div class="ab" style="color:${tcol(G, T.abbr)}">${esc(T.abbr)}</div><div class="nm">${esc(T.name)}</div><div class="rec">${T.record ? esc(T.record) : ""}${T.homeAway === "home" ? " · HOME" : " · AWAY"}</div></div>
      ${right ? "" : `<div class="pts">${T.score}</div>`}</div>`;
    const nq = Math.max(A.linescores.length, H.linescores.length);
    const qh = Array.from({ length: nq }, (_, i) => `<th>${i < 4 ? i + 1 : "OT"}</th>`).join("");
    const row = (T) => `<tr><th style="text-align:left;color:${tcol(G, T.abbr)}">${T.abbr}</th>${T.linescores.map((v) => `<td>${v}</td>`).join("")}<td>${T.score}</td></tr>`;
    el.innerHTML = side(A, false) + `<div class="mid"><div class="st">${esc((G.status || "").toUpperCase())} · WEEK ${G.week ?? ""}</div>
      <table class="ls"><tr><th></th>${qh}<th>T</th></tr>${row(A)}${row(H)}</table>
      <div class="meta">${fmtET(G.date, { weekday: "short", month: "short", day: "numeric", year: "numeric", hour: "numeric", minute: "2-digit" })} ET${G.venue ? " · " + esc(G.venue) : ""}${G.city ? ", " + esc(G.city) : ""}${G.attendance ? " · att. " + G.attendance.toLocaleString() : ""}</div></div>` + side(H, true);
  }

  // ---------------- film notes (computed only from ESPN fields)
  function notes() {
    const out = [];
    const fg = G.keyPlays.filter((k) => k.fgYards).sort((a, b) => b.fgYards - a.fgYards)[0];
    if (fg) out.push({ hero: fg.off === "BAL", k: `LONG FIELD GOAL · ${fg.off}`, big: `${fg.fgYards} yds`, d: `${qLabel(fg.period)} ${fg.clock}${fg.clock === "0:00" ? " (as time expired)" : ""}. “${fg.text.split(",")[0]}”` });
    const stops = G.drives.filter((d) => d.short === "DOWNS");
    stops.forEach((s) => { const nxt = G.drives[s.i + 1]; if (nxt && nxt.team !== s.team && nxt.short === "TD" && nxt.yards >= 80) out.push({ hero: nxt.team === "BAL" && !out.some((o) => o.hero), k: `STOP → ${nxt.team} TD DRIVE`, big: `${nxt.yards} yds`, d: `${s.team} turned it over on downs at ${esc(s.endText)}. Next, ${nxt.team} went ${esc(nxt.desc)} for a touchdown.` }); });
    const bal = G.drives.filter((d) => d.team === "BAL").sort((a, b) => (b.yards || 0) - (a.yards || 0))[0];
    if (bal && !out.some((o) => o.big === `${bal.yards} yds`)) out.push({ k: "RAVENS' LONGEST DRIVE", big: `${bal.yards} yds`, d: `${esc(bal.desc)}. Result: ${esc(bal.result)}. Started at ${esc(bal.startText)}, ${qLabel(bal.period)} ${bal.clock}.` });
    const sw = G.keyPlays.filter((k) => k.wpDelta != null).sort((a, b) => Math.abs(b.wpDelta) - Math.abs(a.wpDelta))[0];
    if (sw) out.push({ k: "BIGGEST WIN-PROB SWING", big: `${sw.wpDelta > 0 ? "+" : "−"}${Math.abs(sw.wpDelta * 100).toFixed(1)}%`, d: `For BAL. ${qLabel(sw.period)} ${sw.clock}: ${esc(sw.text.slice(0, 120))}${sw.text.length > 120 ? "…" : ""}` });
    const pen = G.teamStats.BAL && G.teamStats.BAL.totalPenaltiesYards;
    if (pen) out.push({ k: "RAVENS PENALTIES", big: pen, d: `Flags–yards (ESPN box score). ${G.opp}: ${esc(G.teamStats[G.opp].totalPenaltiesYards || "n/a")}.` });
    $("#notes").innerHTML = out.slice(0, 4).map((n) => `<div class="note ${n.hero ? "hero" : ""}"><div class="k">${n.k}</div><div class="big">${esc(n.big)}</div><div class="d">${n.d}</div></div>`).join("");
  }

  // ---------------- drive chart (shared renderer in common.js)
  function drives() { FR.driveChart($("#drives"), G, { drive: qs.get("drive") != null ? +qs.get("drive") : null }); }

  // ---------------- scoring timeline (step chart + list)
  const GT = (t) => t; // seconds elapsed
  function gameLen() { return Math.max(3600, ...G.drives.flatMap((d) => d.playList.map((p) => p.t || 0))); }
  function axis(W, H, L, R, T, B, len) {
    let s = ""; const X = (t) => L + (t / len) * (W - L - R);
    for (let q = 0; q <= Math.ceil(len / 900); q++) { const t = Math.min(q * 900, len); s += `<line x1="${X(t)}" x2="${X(t)}" y1="${T}" y2="${H - B}" stroke="rgba(255,255,255,.12)"/>`; if (q < Math.ceil(len / 900)) s += `<text x="${X(t + 450)}" y="${H - B + 14}" fill="#8a83b3" font-size="10.5" text-anchor="middle">${q < 4 ? "Q" + (q + 1) : "OT"}</text>`; }
    return { s, X };
  }
  function scoring() {
    const W = 640, H = 220, L = 34, R = 14, T = 12, B = 22, len = gameLen();
    const ax = axis(W, H, L, R, T, B, len); const X = ax.X;
    const max = Math.max(G.teams.BAL.score, G.teams[G.opp].score, 7);
    const Y = (v) => H - B - (v / max) * (H - T - B);
    const step = (ab) => { let pts = [[0, 0]]; G.scoring.forEach((s) => pts.push([s.t, s.score[ab]])); pts.push([len, G.teams[ab].score]); let d = `M${X(0)},${Y(0)}`; for (let i = 1; i < pts.length; i++) d += ` H${X(pts[i][0])} V${Y(pts[i][1])}`; return d; };
    let svg = `<svg viewBox="0 0 ${W} ${H}" width="100%">${ax.s}`;
    for (let v = 0; v <= max; v += 7) svg += `<text x="${L - 6}" y="${Y(v) + 4}" fill="#6d6596" font-size="10" text-anchor="end">${v}</text><line x1="${L}" x2="${W - R}" y1="${Y(v)}" y2="${Y(v)}" stroke="rgba(255,255,255,.05)"/>`;
    svg += `<path d="${step(G.opp)}" fill="none" stroke="var(--opp)" stroke-width="3"/><path d="${step("BAL")}" fill="none" stroke="${RAV}" stroke-width="3.5"/>`;
    G.scoring.forEach((s, i) => { svg += `<circle class="sdot" data-i="${i}" cx="${X(s.t)}" cy="${Y(s.score[s.team === "BAL" ? "BAL" : G.opp])}" r="6" fill="${tcol(G, s.team)}" stroke="#07060f" stroke-width="2" style="cursor:pointer"/>`; });
    svg += `</svg>`;
    $("#scoring").innerHTML = `<h2>Scoring timeline<span class="aside"><span style="color:${RAV}">━</span> BAL · <span style="color:var(--opp)">━</span> ${esc(G.opp)}</span></h2>${svg}
      ${G.scoring.map((s) => `<div class="sp"><div class="q">${qLabel(s.period)} ${esc(s.clock)}</div><div><b style="color:${tcol(G, s.team)}">${esc(s.team)}</b> ${esc(s.type)} · ${esc(s.text)}</div><div class="s">${s.score.BAL}–${s.score[G.opp]}</div></div>`).join("")}`;
    document.querySelectorAll(".sdot").forEach((c) => { c.addEventListener("mousemove", (ev) => { const s = G.scoring[+c.dataset.i]; showTip(ev, `<b>${esc(s.team)} ${esc(s.type)}</b> · ${qLabel(s.period)} ${esc(s.clock)}<br>${esc(s.text)}<br>BAL ${s.score.BAL} – ${esc(G.opp)} ${s.score[G.opp]}`); }); c.addEventListener("mouseleave", hideTip); });
  }

  // ---------------- win probability
  function wp() {
    if (!G.wp.length) { $("#wp").innerHTML = `<h2>Win probability</h2><div class="info">ESPN's summary for this game has no win-probability data, so this chart is left out.</div>`; return; }
    const W = 640, H = 260, L = 38, R = 14, T = 12, B = 22, len = gameLen();
    const ax = axis(W, H, L, R, T, B, len); const X = ax.X, Y = (p) => T + (1 - p) * (H - T - B);
    const pts = G.wp.map((w) => [X(w.t), Y(w.wp)]);
    const line = "M" + pts.map((p) => p.join(",")).join(" L");
    const area = `${line} L${pts[pts.length - 1][0]},${Y(0.5)} L${pts[0][0]},${Y(0.5)} Z`;
    let svg = `<svg viewBox="0 0 ${W} ${H}" width="100%" id="wpsvg"><defs>
      <clipPath id="cTop"><rect x="0" y="0" width="${W}" height="${Y(0.5)}"/></clipPath><clipPath id="cBot"><rect x="0" y="${Y(0.5)}" width="${W}" height="${H}"/></clipPath>
      <linearGradient id="gTop" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${RAV}" stop-opacity=".55"/><stop offset="1" stop-color="${RAV}" stop-opacity=".05"/></linearGradient>
      <linearGradient id="gBot" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="var(--opp)" stop-opacity=".55"/><stop offset="1" stop-color="var(--opp)" stop-opacity=".05"/></linearGradient></defs>${ax.s}
      ${[0, 0.25, 0.5, 0.75, 1].map((p) => `<line x1="${L}" x2="${W - R}" y1="${Y(p)}" y2="${Y(p)}" stroke="rgba(255,255,255,${p === 0.5 ? 0.3 : 0.06})" ${p === 0.5 ? 'stroke-dasharray="4 4"' : ""}/><text x="${L - 6}" y="${Y(p) + 4}" fill="#6d6596" font-size="10" text-anchor="end">${p * 100}%</text>`).join("")}
      <path d="${area}" fill="url(#gTop)" clip-path="url(#cTop)"/><path d="${area}" fill="url(#gBot)" clip-path="url(#cBot)"/>
      <path d="${line}" fill="none" stroke="#fff" stroke-width="1.8" stroke-linejoin="round"/>
      <text x="${L + 6}" y="${T + 12}" fill="${RAV}" font-size="11" font-weight="700">BAL WINS ↑</text><text x="${L + 6}" y="${H - B - 6}" fill="var(--opp)" font-size="11" font-weight="700">${esc(G.opp)} WINS ↓</text>`;
    G.keyPlays.filter((k) => k.wpF != null && k.t != null).forEach((k) => { svg += `<circle cx="${X(k.t)}" cy="${Y(k.wpF)}" r="4.5" fill="${k.tags.includes("Score") ? "#22c55e" : k.tags.includes("Turnover") || k.tags.includes("4th-down stop") ? "#ef4444" : "#e8b931"}" stroke="#07060f" stroke-width="1.5"/>`; });
    svg += `<line id="wpx" x1="0" x2="0" y1="${T}" y2="${H - B}" stroke="#e8b931" opacity="0"/><circle id="wpd" r="5" fill="#e8b931" opacity="0"/><rect id="wphit" x="${L}" y="${T}" width="${W - L - R}" height="${H - T - B}" fill="transparent"/></svg>`;
    const first = G.wp[0].wp, minW = G.wp.reduce((m, w) => (w.wp < m.wp ? w : m), G.wp[0]);
    $("#wp").innerHTML = `<h2>Win probability · BAL<span class="aside">ESPN model, ${G.wp.length} plays · hover to scrub</span></h2>${svg}
      <div class="info" style="font-size:12px;margin-top:6px">Opening BAL win probability ${(first * 100).toFixed(1)}%. Low point ${(minW.wp * 100).toFixed(1)}% (${qLabel(Math.min(5, Math.floor(minW.t / 900) + 1))}). Dots: green = score, red = turnover or stop, gold = big swing.</div>`;
    const svgEl = $("#wpsvg"), hit = $("#wphit");
    hit.addEventListener("mousemove", (ev) => {
      const r = svgEl.getBoundingClientRect(); const vx = ((ev.clientX - r.left) / r.width) * W; const t = ((vx - L) / (W - L - R)) * len;
      let best = G.wp[0]; for (const w of G.wp) if (Math.abs(w.t - t) < Math.abs(best.t - t)) best = w;
      const p = G.drives.flatMap((d) => d.playList).find((x) => x.id === best.id);
      $("#wpx").setAttribute("x1", X(best.t)); $("#wpx").setAttribute("x2", X(best.t)); $("#wpx").setAttribute("opacity", 0.7);
      $("#wpd").setAttribute("cx", X(best.t)); $("#wpd").setAttribute("cy", Y(best.wp)); $("#wpd").setAttribute("opacity", 1);
      showTip(ev, `<b>BAL ${(best.wp * 100).toFixed(1)}%</b> · ${p ? qLabel(p.period) + " " + esc(p.clock) + " · " + esc(p.off) + "<br>" + esc(p.text) : ""}`);
    });
    hit.addEventListener("mouseleave", () => { hideTip(); $("#wpx").setAttribute("opacity", 0); $("#wpd").setAttribute("opacity", 0); });
  }

  // ---------------- key plays
  function keyplays() {
    $("#keyplays").innerHTML = `<h2>Key plays<span class="aside">${G.keyPlays.length} plays · ESPN play-by-play text, verbatim</span></h2>` +
      G.keyPlays.map((k) => `<div class="kp"><div class="q">${qLabel(k.period)} ${esc(k.clock)}<div class="sc">${k.score.BAL}–${k.score[G.opp]}</div></div><div>
        ${k.tags.map((t) => `<span class="tag ${t.split(" ")[0].replace("4th-down", "stop")}">${esc(t)}${t === "WP swing" && k.wpDelta != null ? ` ${k.wpDelta > 0 ? "+" : "−"}${Math.abs(k.wpDelta * 100).toFixed(1)}%` : ""}</span>`).join("")}<span class="tag" style="color:${tcol(G, k.off)}">${esc(k.off)} ball</span>
        <div class="tx">${esc(k.text)}</div></div></div>`).join("");
  }

  // ---------------- leaders + team stats
  function leaders() {
    const col = (ab) => `<div class="ldt"><h4 style="color:${tcol(G, ab)}">${esc(G.teams[ab].name)}</h4>${(G.leaders[ab] || []).map((l) => `<div class="lr"><div class="c">${esc(l.cat)}</div><div class="n">${esc(l.name)} <span class="info">${esc(l.pos || "")}</span></div><div class="v">${esc(l.value)}</div></div>`).join("")}</div>`;
    const S = G.teamStats, a = G.away, h = G.home;
    const rows = [["totalYards", "Total yards"], ["netPassingYards", "Net passing"], ["rushingYards", "Rushing"], ["firstDowns", "First downs"], ["thirdDownEff", "3rd down"], ["possessionTime", "Possession"], ["turnovers", "Turnovers"], ["totalPenaltiesYards", "Penalties"], ["sacksYardsLost", "Sacks–yds lost"]];
    const num = (v) => { if (v == null) return null; if (/^\d+:\d+$/.test(v)) { const [m, s] = v.split(":"); return +m * 60 + +s; } if (/^\d+-\d+$/.test(v)) return +v.split("-")[0]; return parseFloat(v); };
    const ts = rows.filter(([k]) => S[a] && S[h] && S[a][k] != null && S[h][k] != null).map(([k, lab]) => { const va = num(S[a][k]), vh = num(S[h][k]); const tot = (va + vh) || 1;
      return `<div class="tsr"><div style="color:${tcol(G, a)}">${esc(S[a][k])}</div><div class="bar l"><i style="width:${(100 * va) / tot}%;background:${tcol(G, a)}"></i></div><div class="lab">${lab}</div><div class="bar"><i style="width:${(100 * vh) / tot}%;background:${tcol(G, h)}"></i></div><div class="v2" style="color:${tcol(G, h)}">${esc(S[h][k])}</div></div>`; }).join("");
    $("#leaders").innerHTML = `<h2>Box-score leaders</h2><div class="ld">${col(G.away)}${col(G.home)}</div><div class="ts"><h2 style="margin-top:6px">Team stats <span class="aside">${esc(a)} ◀ · ▶ ${esc(h)}</span></h2>${ts}</div>`;
  }

  // ---------------- audit: drive chart vs box score (same checks as tests/smoke_test.py)
  function auditRows(ab) {
    const drs = G.drives.filter((d) => d.team === ab), S = G.teamStats[ab] || {}, P = G.players[ab] || {};
    const mm = (s) => { const [m, x] = s.split(":"); return +m * 60 + +x; };
    const tot = (cat, i) => (P[cat] && P[cat].totals && P[cat].totals[i]) || "0";
    const pts = drs.reduce((s, d) => s + d.points, 0) + G.drives.filter((d) => d.team !== ab).reduce((s, d) => s + d.defPoints, 0);
    const top = drs.reduce((s, d) => s + (d.time ? mm(d.time) : 0), 0);
    return [
      ["Points (drive results)", pts, G.teams[ab].score, true],
      ["Drives", drs.length, S.totalDrives, true],
      ["Touchdown drives", drs.filter((d) => d.short === "TD").length, +tot("passing", 3) + +tot("rushing", 3), true],
      ["FG attempts", drs.filter((d) => /FG/.test(d.short || "")).length, String(tot("kicking", 0)).split("/")[1], true],
      ["Punts", drs.filter((d) => d.short === "PUNT").length, tot("punting", 0), true],
      ["Turnovers (INT/FUM drives)", drs.filter((d) => /^(INT|FUMBLE)/.test(d.short || "")).length, S.turnovers, true],
      ["Time of possession", `${Math.floor(top / 60)}:${String(top % 60).padStart(2, "0")}`, S.possessionTime, true],
      ["Offensive plays*", drs.reduce((s, d) => s + (d.plays || 0), 0), S.totalOffensivePlays, false],
      ["Yards*", drs.reduce((s, d) => s + (d.yards || 0), 0), S.totalYards, false],
    ];
  }
  function audit() {
    const tbl = (ab) => `<div><table><tr><th style="color:${tcol(G, ab)}">${esc(ab)}</th><th>Drive chart</th><th>Box score</th><th></th></tr>${auditRows(ab).map(([l, a, b, hard]) => `<tr><td>${l}</td><td>${a}</td><td>${b ?? "n/a"}</td><td>${hard ? (String(a) === String(b) ? '<span class="ok">✓ match</span>' : '<span style="color:var(--to)">✕ mismatch</span>') : '<span class="info">info</span>'}</td></tr>`).join("")}</table></div>`;
    $("#audit").innerHTML = `<h2>Film-room audit: drives vs. box score<span class="aside">Same checks as tests/smoke_test.py</span></h2><div class="au">${tbl("BAL")}${tbl(G.opp)}</div>
      <div class="info" style="font-size:12px;margin-top:8px">*Shown for information only. ESPN's drive yards include penalty yards, and its drive play counts include plays wiped out by penalties, so they aren't expected to equal the box score.</div>`;
  }

  function sources() {
    const s = G.source;
    $("#sources").innerHTML = `<b>Source:</b> ESPN public JSON. Game summary <code>${esc(s.url)}</code>, fetched ${s.fetchedAt ? fmtET(s.fetchedAt, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) + " ET" : "n/a"}. Schedule <code>${esc(D.season.source.url)}</code>, fetched ${fmtET(D.season.source.fetchedAt, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })} ET.
      ESPN game page: <a href="${esc(s.espnPage)}">${esc(s.espnPage)}</a>. Win probability is ESPN's model. Play text is ESPN's, verbatim. Nothing is estimated or filled in; missing fields are left out. Built ${fmtET(D.generatedAt, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })} ET by TokenMax. Not affiliated with the NFL or the Baltimore Ravens.`;
  }

  function fail(m) { document.getElementById("app").insertAdjacentHTML("afterbegin", `<div class="card" style="border-color:var(--to)"><b>Game data unavailable.</b> ${esc(m)}</div>`); document.body.dataset.ready = "error"; }
  if (window.__FILM__) { try { render(window.__FILM__); } catch (e) { fail(e.message); console.error(e); } }
  else fetch("/api/film").then((r) => (r.ok ? r.json() : Promise.reject(new Error("HTTP " + r.status)))).then((d) => { try { render(d); } catch (e) { fail(e.message); console.error(e); } }).catch((e) => fail(e.message));
})();
