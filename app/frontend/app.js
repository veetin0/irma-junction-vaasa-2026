/* Irma — front end. Vanilla JS, hash routing, SVG charts. Nothing numeric is computed here except chart geometry. */
(function () {
  "use strict";
  const app = document.getElementById("app");
  const bannerSlot = document.getElementById("banner");
  let STATE = null, LAST_RUN = null, RANGE = 30, HORIZON = 36, MODE = "projection", SEARCH = "", SELECTED = null;
  const CHAT = [];
  const MOCK = { region: 0, segment: 0 };
  const REGION_OPTS = {
    en: ["All regions", "Finland", "Nordics", "Europe", "North America", "South America", "Asia", "Africa", "Oceania"],
    fi: ["Kaikki alueet", "Suomi", "Pohjoismaat", "Eurooppa", "Pohjois-Amerikka", "Etelä-Amerikka", "Aasia", "Afrikka", "Oseania"],
  };
  const SEGMENT_OPTS = {
    en: ["All segments", "Data centres", "Energy clusters", "Utility grids", "Renewable generation", "Industry and process", "E-mobility and charging", "Hydrogen and e-fuels", "Buildings"],
    fi: ["Kaikki segmentit", "Datakeskukset", "Energiaklusterit", "Sähköverkot", "Uusiutuva tuotanto", "Teollisuus ja prosessit", "Sähköinen liikenne ja lataus", "Vety ja e-polttoaineet", "Rakennukset"],
  };
  const RED = "#ff000f", GRAY = "#b9bfc7";
  const RANK_COLORS = ["#ff000f", "#2a78d6", "#1baf7a", "#4a3aa7"];
  let LANG = "en";
  try { LANG = localStorage.getItem("irma_lang") || "en"; } catch (_) { /* storage unavailable */ }

  const I18N = {
    en: { overview: "Overview", signals: "Signals", scenarios: "Scenarios", settings: "Settings", search: "Search signals, sources and scenarios",
      summaryTitle: "Current situation", signalsList: "Signals", regionFilter: "Region", segmentFilter: "Segment", preview: "Preview", previewToast: "Filter preview: not connected to the data yet", domainsRemoved: "Removed from the allowlist because Anthropic's search tool cannot access them: {d}", blockedDomains: "Not accessible to the search tool, so excluded automatically: {d}", scoutTitle: "Automatic signal search", scoutRunning: "Searching the web for new signals…", scoutIdle: "Runs on every update. Last run {a}; next update {b}.", scoutNever: "No run yet.", searchNow: "Search now", scoutSummary: "{acc} added · {rej} rejected · {s} searches · about USD {c} · {d} s", scoutCandidates: "Candidates in the last run", scoutEarlier: "Earlier runs", scoutRules: "Rules a source must pass", added: "added", rejectedWord: "rejected", failedWord: "failed", foundAuto: "found automatically", scoutFoundCount: "{n} signal(s) found automatically so far.", whySignal: "Why it is a signal", scoutSettingsTitle: "Automatic search for new signals", scoutEnabled: "Search for new signals on every update", maxCandidates: "Candidates checked per run", discoverySearches: "Searches in the discovery step", maxAge: "Maximum age of a source (days)", minGrade: "Minimum publisher grade", gradeA: "A only: primary sources", gradeAB: "A or B: primary sources and reputable press", minWeight: "Minimum weight to be added", minLoad: "Minimum effect on a scenario theme", clearFound: "Remove automatically found signals", clearConfirm: "Remove all signals added by the automatic search?", scoutCost: "Estimate: about USD 0.10–0.30 per run for discovery, plus about USD 0.20–0.55 for each candidate that reaches the full check. The update frequency sets how many runs happen a day.", scoutStarted: "Automatic search started", scoutBusy: "A search is already running", scoutDone: "Automatic search finished: {acc} added, {rej} rejected", openSignal: "Open signal", rules: ["The link must be a page the search actually returned, and the page must have been read or cited.", "The publisher must be graded {grade} or better: primary sources A, reputable press B.", "The page must show a publication date no older than {days} days.", "The item must belong to a defined theme and state how it moves relay demand or component supply.", "The quoted sentence must be found in the retrieved page text.", "The link and the headline must be new.", "A primary source must corroborate it, and a counter-evidence search is run against it.", "Its weight after counter-evidence and freshness must be at least {w}, and it must move a scenario theme by at least {load}.", "If nothing passes every rule, nothing is added."], webVerification: "Web verification", corroborated: "Corroborated", notCorroborated: "Not corroborated", primarySource: "Primary source", searchesRun: "Searches run", retrievedPages: "Pages retrieved", queries: "Queries", webVerified: "verified on the web", linkRemoved: "link removed: not among retrieved pages", counterSearch: "Counter-evidence search", foundNothing: "nothing contradicting found", webSearch: "Web search", webEnabled: "Agents may search and read the web", maxSearches: "Searches per agent call", maxFetches: "Page fetches per agent call", allowedDomains: "Allowed domains (one per line)", primaryDomains: "Primary-source domains, graded A (one per line)", webPricing: "Web search costs USD 10 per 1,000 searches plus tokens. Fetching a page has no fee; its text counts as input tokens, at most 8,000 per page. Only links the tools actually retrieved are kept.", webNeedsKey: "Active only with an API key; without one the agents run in replay mode.", mockData: "Mock data", fourTitle: "The four most likely situations", fourNote: "Selected from nine candidate situations by the current signals.",
      mostLikely: "Most likely", rankOf: "Rank {n} of 4", sinceYesterday: "since yesterday", noPrev: "no previous day", projection: "Projection", history: "History",
      m6: "6 months", y1: "1 year", y3: "3 years", d7: "7 days", d30: "30 days", d90: "90 days", all: "All", demandIdx: "Demand index", supplyIdx: "Deliverable supply index",
      idxLabel: "Index, 100 = today", probLabel: "Probability on that day (%)", openScenario: "Open scenario", detailsTitle: "Selected situation", whatHappens: "What happens",
      signalsUsed: "Signals and sources used", confirmT: "What would confirm it", refuteT: "What would refute it", implications: "What it would mean for ABB (conditional)",
      demand: "Demand", delivery: "Delivery", components: "Components", marketSummary: "Market summary", demandQuality: "Demand quality", explore: "Explore with Irma",
      openQuality: "Open the demand quality check", allNotifications: "All notifications", allSignals: "All signals", tracked: "tracked", assistant: "Irma assistant",
      greet: "Ask Irma about the market, the signals and the scenarios.", ask: "Ask anything", assistantFoot: "Answers cite signal cards. Irma does not recommend order quantities or timing; the planner decides.",
      composed: "cited, composed answers", strongSignals: "Strong signals", weakSignals: "Weak signals", importData: "Import data", signalsSub: "Contracts, prices, market news and policy. Weight reflects source reliability, recency, size of the move, counter-evidence and your assessments.",
      strongSub: "Recent, reliable and large enough to shape the ranking today.", weakSub: "Early, dated, less reliable or contested indications. They carry little weight today but can become decisive; lock the ones worth following.",
      calcFrom: "Calculated from", reliability: "reliability", freshness: "freshness", strength: "strength", counter: "counter-evidence", weight: "weight", event: "event",
      ranking: "Ranking", scenariosSub: "The four most likely situations for this run, ranked by probability.", probByDay: "Probability by day", uncertainty: "Uncertainty",
      notifications: "Notifications", markAllRead: "Mark all read", notifSub: "Major signals, large daily changes, changes of the leading scenario, and moves in tracked or price signals.",
      noNotif: "No notifications. Thresholds for what counts as a large change are set in Settings.", signal: "Signal", scenario: "Scenario", open: "Open", dismiss: "Dismiss",
      settingsSub: "Update frequency and what counts as a large change.", updates: "Updates", runCycle: "Run the update cycle", lastRun: "Last run", nextRun: "Next run", runsDone: "Runs completed",
      runNow: "Run update now", resetDemo: "Reset demonstration state", notifSettings: "Notifications", ppLabel: "Large change: daily move in a situation's probability (percentage points)",
      majorLabel: "Major signal: computed weight at or above", priceLabel: "Price signal move between the two latest observations (%)", leaderLabel: "Notify when the most likely situation changes",
      strongLabel: "Strong signal: weight at or above", halfNote: "Tracked (locked) signals use half of these thresholds.", save: "Save settings", method: "Method",
      candidates: "Candidate situations", sourcesUsed: "Sources used by the signal cards", agents: "Agents (none of them recommends)", dataLabels: "Data labels",
      observed: "Observed value", weightIn: "Weight in the scenario calculation", source: "Source", date: "Date", access: "Access", why: "Why this classification",
      howWeight: "How the weight is calculated", contribution: "Contribution to each situation", assessment: "Your assessment", confirm: "Confirm", dispute: "Dispute", comment: "Comment",
      trackedNote: "Tracked closely: checked {n} times, last {t}. Alerts at half the usual threshold.", noTracked: "No signals tracked yet. Use the lock on a signal to follow it closely: it is re-checked at every update and alerts at half the usual threshold.",
      every: "Updated every {n} min · last {a} · next {b}.", pathNote: "Red: demand index with its uncertainty band; gray: deliverable supply index. Illustrative scenario path, not a forecast.",
      histNote: "Red: selected situation; gray: the other three.", newItem: "New item", importDemo: "Import demonstration item", importPasted: "Import pasted item",
      importSub: "New data → signal detection → source and counter-evidence review → scenario update → implications → next analysis step.", nextStep: "Next analysis step", brief: "Situation brief", steps: "Processing steps",
      worldNote1: "Public signals, October 2026.", worldNote2: "Constructed downturn dataset (DEMODATA)." },
    fi: { overview: "Yleiskuva", signals: "Signaalit", scenarios: "Skenaariot", settings: "Asetukset", search: "Hae signaaleja, lähteitä ja skenaarioita",
      summaryTitle: "Nykytilanne", signalsList: "Signaalit", regionFilter: "Alue", segmentFilter: "Segmentti", preview: "Esikatselu", previewToast: "Suodattimen esikatselu: ei vielä kytketty dataan", domainsRemoved: "Poistettu sallittujen listalta, koska Anthropicin hakutyökalu ei pääse niihin: {d}", blockedDomains: "Hakutyökalu ei pääse näihin, joten ne on suljettu pois automaattisesti: {d}", scoutTitle: "Automaattinen signaalihaku", scoutRunning: "Haetaan uusia signaaleja verkosta…", scoutIdle: "Ajetaan jokaisella päivityksellä. Viimeksi {a}; seuraava päivitys {b}.", scoutNever: "Ei vielä ajoja.", searchNow: "Hae nyt", scoutSummary: "{acc} lisätty · {rej} hylätty · {s} hakua · noin {c} USD · {d} s", scoutCandidates: "Viimeisen ajon ehdokkaat", scoutEarlier: "Aiemmat ajot", scoutRules: "Säännöt, jotka lähteen on läpäistävä", added: "lisätty", rejectedWord: "hylätty", failedWord: "epäonnistui", foundAuto: "löydetty automaattisesti", scoutFoundCount: "{n} signaalia löydetty automaattisesti tähän mennessä.", whySignal: "Miksi tämä on signaali", scoutSettingsTitle: "Uusien signaalien automaattinen haku", scoutEnabled: "Hae uusia signaaleja jokaisella päivityksellä", maxCandidates: "Tarkistettavia ehdokkaita per ajo", discoverySearches: "Hakuja löytövaiheessa", maxAge: "Lähteen enimmäisikä (päivää)", minGrade: "Julkaisijan vähimmäisluokka", gradeA: "Vain A: ensisijaiset lähteet", gradeAB: "A tai B: ensisijaiset lähteet ja luotettava media", minWeight: "Lisättävän signaalin vähimmäispaino", minLoad: "Vähimmäisvaikutus skenaarioteemaan", clearFound: "Poista automaattisesti löydetyt signaalit", clearConfirm: "Poistetaanko kaikki automaattisen haun lisäämät signaalit?", scoutCost: "Arvio: noin 0,10–0,30 USD per ajo löytövaiheelle sekä noin 0,20–0,55 USD jokaisesta ehdokkaasta, joka etenee täyteen tarkistukseen. Päivitystiheys määrää ajojen määrän päivässä.", scoutStarted: "Automaattinen haku käynnistyi", scoutBusy: "Haku on jo käynnissä", scoutDone: "Automaattinen haku valmis: {acc} lisätty, {rej} hylätty", openSignal: "Avaa signaali", rules: ["Linkin on oltava sivu, jonka haku todella palautti, ja sivu on luettu tai lainattu.", "Julkaisijan luokan on oltava {grade} tai parempi: ensisijaiset lähteet A, luotettava media B.", "Sivulla on oltava julkaisupäivä, joka on enintään {days} päivää vanha.", "Tiedon on kuuluttava määriteltyyn teemaan ja kerrottava, miten se vaikuttaa relekysyntään tai komponenttien saatavuuteen.", "Lainatun lauseen on löydyttävä haetun sivun tekstistä.", "Linkin ja otsikon on oltava uusia.", "Ensisijaisen lähteen on vahvistettava tieto, ja sitä vastaan ajetaan vastanäytön haku.", "Painon vastanäytön ja tuoreuden jälkeen on oltava vähintään {w}, ja sen on liikutettava skenaarioteemaa vähintään {load}.", "Jos mikään ei läpäise kaikkia sääntöjä, mitään ei lisätä."], webVerification: "Verkkotarkistus", corroborated: "Vahvistettu", notCorroborated: "Ei vahvistettu", primarySource: "Ensisijainen lähde", searchesRun: "Hakuja", retrievedPages: "Haettuja sivuja", queries: "Haut", webVerified: "tarkistettu verkosta", linkRemoved: "linkki poistettu: ei haettujen sivujen joukossa", counterSearch: "Vastanäytön haku", foundNothing: "kumoavaa ei löytynyt", webSearch: "Verkkohaku", webEnabled: "Agentit saavat hakea ja lukea verkkoa", maxSearches: "Hakuja per agenttikutsu", maxFetches: "Sivunhakuja per agenttikutsu", allowedDomains: "Sallitut verkkotunnukset (yksi per rivi)", primaryDomains: "Ensisijaisten lähteiden verkkotunnukset, luokka A (yksi per rivi)", webPricing: "Verkkohaku maksaa 10 USD per 1 000 hakua sekä tokenit. Sivun haulla ei ole maksua; sen teksti lasketaan syötetokeneiksi, enintään 8 000 per sivu. Vain työkalujen oikeasti hakemat linkit säilytetään.", webNeedsKey: "Toimii vain API-avaimella; ilman sitä agentit toimivat toistotilassa.", mockData: "Testidata", fourTitle: "Neljä todennäköisintä tilannetta", fourNote: "Valittu yhdeksästä ehdokastilanteesta nykyisten signaalien perusteella.",
      mostLikely: "Todennäköisin", rankOf: "Sija {n}/4", sinceYesterday: "eilisestä", noPrev: "ei edellistä päivää", projection: "Ennuste", history: "Historia",
      m6: "6 kuukautta", y1: "1 vuosi", y3: "3 vuotta", d7: "7 päivää", d30: "30 päivää", d90: "90 päivää", all: "Kaikki", demandIdx: "Kysyntäindeksi", supplyIdx: "Toimituskyvyn indeksi",
      idxLabel: "Indeksi, 100 = tänään", probLabel: "Todennäköisyys kyseisenä päivänä (%)", openScenario: "Avaa skenaario", detailsTitle: "Valittu tilanne", whatHappens: "Mitä tapahtuu",
      signalsUsed: "Käytetyt signaalit ja lähteet", confirmT: "Mikä vahvistaisi tämän", refuteT: "Mikä kumoaisi tämän", implications: "Mitä se tarkoittaisi ABB:lle (ehdollinen)",
      demand: "Kysyntä", delivery: "Toimitus", components: "Komponentit", marketSummary: "Markkinakatsaus", demandQuality: "Kysynnän laatu", explore: "Tutki Irman kanssa",
      openQuality: "Avaa kysynnän laadun tarkistus", allNotifications: "Kaikki ilmoitukset", allSignals: "Kaikki signaalit", tracked: "seurattu", assistant: "Irma-avustaja",
      greet: "Kysy Irmalta markkinasta, signaaleista ja skenaarioista.", ask: "Kysy mitä tahansa", assistantFoot: "Vastaukset viittaavat signaalikortteihin. Irma ei suosittele tilausmääriä tai ajoitusta; päätös on suunnittelijan.",
      composed: "viitatut, koostetut vastaukset", strongSignals: "Vahvat signaalit", weakSignals: "Heikot signaalit", importData: "Tuo dataa", signalsSub: "Sopimukset, hinnat, markkinauutiset ja sääntely. Paino heijastaa lähteen luotettavuutta, tuoreutta, muutoksen kokoa, vastanäyttöä ja arvioitasi.",
      strongSub: "Tuoreita, luotettavia ja riittävän suuria muokkaamaan järjestystä tänään.", weakSub: "Varhaisia, vanhentuneita, epävarmempia tai kiistettyjä merkkejä. Niillä on vähän painoa tänään, mutta ne voivat muuttua ratkaiseviksi; lukitse seurattavat.",
      calcFrom: "Laskettu lähteestä", reliability: "luotettavuus", freshness: "tuoreus", strength: "voimakkuus", counter: "vastanäyttö", weight: "paino", event: "tapahtuma",
      ranking: "Järjestys", scenariosSub: "Tämän ajon neljä todennäköisintä tilannetta todennäköisyysjärjestyksessä.", probByDay: "Todennäköisyys päivittäin", uncertainty: "Epävarmuus",
      notifications: "Ilmoitukset", markAllRead: "Merkitse kaikki luetuiksi", notifSub: "Merkittävät signaalit, suuret päivämuutokset, johtavan skenaarion vaihtumiset sekä seurattujen ja hintasignaalien liikkeet.",
      noNotif: "Ei ilmoituksia. Suuren muutoksen rajat asetetaan Asetuksissa.", signal: "Signaali", scenario: "Skenaario", open: "Avaa", dismiss: "Sulje",
      settingsSub: "Päivitystiheys ja mikä lasketaan suureksi muutokseksi.", updates: "Päivitykset", runCycle: "Aja päivityskierros", lastRun: "Viimeisin ajo", nextRun: "Seuraava ajo", runsDone: "Ajoja tehty",
      runNow: "Aja päivitys nyt", resetDemo: "Palauta esittelytila", notifSettings: "Ilmoitukset", ppLabel: "Suuri muutos: tilanteen todennäköisyyden päivämuutos (prosenttiyksikköä)",
      majorLabel: "Merkittävä signaali: laskettu paino vähintään", priceLabel: "Hintasignaalin liike kahden viimeisimmän havainnon välillä (%)", leaderLabel: "Ilmoita, kun todennäköisin tilanne vaihtuu",
      strongLabel: "Vahva signaali: paino vähintään", halfNote: "Seuratut (lukitut) signaalit käyttävät puolta näistä rajoista.", save: "Tallenna asetukset", method: "Menetelmä",
      candidates: "Ehdokastilanteet", sourcesUsed: "Signaalikorttien lähteet", agents: "Agentit (yksikään ei suosittele)", dataLabels: "Datan merkinnät",
      observed: "Havaittu arvo", weightIn: "Paino skenaariolaskennassa", source: "Lähde", date: "Päivä", access: "Saatavuus", why: "Miksi tämä luokitus",
      howWeight: "Miten paino lasketaan", contribution: "Vaikutus kuhunkin tilanteeseen", assessment: "Oma arviosi", confirm: "Vahvista", dispute: "Kiistä", comment: "Kommentoi",
      trackedNote: "Seurataan tarkasti: tarkistettu {n} kertaa, viimeksi {t}. Hälytykset puolella tavallisesta rajasta.", noTracked: "Ei vielä seurattuja signaaleja. Lukitse signaali seurataksesi sitä tarkasti: se tarkistetaan joka päivityksessä ja hälyttää puolella tavallisesta rajasta.",
      every: "Päivitetään {n} min välein · viimeksi {a} · seuraava {b}.", pathNote: "Punainen: kysyntäindeksi epävarmuusvyöhykkeineen; harmaa: toimituskyvyn indeksi. Havainnollistava skenaariopolku, ei ennuste.",
      histNote: "Punainen: valittu tilanne; harmaa: kolme muuta.", newItem: "Uusi tieto", importDemo: "Tuo esimerkkitieto", importPasted: "Tuo liitetty tieto",
      importSub: "Uusi data → signaalin tunnistus → lähde- ja vastanäyttötarkastus → skenaariopäivitys → vaikutukset → seuraava analyysiaskel.", nextStep: "Seuraava analyysiaskel", brief: "Tilannekatsaus", steps: "Käsittelyvaiheet",
      worldNote1: "Julkiset signaalit, lokakuu 2026.", worldNote2: "Rakennettu laskusuhdanneaineisto (DEMODATA)." },
  };
  const t = (k, vars) => { let s = (I18N[LANG] && I18N[LANG][k]) || I18N.en[k] || k; if (Array.isArray(s)) return s; for (const [a, b] of Object.entries(vars || {})) s = s.replace(`{${a}}`, b); return s; };
  const L = (v) => (v && typeof v === "object" && !Array.isArray(v) ? (v[LANG] || v.en || "") : (v ?? ""));
  const sShort = (s) => (LANG === "fi" ? (s.short_fi || s.short) : s.short);

  // ---------- helpers ----------
  function h(tag, attrs, ...children) {
    const el = tag.startsWith("svg:") ? document.createElementNS("http://www.w3.org/2000/svg", tag.slice(4)) : document.createElement(tag);
    if (attrs) for (const [k, v] of Object.entries(attrs)) {
      if (v === null || v === undefined || v === false) continue;
      if (k === "class") el.setAttribute("class", v);
      else if (k === "style" && typeof v === "object") Object.assign(el.style, v);
      else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2), v);
      else el.setAttribute(k, v);
    }
    for (const c of children.flat()) { if (c === null || c === undefined || c === false) continue; el.append(c instanceof Node ? c : document.createTextNode(String(c))); }
    return el;
  }
  const pct = (x) => (x == null ? "—" : `${Math.round(x * 100)}%`);
  const pp = (x) => (x == null ? "" : `${x >= 0 ? "+" : "−"}${Math.abs(x).toFixed(1)} pp`);
  const f2 = (x) => (x == null ? "—" : Number(x).toFixed(2));
  const num = (x) => (x == null ? "—" : Number(x).toLocaleString(LANG === "fi" ? "fi-FI" : "en-GB", { maximumFractionDigits: 1 }));
  const timeOf = (iso) => (iso ? iso.slice(11, 16) : "—");
  const dateOf = (iso) => (iso ? iso.slice(0, 10) : "—");
  function toast(msg) { const el = document.getElementById("toast"); el.textContent = msg; el.classList.add("show"); setTimeout(() => el.classList.remove("show"), 2000); }
  async function api(path, method, body) {
    const r = await fetch(path, { method: method || "GET", headers: body ? { "Content-Type": "application/json" } : undefined, body: body ? JSON.stringify(body) : undefined });
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.status);
    return r.json();
  }
  function cites(text) {
    const frag = document.createDocumentFragment(); const re = /\[?(SIG-\d{3})\]?/g; let last = 0, m;
    while ((m = re.exec(text))) { frag.append(text.slice(last, m.index)); frag.append(h("a", { class: "cite", href: `#/signal/${m[1]}` }, m[1])); last = re.lastIndex; }
    frag.append(text.slice(last)); return frag;
  }
  // Minimal, safe rendering of model text: paragraphs, "- " lists, **bold**, *italic*, signal links. No innerHTML.
  function inlineRich(text) {
    const frag = document.createDocumentFragment(); const re = /\*\*([^*]+)\*\*|\*([^*\n]+)\*/g; let last = 0, m;
    while ((m = re.exec(text))) {
      frag.append(cites(text.slice(last, m.index)));
      frag.append(m[1] !== undefined ? h("strong", null, cites(m[1])) : h("em", null, cites(m[2])));
      last = re.lastIndex;
    }
    frag.append(cites(text.slice(last))); return frag;
  }
  function rich(text) {
    const wrap = h("div", { class: "rich" }); let list = null;
    for (const raw of String(text || "").split("\n")) {
      const line = raw.trim();
      if (!line) { list = null; continue; }
      const item = line.match(/^(?:[-*\u2022]|\d+[.)])\s+(.*)$/);
      if (item) { if (!list) { list = h("ul"); wrap.append(list); } list.append(h("li", null, inlineRich(item[1]))); continue; }
      list = null;
      const head = line.match(/^#{1,4}\s+(.*)$/);
      wrap.append(head ? h("p", null, h("strong", null, inlineRich(head[1]))) : h("p", null, inlineRich(line)));
    }
    return wrap;
  }
  const scById = (id) => STATE.scenarios.scenarios.find((s) => s.id === id);
  const scColor = (id) => RANK_COLORS[Math.max(0, STATE.scenarios.scenarios.findIndex((s) => s.id === id))] || GRAY;
  const dot = (id) => h("span", { class: "sc-dot", style: { "--sc": scColor(id) } });
  const svgIcon = (inner, vb, cls) => { const s = document.createElementNS("http://www.w3.org/2000/svg", "svg"); s.setAttribute("viewBox", vb || "0 0 16 16"); if (cls) s.setAttribute("class", cls); s.innerHTML = inner; return s; };
  const lockIcon = () => svgIcon('<rect x="3" y="7" width="10" height="7" rx="1.5" fill="none" stroke="currentColor" stroke-width="1.5"/><path d="M5 7V5a3 3 0 0 1 6 0v2" fill="none" stroke="currentColor" stroke-width="1.5"/>');
  const wrenchIcon = () => svgIcon('<path d="M21.7 6.3a6 6 0 0 1-7.4 7.4L7 21l-4-4 7.3-7.3a6 6 0 0 1 7.4-7.4l-3.6 3.6 1 3 3 1z" fill="currentColor"/>', "0 0 24 24", "ico-wrench");
  const chevIcon = () => svgIcon('<path d="M4 6l4 4 4-4" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>');
  const sendIcon = () => svgIcon('<path d="M8 13V3M4 7l4-4 4 4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>');
  function lockBtn(sig) {
    return h("button", { class: `lock ${sig.locked ? "on" : ""}`, title: sig.locked ? "Tracked closely. Click to stop tracking." : "Track this signal closely", "aria-pressed": sig.locked ? "true" : "false",
      onclick: async (e) => { e.preventDefault(); e.stopPropagation(); await api(`/api/signals/${sig.id}/lock`, "POST", { locked: !sig.locked }); toast(sig.locked ? "Tracking stopped" : "Signal tracked"); await load(); route(); } }, lockIcon());
  }
  function deltaEl(x) { if (x == null) return h("span", { class: "delta muted" }, t("noPrev")); const cls = Math.abs(x) < 0.05 ? "muted" : x > 0 ? "pos" : "neg"; return h("span", { class: `delta ${cls}` }, `${pp(x)} ${t("sinceYesterday")}`); }
  function pill(text, cls) { return h("span", { class: `pill ${cls || ""}` }, text); }
  const labelPill = (l) => pill(l, l === "SOURCE" ? "ok" : l === "DEMODATA" ? "warn" : "");
  function disc(title, body, open) { return h("details", { class: "disc", open: open ? "" : null }, h("summary", null, title), h("div", { class: "disc-body" }, body)); }
  const nTitle = (n) => (LANG === "fi" ? (n.title_fi || n.title) : n.title);
  const nText = (n) => (LANG === "fi" ? (n.text_fi || n.text) : n.text);
  function monthLabel(m) { const d = new Date(STATE.meta.today + "T00:00:00"); d.setMonth(d.getMonth() + m); return `${String(d.getMonth() + 1).padStart(2, "0")}/${String(d.getFullYear()).slice(2)}`; }

  // ---------- mock filters (preview only: they change the label, not the data) ----------
  function mockFilters() {
    const dd = (key, labelKey, opts) => {
      const label = h("span", { class: "dd-value" }, opts[MOCK[key]]);
      const menu = h("div", { class: "dd-menu", role: "listbox", hidden: "" });
      const renderMenu = () => menu.replaceChildren(...opts.map((o, i) => h("button", { class: `dd-opt ${MOCK[key] === i ? "on" : ""}`, role: "option", "aria-selected": MOCK[key] === i ? "true" : "false",
        onclick: (e) => { e.stopPropagation(); MOCK[key] = i; label.textContent = o; renderMenu(); menu.hidden = true; toast(t("previewToast")); } }, o)));
      renderMenu();
      const btn = h("button", { class: "dd-btn", "aria-haspopup": "listbox", onclick: (e) => { e.stopPropagation(); const wasHidden = menu.hidden; document.querySelectorAll(".dd-menu").forEach((m) => { m.hidden = true; }); menu.hidden = !wasHidden; } },
        h("span", { class: "dd-label" }, `${t(labelKey)}:`), label, h("span", { class: "dd-caret" }, chevIcon()));
      return h("div", { class: "dd" }, btn, menu);
    };
    return h("div", { class: "mock-filters" }, dd("region", "regionFilter", REGION_OPTS[LANG]), dd("segment", "segmentFilter", SEGMENT_OPTS[LANG]), pill(t("preview"), "warn"));
  }
  document.addEventListener("click", () => document.querySelectorAll(".dd-menu").forEach((m) => { m.hidden = true; }));

  // ---------- charts ----------
  function sparkline(values, color) {
    const w = 160, hh = 44, pad = 3; const svg = h("svg:svg", { class: "spark", viewBox: `0 0 ${w} ${hh}`, preserveAspectRatio: "none", "aria-hidden": "true" });
    const v = values.filter((x) => typeof x === "number"); if (v.length < 2) return svg;
    const mn = Math.min(...v), mx = Math.max(...v), sp = mx - mn || 1;
    const pts = v.map((y, i) => [pad + (i * (w - 2 * pad)) / (v.length - 1), hh - pad - ((y - mn) / sp) * (hh - 2 * pad)]);
    svg.append(h("svg:path", { d: "M" + pts.map((p) => p.join(",")).join(" L"), fill: "none", stroke: color || RED, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
    const lp = pts[pts.length - 1]; svg.append(h("svg:circle", { cx: lp[0], cy: lp[1], r: 3.5, fill: color || RED, stroke: "#fff", "stroke-width": 2 }));
    return svg;
  }
  function lineChart(dates, series, opts) {
    const W = 720, H = opts.height || 260, m = { t: 16, r: 56, b: 30, l: 42 };
    const svg = h("svg:svg", { class: "chart", viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": opts.label || "chart" });
    const n = dates.length; const all = series.flatMap((s) => s.values).concat(opts.band ? opts.band.lower.concat(opts.band.upper) : []).filter((v) => typeof v === "number");
    const yMin = opts.yMin ?? Math.min(...all), yMax = opts.yMax ?? Math.max(...all);
    const x = (i) => m.l + (i * (W - m.l - m.r)) / Math.max(1, n - 1);
    const y = (v) => m.t + (H - m.t - m.b) * (1 - (v - yMin) / ((yMax - yMin) || 1));
    const grid = h("svg:g", { class: "grid" });
    for (let i = 0; i <= 4; i++) { const v = yMin + ((yMax - yMin) * i) / 4; grid.append(h("svg:line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v) })); grid.append(h("svg:text", { x: m.l - 6, y: y(v) + 4, "text-anchor": "end" }, opts.fmt ? opts.fmt(v) : Math.round(v))); }
    svg.append(grid);
    const step = Math.max(1, Math.ceil(n / 6));
    dates.forEach((d, i) => { if ((i % step === 0 && i < n - 1 - step / 2) || i === n - 1) svg.append(h("svg:text", { x: x(i), y: H - 8, "text-anchor": i === n - 1 ? "end" : "middle" }, d)); });
    if (opts.yLabel) svg.append(h("svg:text", { x: m.l, y: 10, "text-anchor": "start" }, opts.yLabel));
    if (opts.band) {
      const up = opts.band.upper.map((v, i) => [x(i), y(v)]), lo = opts.band.lower.map((v, i) => [x(i), y(v)]).reverse();
      svg.append(h("svg:path", { d: "M" + up.concat(lo).map((p) => p.join(",")).join(" L") + " Z", fill: opts.band.color || RED, "fill-opacity": 0.1 }));
    }
    series.forEach((s) => {
      const pts = s.values.map((v, i) => (typeof v === "number" ? [x(i), y(v)] : null)).filter(Boolean);
      svg.append(h("svg:path", { d: "M" + pts.map((p) => p.join(",")).join(" L"), fill: "none", stroke: s.color, "stroke-width": s.emph ? 2.5 : 1.6, "stroke-dasharray": s.dash ? "5 4" : null, "stroke-linejoin": "round", "stroke-linecap": "round" }));
      const lp = pts[pts.length - 1]; if (lp) { if (s.emph) svg.append(h("svg:circle", { cx: lp[0], cy: lp[1], r: 4, fill: s.color, stroke: "#fff", "stroke-width": 2 })); if (s.end) svg.append(h("svg:text", { x: lp[0] + 8, y: lp[1] + 4, style: s.emph ? "fill:#000;font-weight:600" : "" }, s.end)); }
    });
    const cross = h("svg:line", { x1: 0, x2: 0, y1: m.t, y2: H - m.b, stroke: "#8a93a0", "stroke-width": 1, style: "display:none" }); svg.append(cross);
    const tip = h("div", { class: "tooltip" }); document.body.append(tip);
    const hit = h("svg:rect", { x: m.l, y: m.t, width: W - m.l - m.r, height: H - m.t - m.b, fill: "transparent" });
    hit.addEventListener("pointermove", (ev) => {
      const r = svg.getBoundingClientRect(); const px = ((ev.clientX - r.left) / r.width) * W;
      const i = Math.max(0, Math.min(n - 1, Math.round(((px - m.l) / (W - m.l - m.r)) * (n - 1))));
      cross.setAttribute("x1", x(i)); cross.setAttribute("x2", x(i)); cross.style.display = "";
      tip.replaceChildren(h("div", { class: "muted" }, dates[i]), ...series.map((s) => h("div", { class: "tt-row" }, h("span", null, h("span", { style: { background: s.color, display: "inline-block", width: "12px", height: "3px", verticalAlign: "middle", marginRight: "6px" } }), s.name), h("strong", null, opts.fmt ? opts.fmt(s.values[i]) : num(s.values[i])))));
      tip.style.display = "block"; tip.style.left = `${ev.clientX + 12}px`; tip.style.top = `${ev.clientY + 12}px`;
    });
    hit.addEventListener("pointerleave", () => { cross.style.display = "none"; tip.style.display = "none"; });
    svg.append(hit);
    return h("div", null, svg, opts.legend === false ? null : h("div", { class: "legend" }, ...series.map((s) => h("span", null, h("span", { class: "key", style: { background: s.color } }), s.name))));
  }
  function projectionChart(sc, months, height) {
    const n = months + 1; const p = sc.path;
    const dates = p.months.slice(0, n).map(monthLabel);
    const series = [{ name: t("supplyIdx"), values: p.supply.slice(0, n), color: GRAY, dash: true }, { name: t("demandIdx"), values: p.demand.slice(0, n), color: RED, emph: true, end: String(Math.round(p.demand[n - 1])) }];
    const lo = Math.min(...p.lower.slice(0, n), ...p.supply.slice(0, n)), hi = Math.max(...p.upper.slice(0, n), ...p.supply.slice(0, n));
    return lineChart(dates, series, { yMin: Math.floor((lo - 5) / 10) * 10, yMax: Math.ceil((hi + 5) / 10) * 10, fmt: (v) => Math.round(v), yLabel: t("idxLabel"), band: { lower: p.lower.slice(0, n), upper: p.upper.slice(0, n), color: RED }, label: "Scenario path", height });
  }
  function historyChart(selId, height) {
    const pts = RANGE ? STATE.history.points.slice(-RANGE) : STATE.history.points;
    const dates = pts.map((p) => p.date.slice(5));
    const ids = STATE.scenarios.scenarios.map((s) => s.id);
    const series = ids.filter((id) => id !== selId).map((id) => ({ name: L(scById(id).name), values: pts.map((p) => (p.probs[id] == null ? null : p.probs[id] * 100)), color: GRAY }));
    series.push({ name: L(scById(selId).name), values: pts.map((p) => (p.probs[selId] == null ? null : p.probs[selId] * 100)), color: RED, emph: true, end: pct(scById(selId).probability) });
    return lineChart(dates, series, { yMin: 0, yMax: 80, fmt: (v) => `${Math.round(v)}%`, yLabel: t("probLabel"), label: "Daily probability", legend: false, height });
  }
  function miniChart(sc) {
    const w = 200, hh = 64, pad = 4; const n = HORIZON + 1; const p = sc.path;
    const d = p.demand.slice(0, n), up = p.upper.slice(0, n), lo = p.lower.slice(0, n), su = p.supply.slice(0, n);
    const mn = Math.min(...lo, ...su), mx = Math.max(...up, ...su), sp = mx - mn || 1;
    const X = (i) => pad + (i * (w - 2 * pad)) / (n - 1), Y = (v) => hh - pad - ((v - mn) / sp) * (hh - 2 * pad);
    const svg = h("svg:svg", { viewBox: `0 0 ${w} ${hh}`, preserveAspectRatio: "none", "aria-hidden": "true" });
    svg.append(h("svg:path", { d: "M" + up.map((v, i) => `${X(i)},${Y(v)}`).join(" L") + " L" + lo.map((v, i) => `${X(i)},${Y(v)}`).reverse().join(" L") + " Z", fill: RED, "fill-opacity": 0.1 }));
    svg.append(h("svg:path", { d: "M" + su.map((v, i) => `${X(i)},${Y(v)}`).join(" L"), fill: "none", stroke: GRAY, "stroke-width": 1.5, "stroke-dasharray": "4 3" }));
    svg.append(h("svg:path", { d: "M" + d.map((v, i) => `${X(i)},${Y(v)}`).join(" L"), fill: "none", stroke: RED, "stroke-width": 2 }));
    return svg;
  }
  function diverging(contribs) {
    const max = Math.max(...contribs.map((c) => Math.abs(c.contribution)), 0.0001);
    return h("div", { class: "div-rows" }, ...contribs.map((c) => h("div", { class: "div-row" }, h("a", { class: "link", href: `#/signal/${c.signal_id}` }, c.signal_name), h("div", { class: "div-track" }, h("div", { class: `div-fill ${c.contribution >= 0 ? "pos" : "neg"}`, style: { width: `${(Math.abs(c.contribution) / max) * 50}%` } })), h("span", { class: "num" }, (c.contribution >= 0 ? "+" : "") + f2(c.contribution)))));
  }

  // ---------- banner & notifications ----------
  function renderBanner() {
    bannerSlot.replaceChildren();
    const unread = STATE.notifications.filter((n) => !n.read && (n.severity === "high" || n.severity === "medium"));
    const top = unread[0];
    if (!top) return;
    const target = top.signal_id ? `#/signal/${top.signal_id}` : top.scenario_id ? `#/scenarios/${top.scenario_id}` : "#/notifications";
    const more = unread.length - 1;
    bannerSlot.append(h("details", { class: "notice" },
      h("summary", null, h("span", { class: `n-dot ${top.severity}` }), h("span", { class: "n-title" }, nTitle(top)), more > 0 ? h("span", { class: "n-count" }, `+${more}`) : null, h("span", { class: "chev" }, chevIcon())),
      h("div", { class: "n-body" }, h("div", null, nText(top)),
        h("div", { class: "n-actions" }, h("a", { class: "btn sm", href: target }, t("open")), h("button", { class: "btn sm", onclick: async () => { await api(`/api/notifications/${top.id}/read`, "POST"); await load(); } }, t("dismiss")), more > 0 ? h("a", { class: "link small", href: "#/notifications", style: { alignSelf: "center" } }, `${t("allNotifications")} →`) : null))));
  }
  function notifList(items, limit) {
    const list = limit ? items.slice(0, limit) : items;
    if (!list.length) return h("div", { class: "empty" }, t("noNotif"));
    return h("div", { class: "rows" }, ...list.map((n) => h("div", { class: `notif ${n.read ? "read" : ""}` }, h("span", { class: `sev ${n.severity}` }),
      h("div", null, h("div", { class: "r-title" }, nTitle(n)), h("div", { class: "r-sub" }, nText(n)), h("div", { class: "tiny" }, `${dateOf(n.time)} ${timeOf(n.time)} · ${n.kind.replace(/_/g, " ")}`)),
      h("div", null, n.signal_id ? h("a", { class: "btn sm", href: `#/signal/${n.signal_id}` }, t("signal")) : n.scenario_id ? h("a", { class: "btn sm", href: `#/scenarios/${n.scenario_id}` }, t("scenario")) : null))));
  }

  // ---------- assistant ----------
  function assistantPanel() {
    const body = h("div", { class: "a-body" });
    const input = h("input", { type: "text", placeholder: t("ask"), "aria-label": "Ask Irma", onkeydown: (e) => { if (e.key === "Enter") send(input.value); } });
    const prompts = (STATE.meta.suggested_prompts && STATE.meta.suggested_prompts[LANG]) || STATE.meta.suggested_prompts.en;
    function render() {
      body.replaceChildren();
      if (!CHAT.length) {
        body.append(h("div", { class: "greet" }, t("greet")), ...prompts.map((p) => h("button", { class: "prompt", onclick: () => send(p) }, h("span", null, p), wrenchIcon())));
      } else {
        CHAT.forEach((m) => {
          if (m.role === "user") body.append(h("div", { class: "msg user" }, m.text));
          else body.append(h("div", { class: "msg bot" }, m.pending ? h("span", { class: "muted" }, "…") : rich(m.text),
            m.pending ? null : h("div", { class: "meta" }, `mode: ${m.mode}`, ...(m.citations || []).map((c) => h("a", { class: "cite", href: `#/signal/${c.signal_id}`, title: `${c.source.name} ${c.source.date || ""}` }, c.signal_id)))));
        });
        body.append(h("div", { class: "chips" }, ...prompts.map((p) => h("button", { class: "chip", onclick: () => send(p) }, p.length > 34 ? p.slice(0, 32) + "…" : p))));
        body.scrollTop = body.scrollHeight;
      }
    }
    async function send(text) {
      const q = (text || "").trim(); if (!q) return; input.value = "";
      CHAT.push({ role: "user", text: q }); const bot = { role: "bot", pending: true, text: "" }; CHAT.push(bot); render();
      try { const a = await api("/api/ask", "POST", { question: q, lang: LANG }); Object.assign(bot, { pending: false, text: a.answer, mode: a.mode, citations: a.citations }); }
      catch (e) { Object.assign(bot, { pending: false, text: `Could not answer: ${e.message}`, mode: "error", citations: [] }); }
      render();
    }
    window.irmaAsk = send;
    render();
    return h("div", { class: "assistant" },
      h("div", { class: "a-head" }, h("h2", null, wrenchIcon(), t("assistant")), h("span", { class: "tiny" }, STATE.meta.llm_mode === "live" ? `model ${STATE.meta.model}` : t("composed"))),
      body,
      h("div", { class: "a-input" }, h("div", { class: "chatbar" }, h("a", { class: "plus", href: "#/import", title: t("importData") }, "+"), input, h("button", { class: "send", onclick: () => send(input.value), "aria-label": "Send" }, sendIcon()))),
      h("div", { class: "a-foot" }, t("assistantFoot")));
  }

  // ---------- overview ----------
  function viewOverview() {
    const S = STATE; const sc = S.scenarios.scenarios;
    if (!SELECTED || !scById(SELECTED)) SELECTED = sc[0].id;
    const worldBtns = h("div", { class: "world" }, `${t("mockData")}:`, ...S.meta.worlds.map((wd) => h("button", { class: wd.id === S.meta.world ? "on" : "", onclick: async () => { const d = await api("/api/world", "POST", { world: wd.id }); STATE = d.state; CHAT.length = 0; SELECTED = null; LAST_RUN = null; afterLoad(); route(); toast(L(wd.label)); } }, L(wd.label))));
    const summary = h("div", { class: "card summary-card" }, h("div", { class: "label" }, `${t("summaryTitle")} · ${S.meta.today}`), h("div", { class: "s-text", style: { marginTop: "6px" } }, L(S.summary)),
      h("div", { class: "s-foot" }, h("span", { class: "tiny" }, L(S.meta.worlds.find((wd) => wd.id === S.meta.world)?.note)), worldBtns));
    const wl = S.signals.filter((s) => s.computed.weight > 0).sort((a, b) => (b.locked - a.locked) || (b.computed.weight - a.computed.weight)).slice(0, 12);
    const left = h("aside", { class: "gf-left" }, h("h2", null, t("signalsList")), h("div", { class: "wl" }, ...wl.map((s) => h("a", { href: `#/signal/${s.id}` },
      h("div", null, h("div", { class: "wl-name" }, sShort(s)), h("div", { class: "wl-sub" }, s.locked ? t("tracked") : L(s.source_class_label))),
      h("div", null, h("div", { class: "wl-val" }, f2(s.computed.weight)), h("div", { class: `wl-chg ${s.direction > 0 ? "pos" : s.direction < 0 ? "neg" : "muted"}` }, s.direction > 0 ? "▲" : s.direction < 0 ? "▼" : "●"))))),
      h("a", { class: "link small", href: "#/signals", style: { display: "block", marginTop: "10px" } }, `${t("allSignals")} →`));
    const section = h("div", { style: { display: "grid", gap: "12px" } });
    function renderScenarios() {
      const s = scById(SELECTED); const rank = sc.findIndex((x) => x.id === s.id) + 1;
      const chips = MODE === "projection"
        ? h("div", { class: "chips" }, ...[[6, "m6"], [12, "y1"], [36, "y3"]].map(([mv, k]) => h("button", { class: `chip ${HORIZON === mv ? "on" : ""}`, onclick: () => { HORIZON = mv; renderScenarios(); } }, t(k))), h("button", { class: "chip", onclick: () => { MODE = "history"; renderScenarios(); } }, t("history")))
        : h("div", { class: "chips" }, ...[[7, "d7"], [30, "d30"], [90, "d90"], [0, "all"]].map(([rv, k]) => h("button", { class: `chip ${RANGE === rv ? "on" : ""}`, onclick: () => { RANGE = rv; renderScenarios(); } }, t(k))), h("button", { class: "chip", onclick: () => { MODE = "projection"; renderScenarios(); } }, t("projection")));
      const big = h("div", { class: "card big-chart" },
        h("div", { class: "head" }, h("div", null, h("div", { class: "label" }, rank === 1 ? t("mostLikely") : t("rankOf", { n: rank })), h("div", { class: "name" }, dot(s.id), L(s.name)), h("div", { class: "hero-row", style: { gap: "14px" } }, h("div", { class: "figure" }, pct(s.probability)), deltaEl(s.delta_pp))), chips),
        MODE === "projection" ? projectionChart(s, HORIZON, 280) : historyChart(s.id, 280),
        h("div", { class: "section-head", style: { marginTop: "8px" } }, h("span", { class: "tiny" }, MODE === "projection" ? t("pathNote") : `${t("histNote")} ${L(S.history.note)}`), h("a", { class: "link small arrow", href: `#/scenarios/${s.id}` }, t("openScenario"))));
      const others = sc.filter((x) => x.id !== SELECTED);
      const minis = h("div", { class: "small-charts" }, ...others.map((x) => h("div", { class: "mini", role: "button", tabindex: "0", onclick: () => { SELECTED = x.id; renderScenarios(); }, onkeydown: (e) => { if (e.key === "Enter") { SELECTED = x.id; renderScenarios(); } } },
        h("div", { class: "m-name" }, dot(x.id), L(x.name)), h("div", { class: "m-prob" }, pct(x.probability)), h("div", { class: `m-delta ${x.delta_pp == null ? "muted" : x.delta_pp >= 0 ? "pos" : "neg"}` }, x.delta_pp == null ? "" : pp(x.delta_pp)), miniChart(x))));
      const used = s.contributions.slice(0, 8).map((c) => { const sig = S.signals.find((q) => q.id === c.signal_id); return { c, sig }; });
      const detail = h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("detailsTitle")), h("span", { class: "tiny" }, `${L(s.demand)} · ${L(s.supply)}`)),
        h("p", { style: { marginTop: "8px" } }, L(s.narrative)),
        disc(t("signalsUsed"), h("ul", { class: "bullets sources" }, ...used.map(({ c, sig }) => h("li", null, h("div", null, h("a", { class: "link", href: `#/signal/${c.signal_id}` }, sig ? sShort(sig) : c.signal_name), h("div", { class: "src-meta" }, sig ? `${sig.source.name}${sig.source.date ? " · " + sig.source.date : ""} · ${t("weight")} ${f2(c.weight)}` : "")), h("div", { class: "src-val" }, sig ? labelPill(sig.data_label) : null, " ", h("strong", { class: c.contribution >= 0 ? "pos" : "neg" }, (c.contribution >= 0 ? "+" : "") + f2(c.contribution)))))), true),
        disc(t("confirmT"), h("ul", { class: "bullets" }, ...s.signposts.map((p) => h("li", null, h("span", { class: "dot" }), h("span", null, L(p.text)), h("a", { class: "cite", href: `#/signal/${p.signal_id}` }, p.signal_id))))),
        disc(t("refuteT"), h("ul", { class: "bullets" }, ...s.falsifiers.map((p) => h("li", null, h("span", { class: "dot" }), h("span", null, L(p.text)), h("a", { class: "cite", href: `#/signal/${p.signal_id}` }, p.signal_id))))),
        disc(t("implications"), h("dl", { class: "kv" }, h("dt", null, t("demand")), h("dd", null, L(s.abb_interpretation.demand)), h("dt", null, t("delivery")), h("dd", null, L(s.abb_interpretation.delivery)), h("dt", null, t("components")), h("dd", null, L(s.abb_interpretation.components)))));
      section.replaceChildren(h("div", { class: "section-head" }, h("h2", null, t("fourTitle")), h("span", { class: "tiny" }, `${t("fourNote")} ${t("every", { n: S.scheduler.interval_minutes, a: timeOf(S.scheduler.last_run), b: timeOf(S.scheduler.next_run) })}`)), big, minis, detail);
    }
    renderScenarios();
    const bw = S.bullwhip;
    const item = (title, body, open) => h("details", { class: "summary-item", open: open ? "" : null }, h("summary", null, h("span", null, title), h("span", { class: "chev" }, chevIcon())), h("div", { class: "body" }, body));
    const market = h("div", { class: "card" }, h("div", { class: "section-head", style: { marginBottom: "6px" } }, h("h2", null, t("marketSummary")), h("span", { class: "tiny" }, `${S.meta.today} · ${timeOf(S.scheduler.last_run)}`)),
      item(t("brief"), h("div", null, h("p", null, cites(S.brief.text)), h("button", { class: "btn sm", onclick: () => window.irmaAsk && window.irmaAsk((S.meta.suggested_prompts[LANG] || S.meta.suggested_prompts.en)[0]) }, wrenchIcon(), t("explore")))),
      item(`${t("demandQuality")}: ${bw.overall.replace(/_/g, " ")}`, h("div", null, h("p", null, bw.summary), h("a", { class: "link small arrow", href: "#/scenarios#quality" }, t("openQuality")))),
      ...S.notifications.slice(0, 4).map((n) => item(nTitle(n), h("div", null, h("p", null, nText(n)), h("div", { class: "tiny" }, `${dateOf(n.time)} ${timeOf(n.time)}`), n.signal_id ? h("a", { class: "link small arrow", href: `#/signal/${n.signal_id}` }, t("signal")) : n.scenario_id ? h("a", { class: "link small arrow", href: `#/scenarios/${n.scenario_id}` }, t("scenario")) : null))),
      h("div", { style: { marginTop: "10px" } }, h("a", { class: "link small", href: "#/notifications" }, `${t("allNotifications")} →`)));
    const main = h("div", { class: "gf-main" }, section, market);
    return h("div", { style: { display: "grid", gap: "20px" } }, summary, mockFilters(), h("div", { class: "gf" }, left, main, h("aside", { class: "gf-right" }, assistantPanel())));
  }

  // ---------- scenarios page ----------
  function viewScenarios(selected, anchor) {
    const S = STATE; const sc = S.scenarios.scenarios;
    const sel = selected && scById(selected) ? selected : sc[0].id; const s = scById(sel);
    const rank = h("div", { class: "rank" }, ...sc.map((x) => h("div", { class: `rank-row ${x.id === sel ? "on" : ""}`, onclick: () => (location.hash = `#/scenarios/${x.id}`) },
      h("div", null, h("div", { class: "name" }, dot(x.id), L(x.name)), h("div", { class: "bar", style: { marginTop: "8px", "--sc": scColor(x.id) } }, h("span", { style: { width: `${x.probability * 100}%` } }))),
      h("div", { class: "num" }, pct(x.probability), h("small", null, pp(x.delta_pp) || "")))));
    const detail = h("div", { class: "card" },
      h("div", { class: "label" }, sel === sc[0].id ? t("mostLikely") : t("rankOf", { n: sc.findIndex((x) => x.id === sel) + 1 })),
      h("div", { class: "hero-row", style: { marginTop: "6px" } }, h("div", { class: "figure md" }, pct(s.probability)), h("div", null, h("div", { class: "hero-name" }, dot(s.id), L(s.name)), deltaEl(s.delta_pp), h("div", { class: "small muted" }, `${L(s.demand)} · ${L(s.supply)} · prior ${pct(s.prior)}`))),
      h("p", { style: { marginTop: "14px" } }, L(s.narrative)),
      disc(t("confirmT"), h("ul", { class: "bullets" }, ...s.signposts.map((p) => h("li", null, h("span", { class: "dot" }), h("span", null, L(p.text)), h("a", { class: "cite", href: `#/signal/${p.signal_id}` }, p.signal_id))))),
      disc(t("refuteT"), h("ul", { class: "bullets" }, ...s.falsifiers.map((p) => h("li", null, h("span", { class: "dot" }), h("span", null, L(p.text)), h("a", { class: "cite", href: `#/signal/${p.signal_id}` }, p.signal_id))))),
      disc(t("implications"), h("dl", { class: "kv" }, h("dt", null, t("demand")), h("dd", null, L(s.abb_interpretation.demand)), h("dt", null, t("delivery")), h("dd", null, L(s.abb_interpretation.delivery)), h("dt", null, t("components")), h("dd", null, L(s.abb_interpretation.components)))),
      disc(`${t("signalsUsed")}: +${f2(s.evidence_for)} / ${f2(s.evidence_against)}`, s.contributions.length ? diverging(s.contributions.slice(0, 8).map((c) => ({ ...c, signal_name: (S.signals.find((q) => q.id === c.signal_id) && sShort(S.signals.find((q) => q.id === c.signal_id))) || c.signal_name }))) : h("div", { class: "empty" }, "—"), true));
    const chart = h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("probByDay")), h("div", { class: "chips" }, ...[[7, "d7"], [30, "d30"], [90, "d90"], [0, "all"]].map(([rv, k]) => h("button", { class: `chip ${RANGE === rv ? "on" : ""}`, onclick: () => { RANGE = rv; route(); } }, t(k))))), historyChart(sel, 260), h("div", { class: "tiny", style: { marginTop: "8px" } }, L(S.history.note)));
    const bw = S.bullwhip;
    const quality = h("div", { class: "card", id: "quality" }, h("div", { class: "section-head" }, h("h2", null, t("demandQuality")), pill(bw.overall.replace(/_/g, " "), bw.overall === "real_demand" ? "ok" : bw.overall === "hoarding_risk" ? "neg" : "warn")), h("p", { class: "small muted" }, bw.summary),
      disc("Five indicators separating end demand from inventory build-up", h("ul", { class: "bullets" }, ...bw.metrics.map((m) => h("li", null, h("span", { class: `dot ${m.status === "hoarding_risk" ? "strong" : ""}` }), h("div", null, h("div", { class: "b-title" }, m.name), h("div", { class: "b-calc" }, m.reading), h("div", { class: "tiny" }, `Inputs: ${m.inputs_label}. ${m.inputs_note}`)), h("div", { class: "b-right" }, pill(m.status.replace(/_/g, " "), m.status === "real_demand" ? "ok" : m.status === "not_connected" ? "" : "warn")))))));
    const out = h("div", { style: { display: "grid", gap: "20px" } }, h("div", { class: "page-head" }, h("div", null, h("h1", null, t("scenarios")), h("div", { class: "sub" }, t("scenariosSub")))),
      h("div", { class: "grid-2" }, h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("ranking"))), rank, h("div", { class: "tiny", style: { marginTop: "10px" } }, `${t("uncertainty")} ${f2(S.scenarios.entropy)}`)), detail), chart, quality);
    if (anchor === "quality") setTimeout(() => document.getElementById("quality")?.scrollIntoView({ behavior: "smooth" }), 50);
    return out;
  }

  // ---------- signals ----------
  function scoutPanel() {
    const sc = STATE.scout || {}; const last = (sc.runs || [])[0];
    const cfg = sc.settings || {};
    const status = sc.running ? h("div", { class: "note" }, t("scoutRunning"))
      : !sc.eligible ? h("div", { class: "note warn" }, L(sc.skip))
      : h("div", { class: "small muted" }, last ? t("scoutIdle", { a: `${dateOf(last.at)} ${timeOf(last.at)}`, b: timeOf(STATE.scheduler.next_run) }) : t("scoutNever"));
    const btn = h("button", { class: "btn sm", disabled: (!sc.eligible || sc.running) ? "" : null, onclick: async () => {
      const r = await api("/api/scout/run", "POST"); STATE.scout = r.scout; toast(r.status === "started" ? t("scoutStarted") : r.status === "already_running" ? t("scoutBusy") : L(r.scout.skip)); startScoutPoll(); route({ keepScroll: true }); } }, t("searchNow"));
    const decision = (c) => pill(c.decision === "accepted" ? t("added") : t("rejectedWord"), c.decision === "accepted" ? "ok" : "");
    const candRow = (c) => h("li", null, h("span", { class: `dot ${c.decision === "accepted" ? "strong" : ""}` }),
      h("div", null, c.url ? h("a", { class: "b-title link", href: c.url, target: "_blank", rel: "noopener" }, c.title || c.url) : h("span", { class: "b-title" }, c.title || "—"),
        h("div", { class: "b-calc" }, [c.source_name, c.date, c.grade ? `${t("reliability")} ${c.grade}` : null, c.theme ? c.theme.replace(/_/g, " ") : null].filter(Boolean).join(" · ")),
        h("div", { class: "tiny" }, L(c.reason)), c.signal_id ? h("a", { class: "link small", href: `#/signal/${c.signal_id}` }, `${t("openSignal")} →`) : null),
      h("div", { class: "b-right" }, decision(c)));
    const summaryLine = (r) => r.status === "failed" ? `${t("failedWord")}: ${r.error || ""}` : t("scoutSummary", { acc: r.accepted, rej: r.rejected, s: r.searches, c: (r.est_cost_usd ?? 0).toFixed(2), d: r.duration_s ?? "—" });
    const rules = t("rules").map((x) => x.replace("{grade}", cfg.min_grade || "B").replace("{days}", cfg.max_age_days ?? 30).replace("{w}", cfg.min_weight ?? 0.15).replace("{load}", cfg.min_axis_load ?? 0.3));
    return h("div", { class: "card" },
      h("div", { class: "section-head" }, h("h2", null, t("scoutTitle")), h("div", { class: "row", style: { display: "flex", gap: "8px", alignItems: "center" } }, sc.found ? h("span", { class: "tiny" }, t("scoutFoundCount", { n: sc.found })) : null, btn)),
      status,
      last ? h("div", { class: "small", style: { marginTop: "8px" } }, `${dateOf(last.at)} ${timeOf(last.at)} · ${summaryLine(last)}`) : null,
      last && last.note ? h("div", { class: "tiny" }, L(last.note)) : null,
      last && (last.domains_removed || []).length ? h("div", { class: "tiny" }, t("domainsRemoved", { d: last.domains_removed.join(", ") })) : null,
      last && (last.candidates || []).length ? disc(`${t("scoutCandidates")} (${last.candidates.length})`, h("ul", { class: "bullets" }, ...last.candidates.map(candRow))) : null,
      (sc.runs || []).length > 1 ? disc(t("scoutEarlier"), h("ul", { class: "bullets" }, ...sc.runs.slice(1).map((r) => h("li", null, h("span", { class: "dot" }), h("div", null, h("div", { class: "b-title" }, `${dateOf(r.at)} ${timeOf(r.at)} · ${r.reason}`), h("div", { class: "b-calc" }, summaryLine(r))), h("div", { class: "b-right" }))))) : null,
      disc(t("scoutRules"), h("ol", { class: "small", style: { margin: 0, paddingLeft: "1.2rem", display: "grid", gap: "4px" } }, ...rules.map((x) => h("li", null, x)))));
  }

  function viewSignals() {
    const S = STATE; let cls = "all";
    const classes = { all: { en: "All", fi: "Kaikki" }, ...S.meta.source_classes };
    const chips = h("div", { class: "chips" }); const strongList = h("div"); const weakList = h("div"); const countEl = h("span", { class: "small muted" });
    function bullet(s) {
      const c = s.computed.components;
      return h("li", null, h("span", { class: `dot ${s.strength_class === "strong" ? "strong" : ""}` }),
        h("div", null, h("a", { class: "b-title link", href: `#/signal/${s.id}` }, sShort(s)), h("div", { class: "b-calc" }, `${s.direction > 0 ? "▲" : s.direction < 0 ? "▼" : "●"} ${s.value?.number != null ? `${num(s.value.number)} ${s.value.unit || ""}` : t("event")} · ${L(s.source_class_label)} · ${s.classification}`),
          h("div", { class: "tiny" }, `${t("calcFrom")}: ${s.source.name}${s.source.date ? " (" + s.source.date + ")" : ""} · ${t("reliability")} ${s.reliability} · ${t("freshness")} ${f2(c.freshness)} · ${t("strength")} ${f2(c.strength)} · ${t("counter")} ${s.counter_evidence.length} · ${t("weight")} ${f2(s.computed.weight)}`)),
        h("div", { class: "b-right" }, s.origin === "scout" ? pill(t("foundAuto"), "accent") : null, labelPill(s.data_label), lockBtn(s)));
    }
    function render() {
      const q = SEARCH.toLowerCase();
      const rows = S.signals.filter((s) => (cls === "all" || s.source_class === cls) && (!q || `${s.name} ${s.short} ${s.short_fi || ""} ${s.source.name} ${s.excerpt}`.toLowerCase().includes(q))).sort((a, b) => b.computed.weight - a.computed.weight);
      const strong = rows.filter((s) => s.strength_class === "strong"); const weak = rows.filter((s) => s.strength_class !== "strong");
      countEl.textContent = `${rows.length} · ${strong.length} ${t("strongSignals").toLowerCase()}, ${weak.length} ${t("weakSignals").toLowerCase()}`;
      chips.replaceChildren(...[...Object.entries(classes).map(([k, l]) => h("button", { class: `chip ${cls === k ? "on" : ""}`, onclick: () => { cls = k; render(); } }, L(l))), SEARCH ? h("button", { class: "chip on", onclick: () => { SEARCH = ""; document.getElementById("search").value = ""; render(); } }, `${SEARCH} ×`) : null].filter(Boolean));
      strongList.replaceChildren(strong.length ? h("ul", { class: "bullets" }, ...strong.map(bullet)) : h("div", { class: "empty" }, "—"));
      weakList.replaceChildren(weak.length ? h("ul", { class: "bullets" }, ...weak.map(bullet)) : h("div", { class: "empty" }, "—"));
    }
    render();
    return h("div", { style: { display: "grid", gap: "20px" } },
      h("div", { class: "page-head" }, h("div", null, h("h1", null, t("signals")), h("div", { class: "sub" }, t("signalsSub"))), h("a", { class: "btn primary", href: "#/import" }, t("importData"))),
      scoutPanel(),
      mockFilters(),
      h("div", { class: "section-head" }, chips, countEl),
      h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("strongSignals")), h("span", { class: "small muted" }, `${t("weight")} ≥ ${S.settings.strong_signal_weight}`)), h("p", { class: "small muted" }, t("strongSub")), strongList),
      h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("weakSignals")), h("span", { class: "small muted" }, `${t("weight")} < ${S.settings.strong_signal_weight}`)), h("p", { class: "small muted" }, t("weakSub")), weakList));
  }

  function webVerificationView(v) {
    const gradePill = (g) => pill(g, g === "A" ? "ok" : g === "B" ? "accent" : "");
    return h("div", { style: { display: "grid", gap: "8px" } },
      h("div", null, pill(v.corroborated ? t("corroborated") : t("notCorroborated"), v.corroborated ? "ok" : "warn")),
      v.primary ? h("dl", { class: "kv" }, h("dt", null, t("primarySource")), h("dd", null, h("a", { class: "link", href: v.primary.url, target: "_blank", rel: "noopener" }, v.primary.name), ` · ${v.primary.date || "—"} `, gradePill(v.primary.grade))) : null,
      v.quote ? h("div", { class: "quote" }, v.quote) : null,
      v.notes ? h("div", { class: "small muted" }, v.notes) : null,
      h("div", { class: "tiny" }, `${t("searchesRun")}: ${v.searches} · ${t("retrievedPages")}: ${(v.sources || []).length} · ${t("queries")}: ${(v.queries || []).map((q) => q.query || q.url).join(" · ") || "—"}`),
      (v.sources || []).length ? h("ul", { class: "bullets sources" }, ...v.sources.map((x) => h("li", null, h("div", null, h("a", { class: "link", href: x.url, target: "_blank", rel: "noopener" }, x.title || x.url)), h("div", { class: "src-val" }, gradePill(x.grade))))) : null);
  }

  async function viewSignal(id) {
    const s = await api(`/api/signals/${id}`); const c = s.computed.components;
    const contribs = Object.entries(s.contributions).filter(([, v]) => v).map(([sid, v]) => ({ ...v, signal_name: L(s.scenario_names[sid]) }));
    const note = h("input", { type: "text", placeholder: "Reason (logged with your name and time)" });
    async function annotate(action) { await api(`/api/signals/${id}/annotate`, "POST", { action, note: note.value }); toast(`${action} recorded`); await load(); route(); }
    const head = h("div", { class: "page-head" }, h("div", null, h("div", { class: "small muted" }, h("a", { class: "link", href: "#/signals" }, t("signals")), ` › ${s.id}`), h("h1", null, s.name), h("div", { class: "sub" }, `${L(s.source_class_label)} · ${s.region} · ${s.type}, ${s.lead_months} mo · ${s.classification}`)),
      h("div", { style: { display: "flex", gap: "8px", alignItems: "center" } }, s.origin === "scout" ? pill(t("foundAuto"), "accent") : null, labelPill(s.data_label), pill(s.strength_class, s.strength_class === "strong" ? "accent" : ""), lockBtn(s)));
    const valueCard = h("div", { class: "card" }, h("div", { class: "label" }, t("observed")), h("div", { class: "figure sm" }, s.value?.number != null ? `${num(s.value.number)} ${s.value.unit || ""}` : t("event")), h("div", { class: "small muted" }, s.value?.label || ""),
      s.history && s.history.length > 1 ? h("div", { style: { marginTop: "12px" } }, sparkline(s.history.map((p) => p.value)), h("div", { class: "tiny" }, `${s.history_label}. ${s.history_note}`)) : h("div", { class: "tiny", style: { marginTop: "8px" } }, s.history_note));
    const weightCard = h("div", { class: "card" }, h("div", { class: "label" }, t("weightIn")), h("div", { class: "figure sm" }, f2(s.computed.weight)), h("div", { class: "small muted" }, `${t("reliability")} ${s.reliability} · ${t("freshness")} ${f2(c.freshness)} · ${t("strength")} ${f2(c.strength)}`),
      s.locked ? h("div", { class: "note ok", style: { marginTop: "10px" } }, t("trackedNote", { n: s.tracking?.checks || 0, t: timeOf(s.tracking?.last_checked) })) : null);
    const source = h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("source"))), h("div", { class: "quote" }, s.excerpt),
      s.why_signal ? h("p", { class: "small", style: { marginTop: "10px" } }, h("strong", null, `${t("whySignal")}: `), s.why_signal) : null,
      h("dl", { class: "kv", style: { marginTop: "10px" } }, h("dt", null, t("source")), h("dd", null, s.source.url ? h("a", { class: "link", href: s.source.url, target: "_blank", rel: "noopener" }, s.source.name) : s.source.name), h("dt", null, t("date")), h("dd", null, s.source.date || "—"), h("dt", null, t("access")), h("dd", null, s.source.access || "—")),
      s.needs_review ? h("div", { class: "note warn", style: { marginTop: "10px" } }, "Classified by a heuristic or replayed output, not a live model. A reviewer should confirm reliability and strength.") : null);
    const details = h("div", { class: "card" },
      disc(t("why"), h("div", null, h("p", null, h("strong", null, s.classification), ": ", s.classification_rationale), h("p", { class: "small muted" }, s.lead_months_rationale))),
      disc(t("howWeight"), h("div", null, h("div", { class: "formula" }, `w = R × F × S × (1 − C) × H = ${c.reliability} × ${c.freshness} × ${c.strength} × (1 − ${c.counter_penalty}) × ${c.human} = ${s.computed.weight}`),
        h("dl", { class: "kv", style: { marginTop: "10px" } }, h("dt", null, "R"), h("dd", null, `${c.reliability} (${s.reliability})`), h("dt", null, "F"), h("dd", null, `${c.freshness} (${s.update_frequency})`), h("dt", null, "S"), h("dd", null, c.strength), h("dt", null, "C"), h("dd", null, `${c.counter_penalty} (${s.counter_cards.length})`), h("dt", null, "H"), h("dd", null, `${c.human} (${(s.annotations || []).length})`), h("dt", null, "axes"), h("dd", null, Object.entries(s.axes || {}).filter(([, v]) => v).map(([k, v]) => `${k} ${v > 0 ? "+" : ""}${v}`).join(", ") || "—")),
        s.computed.unchallenged_cap_applied ? h("div", { class: "note warn", style: { marginTop: "10px" } }, "Not yet challenged by counter-evidence: weight capped at 0.6.") : null)),
      s.verification ? disc(t("webVerification"), webVerificationView(s.verification), true) : null,
      disc(`${t("counter").charAt(0).toUpperCase()}${t("counter").slice(1)} (${s.counter_cards.length})`, h("div", { style: { display: "grid", gap: "8px" } },
        s.counter_search ? h("div", { class: "tiny" }, `${t("counterSearch")} ${s.counter_search.at}: ${t("searchesRun").toLowerCase()} ${s.counter_search.searches}${s.counter_search.found ? "" : " · " + t("foundNothing")} · ${t("queries")}: ${(s.counter_search.queries || []).map((q) => q.query || q.url).join(" · ")}`) : null,
        ...(s.counter_cards.length ? s.counter_cards.map((ce) => h("div", { class: "ce" }, h("div", null, ce.claim), ce.web?.quote ? h("div", { class: "quote" }, ce.web.quote) : null,
          h("div", { class: "ce-meta" }, h("span", null, ce.id), h("span", null, `${t("reliability")} ${ce.reliability}`), h("span", null, `${t("strength")} ${f2(ce.strength)}`), labelPill(ce.data_label),
            ce.web ? pill(ce.web.verified ? t("webVerified") : t("linkRemoved"), ce.web.verified ? "ok" : "warn") : null,
            ce.source?.url ? h("a", { class: "link", href: ce.source.url, target: "_blank", rel: "noopener" }, ce.source.name) : h("span", null, ce.source?.name || ""), h("span", null, ce.source?.date || "")))) : [s.counter_search ? null : h("div", { class: "empty" }, "—")]))),
      disc(t("contribution"), contribs.length ? diverging(contribs) : h("div", { class: "empty" }, "—")),
      disc(t("assessment"), h("div", { style: { display: "grid", gap: "10px" } }, h("div", { class: "field" }, note), h("div", { class: "form-row" }, h("button", { class: "btn", onclick: () => annotate("confirm") }, t("confirm")), h("button", { class: "btn", onclick: () => annotate("dispute") }, t("dispute")), h("button", { class: "btn", onclick: () => annotate("comment") }, t("comment"))),
        (s.annotations || []).length ? h("ul", { class: "bullets" }, ...s.annotations.map((a) => h("li", null, h("span", { class: "dot" }), h("span", null, h("strong", null, a.action), ` · ${a.author}, ${a.at.slice(0, 16).replace("T", " ")}`, a.note ? `: ${a.note}` : "")))) : null)));
    return h("div", { style: { display: "grid", gap: "20px" } }, head, h("div", { class: "grid-2" }, valueCard, weightCard), source, details);
  }

  // ---------- import ----------
  function viewImport() {
    const S = STATE;
    const f = { title: h("input", { type: "text", placeholder: "e.g. TrendForce: 4Q26 server DRAM contract prices flat" }), text: h("textarea", { placeholder: "Paste the source text. The classifier quotes from it; nothing is invented." }), date: h("input", { type: "date", value: S.meta.today }), source: h("input", { type: "text", placeholder: "Source name" }), url: h("input", { type: "url", placeholder: "https://" }) };
    const out = h("div", { style: { display: "grid", gap: "20px" } });
    async function run(body) {
      out.replaceChildren(h("div", { class: "muted" }, "…"));
      try { const d = await api("/api/run", "POST", body); STATE = d.state; LAST_RUN = d.run; afterLoad(); renderRun(); toast(t("importData")); } catch (e) { out.replaceChildren(h("div", { class: "note warn" }, `Failed: ${e.message}`)); }
    }
    function renderRun() {
      const r = LAST_RUN; if (!r) return;
      const deltas = r.trace.find((x) => x.agent === "Scenario agent")?.output?.deltas || []; const ns = r.brief.next_step;
      out.replaceChildren(
        h("div", { class: "note ok" }, `${r.title} → `, h("a", { class: "link", href: `#/signal/${r.new_signal_id}` }, r.new_signal_id)),
        h("div", { class: "grid-2" },
          h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("scenarios"))), h("div", { class: "rank" }, ...deltas.map((d) => h("div", { class: "rank-row" }, h("div", { class: "name" }, d.name), h("div", { class: "num" }, pct(d.after), h("small", null, d.before == null ? "new" : `${pct(d.before)} (${pp(d.delta == null ? null : d.delta * 100)})`)))))),
          h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("nextStep"))), h("ul", { class: "bullets" }, ...ns.watch.map((w) => h("li", null, h("span", { class: "dot" }), h("span", null, h("a", { class: "link", href: `#/signal/${w.signal_id}` }, w.short), ` — ${w.why}`)))), h("dl", { class: "kv", style: { marginTop: "10px" } }, h("dt", null, "Re-evaluate"), h("dd", null, ns.reevaluate_on), h("dt", null, "Review with"), h("dd", null, ns.review_with.join(" · "))))),
        h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("brief")), h("span", { class: "small muted" }, `mode: ${r.brief.mode}`)), h("p", null, cites(r.brief.text)),
          disc(t("implications"), h("div", { style: { display: "grid", gap: "10px" } }, ...Object.entries(r.interpretation || {}).map(([sid, txt]) => h("div", { class: "quote" }, h("strong", null, sid === "ALL" ? "All" : L((scById(sid) || {}).name) || sid), h("div", null, txt))))),
          disc(t("steps"), h("div", { class: "trace" }, ...r.trace.map((x, i) => h("div", { class: "trace-step" }, h("div", { class: "idx" }, i + 1), h("div", null, h("div", null, h("strong", null, x.agent), " ", pill(x.mode, x.mode.startsWith("live") ? "ok" : x.mode === "code" ? "accent" : "warn"), " ", pill(x.status, x.status === "ok" ? "ok" : "warn")), h("div", { class: "small muted" }, x.summary), x.notes?.length ? h("div", { class: "tiny" }, x.notes.join(" ")) : null, h("details", null, h("summary", { class: "tiny" }, "output"), h("pre", null, JSON.stringify(x.output, null, 2))))))))));
    }
    if (LAST_RUN) setTimeout(renderRun, 0);
    return h("div", { style: { display: "grid", gap: "20px" } },
      h("div", { class: "page-head" }, h("div", null, h("div", { class: "small muted" }, h("a", { class: "link", href: "#/signals" }, t("signals")), ` › ${t("importData")}`), h("h1", null, t("importData")), h("div", { class: "sub" }, t("importSub")))),
      h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("newItem"))),
        h("div", { class: "note" }, "Demonstration item: an illustrative Fingrid Q3 2026 update (DEMODATA). Classification and text steps are replayed when no model key is configured; weights, probabilities and demand-quality indicators are always computed live."),
        h("div", { class: "form-row", style: { marginTop: "10px" } }, h("button", { class: "btn primary", onclick: () => run({ preset: "demo_fingrid_q3" }) }, t("importDemo")), h("span", { class: "tiny" }, `agents: ${S.meta.llm_mode}`)),
        h("div", { style: { display: "grid", gap: "10px", marginTop: "16px" } }, h("div", { class: "field" }, h("label", null, "Title"), f.title), h("div", { class: "field" }, h("label", null, "Text"), f.text), h("div", { class: "grid-3" }, h("div", { class: "field" }, h("label", null, t("date")), f.date), h("div", { class: "field" }, h("label", null, t("source")), f.source), h("div", { class: "field" }, h("label", null, "URL"), f.url)), h("div", null, h("button", { class: "btn", onclick: () => run({ title: f.title.value, text: f.text.value, date: f.date.value, source_name: f.source.value, source_url: f.url.value, data_label: "DEMODATA" }) }, t("importPasted"))))),
      out);
  }

  function viewNotifications() {
    return h("div", { style: { display: "grid", gap: "20px" } },
      h("div", { class: "page-head" }, h("div", null, h("h1", null, t("notifications")), h("div", { class: "sub" }, t("notifSub"))), h("button", { class: "btn", onclick: async () => { await api("/api/notifications/read-all", "POST"); await load(); route(); } }, t("markAllRead"))),
      h("div", { class: "card" }, notifList(STATE.notifications)));
  }

  async function viewSettings() {
    const S = STATE; const m = await api("/api/method"); const n = S.settings.notifications;
    const interval = h("select", null, ...[[15, "15 min"], [30, "30 min"], [60, "60 min"], [180, "3 h"], [360, "6 h"], [1440, "24 h"]].map(([v, l]) => h("option", { value: v, selected: S.settings.run_interval_minutes === v ? "" : null }, l)));
    const ppIn = h("input", { type: "number", step: "0.5", min: "0.1", value: n.probability_change_pp }); const wIn = h("input", { type: "number", step: "0.05", min: "0.05", max: "1", value: n.major_signal_weight });
    const pIn = h("input", { type: "number", step: "0.5", min: "0.1", value: n.price_change_pct }); const leaderIn = h("input", { type: "checkbox", checked: n.leader_change ? "" : null }); const strongIn = h("input", { type: "number", step: "0.05", min: "0.05", max: "1", value: S.settings.strong_signal_weight });
    const ws = S.settings.web_search || {};
    const webOn = h("input", { type: "checkbox", checked: ws.enabled ? "" : null });
    const msIn = h("input", { type: "number", min: "1", max: "10", step: "1", value: ws.max_searches ?? 3 });
    const mfIn = h("input", { type: "number", min: "0", max: "10", step: "1", value: ws.max_fetches ?? 2 });
    const adIn = h("textarea", { rows: "6", spellcheck: "false" }, (ws.allowed_domains || []).join("\n"));
    const pdIn = h("textarea", { rows: "6", spellcheck: "false" }, (ws.primary_domains || []).join("\n"));
    const lines = (el) => el.value.split(/[\s,]+/).map((x) => x.trim()).filter(Boolean);
    const sc = ws.scout || {};
    const scOn = h("input", { type: "checkbox", checked: sc.enabled ? "" : null });
    const scCand = h("input", { type: "number", min: "1", max: "5", step: "1", value: sc.max_candidates ?? 3 });
    const scSearch = h("input", { type: "number", min: "1", max: "10", step: "1", value: sc.max_searches ?? 4 });
    const scAge = h("input", { type: "number", min: "1", max: "180", step: "1", value: sc.max_age_days ?? 30 });
    const scGrade = h("select", null, h("option", { value: "A", selected: sc.min_grade === "A" ? "" : null }, t("gradeA")), h("option", { value: "B", selected: sc.min_grade !== "A" ? "" : null }, t("gradeAB")));
    const scWeight = h("input", { type: "number", min: "0", max: "1", step: "0.05", value: sc.min_weight ?? 0.15 });
    const scLoad = h("input", { type: "number", min: "0", max: "1", step: "0.05", value: sc.min_axis_load ?? 0.3 });
    async function save() { await api("/api/settings", "PUT", { run_interval_minutes: Number(interval.value), strong_signal_weight: Number(strongIn.value), notifications: { probability_change_pp: Number(ppIn.value), major_signal_weight: Number(wIn.value), price_change_pct: Number(pIn.value), leader_change: leaderIn.checked }, web_search: { enabled: webOn.checked, max_searches: Number(msIn.value), max_fetches: Number(mfIn.value), allowed_domains: lines(adIn), primary_domains: lines(pdIn), scout: { enabled: scOn.checked, max_candidates: Number(scCand.value), max_searches: Number(scSearch.value), max_age_days: Number(scAge.value), min_grade: scGrade.value, min_weight: Number(scWeight.value), min_axis_load: Number(scLoad.value) } } }); toast(t("save")); await load(); route(); }
    const webCard = h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("webSearch")), pill(S.meta.llm_mode === "live" ? "live" : "replay", S.meta.llm_mode === "live" ? "ok" : "warn")),
      h("div", { style: { display: "grid", gap: "12px" } },
        h("label", { class: "small", style: { display: "flex", gap: "8px", alignItems: "center" } }, webOn, t("webEnabled")),
        h("div", { class: "grid-2" }, h("div", { class: "field" }, h("label", null, t("maxSearches")), msIn), h("div", { class: "field" }, h("label", null, t("maxFetches")), mfIn)),
        h("div", { class: "grid-2" }, h("div", { class: "field" }, h("label", null, t("allowedDomains")), adIn), h("div", { class: "field" }, h("label", null, t("primaryDomains")), pdIn)),
        h("div", { class: "tiny" }, t("webPricing")), S.meta.llm_mode !== "live" ? h("div", { class: "tiny" }, t("webNeedsKey")) : null,
        (ws.blocked_domains || []).length ? h("div", { class: "tiny" }, t("blockedDomains", { d: ws.blocked_domains.join(", ") })) : null,
        h("h3", { style: { marginTop: "6px" } }, t("scoutSettingsTitle")),
        h("label", { class: "small", style: { display: "flex", gap: "8px", alignItems: "center" } }, scOn, t("scoutEnabled")),
        h("div", { class: "grid-3" }, h("div", { class: "field" }, h("label", null, t("maxCandidates")), scCand), h("div", { class: "field" }, h("label", null, t("discoverySearches")), scSearch), h("div", { class: "field" }, h("label", null, t("maxAge")), scAge)),
        h("div", { class: "grid-3" }, h("div", { class: "field" }, h("label", null, t("minGrade")), scGrade), h("div", { class: "field" }, h("label", null, t("minWeight")), scWeight), h("div", { class: "field" }, h("label", null, t("minLoad")), scLoad)),
        h("div", { class: "tiny" }, t("scoutCost")),
        h("div", { class: "form-row" }, h("button", { class: "btn primary", onclick: save }, t("save")),
          h("button", { class: "btn", onclick: async () => { if (!window.confirm(t("clearConfirm"))) return; await api("/api/scout/clear", "POST"); toast(t("clearFound")); await load(); route(); } }, t("clearFound")))));
    return h("div", { style: { display: "grid", gap: "20px" } },
      h("div", { class: "page-head" }, h("div", null, h("h1", null, t("settings")), h("div", { class: "sub" }, t("settingsSub")))),
      h("div", { class: "grid-2" },
        h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("updates"))), h("div", { style: { display: "grid", gap: "12px" } }, h("div", { class: "field" }, h("label", null, t("runCycle")), interval),
          h("dl", { class: "kv" }, h("dt", null, t("lastRun")), h("dd", null, `${dateOf(S.scheduler.last_run)} ${timeOf(S.scheduler.last_run)}`), h("dt", null, t("nextRun")), h("dd", null, `${dateOf(S.scheduler.next_run)} ${timeOf(S.scheduler.next_run)}`), h("dt", null, t("runsDone")), h("dd", null, S.scheduler.runs_completed)),
          h("div", { class: "form-row" }, h("button", { class: "btn", onclick: async () => { const d = await api("/api/cycle", "POST"); toast(d.scout === "started" ? t("scoutStarted") : `+${d.notifications_created.length}`); await load(); startScoutPoll(); route(); } }, t("runNow")), h("button", { class: "btn", onclick: async () => { await api("/api/reset", "POST"); LAST_RUN = null; CHAT.length = 0; SELECTED = null; toast(t("resetDemo")); await load(); route(); } }, t("resetDemo"))))),
        h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("notifSettings"))), h("div", { style: { display: "grid", gap: "12px" } },
          h("div", { class: "field" }, h("label", null, t("ppLabel")), ppIn), h("div", { class: "field" }, h("label", null, t("majorLabel")), wIn), h("div", { class: "field" }, h("label", null, t("priceLabel")), pIn),
          h("label", { class: "small", style: { display: "flex", gap: "8px", alignItems: "center" } }, leaderIn, t("leaderLabel")), h("div", { class: "field" }, h("label", null, t("strongLabel")), strongIn), h("div", { class: "tiny" }, t("halfNote")), h("div", null, h("button", { class: "btn primary", onclick: save }, t("save")))))),
      webCard,
      h("div", { class: "card" }, h("div", { class: "section-head" }, h("h2", null, t("method"))), h("p", { class: "small muted" }, m.principle),
        disc(t("candidates"), h("ul", { class: "bullets" }, ...m.candidates.map((a) => h("li", null, h("span", { class: `dot ${S.scenarios.scenarios.some((x) => x.id === a.id) ? "strong" : ""}` }), h("div", null, h("div", { class: "b-title" }, L(a.name)), h("div", { class: "b-calc" }, Object.entries(a.profile).filter(([, v]) => v).map(([k, v]) => `${k} ${v > 0 ? "+" : ""}${v}`).join(", ") + ` · prior ${pct(a.prior)}`)), h("div", { class: "b-right" }, S.scenarios.scenarios.some((x) => x.id === a.id) ? pill("shown", "accent") : null)))), true),
        disc("Signal weight", h("div", null, h("div", { class: "formula" }, m.weight_formula), h("dl", { class: "kv", style: { marginTop: "10px" } }, h("dt", null, "R"), h("dd", null, Object.entries(m.reliability).map(([k, v]) => `${k} = ${v}`).join(", ")), h("dt", null, "F"), h("dd", null, `0.5^(age / half-life); ${Object.entries(m.half_life_days).map(([k, v]) => `${k} ${v}`).join(", ")}`), h("dt", null, "C"), h("dd", null, `min(${m.counter_cap}, 1 − Π(1 − R_ce × strength_ce))`), h("dt", null, "H"), h("dd", null, Object.entries(m.human_multipliers).map(([k, v]) => `${k} ×${v}`).join(", ")), h("dt", null, "cap"), h("dd", null, m.unchallenged_cap)))),
        disc("Scenario selection", h("div", null, h("div", { class: "formula" }, m.scenario_formula), h("p", { class: "small muted", style: { marginTop: "8px" } }, `k = ${m.k}. ${m.k_note}`))),
        disc(t("agents"), h("ul", { class: "bullets" }, ...m.agents.map((a) => h("li", null, h("span", { class: "dot" }), h("div", null, h("div", { class: "b-title" }, a.name), h("div", { class: "b-calc" }, a.responsibility)))))),
        disc(t("dataLabels"), h("div", { class: "small" }, h("p", null, labelPill("SOURCE"), " named public source with date and link on the card."), h("p", null, labelPill("DEMODATA"), " illustrative value in the prototype, to be replaced by licensed or internal data."), h("p", null, labelPill("ASSUMPTION"), " stated assumption with its reasoning, to verify with ABB."))),
        disc(t("sourcesUsed"), h("ul", { class: "bullets" }, ...S.signals.map((s) => h("li", null, h("span", { class: "dot" }), h("div", null, h("a", { class: "b-title link", href: `#/signal/${s.id}` }, sShort(s)), h("div", { class: "b-calc" }, s.source.url ? h("a", { class: "link", href: s.source.url, target: "_blank", rel: "noopener" }, s.source.name) : s.source.name, s.source.date ? ` · ${s.source.date}` : "", ` · ${s.source.access}`)), h("div", { class: "b-right" }, labelPill(s.data_label))))))));
  }

  // ---------- routing ----------
  function applyLang() {
    document.documentElement.lang = LANG;
    document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
    document.getElementById("search").placeholder = t("search");
    document.getElementById("lang-en").classList.toggle("on", LANG === "en");
    document.getElementById("lang-fi").classList.toggle("on", LANG === "fi");
  }
  function setLang(l) { LANG = l; try { localStorage.setItem("irma_lang", l); } catch (_) { /* ignore */ } applyLang(); if (STATE) { renderBanner(); route(); } }
  document.getElementById("lang-en").addEventListener("click", () => setLang("en"));
  document.getElementById("lang-fi").addEventListener("click", () => setLang("fi"));
  let SCOUT_POLL = null;
  function startScoutPoll() {
    if (SCOUT_POLL || !(STATE && STATE.scout && STATE.scout.running)) return;
    SCOUT_POLL = setInterval(async () => {
      try {
        const sc = await api("/api/scout");
        STATE.scout = sc;
        if (!sc.running) {
          clearInterval(SCOUT_POLL); SCOUT_POLL = null;
          await load();
          const r = (sc.runs || [])[0];
          if (r) toast(t("scoutDone", { acc: r.accepted, rej: r.rejected }));
          route({ keepScroll: true });
        } else { afterLoad(); }
      } catch (_) { /* keep polling */ }
    }, 4000);
  }
  function afterLoad() {
    document.getElementById("status-text").textContent = STATE.scout && STATE.scout.running ? t("scoutRunning") : `${timeOf(STATE.scheduler.last_run)} → ${timeOf(STATE.scheduler.next_run)}`;
    startScoutPoll();
    const bc = document.getElementById("bell-count"); bc.textContent = STATE.unread; bc.hidden = !STATE.unread;
    renderBanner();
  }
  async function load() { STATE = await api("/api/state"); afterLoad(); }
  function setNav(route) { document.querySelectorAll(".nav a").forEach((a) => a.classList.toggle("active", a.dataset.route === route)); }
  async function route(opts) {
    const keep = opts && opts.keepScroll; const y = window.scrollY;
    const hash = location.hash || "#/"; const [path, anchor] = hash.slice(2).split("#"); const parts = path.split("/").filter(Boolean);
    document.querySelectorAll(".tooltip").forEach((x) => x.remove());
    let view;
    try {
      if (parts[0] === "scenarios") { setNav("scenarios"); view = viewScenarios(parts[1], anchor); }
      else if (parts[0] === "signals") { setNav("signals"); view = viewSignals(); }
      else if (parts[0] === "signal" && parts[1]) { setNav("signals"); view = await viewSignal(parts[1]); }
      else if (parts[0] === "import" || parts[0] === "add") { setNav("signals"); view = viewImport(); }
      else if (parts[0] === "settings") { setNav("settings"); view = await viewSettings(); }
      else if (parts[0] === "notifications") { setNav(""); view = viewNotifications(); }
      else { setNav("overview"); view = viewOverview(); }
    } catch (e) { view = h("div", { class: "note warn" }, `Could not render this page: ${e.message}`); }
    app.replaceChildren(view);
    if (keep) window.scrollTo(0, y); else if (!anchor) window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", route);
  document.getElementById("search").addEventListener("keydown", (e) => { if (e.key === "Enter") { SEARCH = e.target.value.trim(); if (location.hash.startsWith("#/signals")) route(); else location.hash = "#/signals"; } });
  applyLang();
  load().then(route).catch((e) => app.replaceChildren(h("div", { class: "note warn" }, `Could not load state from the API: ${e.message}. Start the backend with app/run.sh.`)));
  setInterval(async () => { try { await load(); } catch (_) { /* offline */ } }, 60000);
})();
