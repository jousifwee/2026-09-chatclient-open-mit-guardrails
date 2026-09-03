# Fullstack-App mit BFF als Proxy vor dem MessageHub v2

> Vorlage für Confluence. Stand 2026-09-03, geprüft gegen `0.1.34+69b185d`.
> Gegenstück zur Seite *UTZ MessageHub v2 direkt aus einer HTML-Seite ansprechen*.

**Ziel:** Angular-SPA im Browser, dahinter ein eigener Server, der den MessageHub anspricht.
Der Browser redet nur mit dem eigenen Server.

Das ist das ITZ-Hausmuster: NestJS-BFF als alleiniges Gateway (EAST-ADR-0022), Cookie-Session
für Web und Bearer für native Clients (EAST-ADR-0023).

---

## Was ein BFF löst — und was nicht

**Löst er:**

| Problem im Browser | Mit BFF |
|---|---|
| CORS-Regeln des Hubs überhaupt | ✅ CORS ist ein **Browser**-Mechanismus. Server-zu-Server gibt es keinen Preflight |
| `credentials`/SameSite-Fragen gegen den Hub | ✅ entfällt — der Browser ruft nur die eigene Herkunft |
| v2-Kennwort liegt im Browser | ✅ kann im BFF bleiben |
| kein serverseitiges Rate-Limiting, keine Protokollierung | ✅ jetzt möglich |

**Löst er nicht:**

- **Die Grenzen des Hubs.** `413`, `429`, `503`, Verfall — alles unverändert, nur eine Ebene
  weiter weg.
- **Den Betrieb.** Ein BFF ist ein Dienst: bauen, ausliefern, betreiben, überwachen.
- **Und er nimmt die Fallen aus dem Blick.** CORS, SameSite, der `PUT`-Block sind nach dem
  Umbau unsichtbar. Wenn das Sichtbarmachen der Zweck war, ist das ein Verlust — dieselbe
  Kritik wie am Dev-Proxy, nur eine Ebene höher.

> **Der Anlassfall hat sich erledigt — und zeigt genau das.** Bis `0.1.29` war
> `PUT /v2/me/key` aus dem Browser unerreichbar, weil `PUT` in
> `Access-Control-Allow-Methods` fehlte. Der Weg heraus war **ein Eintrag in der
> CORS-Konfiguration** des Dienstes (`0.1.34`), nicht ein BFF. Ein BFF rechtfertigt sich über
> die anderen Punkte in dieser Tabelle, nicht über CORS.

---

## ⚠️ Die zwei Entwurfsentscheidungen, die man nicht übersehen darf

### 1. Wer ist der Absender?

Auf v2 wird `from` **aus den Zugangsdaten abgeleitet** — das ist die zentrale Eigenschaft der
Stufe. Ein BFF muss beantworten, wessen Zugangsdaten er benutzt:

| Variante | Folge |
|---|---|
| **Ein gemeinsames Kurs-Konto im BFF** | Alle Nutzer erscheinen als *derselbe* Absender. Der Nachweis kollabiert zu „der BFF war's" — die Eigenschaft, um die es auf v2 geht, ist weg |
| **Zugangsdaten je Sitzung im BFF halten** | Absender bleibt korrekt. Aber du betreibst jetzt einen **Credential-Store** — nur im Arbeitsspeicher, an eine Sitzung gebunden, nie auf Platte, nie im Protokoll |
| **Eigenes Konto-Modell im BFF, ein v2-Konto je Nutzer** | Sauber, aber du baust Nutzerverwaltung |

Es gibt hier keine bequeme Antwort. Die Entscheidung gehört dokumentiert, bevor Code entsteht.

### 2. Wo bleibt die Verschlüsselung?

Wenn die Nutzlast Ende-zu-Ende verschlüsselt sein soll, **muss die Krypto im Browser
bleiben**. Der private Schlüssel liegt dort als nicht exportierbarer `CryptoKey`
(`extractable: false`) in der IndexedDB — dann kann selbst der eigene Server nicht mitlesen.

**Verschlüsselt der BFF, ist es kein Ende-zu-Ende mehr.** Der Schlüssel liegt auf dem Server,
und der Server liest alles. Das ist eine legitime Architektur — aber eine andere, und sie muss
so benannt werden.

**Die saubere Variante:** Browser verschlüsselt, **BFF ist reiner Durchreiche-Proxy** für eine
opake Nutzlast. Er sieht Chiffrate, keine Klartexte, und hält keine Schlüssel. Damit bleibt
E2E erhalten *und* `PUT` funktioniert.

---

## Topologie

```
┌──────────────────────────┐   gleiche Herkunft    ┌─────────────────────────┐
│  Angular-SPA (Browser)   │ ────────────────────> │  BFF (NestJS)           │
│  Krypto: WebCrypto       │   Cookie-Session      │  hält v2-Zugangsdaten   │
│  Schlüssel: IndexedDB    │ <──────────────────── │  je Sitzung, im RAM     │
│  extractable: false      │   kein CORS           └───────────┬─────────────┘
└──────────────────────────┘                                   │
                                                Basic Auth,    │  Server-zu-Server:
                                                Header         │  kein CORS, PUT geht
                                                               ▼
                                                   ┌───────────────────────┐
                                                   │  UTZ MessageHub /v2   │
                                                   └───────────────────────┘
```

