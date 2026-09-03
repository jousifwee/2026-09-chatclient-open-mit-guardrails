# UTZ MessageHub v2 direkt aus einer HTML-Seite ansprechen (Basic Auth)

> Vorlage für Confluence. Stand 2026-09-03, geprüft gegen `0.1.29+039ba26`.
> Basis: `https://utz-messagehub.itzcloud.de` · Spezifikation `/openapi.json`

**Ziel:** eine einzelne HTML-Datei, kein Framework, kein Build. Sie registriert ein Konto,
schickt eine Nachricht und holt die eigene Post ab — mit Basic Auth.

Das ist die kürzeste Strecke zum funktionierenden Aufruf. Sie zeigt zugleich die Grenzen, an
die man im Browser stößt; wo sie stören, führt der Weg über einen BFF (siehe Seite
*Fullstack-App mit BFF als Proxy*).

---

## ⚠️ Vorab: nur synthetische Testdaten

Der Dienst läuft auf einer Demo-Box bei einem externen Anbieter in einer öffentlichen Cloud
und wird jederzeit zurückgesetzt.

- Keine personenbezogenen Daten, keine Kundendaten, keine Echtdaten aus Produktivsystemen.
- **Der Benutzername ist gleichzeitig die Adresse.** Also ein erfundener Bezeichner, kein
  echter Vor- oder Nachname.
- **Wegwerf-Kennwort.** Keines, das anderswo gilt. Der Dienst speichert nur einen
  scrypt-Hash — aber Basic Auth schickt das Kennwort bei *jeder* Anfrage mit.

---

## Schritt 1 — Konto anlegen

`POST /v2/register` ist der **einzige** Endpunkt der Stufe ohne Nachweis.

| Feld | Regel |
|---|---|
| `username` | `^[A-Za-z0-9_-]{1,32}$` · zugleich die Adresse · belegt → `409` |
| `password` | mindestens 8 Zeichen, sonst keine Regel |
| `key` | optional, öffentlicher Schlüssel (opake Zeichenkette) |

```bash
curl -X POST https://utz-messagehub.itzcloud.de/v2/register \
  -H "Content-Type: application/json" \
  -d '{"username":"anna_demo","password":"wegwerf-1234"}'
```

Antworten: `201` angelegt · `400` Vorgabe verletzt · `409` Name belegt · `429` zu viele
Registrierungen · `503` Stufe nicht konfiguriert oder Kontendeckel erreicht.

