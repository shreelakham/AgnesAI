// ---- state ----------------------------------------------------------------
const state = { pitch: null, imageFile: null, brand: null, lineChart: null, barChart: null };

// ---- helpers --------------------------------------------------------------
const $ = (s) => document.querySelector(s);
const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; };
const esc = (s) => (s || "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function toast(msg) { const t = $("#toast"); t.textContent = msg; t.classList.add("show"); setTimeout(() => t.classList.remove("show"), 2600); }
function busy(btn, on, label) { btn.disabled = on; btn.dataset.t = btn.dataset.t || btn.textContent; btn.innerHTML = on ? `<span class="spinner"></span>${label || "Working…"}` : btn.dataset.t; }

async function api(path, body) {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || `Request failed (${r.status})`); }
  return r.json();
}

// ---- tab nav --------------------------------------------------------------
document.querySelectorAll(".nav-item").forEach(b => b.onclick = () => {
  document.querySelectorAll(".nav-item").forEach(n => n.classList.remove("active"));
  document.querySelectorAll(".tab").forEach(t => t.classList.remove("active"));
  b.classList.add("active");
  $("#tab-" + b.dataset.tab).classList.add("active");
});
function goTab(name) { document.querySelector(`.nav-item[data-tab="${name}"]`).click(); }

function setBrandState() {
  $("#dot-brand").classList.toggle("on", !!state.brand);
  $("#pipelineState").querySelector(".ps-row").lastChild.textContent =
    state.brand ? " " + state.brand : " No brand selected";
  $("#deckEmpty").classList.toggle("hidden", !!state.pitch);
  $("#deckArea").classList.toggle("hidden", !state.pitch);
  $("#dashEmpty").classList.toggle("hidden", !!state.pitch);
  $("#dashArea").classList.toggle("hidden", !state.pitch);
}

// ---- 1. LEADS -------------------------------------------------------------
$("#findLeads").onclick = async (e) => {
  const icp = $("#icp").value.trim();
  if (!icp) return toast("Describe an ICP first.");
  busy(e.target, true, "Finding leads…");
  try {
    const data = await api("/api/leads", { icp, count: 6 });
    const box = $("#leadsResult"); box.innerHTML = "";
    (data.leads || []).forEach(l => {
      const c = el("div", "lead");
      c.innerHTML = `<span class="score">${Math.round(l.fit_score)}</span>
        <h3>${esc(l.brand)}</h3>
        <div class="meta">${esc(l.category || "")} · ${esc(l.market || "")}</div>
        <div class="reason">${esc(l.reason || "")}</div>`;
      const btn = el("button", "btn primary", "Research →");
      btn.onclick = () => { $("#brandInput").value = l.brand; goTab("research"); $("#runResearch").click(); };
      c.appendChild(btn); box.appendChild(c);
    });
    if (!data.leads || !data.leads.length) toast("No leads returned — try a more specific ICP.");
  } catch (err) { toast(err.message); }
  busy(e.target, false);
};

// ---- 2. RESEARCH ----------------------------------------------------------
$("#runResearch").onclick = async (e) => {
  const brand = $("#brandInput").value.trim();
  if (!brand) return toast("Enter a brand name.");
  busy(e.target, true, "Analysing…");
  try {
    const pitch = await api("/api/research", { brand });
    state.pitch = pitch; state.brand = pitch.brand || brand; state.imageFile = null;
    $("#imageWrap").innerHTML = "";
    renderResearch(pitch); setBrandState();
  } catch (err) { toast(err.message); }
  busy(e.target, false);
};

