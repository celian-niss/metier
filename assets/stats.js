/* ============================================================
   stats.js — tests statistiques du CM2 appliqués à Pulse Emploi.
   Dépend de jStat (distributions de Student, F et Chi²).
   Les fonctions renvoient toujours les effectifs et tailles d'effet :
   une p-value seule ne suffit pas à interpréter un résultat.
   ============================================================ */

const valeursNumeriques = a => (a || []).filter(v => typeof v === "number" && Number.isFinite(v));

function moyenneStat(a) {
  const v = valeursNumeriques(a);
  return v.length ? v.reduce((s, x) => s + x, 0) / v.length : null;
}

function varianceStat(a, echantillon = true) {
  const v = valeursNumeriques(a);
  if (v.length < (echantillon ? 2 : 1)) return null;
  const m = moyenneStat(v);
  const den = echantillon ? v.length - 1 : v.length;
  return v.reduce((s, x) => s + (x - m) ** 2, 0) / den;
}

function ecartTypeStat(a, echantillon = true) {
  const v = varianceStat(a, echantillon);
  return v == null ? null : Math.sqrt(v);
}

function formatP(p) {
  if (p == null || !Number.isFinite(p)) return "p non calculable";
  if (p < 0.001) return "p < 0,001";
  return "p = " + p.toLocaleString("fr-FR", { minimumFractionDigits: 3, maximumFractionDigits: 3 });
}

