/* Irma signal market map (C12). window.renderSignalMap(root, { state, lang, t, api, reload }).
   Scatter of every signal: x = impact (-100..+100), y = weight on the chosen horizon (0..100).
   Everything on screen is computed by the engine; this file only draws it. No innerHTML. */
(function () {
  "use strict";

  // Small string table. Used when t() has no key of that name (t() returns the key itself when missing).
  const STR = {
    en: {
      map_title: "Signal market map", map_segment: "Segment", map_region: "Region", map_class: "Signal type", map_horizon: "Time horizon",
      map_all_segments: "All segments", map_all_regions: "All regions", map_all_classes: "All types", map_years: "{n} years", map_year: "1 year",
      map_note: "Changing the time horizon recomputes the weight of every signal, so the dots move.", map_selected_horizon: "Selected horizon: {n}.",
      map_view_chart: "Chart", map_view_table: "Table", map_view: "View", map_scale: "Weight scale", map_scale_fit: "Fit to data", map_scale_full: "0 to 100",
      map_count: "{n} signals", map_none: "No signal matches these filters.", map_none_hint: "Widen the region or signal type.",
      map_q_crit: "Critical risks", map_q_strat: "Strategic opportunities", map_q_watch: "Risks to monitor", map_q_small: "Small opportunities",
      map_x_axis: "Impact (negative to positive)", map_y_axis: "Weight (small to large)", map_neg: "Negative", map_pos: "Positive",
      map_threshold: "Strong-signal threshold {n}", map_chart_label: "Scatter chart of signals by impact and weight. Use the Table view for the same data as a list.",
      map_th_signal: "Signal", map_th_region: "Region", map_th_type: "Type", map_th_weight: "Weight", map_th_impact: "Impact", map_th_group: "Group",
      map_weight: "Weight", map_impact: "Impact", map_weight_short: "Weight: {n}", map_impact_short: "Impact: {n}", map_marker: "{title}. Weight {w}, impact {i}.",
      map_source: "Source", map_published: "Published {d}", map_open_source: "Open source", map_counter: "Counter-evidence", map_counter_more: "{n} more", map_counter_none: "None recorded.",
      map_ai: "AI recommendation", map_ai_note: "A conditional analysis step. The planner decides.",
      map_ai_crit: "If a second source confirms this reading, check which relay lines depend on it and raise it at the next planning meeting.",
      map_ai_strat: "If a second source confirms this reading, check whether the scenario it supports needs a new look at the next planning meeting.",
      map_ai_watch: "Keep watching this signal. Read it again if its weight passes the threshold or if the counter-evidence weakens.",
      map_ai_small: "No action now. Note it and read it again when the next update arrives.",
      map_formulas: "How the weight is calculated", map_formulas_note: "Four formulas combine the same four conditions. The product is the weight used on the map before the time horizon is applied.",
      map_f_product: "Product (used)", map_f_minimum: "Minimum", map_f_geometric: "Geometric mean", map_f_arithmetic: "Arithmetic mean",
      map_f_used: "Weight used", map_f_horizon: "Weight on this horizon", map_f_range: "Range across formulas",
      map_assess: "Assessment log", map_assess_none: "No assessments yet.", map_assess_confirm: "Approved", map_assess_comment: "Edited", map_assess_dispute: "Rejected",
      map_approve: "Approve", map_edit: "Edit", map_reject: "Reject", map_name: "Your name", map_reason: "Reason",
      map_save_confirm: "Save approval", map_save_comment: "Save edit", map_save_dispute: "Save rejection", map_cancel: "Cancel",
      map_hint_confirm: "Approving raises the weight. Add a reason if you like.", map_hint_comment: "Add a comment or correction. The weight does not change.", map_hint_dispute: "Rejecting lowers the weight. A reason is required.",
      map_need_reason: "Write a reason first.", map_need_name: "Write your name first.", map_saved: "Saved. The weights are recalculated.", map_failed: "Could not save: {e}",
      map_empty_panel: "Select a signal to see its source, counter-evidence and recommendation.",
      map_cat_demand: "Demand", map_cat_supply: "Supply", map_cat_policy: "Policy", map_cat_price: "Price", map_cat_bullwhip: "Demand quality", map_cat_other: "Signal",
      map_label_SOURCE: "Source", map_label_DEMODATA: "Demo data", map_label_ASSUMPTION: "Assumption", map_impact_note: "Impact is an assumption: sign from direction and measure, size from materiality and theme load.",
      map_reg_FI: "Finland", map_reg_NORDICS: "Nordics", map_reg_EU: "Europe", map_reg_US: "North America", map_reg_GLOBAL: "Global",
    },
    fi: {
      map_title: "Signaalien markkinakartta", map_segment: "Segmentti", map_region: "Alue", map_class: "Signaalityyppi", map_horizon: "Aikajänne",
      map_all_segments: "Kaikki segmentit", map_all_regions: "Kaikki alueet", map_all_classes: "Kaikki tyypit", map_years: "{n} vuotta", map_year: "1 vuosi",
      map_note: "Aikajänteen muuttaminen laskee kaikkien signaalien painoarvon uudelleen, ja pisteet siirtyvät.", map_selected_horizon: "Valittu aikajänne: {n}.",
      map_view_chart: "Kaavio", map_view_table: "Taulukko", map_view: "Näkymä", map_scale: "Painoarvon asteikko", map_scale_fit: "Sovita aineistoon", map_scale_full: "0–100",
      map_count: "{n} signaalia", map_none: "Mikään signaali ei vastaa valittuja rajauksia.", map_none_hint: "Laajenna aluetta tai signaalityyppiä.",
      map_q_crit: "Kriittiset riskit", map_q_strat: "Strategiset mahdollisuudet", map_q_watch: "Seurattavat riskit", map_q_small: "Pienet mahdollisuudet",
      map_x_axis: "Vaikutus (negatiivinen – positiivinen)", map_y_axis: "Painoarvo (pieni – suuri)", map_neg: "Negatiivinen", map_pos: "Positiivinen",
      map_threshold: "Vahvan signaalin raja {n}", map_chart_label: "Hajontakaavio signaaleista vaikutuksen ja painoarvon mukaan. Taulukkonäkymä näyttää samat tiedot luettelona.",
      map_th_signal: "Signaali", map_th_region: "Alue", map_th_type: "Tyyppi", map_th_weight: "Painoarvo", map_th_impact: "Vaikutus", map_th_group: "Ryhmä",
      map_weight: "Painoarvo", map_impact: "Vaikutus", map_weight_short: "Painoarvo: {n}", map_impact_short: "Vaikutus: {n}", map_marker: "{title}. Painoarvo {w}, vaikutus {i}.",
      map_source: "Lähde", map_published: "Julkaistu {d}", map_open_source: "Avaa lähde", map_counter: "Vastatodisteet", map_counter_more: "{n} lisää", map_counter_none: "Ei kirjattuja.",
      map_ai: "Tekoälyn suositus", map_ai_note: "Ehdollinen analyysiaskel. Suunnittelija päättää.",
      map_ai_crit: "Jos toinen lähde vahvistaa tämän havainnon, selvitä, mitkä releiden tuotelinjat siitä riippuvat, ja nosta asia seuraavaan suunnittelukokoukseen.",
      map_ai_strat: "Jos toinen lähde vahvistaa tämän havainnon, selvitä, tarvitseeko sen tukema skenaario uuden tarkastelun seuraavassa suunnittelukokouksessa.",
      map_ai_watch: "Seuraa tätä signaalia. Lue se uudelleen, jos sen painoarvo ylittää rajan tai vastatodisteet heikkenevät.",
      map_ai_small: "Ei toimenpiteitä nyt. Merkitse signaali muistiin ja lue se uudelleen seuraavan päivityksen jälkeen.",
      map_formulas: "Painoarvon laskenta", map_formulas_note: "Neljä kaavaa yhdistää samat neljä ehtoa. Tulo on kartalla käytettävä painoarvo ennen aikajänteen huomioimista.",
      map_f_product: "Tulo (käytössä)", map_f_minimum: "Minimi", map_f_geometric: "Geometrinen keskiarvo", map_f_arithmetic: "Aritmeettinen keskiarvo",
      map_f_used: "Käytetty painoarvo", map_f_horizon: "Painoarvo tällä aikajänteellä", map_f_range: "Vaihteluväli kaavojen välillä",
      map_assess: "Arviointiloki", map_assess_none: "Ei vielä arvioita.", map_assess_confirm: "Hyväksytty", map_assess_comment: "Muokattu", map_assess_dispute: "Hylätty",
      map_approve: "Hyväksy", map_edit: "Muokkaa", map_reject: "Hylkää", map_name: "Nimesi", map_reason: "Perustelu",
      map_save_confirm: "Tallenna hyväksyntä", map_save_comment: "Tallenna muokkaus", map_save_dispute: "Tallenna hylkäys", map_cancel: "Peruuta",
      map_hint_confirm: "Hyväksyminen nostaa painoarvoa. Perustelu on vapaaehtoinen.", map_hint_comment: "Kirjoita kommentti tai korjaus. Painoarvo ei muutu.", map_hint_dispute: "Hylkääminen laskee painoarvoa. Perustelu vaaditaan.",
      map_need_reason: "Kirjoita ensin perustelu.", map_need_name: "Kirjoita ensin nimesi.", map_saved: "Tallennettu. Painoarvot on laskettu uudelleen.", map_failed: "Tallennus epäonnistui: {e}",
      map_empty_panel: "Valitse signaali nähdäksesi sen lähteen, vastatodisteet ja suosituksen.",
      map_cat_demand: "Kysyntä", map_cat_supply: "Saatavuus", map_cat_policy: "Sääntely", map_cat_price: "Hinta", map_cat_bullwhip: "Kysynnän laatu", map_cat_other: "Signaali",
      map_label_SOURCE: "Lähde", map_label_DEMODATA: "Esimerkkiaineisto", map_label_ASSUMPTION: "Oletus", map_impact_note: "Vaikutus on oletus: etumerkki tulee suunnasta ja mittarista, suuruus olennaisuudesta ja teemakuormasta.",
      map_reg_FI: "Suomi", map_reg_NORDICS: "Pohjoismaat", map_reg_EU: "Eurooppa", map_reg_US: "Pohjois-Amerikka", map_reg_GLOBAL: "Globaali",
    },
  };

  // Regions follow the card `region` field; a wider region includes the narrower ones inside it (same rule as the signal list).
  const REGION_INCLUDE = { ALL: null, FI: ["FI"], NORDICS: ["FI", "NORDICS"], EU: ["FI", "NORDICS", "EU"], US: ["US"], GLOBAL: ["GLOBAL"] };
  const REGION_ORDER = ["ALL", "FI", "NORDICS", "EU", "US", "GLOBAL"];
  const HORIZONS = [["12", 1], ["24", 2], ["36", 3]];
  const SVGNS = "http://www.w3.org/2000/svg";

  // View state survives reload(): filters, view, selection. The data itself always comes from ctx.state.
  const ST = { horizon: "36", region: "ALL", cls: "all", view: "chart", scale: "fit", sel: null, act: null, msg: null, err: null, name: "", reason: "" };
  try { ST.name = localStorage.getItem("irma_map_name") || ""; } catch (_) { /* storage unavailable */ }

  function h(tag, attrs, ...kids) {
    const svg = tag.startsWith("svg:");
    const el = svg ? document.createElementNS(SVGNS, tag.slice(4)) : document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v == null || v === false) continue;
      if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v);
      else if (k === "class") el.setAttribute("class", v);
      else if (k === "value" && !svg) el.value = v;
      else el.setAttribute(k, v === true ? "" : v);
    }
    for (const c of kids.flat()) if (c != null && c !== false) el.append(c.nodeType ? c : document.createTextNode(String(c)));
    return el;
  }

  window.renderSignalMap = function renderSignalMap(root, ctx) {
    const { state, lang, api, reload } = ctx;
    const LANG = lang === "fi" ? "fi" : "en";
    const own = STR[LANG];
    const T = (k, vars) => {
      let s = typeof ctx.t === "function" ? ctx.t(k) : k;
      if (s === k || Array.isArray(s) || s == null) s = own[k] != null ? own[k] : (STR.en[k] != null ? STR.en[k] : k);
      for (const [a, b] of Object.entries(vars || {})) s = s.replace(`{${a}}`, b);
      return s;
    };
    const L = (v) => (v && typeof v === "object" ? (v[LANG] || v.en || "") : (v ?? ""));
    const nf = new Intl.NumberFormat(LANG === "fi" ? "fi-FI" : "en-GB", { maximumFractionDigits: 0 });
    const nf2 = new Intl.NumberFormat(LANG === "fi" ? "fi-FI" : "en-GB", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    const signed = (n) => (n > 0 ? `+${nf.format(n)}` : n < 0 ? `−${nf.format(Math.abs(n))}` : "0");
    const fdate = (iso) => { try { return new Date(`${iso}T00:00:00`).toLocaleDateString(LANG === "fi" ? "fi-FI" : "en-GB", { day: "numeric", month: "short", year: "numeric" }); } catch (_) { return iso || ""; } };

    const meta = state.meta || {};
    const strong = Number((state.settings || {}).strong_signal_weight ?? 0.25);
    const thr = strong * 100;
    const segs = meta.segments || [];
    const segment = meta.segment || "datacenter";
    const classLabels = meta.source_classes || {};
    const classOf = (s) => L(classLabels[s.source_class]) || L(s.source_class_label) || s.source_class || "";
    const regionName = (code) => (code === "ALL" ? T("map_all_regions") : T(`map_reg_${code}`) === `map_reg_${code}` ? code : T(`map_reg_${code}`));
    const catName = (c) => { const k = `map_cat_${c}`; return own[k] ? own[k] : T("map_cat_other"); };
    const title = (s) => (LANG === "fi" ? (s.short_fi || s.name) : s.name);

    // ---- data ------------------------------------------------------------------------------
    const wOf = (s) => {
      const c = s.computed || {};
      const v = (c.horizon && c.horizon[ST.horizon] != null) ? c.horizon[ST.horizon] : c.weight;
      return Math.round((v || 0) * 1000) / 10; // 0..100, one decimal
    };
    const iOf = (s) => Math.round(((s.impact && s.impact.impact) || 0));
    const quad = (s) => {
      const hi = wOf(s) >= thr;
      const i = iOf(s);
      if (i < 0) return hi ? "crit" : "watch";
      return hi ? "strat" : "small";
    };
    const QNAME = { crit: "map_q_crit", strat: "map_q_strat", watch: "map_q_watch", small: "map_q_small" };
    const all = state.signals || [];
    const regionOk = (code) => { const inc = REGION_INCLUDE[ST.region]; return !inc || inc.includes(code); };
    let rows = [], sel = null;
    function compute() {
      rows = all.filter((s) => regionOk(s.region) && (ST.cls === "all" || s.source_class === ST.cls)).sort((a, b) => wOf(b) - wOf(a));
      if (!rows.some((s) => s.id === ST.sel)) { ST.sel = rows.length ? rows[0].id : null; ST.act = null; }
      sel = rows.find((s) => s.id === ST.sel) || null;
    }

    // ---- filter row ------------------------------------------------------------------------
    function field(label, control) { return h("label", { class: "sm-field" }, h("span", { class: "sm-field-l" }, label), control); }
    function select(opts, value, onchange) {
      const el = h("select", { class: "sm-select", onchange: (e) => onchange(e.target.value) }, opts.map(([v, l]) => h("option", { value: v, selected: v === value }, l)));
      el.value = value; return el;
    }
    const segOpts = [["all", T("map_all_segments")], ...segs.map((x) => [x.id, L(x.label)])];
    const regionsPresent = new Set(all.map((s) => s.region));
    const regionOpts = REGION_ORDER.filter((r) => r === "ALL" || regionsPresent.has(r) || r === "EU" || r === "NORDICS").map((r) => [r, regionName(r)]);
    const classOpts = [["all", T("map_all_classes")], ...Object.keys(classLabels).filter((k) => all.some((s) => s.source_class === k)).map((k) => [k, L(classLabels[k])])];
    const horizonOpts = HORIZONS.map(([k, y]) => [k, y === 1 ? T("map_year") : T("map_years", { n: y })]);

    const filters = h("div", { class: "sm-filters" },
      field(T("map_segment"), select(segOpts, segment, async (v) => {
        if (v === segment) return;
        try { await api("/api/segment", "POST", { segment: v }); ST.sel = null; await reload(); } catch (e) { ST.err = T("map_failed", { e: e.message }); draw(); }
      })),
      field(T("map_region"), select(regionOpts, ST.region, (v) => { ST.region = v; draw(); })),
      field(T("map_class"), select(classOpts, ST.cls, (v) => { ST.cls = v; draw(); })),
      field(T("map_horizon"), select(horizonOpts, ST.horizon, (v) => { ST.horizon = v; draw(); })));

    // ---- chart -----------------------------------------------------------------------------
    const W = 760, H = 500, M = { l: 62, r: 20, t: 18, b: 58 };
    const PW = W - M.l - M.r, PH = H - M.t - M.b;
    function chart() {
      const maxW = rows.reduce((m, s) => Math.max(m, wOf(s)), 0);
      const yMax = ST.scale === "full" ? 100 : Math.max(2 * thr, Math.ceil((maxW + 7) / 10) * 10);
      const padX = 4, padY = yMax * 0.09;
      const px = (i) => M.l + ((i + 100 + padX) / (200 + 2 * padX)) * PW;
      const py = (w) => M.t + PH - ((w + padY) / (yMax + padY)) * PH;
      const x0 = px(0), yT = py(thr);
      const svg = h("svg:svg", { class: "sm-svg", viewBox: `0 0 ${W} ${H}`, role: "group", "aria-label": T("map_chart_label"), focusable: "false" });
      svg.setAttribute("xmlns", SVGNS);
      // quadrant tint on the critical corner only: one accent, the rest neutral
      svg.append(h("svg:rect", { x: M.l, y: M.t, width: x0 - M.l, height: yT - M.t, class: "sm-crit-zone" }));
      // grid and ticks
      const yStep = yMax <= 50 ? 10 : 20;
      for (let v = 0; v <= yMax; v += yStep) {
        svg.append(h("svg:line", { x1: M.l, x2: W - M.r, y1: py(v), y2: py(v), class: "sm-grid" }));
        svg.append(h("svg:text", { x: M.l - 10, y: py(v) + 4, class: "sm-tick", "text-anchor": "end" }, nf.format(v)));
      }
      for (const v of [-100, -50, 0, 50, 100]) {
        svg.append(h("svg:line", { x1: px(v), x2: px(v), y1: M.t, y2: M.t + PH, class: "sm-grid" }));
        svg.append(h("svg:text", { x: px(v), y: M.t + PH + 18, class: "sm-tick", "text-anchor": "middle" }, v > 0 ? `+${v}` : v < 0 ? `−${Math.abs(v)}` : "0"));
      }
      svg.append(h("svg:rect", { x: M.l, y: M.t, width: PW, height: PH, class: "sm-frame" }));
      // midlines
      svg.append(h("svg:line", { x1: x0, x2: x0, y1: M.t, y2: M.t + PH, class: "sm-mid" }));
      svg.append(h("svg:line", { x1: M.l, x2: W - M.r, y1: yT, y2: yT, class: "sm-mid" }));
      svg.append(h("svg:text", { x: W - M.r - 8, y: yT - 6, class: "sm-thr", "text-anchor": "end" }, T("map_threshold", { n: nf.format(thr) })));
      // quadrant names
      svg.append(h("svg:text", { x: M.l + 12, y: M.t + 22, class: "sm-q sm-q-neg" }, T("map_q_crit").toUpperCase()));
      svg.append(h("svg:text", { x: W - M.r - 12, y: M.t + 22, class: "sm-q", "text-anchor": "end" }, T("map_q_strat").toUpperCase()));
      svg.append(h("svg:text", { x: M.l + 12, y: M.t + PH - 12, class: "sm-q sm-q-neg" }, T("map_q_watch").toUpperCase()));
      svg.append(h("svg:text", { x: W - M.r - 12, y: M.t + PH - 12, class: "sm-q", "text-anchor": "end" }, T("map_q_small").toUpperCase()));
      // axis titles
      svg.append(h("svg:text", { x: M.l + PW / 2, y: H - 14, class: "sm-axis", "text-anchor": "middle" }, T("map_x_axis")));
      svg.append(h("svg:text", { x: M.l, y: H - 14, class: "sm-axis sm-axis-neg" }, T("map_neg")));
      svg.append(h("svg:text", { x: W - M.r, y: H - 14, class: "sm-axis sm-axis-pos", "text-anchor": "end" }, T("map_pos")));
      svg.append(h("svg:text", { transform: `translate(15 ${M.t + PH / 2}) rotate(-90)`, class: "sm-axis", "text-anchor": "middle" }, T("map_y_axis")));

      // markers: selected last so its halo sits on top. Tab order follows weight, largest first.
      const ordered = rows.slice().sort((a, b) => (a.id === ST.sel) - (b.id === ST.sel));
      const R = 8;
      const layer = h("svg:g", {});
      const focusable = rows.map((s) => s.id);
      for (const s of ordered) {
        const w = wOf(s), i = iOf(s), cx = px(i), cy = py(w), on = s.id === ST.sel;
        const kind = i < 0 ? "neg" : i > 0 ? "pos" : "zero";
        const label = T("map_marker", { title: title(s), w: nf.format(w), i: signed(i) });
        const g = h("svg:g", {
          class: `sm-dot sm-${kind}${on ? " is-sel" : ""}`, transform: `translate(${cx.toFixed(1)} ${cy.toFixed(1)})`, tabindex: "0", role: "button",
          "aria-label": label, "aria-pressed": on ? "true" : "false", "data-id": s.id,
          onclick: () => pick(s.id),
          onkeydown: (e) => {
            if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(s.id); }
            else if (e.key === "ArrowRight" || e.key === "ArrowDown") { e.preventDefault(); stepFocus(focusable, s.id, 1); }
            else if (e.key === "ArrowLeft" || e.key === "ArrowUp") { e.preventDefault(); stepFocus(focusable, s.id, -1); }
          },
        });
        g.append(h("svg:title", {}, `${title(s)}\n${T("map_weight_short", { n: nf.format(w) })} · ${T("map_impact_short", { n: signed(i) })}`));
        if (on) g.append(h("svg:circle", { r: R + 8, class: "sm-halo" }));
        g.append(h("svg:circle", { r: R + 4, class: "sm-focus" }));
        g.append(h("svg:circle", { r: R, class: "sm-fill" }));
        // shape cue besides colour: minus inside a negative dot, plus inside a positive one
        if (kind === "neg") g.append(h("svg:path", { d: "M-3.6 0H3.6", class: "sm-glyph" }));
        else if (kind === "pos") g.append(h("svg:path", { d: "M-3.6 0H3.6M0 -3.6V3.6", class: "sm-glyph" }));
        layer.append(g);
      }
      svg.append(layer);
      return svg;
    }
    function stepFocus(ids, cur, d) {
      const i = ids.indexOf(cur); const n = ids[(i + d + ids.length) % ids.length];
      const el = root.querySelector(`.sm-dot[data-id="${n}"]`); if (el) el.focus();
    }

    // ---- table view -------------------------------------------------------------------------
    function table() {
      const bodyRows = rows.map((s) => {
        const q = quad(s), on = s.id === ST.sel, i = iOf(s);
        return h("tr", { class: on ? "is-sel" : "", "aria-selected": on ? "true" : "false" },
          h("th", { scope: "row" }, h("button", { type: "button", class: "sm-rowbtn", onclick: () => pick(s.id), "aria-pressed": on ? "true" : "false" }, title(s))),
          h("td", null, regionName(s.region)),
          h("td", null, classOf(s)),
          h("td", { class: "num" }, nf.format(wOf(s))),
          h("td", { class: `num ${i < 0 ? "sm-neg-t" : i > 0 ? "sm-pos-t" : ""}` }, signed(i)),
          h("td", null, T(QNAME[q])));
      });
      return h("div", { class: "sm-tablewrap" },
        h("table", { class: "sm-table" },
          h("thead", null, h("tr", null, h("th", { scope: "col" }, T("map_th_signal")), h("th", { scope: "col" }, T("map_th_region")), h("th", { scope: "col" }, T("map_th_type")),
            h("th", { scope: "col", class: "num" }, T("map_th_weight")), h("th", { scope: "col", class: "num" }, T("map_th_impact")), h("th", { scope: "col" }, T("map_th_group")))),
          h("tbody", null, bodyRows)));
    }

    // ---- detail panel -----------------------------------------------------------------------
    function recommendationFor(s) {
      // Use the recommended move that names this signal as a trigger, when the segment has exactly one scenario pool.
      const rec = state.recommendation;
      if (rec && !meta.scenario_segment_required) {
        const mv = (rec.moves || []).find((m) => (m.trigger_signals || []).includes(s.id));
        if (mv) return { text: L(mv.text), trigger: L(mv.trigger), fromMove: true };
      }
      const key = { crit: "map_ai_crit", strat: "map_ai_strat", watch: "map_ai_watch", small: "map_ai_small" }[quad(s)];
      return { text: T(key), fromMove: false };
    }
    function counterCards(s) {
      const ids = new Set(s.counter_evidence || []);
      return (state.evidence || []).filter((e) => ids.has(e.id) || e.against === s.id);
    }
    function annotate(action) {
      if (ST.act !== action) ST.reason = ""; ST.act = ST.act === action ? null : action; ST.err = null; ST.msg = null; draw();
      if (ST.act) { const f = root.querySelector(ST.name ? ".sm-reason" : ".sm-name"); if (f) f.focus(); }
    }
    async function submit(s, action) {
      const nameEl = root.querySelector(".sm-name"), reasonEl = root.querySelector(".sm-reason");
      const name = nameEl.value.trim(), reason = reasonEl.value.trim();
      ST.name = name; ST.reason = reason;
      if (!name) { ST.err = T("map_need_name"); draw(); root.querySelector(".sm-name").focus(); return; }
      if (action !== "confirm" && !reason) { ST.err = T("map_need_reason"); draw(); root.querySelector(".sm-reason").focus(); return; }
      try { localStorage.setItem("irma_map_name", name); } catch (_) { /* storage unavailable */ }
      try {
        await api(`/api/signals/${encodeURIComponent(s.id)}/annotate`, "POST", { action, note: reason, author: name });
        ST.act = null; ST.err = null; ST.reason = ""; ST.msg = T("map_saved");
        await reload();
      } catch (e) { ST.err = T("map_failed", { e: e.message }); draw(); }
    }
    function badge(kind, text) { return h("span", { class: `sm-badge sm-badge-${kind}` }, text); }

    function panel() {
      if (!sel) return h("aside", { class: "sm-panel", "aria-label": T("map_title") }, h("p", { class: "sm-empty" }, T("map_empty_panel")));
      const s = sel, i = iOf(s), w = wOf(s), c = s.computed || {}, methods = (c.band && c.band.methods) || {};
      const cc = counterCards(s), rec = recommendationFor(s);
      const kind = i < 0 ? "neg" : i > 0 ? "pos" : "zero";
      const showMarket = segment === "all" && s.market;
      const srcLink = s.source && s.source.url ? h("a", { class: "sm-link", href: s.source.url, target: "_blank", rel: "noopener noreferrer" }, T("map_open_source"), h("span", { "aria-hidden": "true" }, " ↗")) : null;

      const formulas = h("details", { class: "sm-disc" }, h("summary", null, T("map_formulas")),
        h("p", { class: "sm-small" }, T("map_formulas_note")),
        h("dl", { class: "sm-kv" },
          ...["product", "minimum", "geometric", "arithmetic"].flatMap((k) => methods[k] == null ? [] : [
            h("dt", { class: k === "product" ? "is-used" : "" }, T(`map_f_${k}`)),
            h("dd", { class: k === "product" ? "is-used" : "" }, nf2.format(methods[k] * 1)),
          ]),
          h("dt", { class: "sm-kv-sep" }, T("map_f_used")), h("dd", { class: "sm-kv-sep" }, nf2.format(c.weight != null ? c.weight : 0)),
          h("dt", null, T("map_f_horizon")), h("dd", null, nf2.format(w / 100)),
          c.band ? h("dt", null, T("map_f_range")) : null, c.band ? h("dd", null, `${nf2.format(c.band.min)} – ${nf2.format(c.band.max)}`) : null),
        h("p", { class: "sm-small sm-muted" }, T("map_impact_note")));

      const anns = (s.annotations || []).slice().reverse();
      const log = h("details", { class: "sm-disc" }, h("summary", null, `${T("map_assess")} (${anns.length})`),
        anns.length ? h("ul", { class: "sm-log" }, anns.map((a) => h("li", null, h("strong", null, T(`map_assess_${a.action}`) === `map_assess_${a.action}` ? a.action : T(`map_assess_${a.action}`)), ` · ${a.author || ""}, ${(a.at || "").slice(0, 10)}`, a.note ? h("div", { class: "sm-small sm-muted" }, a.note) : null))) : h("p", { class: "sm-small sm-muted" }, T("map_assess_none")));

      const act = ST.act;
      const form = act ? h("form", { class: "sm-form", onsubmit: (e) => { e.preventDefault(); submit(s, act); }, novalidate: true },
        h("p", { class: "sm-small sm-muted", id: "sm-hint" }, T(`map_hint_${act}`)),
        h("label", { class: "sm-field" }, h("span", { class: "sm-field-l" }, T("map_name")), h("input", { class: "sm-input sm-name", type: "text", autocomplete: "name", value: ST.name, required: true })),
        h("label", { class: "sm-field" }, h("span", { class: "sm-field-l" }, T("map_reason")), h("textarea", { class: "sm-input sm-reason", rows: "3", "aria-describedby": "sm-hint", value: ST.reason })),
        h("div", { class: "sm-form-row" }, h("button", { type: "submit", class: "sm-btn sm-btn-primary" }, T(`map_save_${act}`)), h("button", { type: "button", class: "sm-btn", onclick: () => annotate(act) }, T("map_cancel")))) : null;

      return h("aside", { class: "sm-panel", "aria-label": title(s) },
        h("div", { class: "sm-eyebrow" }, h("span", { class: `sm-eyedot sm-${kind}`, "aria-hidden": "true" }),
          [catName(s.category), regionName(s.region), classOf(s), showMarket ? (segs.find((x) => x.id === s.market) ? L(segs.find((x) => x.id === s.market).label) : s.market) : null].filter(Boolean).join(" · ")),
        h("h2", { class: "sm-ptitle" }, title(s)),
        h("div", { class: "sm-badges" }, badge("w", T("map_weight_short", { n: nf.format(w) })), badge(kind, T("map_impact_short", { n: signed(i) })),
          s.data_label && s.data_label !== "SOURCE" ? badge("label", T(`map_label_${s.data_label}`) === `map_label_${s.data_label}` ? s.data_label : T(`map_label_${s.data_label}`)) : null),
        h("section", { class: "sm-sec" }, h("h3", { class: "sm-h" }, T("map_source")),
          h("p", { class: "sm-src" }, (s.source && s.source.name) || ""),
          h("p", { class: "sm-small sm-muted" }, s.source && s.source.date ? T("map_published", { d: fdate(s.source.date) }) : "", srcLink ? " · " : "", srcLink)),
        h("section", { class: "sm-sec" }, h("h3", { class: "sm-h" }, T("map_counter")),
          cc.length ? [h("p", { class: "sm-body" }, cc[0].claim), cc[0].source && cc[0].source.name ? h("p", { class: "sm-small sm-muted" }, cc[0].source.name) : null,
            cc.length > 1 ? h("details", { class: "sm-disc sm-disc-in" }, h("summary", null, T("map_counter_more", { n: cc.length - 1 })), cc.slice(1).map((e) => h("div", { class: "sm-more" }, h("p", { class: "sm-body" }, e.claim), e.source && e.source.name ? h("p", { class: "sm-small sm-muted" }, e.source.name) : null))) : null]
            : h("p", { class: "sm-small sm-muted" }, T("map_counter_none"))),
        h("section", { class: "sm-ai" }, h("h3", { class: "sm-ai-h" }, T("map_ai")),
          h("p", { class: "sm-body" }, rec.text),
          rec.trigger ? h("p", { class: "sm-small sm-muted" }, rec.trigger) : null,
          h("p", { class: "sm-small sm-muted sm-ai-foot" }, T("map_ai_note"))),
        h("div", { class: "sm-actions", role: "group", "aria-label": T("map_assess") },
          h("button", { type: "button", class: `sm-btn sm-btn-primary${act === "confirm" ? " is-on" : ""}`, "aria-expanded": act === "confirm" ? "true" : "false", onclick: () => annotate("confirm") }, h("span", { "aria-hidden": "true" }, "✓ "), T("map_approve")),
          h("button", { type: "button", class: `sm-btn${act === "comment" ? " is-on" : ""}`, "aria-expanded": act === "comment" ? "true" : "false", onclick: () => annotate("comment") }, T("map_edit")),
          h("button", { type: "button", class: `sm-btn sm-btn-danger${act === "dispute" ? " is-on" : ""}`, "aria-expanded": act === "dispute" ? "true" : "false", onclick: () => annotate("dispute") }, h("span", { "aria-hidden": "true" }, "✕ "), T("map_reject"))),
        form,
        ST.err ? h("p", { class: "sm-msg sm-msg-err", role: "alert" }, ST.err) : null,
        ST.msg ? h("p", { class: "sm-msg", role: "status" }, ST.msg) : null,
        formulas, log);
    }

    // ---- assemble ---------------------------------------------------------------------------
    function pick(id) { ST.sel = id; ST.act = null; ST.reason = ""; ST.msg = null; ST.err = null; draw(id); }
    function draw(focusId) {
      compute();
      const hadFocus = root.contains(document.activeElement) ? document.activeElement : null;
      const refocus = focusId || (hadFocus && hadFocus.getAttribute && hadFocus.getAttribute("data-id"));
      const refocusSel = !refocus && hadFocus && hadFocus.classList && hadFocus.classList.contains("sm-select") ? [...hadFocus.parentNode.parentNode.children].indexOf(hadFocus.parentNode) : -1;
      const scaleToggle = ST.view === "chart" ? h("div", { class: "sm-seg", role: "group", "aria-label": T("map_scale") },
        ...[["fit", T("map_scale_fit")], ["full", T("map_scale_full")]].map(([v, l]) => h("button", { type: "button", class: `sm-seg-b${ST.scale === v ? " on" : ""}`, "aria-pressed": ST.scale === v ? "true" : "false", onclick: () => { ST.scale = v; draw(); } }, l))) : null;
      const viewToggle = h("div", { class: "sm-seg", role: "group", "aria-label": T("map_view") },
        ...[["chart", T("map_view_chart")], ["table", T("map_view_table")]].map(([v, l]) => h("button", { type: "button", class: `sm-seg-b${ST.view === v ? " on" : ""}`, "aria-pressed": ST.view === v ? "true" : "false", onclick: () => { ST.view = v; draw(); } }, l)));
      const body = rows.length ? (ST.view === "chart" ? chart() : table()) : h("div", { class: "sm-emptybox" }, h("p", { class: "sm-body" }, T("map_none")), h("p", { class: "sm-small sm-muted" }, T("map_none_hint")));
      const hz = (horizonOpts.find(([k]) => k === ST.horizon) || [])[1];
      const main = h("section", { class: "sm-main", "aria-label": T("map_title") },
        h("p", { class: "sm-note" }, h("strong", null, T("map_horizon")), ": ", T("map_note"), " ", T("map_selected_horizon", { n: hz })),
        h("div", { class: "sm-toolbar" }, h("span", { class: "sm-count", role: "status" }, T("map_count", { n: rows.length })), h("div", { class: "sm-tools" }, scaleToggle, viewToggle)),
        body);
      root.replaceChildren(h("div", { class: "sm" }, filters, h("div", { class: "sm-grid-layout" }, main, panel())));
      if (refocus) { const el = root.querySelector(`.sm-dot[data-id="${refocus}"]`) || root.querySelector(`.sm-rowbtn[aria-pressed="true"]`); if (el && ST.view) el.focus({ preventScroll: true }); }
      else if (refocusSel >= 0) { const el = root.querySelectorAll(".sm-filters .sm-select")[refocusSel]; if (el) el.focus(); }
    }
    // filters are rebuilt on every draw(), so draw() must see the same closure
    draw();
  };
})();