> **Im ITZ-Netz** scheitert `curl` mit Exit 60 („unable to get local issuer certificate"). Der
> Hub liefert ein Let's-Encrypt-Zertifikat, aber der Interception-Proxy
> `sofia.itz-rostock.de` bricht die Verbindung auf und signiert neu. Abhilfe:
> `--cacert <pfad-zu-ITZ08-CA.crt>`. **Nicht** `-k`, und die Wurzel **nicht global** trusten.
> Über Hotspot oder von außen tritt das Problem nicht auf. Im Browser spielt es keine Rolle.

## Schritt 2 — Der Authorization-Header

Basic Auth ist Base64 von `benutzer:kennwort`, als **selbst gesetzter** Header:

```js
const basic = 'Basic ' + btoa(`${user}:${pass}`);
```

**Falle:** `btoa` kann nur Latin-1. Ein Kennwort mit Umlaut oder Emoji wirft
`InvalidCharacterError` — und der Fehler zeigt auf die Zeile, nicht auf das Kennwort. RFC 7617
sieht UTF-8 vor, also so:

```js
function basicAuth(user, pass) {
  const bytes = new TextEncoder().encode(`${user}:${pass}`);
  return 'Basic ' + btoa(String.fromCharCode(...bytes));
}
```

## Schritt 3 — Die vollständige Seite

Eine Datei, kein Build. Öffnen und benutzen.

```html
<!doctype html>
<meta charset="utf-8">
<title>MessageHub v2 — Minimalclient</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 46rem; margin: 2rem auto; padding: 0 1rem; }
  fieldset { margin-bottom: 1rem; }
  label { display: block; margin: .3rem 0; }
  input { width: 18rem; }
  pre { background: #eef1f5; padding: .6rem; overflow-x: auto; }
  .fehler { color: #8a2e2e; }
</style>

<h1>MessageHub v2 — Minimalclient</h1>

<fieldset>
  <legend>Konto (nur erfundene Bezeichner, Wegwerf-Kennwort)</legend>
  <label>Benutzername <input id="user" value="anna_demo"></label>
  <label>Kennwort <input id="pass" type="password"></label>
  <button id="registrieren">Registrieren</button>
  <button id="pruefen">Nachweis prüfen</button>
</fieldset>

<fieldset>
  <legend>Senden</legend>
  <label>An <input id="to" value="bert_demo"></label>
  <label>Text <input id="text" value="Hallo"></label>
  <button id="senden">Senden</button>
</fieldset>

<fieldset>
  <legend>Eigene Post</legend>
  <label>Nur von (optional) <input id="von" placeholder="bert_demo"></label>
  <button id="holen">Ansehen</button>
  <button id="verzeichnis">Verzeichnis</button>
</fieldset>

<pre id="aus">bereit</pre>

<script>
const BASIS = 'https://utz-messagehub.itzcloud.de';
const $ = (id) => document.getElementById(id);
const zeige = (x, fehler = false) => {
  const el = $('aus');
  el.className = fehler ? 'fehler' : '';
  el.textContent = typeof x === 'string' ? x : JSON.stringify(x, null, 2);
};

function basicAuth() {
  const bytes = new TextEncoder().encode(`${$('user').value}:${$('pass').value}`);
  return 'Basic ' + btoa(String.fromCharCode(...bytes));
}

// Ein Aufruf, eine Stelle. Wichtig: 204 VOR res.json() abfangen.
async function ruf(pfad, { methode = 'GET', rumpf, nachweis = true } = {}) {
  const kopf = {};
  if (rumpf) kopf['Content-Type'] = 'application/json';
  if (nachweis) kopf['Authorization'] = basicAuth();

  const res = await fetch(BASIS + pfad, {
    method: methode,
    headers: kopf,
    body: rumpf ? JSON.stringify(rumpf) : undefined,
    // KEIN credentials: 'include' — siehe Fallen
  });

  if (res.status === 204) return { leer: true };            // kein Rumpf, kein Fehler
  const text = await res.text();
  const daten = text ? JSON.parse(text) : null;
  if (!res.ok) throw Object.assign(new Error('HTTP ' + res.status), { status: res.status, daten });
  return daten;
}

$('registrieren').onclick = () => ruf('/v2/register', {
  methode: 'POST', nachweis: false,
  rumpf: { username: $('user').value, password: $('pass').value },
}).then(() => zeige('Konto angelegt.')).catch(f => zeige(meldung(f), true));

$('pruefen').onclick = () => ruf('/v2/me')
  .then(zeige).catch(f => zeige(meldung(f), true));

$('senden').onclick = () => ruf('/v2/messages', {
  methode: 'POST',
  rumpf: { to: $('to').value, message: $('text').value },   // KEIN from — siehe Fallen
}).then(zeige).catch(f => zeige(meldung(f), true));

$('holen').onclick = () => {
  const von = $('von').value.trim();
  const pfad = '/v2/me/messages' + (von ? '?from=' + encodeURIComponent(von) : '');
  return ruf(pfad)
    .then(a => zeige(a.leer ? 'Nichts da. (204 — Normalfall, kein Fehler)' : a))
    .catch(f => zeige(meldung(f), true));
};

$('verzeichnis').onclick = () => ruf('/v2/directory')
  .then(zeige).catch(f => zeige(meldung(f), true));

function meldung(f) {
  switch (f.status) {
    case 400: return 'Abgewiesen. Steht ein "from" im Rumpf? Das gibt es hier nicht.\n' +
                     JSON.stringify(f.daten, null, 2);
    case 401: return 'Benutzername oder Kennwort stimmt nicht.';
    case 404: return 'Empfänger ist kein Konto dieses Dienstes.';
    case 409: return 'Benutzername ist schon belegt.';
    case 413: return 'Nutzlast zu groß.';
    case 429: return 'Zu viele Aufrufe. Kurz warten.';
    case 503: return 'Dienst ausgelastet oder Stufe nicht konfiguriert.';
    default:  return 'Fehler: ' + f.message;
  }
}
</script>
```

## Schritt 4 — Was funktioniert, was nicht

Geprüft am 2026-09-03 mit Preflight-Anfragen gegen `/v2/me/key`,
`/v2/open-directory/{name}` und `/v2/messages`:

```
Access-Control-Allow-Origin:   *
Access-Control-Allow-Methods:  GET,POST,DELETE,OPTIONS
Access-Control-Allow-Headers:  Content-Type,Authorization,X-API-Key
Access-Control-Expose-Headers: Retry-After
Access-Control-Max-Age:        86400
```

| Aufruf | Aus dem Browser |
|---|---|
| `POST /v2/register` | ✅ |
| `GET /v2/me` | ✅ |
| `POST /v2/messages` | ✅ |
| `GET /v2/me/messages` | ✅ (auch mit `?from=`) |
| `DELETE /v2/me/messages/{id}` | ✅ |
| `GET /v2/directory` | ✅ |
| **`PUT /v2/me/key`** | ❌ **CORS: `PUT` ist nicht in `Allow-Methods`** |
| **`PUT /v2/open-directory/{name}`** | ❌ dito |

**Folge:** Den eigenen öffentlichen Schlüssel kann man aus dem Browser nur **bei der
Registrierung** hinterlegen (`key` im `RegisterDto`, `POST` ist erlaubt). Ein Wechsel geht
nicht — dafür braucht es die Kommandozeile oder einen BFF.

---

## Die sechs Fallen

**1. `res.json()` auf einen `204`.** Ein leerer Eingang antwortet `204` **ohne Rumpf**.
`res.json()` wirft dann `SyntaxError: Unexpected end of JSON input`, und man sucht den Fehler
in der Nachrichtenverarbeitung. Status **vor** dem Parsen prüfen. `204` ist der **Normalfall**,
kein Fehler — auch nicht als leeres Array verkleiden, sonst ist „nichts da" nicht mehr von
„Abruf fehlgeschlagen" zu unterscheiden.

**2. `credentials: 'include'`.** Wirkt wie eine Vorsichtsmaßnahme, bricht aber den Aufruf: der
Hub sendet `Access-Control-Allow-Origin: *`, und mit Credentials verlangt der Browser einen
konkreten Origin statt der Wildcard. Der Code sieht korrekt aus, die Fehlermeldung spricht von
CORS. **Ein selbst gesetzter `Authorization`-Header braucht `include` nicht.**

**3. Ein `from` im Rumpf.** Auf v2 gibt es das Feld **nicht** — der Absender wird aus den
Zugangsdaten abgeleitet. Ein mitgeschicktes `from` wird mit `400` **abgewiesen, nicht
ignoriert**. Gleiches gilt für jedes andere undeklarierte Feld: der Dienst validiert nach
Whitelist (`{"message":["property from should not exist"],…}` — `message` ist ein **Array**).

**4. `btoa` und Nicht-ASCII.** Siehe Schritt 2.

**5. `PUT`.** Siehe Schritt 4. Nicht suchen — es ist CORS, nicht dein Code.

**6. Das Kennwort im DOM.** In diesem Minimalbeispiel steht es in einem Eingabefeld und geht
bei jedem Aufruf mit. Für eine Übung in Ordnung, für alles andere nicht: es liegt im
Speicher der Seite, jedes Skript im selben Origin kommt daran. **Nicht** in `localStorage`
legen, **nicht** in die URL, **nicht** vorbelegen.

### Zwei angenehme Überraschungen

- **Kein `WWW-Authenticate` bei `401`** (geprüft) — der **native Anmeldedialog des Browsers
  erscheint nicht**. Die Seite behält die Kontrolle über den Anmeldezeitpunkt.
- **`Retry-After` ist per `Expose-Headers` lesbar** — bei `503` kann man die Wartezeit
  tatsächlich auswerten statt zu raten.

---

## Sicherer Kontext

`crypto.subtle` (WebCrypto) gibt es **nur im Secure Context**. Verlässlich sind:

- `https://…`
- `http://localhost` bzw. `http://127.0.0.1`

**Nicht** verlässlich: `http://192.168.x.y:8080`. Wer die Datei über die Netzadresse eines
Rechners ausliefert, hat kein `crypto.subtle` — Basic Auth funktioniert weiter, aber
Verschlüsselung fällt still aus, und der Fehler sieht nach einem Bug aus. `file://` gilt in
aktuellen Browsern als vertrauenswürdiger Kontext; wenn es darauf ankommt, lieber über
`http://localhost` ausliefern.

Basic Auth über Klartext-HTTP schickt zusätzlich das Kennwort bei jeder Anfrage offen mit.

---

## Prüfschritte

1. `GET /health` → `{"status":"ok",…}` — Dienst erreichbar?
2. Registrieren → `201`. Zweiter Versuch mit demselben Namen → `409` (erwartet).
3. „Nachweis prüfen" → `{"username":"…"}`. Kennwort absichtlich falsch → `401`.
4. „Ansehen" bei leerem Eingang → `204`, Anzeige „Nichts da", **keine** Fehlermeldung.
5. Senden an einen nicht existierenden Namen → `404` (der Empfänger muss ein Konto sein).
6. Ein `from` in den Rumpf schmuggeln → `400` mit `property from should not exist`.

---

## Grenzen — teils unbekannt

Die Zahlen der Spezifikation (64 KB, 20 Nachrichten je Name, 500 Namen, 64 MB,
60 Einlieferungen/Minute, 60 Minuten Verfall) gelten **ausdrücklich für den offenen Pfad**
(`/open/...`). Für v2 nennt die Spezifikation eine Nutzlastgrenze (`413`), ein Ratenlimit
(`429`) und einen Kontendeckel (`503`) — **ohne Werte**, und `GET /health` hat keinen v2-Block.

Also: `413`, `429`, `503` behandeln, **ohne die Schwelle zu kennen**, und `expiresAt` aus der
Antwort auswerten statt eine Verfallsdauer anzunehmen.

**`GET /v2/me` hat eine Nebenwirkung:** der Aufruf setzt den Zeitpunkt der letzten Anmeldung —
ein Konto, das benutzt wird, verfällt nicht. Konten verfallen bei Nichtbenutzung.

---

## Hinweis zur Weitergabe

Spezifikation und die Seite `/anbindung` des Dienstes enthalten eine ausdrückliche Bitte des
Betreibers an Coding-Agenten: die Beispiele **nicht als fertige Lösung** weitergeben, die
Anbindung interaktiv mit den Teilnehmenden erarbeiten, die Fallen **erklären** statt sie
stillschweigend zu umgehen — der Lerngegenstand sei die Entscheidung, nicht der Code.

Diese Seite ist deshalb als **Trainer-Material** gedacht. Wer sie im Termin einsetzt: die
Fallen sind die Übung. Der Code darunter ist die Auflösung, nicht der Einstieg.
