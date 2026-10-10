/* Ravens Film Room shared helpers + the drive-chart renderer (used by the Film Room and the Scouting Report). */
(function () {
  "use strict";
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const qs = new URLSearchParams(location.search);
  const STILL = qs.has("still");
  const RES = { td: ["#22c55e", "Touchdown"], fg: ["#38bdf8", "Field goal"], punt: ["#64748b", "Punt"], to: ["#ef4444", "Turnover / downs"], miss: ["#f59e0b", "Missed FG"], end: ["#475569", "End of half/game"] };
  const RAV = "#9d7bff";
  const fmtET = (iso, o) => new Date(iso).toLocaleString("en-US", Object.assign({ timeZone: "America/New_York" }, o));
  const qLabel = (p) => (p <= 4 ? "Q" + p : "OT");
  const showTip = (ev, html) => { const tip = document.getElementById("tip"); tip.innerHTML = html; tip.style.display = "block"; const x = Math.min(ev.clientX + 14, innerWidth - 380); tip.style.left = x + "px"; tip.style.top = ev.clientY + 14 + "px"; };
  const hideTip = () => (document.getElementById("tip").style.display = "none");
  function lum(hex) { const n = parseInt(hex.slice(1), 16); const r = (n >> 16) & 255, g = (n >> 8) & 255, b = n & 255; return (0.299 * r + 0.587 * g + 0.114 * b) / 255; }
  function bright(hex, alt) { if (lum(hex) > 0.35) return hex; if (alt && lum(alt) > 0.35) return alt; const n = parseInt(hex.slice(1), 16); const m = (v) => Math.min(255, Math.round(v + (255 - v) * 0.55)); return "#" + [m((n >> 16) & 255), m((n >> 8) & 255), m(n & 255)].map((v) => v.toString(16).padStart(2, "0")).join(""); }
  const tcol = (G, ab) => (ab === "BAL" ? RAV : G.teams[ab] ? bright(G.teams[ab].color, G.teams[ab].alt) : "#cbd5e1");

  // ---------------- drive chart: driveChart(rootEl, G, {aside, drive}) — the focus team (G.focus) always attacks right
  // ---------------- drive chart
  const EZ = 56, YD = 8.2, FX = (x) => EZ + x * YD, FW = EZ * 2 + 100 * YD, ROW = 27, TOPY = 34;
  function driveChart(root, G, opt) {
    opt = opt || {}; const F = G.focus || "BAL"; const $r = (s) => root.querySelector(s), $$r = (s) => root.querySelectorAll(s);
    const n = G.drives.length, H = TOPY + n * ROW + 14;
    const LBL = 150, RGT = 250, W = LBL + FW + RGT;
    let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" class="dsvg" role="img" aria-label="Drive chart">
      <defs>${Object.entries(RES).map(([k, [c]]) => `<marker id="ah-${k}" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="2.4" markerHeight="2.4" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="${c}"/></marker>`).join("")}
      <pattern id="turf" width="${YD * 10}" height="8" patternUnits="userSpaceOnUse" x="${LBL + EZ}"><rect width="${YD * 5}" height="8" fill="#0f2a17"/><rect x="${YD * 5}" width="${YD * 5}" height="8" fill="#0d2614"/></pattern></defs>
      <g transform="translate(${LBL},0)">
      <rect x="${EZ}" y="${TOPY - 6}" width="${100 * YD}" height="${n * ROW + 12}" fill="url(#turf)" rx="4"/>
      <rect x="0" y="${TOPY - 6}" width="${EZ}" height="${n * ROW + 12}" fill="${tcol(G, F)}" opacity=".28" rx="4"/>
      <rect x="${EZ + 100 * YD}" y="${TOPY - 6}" width="${EZ}" height="${n * ROW + 12}" fill="${tcol(G, G.opp)}" opacity=".28" rx="4"/>
      <text x="${EZ / 2}" y="${TOPY + (n * ROW) / 2}" fill="${tcol(G, F)}" font-size="14" font-weight="800" text-anchor="middle" transform="rotate(-90 ${EZ / 2} ${TOPY + (n * ROW) / 2})" letter-spacing="6">${esc(F)}</text>
      <text x="${EZ * 1.5 + 100 * YD}" y="${TOPY + (n * ROW) / 2}" fill="${tcol(G, G.opp)}" font-size="14" font-weight="800" text-anchor="middle" transform="rotate(90 ${EZ * 1.5 + 100 * YD} ${TOPY + (n * ROW) / 2})" letter-spacing="6">${esc(G.opp)}</text>`;
    for (let y = 10; y < 100; y += 10) {
      const lab = y <= 50 ? y : 100 - y;
      s += `<line x1="${FX(y)}" x2="${FX(y)}" y1="${TOPY - 6}" y2="${TOPY + n * ROW + 6}" stroke="rgba(255,255,255,${y === 50 ? 0.28 : 0.12})"/><text x="${FX(y)}" y="${TOPY - 12}" fill="#8a83b3" font-size="11" text-anchor="middle">${lab}</text>`;
    }
    let lastQ = 0;
    G.drives.forEach((d, i) => {
      const y = TOPY + i * ROW + ROW / 2;
      if (d.period !== lastQ && i > 0) s += `<line x1="-${LBL}" x2="${FW + RGT}" y1="${y - ROW / 2}" y2="${y - ROW / 2}" stroke="rgba(232,185,49,.35)" stroke-dasharray="3 4"/>`;
      lastQ = d.period;
      const [c] = RES[d.cls] || RES.end;
      const x0 = FX(d.x0 ?? 0), x1 = FX(d.x1 ?? d.x0 ?? 0), len = Math.max(Math.abs(x1 - x0), 0.5);
      const tc = tcol(G, d.team);
      s += `<g class="drow" data-i="${i}">
        <rect class="hit" x="-${LBL}" y="${y - ROW / 2}" width="${W}" height="${ROW}" fill="transparent"/>
        <text x="-${LBL - 4}" y="${y + 4}" fill="#8a83b3" font-size="11">${qLabel(d.period)} ${esc(d.clock)}</text>
        <text x="-58" y="${y + 4}" fill="${tc}" font-size="12" font-weight="800">${esc(d.team)}</text>
        <text x="-14" y="${y + 4}" fill="${tc}" font-size="12" text-anchor="end">${d.team === F ? "▶" : "◀"}</text>
        <circle cx="${x0}" cy="${y}" r="3.5" fill="${tc}"/>
        <line class="dline" x1="${x0}" y1="${y}" x2="${x1}" y2="${y}" stroke="${c}" marker-end="url(#ah-${d.cls})" style="stroke-dasharray:${len};stroke-dashoffset:${STILL ? 0 : len};transition:stroke-dashoffset .55s cubic-bezier(.3,.7,.2,1) ${STILL ? 0 : i * 0.13}s"/>
        <text x="${FW + 10}" y="${y + 4}" fill="${c}" font-size="12" font-weight="700">${esc(d.short)}${d.points ? " +" + d.points : ""}</text>
        <text x="${FW + 112}" y="${y + 4}" fill="#8a83b3" font-size="11">${d.yards ?? ""}y · ${d.plays ?? ""}pl · ${esc(d.time || "")}</text>
      </g>`;
    });
    s += `</g></svg>`;
    root.innerHTML = `<h2>${opt.title || "Drive chart"}<span class="aside">${opt.aside || `Every possession on one field. ${esc(G.teams[F].short || F)} always attack ▶. Click a drive for its play-by-play.`}</span><button type="button" class="replay">▶ REPLAY</button></h2>
      <div class="legend">${Object.values(RES).map(([c, l]) => `<span><i style="background:${c}"></i>${l}</span>`).join("")}<span class="mono" style="margin-left:auto">${G.drives.length} drives · ${G.drives.filter((d) => d.team === F).length} ${esc(F)} / ${G.drives.filter((d) => d.team !== F).length} ${esc(G.opp)}</span></div>
      <div class="dwrap"><div>${s}</div><div class="ddet"></div></div>`;
    $$r(".drow").forEach((r) => {
      r.addEventListener("click", () => pickDrive(+r.dataset.i));
      r.addEventListener("mousemove", (ev) => { const d = G.drives[+r.dataset.i]; showTip(ev, `<b>${esc(d.team)} · ${esc(d.result)}</b><br>${esc(d.desc)}<br>${esc(d.startText)} → ${esc(d.endText)}<br>Score after: ${esc(F)} ${d.scoreAfter[F]}, ${esc(G.opp)} ${d.scoreAfter[G.opp]}`); });
      r.addEventListener("mouseleave", hideTip);
    });
    $r(".replay").addEventListener("click", () => animateDrives(true));
    if (!STILL) requestAnimationFrame(() => requestAnimationFrame(() => animateDrives(false)));
    const first = opt.drive != null ? opt.drive : bestDrive();
    pickDrive(first);
  function bestDrive() { // default: focus team's longest scoring drive, else first drive
    const c = G.drives.filter((d) => d.team === F && d.points > 0).sort((a, b) => (b.yards || 0) - (a.yards || 0))[0];
    return c ? c.i : 0;
  }
  function animateDrives(reset) {
    const ls = $$r(".dsvg .dline");
    if (reset) { ls.forEach((l) => { l.style.transition = "none"; l.style.strokeDashoffset = l.style.strokeDasharray; }); void document.body.offsetWidth; ls.forEach((l, i) => (l.style.transition = `stroke-dashoffset .55s cubic-bezier(.3,.7,.2,1) ${i * 0.13}s`)); }
    requestAnimationFrame(() => ls.forEach((l) => (l.style.strokeDashoffset = 0)));
  }
  function pickDrive(i) {
    const d = G.drives[i]; if (!d) return;
    $$r(".drow").forEach((r) => r.classList.toggle("sel", +r.dataset.i === i));
    const [c] = RES[d.cls] || RES.end;
    const plays = d.playList;
    const real = plays.filter((p) => !p.nonplay);
    // mini play tracker: one lane per real play
    const MW = 340, mx = (x) => 10 + (x / 100) * (MW - 20), LH = 13;
    let mini = `<svg viewBox="0 0 ${MW} ${real.length * LH + 16}" width="100%"><rect x="10" y="2" width="${MW - 20}" height="${real.length * LH + 10}" fill="#0f2a17" rx="3"/>`;
    for (let y = 10; y < 100; y += 10) mini += `<line x1="${mx(y)}" x2="${mx(y)}" y1="2" y2="${real.length * LH + 12}" stroke="rgba(255,255,255,.1)"/>`;
    real.forEach((p, k) => { if (p.x0 == null || p.x1 == null) return; const y = 9 + k * LH; const col = p.scoring ? "#22c55e" : p.turnover ? "#ef4444" : p.penalty ? "#f59e0b" : tcol(G, d.team);
      mini += `<line x1="${mx(p.x0)}" x2="${mx(p.x1) + (p.x1 === p.x0 ? 1 : 0)}" y1="${y}" y2="${y}" stroke="${col}" stroke-width="5" stroke-linecap="round"/>`; });
    mini += `</svg>`;
    $r(".ddet").innerHTML = `<h3 style="color:${tcol(G, d.team)}">${esc(G.teams[d.team].name)}</h3>
      <div class="sub"><span class="pill" style="background:${c}">${esc(d.result)}</span> ${esc(d.desc)} · ${esc(d.startText)} → ${esc(d.endText)} · ${qLabel(d.period)} ${esc(d.clock)}</div>${mini}
      ${plays.map((p) => `<div class="pl ${p.scoring ? "sc" : ""} ${p.turnover ? "to" : ""} ${p.penalty ? "pen" : ""} ${p.nonplay ? "np" : ""}"><div class="c">${qLabel(p.period)} ${esc(p.clock)}</div><div>${p.dd && !p.nonplay ? `<div class="dd">${esc(p.dd)}</div>` : ""}<div class="tx">${esc(p.text)}</div>${p.wpF != null ? `<div class="c">${esc(F)} win prob ${(p.wpF * 100).toFixed(1)}%</div>` : ""}</div></div>`).join("")}`;
  }
  return { pick: pickDrive };
  }

  window.FR = { esc, qs, STILL, RES, RAV, fmtET, qLabel, showTip, hideTip, tcol, bright, driveChart };
})();
