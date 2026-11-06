// Gate check for the interface text (C14). Run with: node app/tests/i18n_parity.js   (exit code 1 on any finding)
//   1. frontend/app.js: the en and fi dictionaries have identical keys.
//   2. frontend/map.js: its string table (STR) has identical en and fi keys.
//   3. Every literal t("key") used in app.js has an entry in both languages.
//   4. No internal wording in visible text (English: no-regret, hedge, kernel, contingent, runner-up;
//      Finnish: one term per concept, so vastanäyttö, bare paino/painon, laukaisija and the slang "kakkonen" are rejected).
const fs = require("fs");
const path = require("path");
const root = path.join(__dirname, "..", "frontend");
const appSrc = fs.readFileSync(path.join(root, "app.js"), "utf8");
const mapSrc = fs.readFileSync(path.join(root, "map.js"), "utf8");

function literalAfter(src, startMarker, endMarker) {
  const a = src.indexOf(startMarker);
  if (a < 0) throw new Error("marker not found: " + startMarker);
  const b = src.indexOf(endMarker, a);
  if (b < 0) throw new Error("end marker not found: " + endMarker);
  return new Function("return (" + src.slice(a + startMarker.length, b + 4) + ")")();
}

const I18N = literalAfter(appSrc, "const I18N = ", "\n  };\n  const t =");
const STR = literalAfter(mapSrc, "const STR = ", "\n  };\n\n");
const problems = [];

function parity(name, dict) {
  const en = Object.keys(dict.en), fi = Object.keys(dict.fi);
  for (const k of en) if (!fi.includes(k)) problems.push(`${name}: key "${k}" is missing in fi`);
  for (const k of fi) if (!en.includes(k)) problems.push(`${name}: key "${k}" is missing in en`);
  return en.length;
}
const nApp = parity("app.js I18N", I18N);
const nMap = parity("map.js STR", STR);

const used = new Set();
for (const m of appSrc.matchAll(/\bt\("([A-Za-z0-9_]+)"/g)) used.add(m[1]);
for (const m of mapSrc.matchAll(/\bT\("([A-Za-z0-9_]+)"/g)) used.add(m[1]);
for (const k of used) {
  const known = (k in I18N.en && k in I18N.fi) || (k in STR.en && k in STR.fi);
  if (!known) problems.push(`key "${k}" is used in the code but not defined in both languages`);
}

const flat = (v) => (Array.isArray(v) ? v.join(" ") : String(v));
const EN_BAD = /no[-_ ]regret|\bhedge\b|\bkernel\b|\bcontingent\b|runner-up/i;
const FI_BAD = /vastanäyt|\bpaino\b|\bpainon\b|laukaisij|kakkonen/i;
for (const [name, dict] of [["app.js I18N", I18N], ["map.js STR", STR]]) {
  for (const [k, v] of Object.entries(dict.en)) if (EN_BAD.test(flat(v))) problems.push(`${name}.en.${k}: internal term in "${flat(v).slice(0, 60)}"`);
  for (const [k, v] of Object.entries(dict.fi)) if (FI_BAD.test(flat(v))) problems.push(`${name}.fi.${k}: wrong term in "${flat(v).slice(0, 60)}"`);
}

if (problems.length) {
  console.error("i18n check failed:\n  " + problems.join("\n  "));
  process.exit(1);
}
console.log(`i18n OK: app.js ${nApp} keys, map.js ${nMap} keys, ${used.size} keys used, same keys in en and fi, no internal terms`);