function formatStat(v, digits = 2) {
  return v == null || !Number.isFinite(v) ? "—" : v.toLocaleString("fr-FR", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

function effetCohen(d) {
  const a = Math.abs(d ?? 0);
  return a < 0.2 ? "très faible" : a < 0.5 ? "faible" : a < 0.8 ? "modéré" : "fort";
}

function effetR(r) {
  const a = Math.abs(r ?? 0);
  return a < 0.1 ? "très faible" : a < 0.3 ? "faible" : a < 0.5 ? "modéré" : "fort";
}

function effetEta2(x) {
  const a = Math.abs(x ?? 0);
  return a < 0.01 ? "très faible" : a < 0.06 ? "faible" : a < 0.14 ? "modéré" : "fort";
}

function effetCramer(v) {
  const a = Math.abs(v ?? 0);
  return a < 0.1 ? "très faible" : a < 0.3 ? "faible" : a < 0.5 ? "modéré" : "fort";
}

function welchTTest(a, b) {
  const x = valeursNumeriques(a), y = valeursNumeriques(b);
  if (x.length < 2 || y.length < 2) return null;
  const m1 = moyenneStat(x), m2 = moyenneStat(y);
  const v1 = varianceStat(x), v2 = varianceStat(y);
  const se2 = v1 / x.length + v2 / y.length;
  if (!se2) return null;
  const t = (m1 - m2) / Math.sqrt(se2);
  const num = se2 ** 2;
  const den = ((v1 / x.length) ** 2) / (x.length - 1) + ((v2 / y.length) ** 2) / (y.length - 1);
  const df = num / den;
  const p = typeof jStat !== "undefined" ? 2 * (1 - jStat.studentt.cdf(Math.abs(t), df)) : null;
  const pooled = Math.sqrt(((x.length - 1) * v1 + (y.length - 1) * v2) / (x.length + y.length - 2));
  const d = pooled ? (m1 - m2) / pooled : null;
  return { n1: x.length, n2: y.length, m1, m2, t, df, p, d };
}

function anovaUnFacteur(groupes) {
  const gs = (groupes || []).map(g => ({ label: g.label, valeurs: valeursNumeriques(g.valeurs) })).filter(g => g.valeurs.length >= 2);
  if (gs.length < 2) return null;
  const n = gs.reduce((s, g) => s + g.valeurs.length, 0);
  const tous = gs.flatMap(g => g.valeurs);
  const grand = moyenneStat(tous);
  const ssEntre = gs.reduce((s, g) => s + g.valeurs.length * (moyenneStat(g.valeurs) - grand) ** 2, 0);
  const ssIntra = gs.reduce((s, g) => {
    const m = moyenneStat(g.valeurs);
    return s + g.valeurs.reduce((acc, x) => acc + (x - m) ** 2, 0);
  }, 0);
  const df1 = gs.length - 1, df2 = n - gs.length;
  if (df2 <= 0 || ssIntra === 0) return null;
  const f = (ssEntre / df1) / (ssIntra / df2);
  const p = typeof jStat !== "undefined" ? 1 - jStat.centralF.cdf(f, df1, df2) : null;
  const eta2 = (ssEntre + ssIntra) ? ssEntre / (ssEntre + ssIntra) : null;
  return { groupes: gs, n, f, df1, df2, p, eta2 };
}

function pearsonStat(xs, ys) {
  const paires = [];
  for (let i = 0; i < Math.min(xs.length, ys.length); i++) {
    if (Number.isFinite(xs[i]) && Number.isFinite(ys[i])) paires.push([xs[i], ys[i]]);
  }
  const n = paires.length;
  if (n < 3) return null;
  const x = paires.map(p => p[0]), y = paires.map(p => p[1]);
  const mx = moyenneStat(x), my = moyenneStat(y);
  const sxx = x.reduce((s, v) => s + (v - mx) ** 2, 0);
  const syy = y.reduce((s, v) => s + (v - my) ** 2, 0);
  if (!sxx || !syy) return null;
  const sxy = paires.reduce((s, p) => s + (p[0] - mx) * (p[1] - my), 0);
  const r = Math.max(-1, Math.min(1, sxy / Math.sqrt(sxx * syy)));
  const t = Math.abs(r) === 1 ? Infinity : r * Math.sqrt((n - 2) / Math.max(1e-12, 1 - r * r));
  const p = typeof jStat !== "undefined" ? 2 * (1 - jStat.studentt.cdf(Math.abs(t), n - 2)) : null;
  return { n, r, t, df: n - 2, p, mx, my, sxx, sxy };
}

function regressionLineaire(xs, ys) {
  const c = pearsonStat(xs, ys);
  if (!c) return null;
  const pente = c.sxy / c.sxx;
  const intercept = c.my - pente * c.mx;
  return { ...c, pente, intercept, r2: c.r * c.r };
}

function chiDeux(tableau) {
  if (!Array.isArray(tableau) || tableau.length < 2 || !Array.isArray(tableau[0]) || tableau[0].length < 2) return null;
  const r = tableau.length, c = tableau[0].length;
  if (tableau.some(l => !Array.isArray(l) || l.length !== c || l.some(v => !Number.isFinite(v) || v < 0))) return null;
  const lignes = tableau.map(l => l.reduce((a, b) => a + b, 0));
  const colonnes = Array.from({ length: c }, (_, j) => tableau.reduce((s, l) => s + l[j], 0));
  const n = lignes.reduce((a, b) => a + b, 0);
  if (!n || lignes.some(v => v === 0) || colonnes.some(v => v === 0)) return null;
  let chi2 = 0, faibles = 0, tresFaibles = 0, cellules = 0;
  for (let i = 0; i < r; i++) {
    for (let j = 0; j < c; j++) {
      const attendu = lignes[i] * colonnes[j] / n;
      cellules++;
      if (attendu < 5) faibles++;
      if (attendu < 1) tresFaibles++;
      chi2 += (tableau[i][j] - attendu) ** 2 / attendu;
    }
  }
  const df = (r - 1) * (c - 1);
  const p = typeof jStat !== "undefined" ? 1 - jStat.chisquare.cdf(chi2, df) : null;
  const denom = n * Math.min(r - 1, c - 1);
  const v = denom ? Math.sqrt(chi2 / denom) : null;
  const partFaibles = cellules ? faibles / cellules : 1;
  return {
    n, chi2, df, p, v,
    hypothesesOk: tresFaibles === 0 && partFaibles <= 0.2,
    faibles, tresFaibles, cellules, partFaibles
  };
}

function carteTestStat({ titre, question, h0, resultat, effet, effectif, interpretation, avertissement = "" }) {
  return `<div class="stat-test-head"><span>Test statistique</span><h3>${titre}</h3></div>
    <p class="stat-question">${question}</p>
    <p class="stat-h0"><b>H0 :</b> ${h0}</p>
    <div class="stat-result">${resultat}</div>
    <div class="stat-meta">${effet ? `<span><b>Taille d’effet</b>${effet}</span>` : ""}${effectif ? `<span><b>Effectif</b>${effectif}</span>` : ""}</div>
    <p class="stat-interpretation">${interpretation}</p>
    ${avertissement ? `<p class="stat-warning">${avertissement}</p>` : ""}`;
}
