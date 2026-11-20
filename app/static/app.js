/* Paranın Zaman Maliyeti — tarayıcı uygulaması (Alpine.js + Chart.js).
 * Tüm finansal hesaplar sunucudaki Python hesaplama modülünde yapılır;
 * bu dosya yalnızca girdi toplar ve sonuçları gösterir. */

const TL = new Intl.NumberFormat("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const TL0 = new Intl.NumberFormat("tr-TR", { maximumFractionDigits: 0 });
const PCT = new Intl.NumberFormat("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function fmtTL(v) { return v === null || v === undefined || v === "" ? "—" : TL.format(Number(v)) + " TL"; }
function fmtTLshort(v) {
  const n = Number(v);
  if (Math.abs(n) >= 1e6) return TL.format(n / 1e6).replace(/,00$/, "") + " Mn TL";
  if (Math.abs(n) >= 1e3) return TL0.format(n / 1e3) + " B TL";
  return TL0.format(n) + " TL";
}
function fmtPct(v) { return v === null || v === undefined ? "—" : "%" + PCT.format(Number(v)); }
function fmtDate(iso) {
  if (!iso) return "—";
  const [y, m, d] = iso.split("-");
  return `${d}.${m}.${y}`;
}
function isoToday() {
  // Türkiye saati (UTC+3)
  const d = new Date(Date.now() + 3 * 3600 * 1000);
  return d.toISOString().slice(0, 10);
}
function addDaysIso(iso, days) {
  const d = new Date(iso + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + Number(days));
  return d.toISOString().slice(0, 10);
}
function addMonthsIso(iso, months) {
  const [y, m, d] = iso.split("-").map(Number);
  const idx = m - 1 + months;
  const ny = y + Math.floor(idx / 12), nm = (idx % 12) + 1;
  const last = new Date(Date.UTC(ny, nm, 0)).getUTCDate();
  return `${ny}-${String(nm).padStart(2, "0")}-${String(Math.min(d, last)).padStart(2, "0")}`;
}

/** "1.250.000,50" veya "1250000.50" → "1250000.50" (sunucuya metin olarak gider). */
function parseTR(s) {
  if (s === null || s === undefined) return "";
  let t = String(s).trim().replace(/\s|TL|%/gi, "");
  if (t === "") return "";
  if (t.includes(",")) t = t.replace(/\./g, "").replace(",", ".");
  else if ((t.match(/\./g) || []).length > 1 || /\.\d{3}$/.test(t)) t = t.replace(/\./g, "");
  return t;
}
function prettyTR(s) {
  const t = parseTR(s);
  if (t === "" || isNaN(Number(t))) return s;
  const [i, f] = t.split(".");
  const intPart = TL0.format(Number(i));
  return f !== undefined ? `${intPart},${f}` : intPart;
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    method: opts.method || "GET",
    headers: opts.body ? { "Content-Type": "application/json" } : {},
    body: opts.body ? JSON.stringify(opts.body) : undefined,
    credentials: "same-origin",
  });
  let data = null;
  try { data = await res.json(); } catch (_) { /* boş yanıt */ }
  if (!res.ok) {
    const err = new Error((data && data.detail) || `Sunucu hatası (${res.status})`);
    err.status = res.status;
    err.field = data && data.alan;
    throw err;
  }
  return data;
}