function renderResearch(p) {
  const box = $("#researchResult"); box.innerHTML = "";

  box.appendChild(el("div", "section-title", "WHO THEY ARE"));
  box.appendChild(el("div", "prose", esc(p.brand_summary)));
  box.appendChild(el("div", "section-title", "COMPETITIVE POSITION"));
  box.appendChild(el("div", "prose", esc(p.competitive_position)));

  box.appendChild(el("div", "section-title", "KEY COMPETITORS"));
  const chips = el("div", "chips");
  (p.likely_competitors || []).forEach(c => chips.appendChild(el("span", "chip", esc(c))));
  box.appendChild(chips);

  box.appendChild(el("div", "section-title", "GAPS"));
  const grid = el("div", "grid");
  (p.gaps || []).forEach(g => {
    const sev = (g.severity || "medium").toLowerCase();
    grid.appendChild(el("div", "gapcard",
      `<span class="badge ${sev}">${sev.toUpperCase()}</span>
       <h4>${esc(g.gap)}</h4><p>${esc(g.why_it_matters)}</p>`));
  });
  box.appendChild(grid);

  box.appendChild(el("div", "section-title", "HOW ANYMIND CLOSES THE GAPS"));
  (p.solution_mapping || []).forEach(m => {
    box.appendChild(el("div", "solrow",
      `<div class="pill">${esc(m.product)}</div>
       <div class="ga">${esc(m.gap_addressed)}</div>
       <div class="hh">${esc(m.how_it_helps)}</div>`));
  });

  const imp = p.projected_impact || {}, rev = imp.revenue_or_profit_uplift || {}, eff = imp.time_or_efficiency_gain || {};
  box.appendChild(el("div", "section-title", "PROJECTED IMPACT"));
  box.appendChild(el("div", "stats",
    `<div class="stat"><div class="big">${esc(rev.low)}–${esc(rev.high)}</div><div class="lbl">Revenue / profit uplift</div><div class="sub">${esc(rev.basis)} (${esc(rev.timeframe)})</div></div>
     <div class="stat"><div class="big">${esc(eff.low)}–${esc(eff.high)}</div><div class="lbl">Time / efficiency gain</div><div class="sub">${esc(eff.what_it_speeds_up)}</div></div>
     <div class="stat"><div class="big">${esc(imp.time_to_value)}</div><div class="lbl">Time to value</div><div class="sub">From kickoff to measurable results.</div></div>`));

  const pkg = p.recommended_package || {};
  const pk = el("div", "pkg");
  pk.innerHTML = `<div class="kicker">RECOMMENDED PACKAGE</div><h3>${esc(pkg.package_name)}</h3>
    <p>${esc(pkg.rationale)}</p><div class="chips">${(pkg.included_products || []).map(x => `<span class="chip">${esc(x)}</span>`).join("")}</div>`;
  box.appendChild(pk);

  toast("Analysis ready. Build a deck or project revenue from the sidebar.");
}

// ---- 3. DECK --------------------------------------------------------------
$("#genImage").onclick = async (e) => {
  if (!state.pitch) return;
  busy(e.target, true, "Generating image…");
  try {
    const r = await api("/api/image", { pitch: state.pitch });
    state.imageFile = r.image_file;
    $("#imageWrap").innerHTML = `<img src="${r.image_url}" alt="concept" />`;
  } catch (err) { toast(err.message); }
  busy(e.target, false);
};

$("#buildDeck").onclick = async (e) => {
  if (!state.pitch) return;
  busy(e.target, true, "Building deck…");
  try {
    const r = await api("/api/deck", { pitch: state.pitch, image_file: state.imageFile });
    const a = document.createElement("a"); a.href = r.deck_url; a.download = ""; a.click();
    toast("Deck downloaded.");
  } catch (err) { toast(err.message); }
  busy(e.target, false);
};

// ---- 4. DASHBOARD ---------------------------------------------------------
$("#runDash").onclick = async (e) => {
  if (!state.pitch) return;
  busy(e.target, true, "Projecting…");
  try {
    const data = await api("/api/dashboard", {
      pitch: state.pitch,
      assumptions: {
        start_gmv: +$("#startGmv").value,
        monthly_growth: +$("#growth").value,
        months: +$("#months").value,
      }
    });
    renderDashboard(data);
  } catch (err) { toast(err.message); }
  busy(e.target, false);
};

function renderDashboard(d) {
  const cards = $("#dashCards"); cards.innerHTML = "";
  d.strategies.forEach(s => {
    const best = s.strategy === d.recommended;
    cards.appendChild(el("div", "stratcard" + (best ? " best" : ""),
      `${best ? '<span class="tag">TOP REVENUE</span>' : ""}
       <h3>${esc(s.label)}</h3>
       <div class="total">$${s.total_revenue.toLocaleString()}</div>
       <div class="mrr">Ending MRR $${s.ending_mrr.toLocaleString()}</div>
       <div class="blurb">${esc(s.blurb)}</div>`));
  });

  const labels = d.strategies[0].monthly_revenue.map((_, i) => "M" + (i + 1));
  const colors = { "Land & Expand": "#028090", "Full Suite Now": "#1B2A41", "Performance Partnership": "#02C39A" };

  if (state.lineChart) state.lineChart.destroy();
  state.lineChart = new Chart($("#lineChart"), {
    type: "line",
    data: {
      labels,
      datasets: d.strategies.map(s => ({
        label: s.label, data: s.monthly_revenue,
        borderColor: colors[s.label] || "#028090", backgroundColor: "transparent",
        tension: .3, pointRadius: 0, borderWidth: 2
      }))
    },
    options: { responsive: true, plugins: { legend: { position: "bottom" } },
      scales: { y: { ticks: { callback: v => "$" + (v / 1000) + "k" } } } }
  });

  if (state.barChart) state.barChart.destroy();
  state.barChart = new Chart($("#barChart"), {
    type: "bar",
    data: {
      labels: d.strategies.map(s => s.label),
      datasets: [{ data: d.strategies.map(s => s.total_revenue),
        backgroundColor: d.strategies.map(s => colors[s.label] || "#028090") }]
    },
    options: { responsive: true, plugins: { legend: { display: false } },
      scales: { y: { ticks: { callback: v => "$" + (v / 1000) + "k" } } } }
  });
}

setBrandState();