Die opake Nutzlast wird im Browser erzeugt und im Browser gelesen. Der BFF transportiert.

---

## Der BFF konkret (NestJS)

### Endpunkte, die er nach außen anbietet

Bewusst **nicht** 1:1 die Hub-Endpunkte, sondern fachlich:

| BFF | dahinter am Hub |
|---|---|
| `POST /api/session` (Benutzername + Kennwort) | `GET /v2/me` zur Prüfung, dann Sitzungscookie setzen |
| `DELETE /api/session` | Sitzung verwerfen |
| `GET /api/me` | `GET /v2/me` |
| `POST /api/messages` | `POST /v2/messages` |
| `GET /api/messages?from=` | `GET /v2/me/messages?from=` |
| `DELETE /api/messages/:id` | `DELETE /v2/me/messages/:id` |
| `PUT /api/me/key` | **`PUT /v2/me/key`** — hier funktioniert es |
| `GET /api/directory` | `GET /v2/directory` |

### Sitzung und Cookie

Weil Browser und BFF **gleiche Herkunft** haben, ist der Cookie-Teil unspektakulär:

```
Set-Cookie: sid=<opak>; HttpOnly; Secure; SameSite=Strict; Path=/
```

- **`HttpOnly`** — kein Zugriff aus JavaScript.
- **`Secure`** — nur über HTTPS.
- **`SameSite=Strict`** genügt bei gleicher Herkunft und deckt CSRF weitgehend ab.
- **Kein `Domain`-Attribut.** `Domain=.itzcloud.de` würde das Cookie an *jeden* Tenant der
  Box schicken — auch an `east`, `hkworkflow`, `itc-dim`, `auth`. Host-only.
- **`SameSite=None` braucht man hier nicht** und will man nicht: nur für echt cross-site
  nötig, erzwingt `Secure` und fällt unter den Third-Party-Cookie-Abbau.

**CSRF:** Mit einem Cookie hängt der Browser den Nachweis **automatisch** an — jede fremde
Seite kann damit authentifizierte Aufrufe auslösen. Beim `Authorization`-Header gibt es diese
Fläche nicht, weil ein Angreifer den Header nicht setzen kann. `SameSite=Strict` deckt den
Normalfall; wer sicher gehen will, nimmt zusätzlich ein Double-Submit-Token. `csurf` ist
abgekündigt, also selbst bauen oder eine gepflegte Bibliothek nehmen.

**Die v2-Zugangsdaten** liegen in der Sitzung des BFF — im **Arbeitsspeicher**, nie auf Platte,
nie im Protokoll, nie in einer Fehlermeldung. Ein Sitzungsspeicher, der auf Platte oder in
Redis persistiert, würde das Kennwort mitschreiben.

### Der Aufruf nach hinten

Server-zu-Server, ohne Browser-Regeln:

```ts
const auth = 'Basic ' + Buffer.from(`${user}:${pass}`).toString('base64');

const res = await fetch(`${HUB}/v2/me/messages`, { headers: { Authorization: auth } });
if (res.status === 204) return [];        // wie im Browser: 204 ist der Normalfall
if (!res.ok) throw abbilden(res);         // 400/401/404/413/429/503 fachlich abbilden
return res.json();
```

Zwei Dinge, die auch hier gelten:

- **`204` vor dem Parsen abfangen.** Der Fehler wandert sonst nur vom Browser in den Server.
- **Kein `from` im Rumpf** von `POST /v2/messages` — der Absender kommt aus dem Nachweis, ein
  mitgeschicktes `from` ergibt `400`.

Und eins, das *nur* hier gilt: **im ITZ-Netz** bricht der Interception-Proxy
`sofia.itz-rostock.de` die TLS-Verbindung auf. Node vertraut dessen Wurzel nicht, also
`NODE_EXTRA_CA_CERTS=<pfad-zu-ITZ08-CA.crt>` setzen. **Nicht**
`NODE_TLS_REJECT_UNAUTHORIZED=0` — das schaltet die Prüfung für *alle* Verbindungen ab.

---

## Gibt es bei Angular noch etwas anderes?

Ja, drei Wege neben dem separaten BFF. Bewertung ehrlich:

### a) Dev-Server-Proxy (`proxy.config.json`)

```json
{ "/api": { "target": "https://utz-messagehub.itzcloud.de", "secure": true, "changeOrigin": true } }
```

`ng serve` reicht die Aufrufe serverseitig weiter, damit sind sie gleiche Herkunft: CORS
entfällt vollständig, `PUT` inbegriffen.

**Aber nur in der Entwicklung.** Ein gebautes Bundle auf statischem Hosting hat keinen Proxy —
dann ist das Problem zurück. Genau die Dev-Prod-Divergenz, die man sonst dokumentiert:
funktioniert im Termin, bricht in der Auslieferung. **Als Lösung nicht geeignet, als
Zwischenschritt in Ordnung.**

### b) Angular SSR — `server.ts` als BFF im selben Projekt