const ICONS = {
  home: '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
  calc: '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M8 7h8M8 11h2M12 11h2M16 11h0M8 15h2M12 15h2M8 18h2M12 18h4"/>',
  wallet: '<path d="M3 7a2 2 0 0 1 2-2h12v4"/><rect x="3" y="7" width="18" height="13" rx="2"/><circle cx="16" cy="13.5" r="1.3"/>',
  chart: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  scale: '<path d="M12 3v18M5 21h14M6 7h12M6 7l-3 7a3 3 0 0 0 6 0zM18 7l-3 7a3 3 0 0 0 6 0z"/>',
  report: '<path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z"/><path d="M14 3v6h6M8 13h8M8 17h5"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  edit: '<path d="M4 20h4L19 9l-4-4L4 16z"/>',
  trash: '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
  download: '<path d="M12 4v12M6 11l6 6 6-6M4 20h16"/>',
  print: '<path d="M6 9V3h12v6M6 18H4v-7h16v7h-2"/><rect x="6" y="14" width="12" height="7"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  logout: '<path d="M15 4h4v16h-4M10 8l-4 4 4 4M6 12h10"/>',
  check: '<path d="m5 12 5 5 9-10"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  x: '<path d="M6 6l12 12M18 6 6 18"/>',
  save: '<path d="M5 3h11l3 3v15H5z"/><path d="M8 3v5h7M8 21v-7h8v7"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
  moon: '<path d="M20 15A8 8 0 1 1 9 4a7 7 0 0 0 11 11z"/>',
};
function icon(name) {
  return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">${ICONS[name] || ""}</svg>`;
}

const charts = {};
function cssVar(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
function drawChart(id, config) {
  const el = document.getElementById(id);
  if (!el || !window.Chart) return;
  if (charts[id]) charts[id].destroy();
  const grid = cssVar("--chart-grid"), text = cssVar("--muted");
  Chart.defaults.font.family = "Inter, system-ui, sans-serif";
  Chart.defaults.color = text;
  const base = {
    responsive: true, maintainAspectRatio: false,
    plugins: {
      legend: { labels: { usePointStyle: true, boxWidth: 8, padding: 16 } },
      tooltip: {
        backgroundColor: "#0f172a", padding: 12, cornerRadius: 10, titleFont: { weight: "600" },
        callbacks: { label: (c) => ` ${c.dataset.label || c.label}: ${fmtTL(c.parsed.y ?? c.parsed)}` },
      },
    },
  };
  if (config.type !== "doughnut") {
    base.scales = {
      x: { grid: { display: false }, border: { display: false } },
      y: { grid: { color: grid }, border: { display: false }, ticks: { callback: (v) => fmtTLshort(v) } },
    };
  }
  config.options = deepMerge(base, config.options || {});
  charts[id] = new Chart(el, config);
}
function deepMerge(a, b) {
  const out = { ...a };
  for (const k of Object.keys(b)) {
    out[k] = b[k] && typeof b[k] === "object" && !Array.isArray(b[k]) && a[k] ? deepMerge(a[k], b[k]) : b[k];
  }
  return out;
}

const PAGES = {
  panel: { title: "Genel Bakış", sub: "Firma portföyünün özeti ve hızlı erişim", icon: "home" },
  hesap: { title: "Yeni Hesaplama", sub: "Vadeli bir çek veya senedin bugünkü ekonomik değeri", icon: "calc" },
  portfoy: { title: "Çek / Senet Portföyü", sub: "Kayıtlı vadeli evraklar ve güncel değerleri", icon: "wallet" },
  oran: { title: "Oran Karşılaştırması", sub: "Farklı iskonto oranlarının bugünkü değere etkisi", icon: "chart" },
  pesin: { title: "Peşin / Vadeli Karşılaştırma", sub: "Peşin teklif mi, vadeli tahsilat mı?", icon: "scale" },
  rapor: { title: "Raporlar", sub: "Yazdırılabilir portföy raporu ve Excel aktarımı", icon: "report" },
  ayar: { title: "Ayarlar", sub: "Firmalar, kullanıcılar ve tercihler", icon: "settings" },
};

function emptyDoc(company) {
  return {
    id: null, evrak_no: "", muhatap: "", evrak_turu: "cek", nominal: "", duzenleme_tarihi: isoToday(),
    vade_tarihi: "", yillik_oran: company ? prettyTR(company.varsayilan_oran) : "40",
    yontem: company ? company.varsayilan_yontem : "bilesik", durum: "portfoyde", banka: "", notlar: "",
  };
}

document.addEventListener("alpine:init", () => {
  Alpine.data("app", () => ({
    // ---- durum ----
    booting: true, needsSetup: false, setupKeyRequired: false, user: null,
    page: "panel", menuOpen: false, theme: "light",
    companies: [], companyId: null,
    toasts: [],
    auth: { kullanici_adi: "", parola: "", ad_soyad: "", ilk_firma: "", anahtar: "", error: "" },
    // hesaplama
    calc: { evrak_turu: "cek", nominal: "1.000.000", duzenleme_tarihi: isoToday(), vade_tarihi: addDaysIso(isoToday(), 240),
            yillik_oran: "40", yontem: "bilesik", degerleme_esasi: "bugun", degerleme_tarihi: isoToday() },
    calcRes: null, calcErr: null, calcBusy: false,
    // oran
    rate: { nominal: "1.000.000", vade_tarihi: addMonthsIso(isoToday(), 8), yontem: "bilesik",
            oranlar: ["25", "30", "35", "40", "45", "50"], yeni: "" },
    rateRes: null, rateErr: null,
    // peşin
    cash: { nominal: "1.000.000", vade_tarihi: addDaysIso(isoToday(), 240), sermaye_maliyeti: "40", pesin_teklif: "820.000", yontem: "bilesik" },
    cashRes: null, cashErr: null,
    // portföy
    port: null, portErr: null, docs: [], docFilter: "portfoyde", docSearch: "", portDate: isoToday(), portRate: "",
    docModal: null, docErr: null, docBusy: false,
    // ayarlar
    users: [], companyModal: null, userModal: null, modalErr: null,
    pw: { mevcut_parola: "", yeni_parola: "", tekrar: "" },
    confirmBox: null,

    icon, fmtTL, fmtPct, fmtDate, fmtTLshort, prettyTR, PAGES,

    async init() {
      try { this.theme = localStorage.getItem("pzm_tema") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"); } catch (_) {}
      document.documentElement.dataset.theme = this.theme;
      window.addEventListener("hashchange", () => this.route());
      try {
        const s = await api("/api/kurulum");
        this.needsSetup = s.kurulum_gerekli;
        this.setupKeyRequired = s.anahtar_gerekli;
        if (!this.needsSetup) this.user = await api("/api/ben");
      } catch (e) { this.user = null; }
      if (this.user) await this.afterLogin();
      this.booting = false;
    },

    // ---- yardımcılar ----
    toast(msg, err = false) {
      const t = { id: Math.random(), msg, err };
      this.toasts.push(t);
      setTimeout(() => (this.toasts = this.toasts.filter((x) => x !== t)), 3800);
    },
    get company() { return this.companies.find((c) => c.id === this.companyId) || null; },
    initials(n) { return (n || "?").split(/\s+/).map((p) => p[0]).slice(0, 2).join("").toUpperCase(); },
    toggleTheme() {
      this.theme = this.theme === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = this.theme;
      try { localStorage.setItem("pzm_tema", this.theme); } catch (_) {}
      this.$nextTick(() => this.renderPageCharts());
    },
    go(p) { location.hash = p; this.menuOpen = false; },
    route() {
      const p = (location.hash || "#panel").slice(1);
      this.page = PAGES[p] ? p : "panel";
      this.loadPage();
      window.scrollTo({ top: 0 });
    },
    blurPretty(obj, key) { obj[key] = prettyTR(obj[key]); },

    // ---- oturum ----
    async doLogin() {
      this.auth.error = "";
      try {
        this.user = await api("/api/giris", { method: "POST", body: { kullanici_adi: this.auth.kullanici_adi, parola: this.auth.parola } });
        this.auth.parola = "";
        await this.afterLogin();
      } catch (e) { this.auth.error = e.message; }
    },
    async doSetup() {
      this.auth.error = "";
      try {
        this.user = await api("/api/kurulum", { method: "POST", body: { kullanici_adi: this.auth.kullanici_adi, ad_soyad: this.auth.ad_soyad, parola: this.auth.parola, ilk_firma: this.auth.ilk_firma, anahtar: this.auth.anahtar } });
        this.needsSetup = false;
        await this.afterLogin();
      } catch (e) { this.auth.error = e.message; }
    },
    async logout() {
      await api("/api/cikis", { method: "POST" }).catch(() => {});
      this.user = null; this.companies = []; this.port = null;
    },
    async afterLogin() {
      await this.loadCompanies();
      this.route();
    },
    async loadCompanies() {
      this.companies = await api("/api/firmalar");
      let saved = null;
      try { saved = Number(localStorage.getItem("pzm_firma")); } catch (_) {}
      this.companyId = this.companies.some((c) => c.id === saved) ? saved : (this.companies[0] ? this.companies[0].id : null);
      this.applyCompanyDefaults();
    },
    selectCompany(id) {
      this.companyId = Number(id);
      try { localStorage.setItem("pzm_firma", String(this.companyId)); } catch (_) {}
      this.applyCompanyDefaults();
      this.loadPage();
    },
    applyCompanyDefaults() {
      const c = this.company;
      if (!c) return;
      const r = prettyTR(c.varsayilan_oran);
      this.calc.yillik_oran = r; this.calc.yontem = c.varsayilan_yontem; this.calc.degerleme_esasi = c.degerleme_esasi;
      this.cash.sermaye_maliyeti = r; this.cash.yontem = c.varsayilan_yontem;
      this.rate.yontem = c.varsayilan_yontem;
    },

    async loadPage() {
      this.$nextTick(async () => {
        if (this.page === "hesap" && !this.calcRes) await this.runCalc();
        if (this.page === "oran") await this.runRates();
        if (this.page === "pesin" && !this.cashRes) await this.runCash();
        if (["panel", "portfoy", "rapor"].includes(this.page)) await this.loadPortfolio();
        if (this.page === "ayar" && this.user.yonetici) this.users = await api("/api/kullanicilar").catch(() => []);
        this.renderPageCharts();
      });
    },
    renderPageCharts() {
      if (this.page === "hesap") this.drawCalcChart();
      if (this.page === "oran") this.drawRateChart();
      if (this.page === "pesin") this.drawCashChart();
      if (["panel", "portfoy", "rapor"].includes(this.page)) this.drawPortfolioCharts();
    },

    // ---- yeni hesaplama ----
    setDays(obj, d) { obj.vade_tarihi = addDaysIso(obj === this.calc && this.calc.degerleme_esasi === "teslim" ? this.calc.duzenleme_tarihi : isoToday(), d); },
    setMonths(obj, m) { obj.vade_tarihi = addMonthsIso(obj === this.calc && this.calc.degerleme_esasi === "teslim" ? this.calc.duzenleme_tarihi : isoToday(), m); },
    async runCalc() {
      this.calcErr = null; this.calcBusy = true;
      try {
        this.calcRes = await api("/api/hesap/deger", { method: "POST", body: {
          ...this.calc, nominal: parseTR(this.calc.nominal), yillik_oran: parseTR(this.calc.yillik_oran) } });
        this.$nextTick(() => this.drawCalcChart());
      } catch (e) { this.calcErr = e; this.calcRes = null; }
      this.calcBusy = false;
    },
    drawCalcChart() {
      const r = this.calcRes;
      if (!r) return;
      drawChart("calcDonut", {
        type: "doughnut",
        data: { labels: ["Bugünkü değer", "Zaman maliyeti"],
          datasets: [{ data: [Number(r.sonuc.bugunku_deger), Number(r.sonuc.zaman_maliyeti)], backgroundColor: [cssVar("--value"), cssVar("--cost")], borderWidth: 0, hoverOffset: 6 }] },
        options: { cutout: "72%", plugins: { legend: { position: "bottom" }, tooltip: { callbacks: { label: (c) => ` ${c.label}: ${fmtTL(c.parsed)}` } } } },
      });
    },
    saveCalcAsDoc() {
      const d = emptyDoc(this.company);
      Object.assign(d, { evrak_turu: this.calc.evrak_turu, nominal: this.calc.nominal, duzenleme_tarihi: this.calc.duzenleme_tarihi,
        vade_tarihi: this.calc.vade_tarihi, yillik_oran: this.calc.yillik_oran, yontem: this.calc.yontem });
      this.openDoc(d);
    },

    // ---- oran karşılaştırması ----
    addRate() {
      const v = parseTR(this.rate.yeni);
      if (v === "" || isNaN(Number(v))) return;
      if (!this.rate.oranlar.includes(v)) this.rate.oranlar.push(v);
      this.rate.oranlar.sort((a, b) => Number(a) - Number(b));
      this.rate.yeni = "";
      this.runRates();
    },
    removeRate(r) { this.rate.oranlar = this.rate.oranlar.filter((x) => x !== r); this.runRates(); },
    async runRates() {
      this.rateErr = null;
      try {
        const res = await api("/api/hesap/oran-karsilastirma", { method: "POST", body: {
          nominal: parseTR(this.rate.nominal), vade_tarihi: this.rate.vade_tarihi, yontem: this.rate.yontem, oranlar: this.rate.oranlar } });
        this.rateRes = res.satirlar;
        this.$nextTick(() => this.drawRateChart());
      } catch (e) { this.rateErr = e; this.rateRes = null; }
    },
    drawRateChart() {
      const rows = this.rateRes;
      if (!rows) return;
      drawChart("rateChart", {
        type: "bar",
        data: {
          labels: rows.map((r) => "%" + prettyTR(r.yillik_oran)),
          datasets: [
            { label: "Bugünkü değer", data: rows.map((r) => Number(r.bugunku_deger)), backgroundColor: cssVar("--value"), borderRadius: 8, stack: "s", maxBarThickness: 56 },
            { label: "Zaman maliyeti", data: rows.map((r) => Number(r.zaman_maliyeti)), backgroundColor: cssVar("--cost"), borderRadius: 8, stack: "s", maxBarThickness: 56 },
          ],
        },
        options: { scales: { x: { stacked: true }, y: { stacked: true } } },
      });
    },
    rateMaxCost() { return this.rateRes ? Math.max(...this.rateRes.map((r) => Number(r.zaman_maliyeti)), 1) : 1; },

    // ---- peşin / vadeli ----
    async runCash() {
      this.cashErr = null;
      try {
        this.cashRes = await api("/api/hesap/pesin-vadeli", { method: "POST", body: {
          ...this.cash, nominal: parseTR(this.cash.nominal), sermaye_maliyeti: parseTR(this.cash.sermaye_maliyeti), pesin_teklif: parseTR(this.cash.pesin_teklif) } });
        this.$nextTick(() => this.drawCashChart());
      } catch (e) { this.cashErr = e; this.cashRes = null; }
    },
    drawCashChart() {
      const r = this.cashRes;
      if (!r) return;
      drawChart("cashChart", {
        type: "bar",
        data: {
          labels: ["Vadeli nominal", "Vadelinin bugünkü değeri", "Peşin teklif"],
          datasets: [{ label: "Tutar", data: [Number(r.degerleme.nominal), Number(r.esdeger_pesin_tutar), Number(r.pesin_teklif)],
            backgroundColor: [cssVar("--faint"), cssVar("--primary"), r.karar === "pesin" ? cssVar("--value") : cssVar("--warn")], borderRadius: 10, maxBarThickness: 90 }],
        },
        options: { plugins: { legend: { display: false } } },
      });
    },

    // ---- portföy ----
    async loadPortfolio() {
      if (!this.companyId) { this.port = null; this.docs = []; return; }
      this.portErr = null;
      try {
        const q = new URLSearchParams({ tarih: this.portDate || isoToday() });
        const rate = parseTR(this.portRate);
        if (rate) q.set("oran", rate);
        const [p, docs] = await Promise.all([
          api(`/api/firmalar/${this.companyId}/portfoy?${q}`),
          api(`/api/firmalar/${this.companyId}/evraklar?tarih=${this.portDate || isoToday()}`),
        ]);
        this.port = p; this.docs = docs;
        this.$nextTick(() => this.drawPortfolioCharts());
      } catch (e) { this.portErr = e.message; }
    },
    get filteredDocs() {
      const s = this.docSearch.trim().toLocaleLowerCase("tr");
      return this.docs.filter((d) => (this.docFilter === "hepsi" || d.durum === this.docFilter) &&
        (!s || d.evrak_no.toLocaleLowerCase("tr").includes(s) || d.muhatap.toLocaleLowerCase("tr").includes(s)));
    },
    sumDocs(key) {
      return this.filteredDocs.reduce((a, d) => a + Math.round(Number(key === "nominal" ? d.nominal : d.guncel[key]) * 100), 0) / 100;
    },
    drawPortfolioCharts() {
      const p = this.port;
      if (!p) return;
      const prefix = this.page === "rapor" ? "r_" : this.page === "panel" ? "p_" : "";
      drawChart(prefix + "monthlyChart", {
        type: "bar",
        data: { labels: p.aylik_tahsilat.map((m) => m.etiket),
          datasets: [
            { label: "Nominal tahsilat", data: p.aylik_tahsilat.map((m) => Number(m.nominal)), backgroundColor: cssVar("--primary"), borderRadius: 8, maxBarThickness: 40 },
            { label: "Bugünkü değer", data: p.aylik_tahsilat.map((m) => Number(m.bugunku_deger)), backgroundColor: cssVar("--value"), borderRadius: 8, maxBarThickness: 40 },
          ] },
      });
      const b = p.vade_dagilimi;
      drawChart(prefix + "bucketChart", {
        type: "doughnut",
        data: { labels: b.map((x) => x.etiket),
          datasets: [{ data: b.map((x) => Number(x.nominal)), borderWidth: 0,
            backgroundColor: ["#e11d48", "#f59e0b", "#10b981", "#06b6d4", "#6366f1", "#8b5cf6"] }] },
        options: { cutout: "68%", plugins: { legend: { position: "right" }, tooltip: { callbacks: { label: (c) => ` ${c.label}: ${fmtTL(c.parsed)}` } } } },
      });
    },
    openDoc(d) { this.docErr = null; this.docModal = JSON.parse(JSON.stringify(d)); this.docModal.nominal = prettyTR(this.docModal.nominal); this.docModal.yillik_oran = prettyTR(this.docModal.yillik_oran); },
    newDoc() { this.openDoc(emptyDoc(this.company)); },
    editDoc(d) { this.openDoc({ ...d, duzenleme_tarihi: d.duzenleme_tarihi || "", banka: d.banka || "", notlar: d.notlar || "" }); },
    async saveDoc() {
      if (!this.companyId) { this.docErr = { message: "Önce Ayarlar'dan bir firma oluşturun." }; return; }
      this.docErr = null; this.docBusy = true;
      const d = this.docModal;
      const body = { ...d, nominal: parseTR(d.nominal), yillik_oran: parseTR(d.yillik_oran) };
      try {
        if (d.id) await api(`/api/firmalar/${this.companyId}/evraklar/${d.id}`, { method: "PUT", body });
        else await api(`/api/firmalar/${this.companyId}/evraklar`, { method: "POST", body });
        this.docModal = null;
        this.toast(d.id ? "Evrak güncellendi." : "Evrak portföye eklendi.");
        await this.loadCompanies();
        if (this.page !== "portfoy") this.go("portfoy"); else await this.loadPortfolio();
      } catch (e) { this.docErr = e; }
      this.docBusy = false;
    },
    askDelete(d) {
      this.confirmBox = { text: `${d.evrak_no} numaralı evrak kalıcı olarak silinsin mi?`, run: async () => {
        await api(`/api/firmalar/${this.companyId}/evraklar/${d.id}`, { method: "DELETE" });
        this.toast("Evrak silindi."); await this.loadPortfolio();
      } };
    },
    async markCollected(d) {
      const body = { ...d, durum: "tahsil_edildi" };
      try {
        await api(`/api/firmalar/${this.companyId}/evraklar/${d.id}`, { method: "PUT", body });
        this.toast("Evrak tahsil edildi olarak işaretlendi."); await this.loadPortfolio();
      } catch (e) { this.toast(e.message, true); }
    },
    statusChip(d) {
      if (d.durum !== "portfoyde") return { cls: "gray", text: d.durum_adi };
      if (d.guncel.durum === "vadesi_gecmis") return { cls: "cost", text: "Vadesi geçti" };
      if (d.guncel.durum === "bugun") return { cls: "warn", text: "Bugün" };
      if (d.guncel.gun <= 30) return { cls: "warn", text: d.guncel.gun + " gün" };
      return { cls: "value", text: d.guncel.gun + " gün" };
    },
    exportCsv() { if (this.companyId) location.href = `/api/firmalar/${this.companyId}/disa-aktar.csv?tarih=${this.portDate || isoToday()}`; },

    // ---- ayarlar ----
    openCompany(c) {
      this.modalErr = null;
      this.companyModal = c ? { id: c.id, ad: c.ad, vergi_no: c.vergi_no || "", varsayilan_oran: prettyTR(c.varsayilan_oran), varsayilan_yontem: c.varsayilan_yontem, degerleme_esasi: c.degerleme_esasi }
        : { id: null, ad: "", vergi_no: "", varsayilan_oran: "40", varsayilan_yontem: "bilesik", degerleme_esasi: "bugun" };
    },
    async saveCompany() {
      const c = this.companyModal; this.modalErr = null;
      const body = { ...c, varsayilan_oran: parseTR(c.varsayilan_oran) };
      try {
        const res = c.id ? await api(`/api/firmalar/${c.id}`, { method: "PUT", body }) : await api("/api/firmalar", { method: "POST", body });
        this.companyModal = null; this.toast("Firma kaydedildi.");
        await this.loadCompanies();
        if (!c.id) this.selectCompany(res.id);
      } catch (e) { this.modalErr = e.message; }
    },
    askDeleteCompany(c) {
      this.confirmBox = { text: `"${c.ad}" firması ve tüm evrakları (${c.evrak_sayisi} portföyde) kalıcı olarak silinsin mi?`, run: async () => {
        await api(`/api/firmalar/${c.id}`, { method: "DELETE" }); this.toast("Firma silindi."); await this.loadCompanies();
      } };
    },
    openUser(u) {
      this.modalErr = null;
      this.userModal = u ? { id: u.id, kullanici_adi: u.kullanici_adi, ad_soyad: u.ad_soyad, parola: "", yonetici: u.yonetici, aktif: u.aktif, firmalar: [...u.firmalar] }
        : { id: null, kullanici_adi: "", ad_soyad: "", parola: "", yonetici: false, aktif: true, firmalar: this.companyId ? [this.companyId] : [] };
    },
    async saveUser() {
      const u = this.userModal; this.modalErr = null;
      try {
        if (u.id) await api(`/api/kullanicilar/${u.id}`, { method: "PUT", body: u });
        else await api("/api/kullanicilar", { method: "POST", body: u });
        this.userModal = null; this.toast("Kullanıcı kaydedildi.");
        this.users = await api("/api/kullanicilar");
      } catch (e) { this.modalErr = e.message; }
    },
    askDeleteUser(u) {
      this.confirmBox = { text: `${u.ad_soyad} (${u.kullanici_adi}) kullanıcısı silinsin mi?`, run: async () => {
        await api(`/api/kullanicilar/${u.id}`, { method: "DELETE" }); this.toast("Kullanıcı silindi."); this.users = await api("/api/kullanicilar");
      } };
    },
    companyNames(ids) { return ids.map((id) => (this.companies.find((c) => c.id === id) || {}).ad).filter(Boolean).join(", ") || "—"; },
    async changePassword() {
      if (this.pw.yeni_parola !== this.pw.tekrar) { this.toast("Yeni parolalar eşleşmiyor.", true); return; }
      try {
        await api("/api/ben/parola", { method: "POST", body: { mevcut_parola: this.pw.mevcut_parola, yeni_parola: this.pw.yeni_parola } });
        this.pw = { mevcut_parola: "", yeni_parola: "", tekrar: "" }; this.toast("Parolanız değiştirildi.");
      } catch (e) { this.toast(e.message, true); }
    },
    async runConfirm() {
      const box = this.confirmBox; this.confirmBox = null;
      try { await box.run(); } catch (e) { this.toast(e.message, true); }
    },
  }));
});