Mit `@angular/ssr` (`ng add @angular/ssr`) liefert Angular einen Node-Server mit. Der ist
eine ganz normale Express-Anwendung, also kann man dort Server-Routen ergänzen: dieselbe
Herkunft für App und API, ohne ein zweites Projekt.

- **Vorteil:** ein Repo, ein Build, ein Deployment. Für zwei Handvoll Endpunkte deutlich
  weniger Gerüst als ein eigener NestJS-Dienst.
- **Nachteil:** Das Frontend wird serverseitig gerendert, obwohl es das nicht braucht — SSR
  bringt Hydration, Zustandsübertragung und eine zweite Ausführungsumgebung ins Spiel, in der
  `window`, `localStorage` und **`crypto.subtle`** nicht existieren. Für eine App mit
  WebCrypto und IndexedDB ist das eine Fehlerquelle, die man sich einkauft, ohne den Nutzen
  von SSR zu wollen.
- **Hausstand:** `extended-angular-standard-template` nutzt **kein** SSR (Builder
  `@angular/build:application`, keine `ssr`-Option). Wer SSR nur als BFF-Träger einführt,
  weicht vom Haus ab.

### c) Analog.js

Angular-Meta-Framework auf Vite, mit API-Routen im selben Projekt (`src/server/routes/`).
Kommt dem „Fullstack-Angular" am nächsten und braucht kein SSR für die Client-Teile.

**Aber:** kein ITZ-Hausstandard, eigene Konventionen, eigener Build. Für ein Lehrprojekt
interessant, für den Regelfall eine Abweichung, die man begründen muss.

### Nicht verwechseln: `HttpInterceptor`

Ein Interceptor, der `Authorization` an jeden Aufruf hängt, ist gute Praxis — aber **keine**
Lösung für CORS oder `PUT`. Er ändert nichts an den Browser-Regeln. (Und: er wirkt nur auf dem
Weg, in den er sich hängt — ein `fetch` daneben geht ohne Header hinaus, und der Fehler zeigt
auf den Dienst statt auf die verursachende Stelle.)

---

## Entscheidungshilfe

| Wenn … | dann |
|---|---|
| eine Methode ist im Browser blockiert | **eine Zeile CORS am Hub**, kein Umbau — so gelöst bei `PUT` in `0.1.34` |
| CORS und SameSite sollen sichtbar bleiben (Lehrzweck) | **direkt aus dem Browser**, siehe Seite 1 |
| Kennwort soll nicht in den Browser | **BFF** — separater NestJS-Dienst, Hausmuster |
| serverseitiges Rate-Limiting / Protokollierung nötig | **BFF** |
| Ende-zu-Ende-Verschlüsselung soll bleiben | BFF **nur als Durchreiche**, Krypto im Browser |
| ein Repo, wenig Gerüst, kein SSR-Bedarf | **Analog.js** prüfen — mit Abweichungsbegründung |
| schnell etwas zeigen, nur lokal | **Dev-Proxy** — und wissen, dass es in Prod nicht trägt |

---

## Fallen des BFF-Wegs

1. **Das Kennwort landet doch auf Platte** — über einen persistenten Sitzungsspeicher, ein
   Debug-Log oder eine Fehlermeldung, die den ganzen Request mitschreibt. Zugangsdaten aus
   Protokollen ausdrücklich herausfiltern.
2. **Der BFF wird zum offenen Weiterleiter.** Wer `/api/*` ungeprüft an den Hub durchreicht,
   hat einen Proxy gebaut, den jeder für beliebige Hub-Aufrufe benutzen kann. Nur die
   fachlichen Endpunkte anbieten, keine Wildcard-Route.
3. **`NODE_TLS_REJECT_UNAUTHORIZED=0`** als Abkürzung im ITZ-Netz. Schaltet die
   Zertifikatsprüfung für **alle** Verbindungen des Prozesses ab. Stattdessen
   `NODE_EXTRA_CA_CERTS`.
4. **Fehler werden verschluckt.** `429` und `503` vom Hub müssen als solche beim Client
   ankommen — mit `Retry-After`. Ein BFF, der alles auf `500` abbildet, macht die Grenzen des
   Hubs unsichtbar.
5. **Der BFF cacht.** Verlockend bei `GET /v2/me/messages`, aber der Abruf ist die einzige
   Quelle für neue Nachrichten. Ein Cache erzeugt „meine Nachricht kommt nicht an".
6. **Ende-zu-Ende wird still aufgegeben**, weil Verschlüsseln im BFF bequemer war. Wenn, dann
   als benannte Entscheidung.

---

## Compliance

Unverändert, auf beiden Wegen: nur synthetische Testdaten, erfundene Benutzernamen (sie sind
die Adresse), Wegwerf-Kennwörter. Der Hub läuft auf einer Demo-Box bei einem externen Anbieter
in einer öffentlichen Cloud und wird jederzeit zurückgesetzt.

Ein BFF ändert daran nichts — er verlagert nur, wo die Daten durchlaufen. Er ist selbst eine
Stelle mehr, an der ein Kennwort versehentlich im Protokoll landet.
