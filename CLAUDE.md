# CLAUDE.md

Verbindliche Instruktionen für Agenten/LLMs, die in diesem Repo arbeiten. **Diese Datei ist
die Quelle der Wahrheit.** [AGENTS.md](AGENTS.md) und
[.github/copilot-instructions.md](.github/copilot-instructions.md) sind nur Zeiger hierher
und dürfen inhaltlich nicht abweichen — wer hier etwas ändert, prüft beide Zeiger.

## Worum es geht

Ein Chatclient gegen den **UTZ MessageHub** (<https://utz-messagehub.itzcloud.de/>), einen
öffentlichen Store-and-forward-Vermittlungsdienst. Der eigentliche Zweck des Projekts ist
**nicht der Chatclient**, sondern das Erlernen von zwei Dingen:

1. **Guardrails** — ausführbare und dokumentierte Grenzen für Agentenarbeit.
2. **Agentenlesbare Projektdokumentation** — Architektur, Funktion und UX so festgelegt,
   dass ein Agent beim Codieren keine Freiräume mit Annahmen füllt.

Daraus folgt die zentrale Arbeitsregel dieses Repos:

> **⚠️ Doku zuerst, Code danach.** Jede Architektur-, Funktions- und UX-Entscheidung wird
> **vor** der Implementierung in Markdown fixiert — als ADR unter [`docs/adr/`](docs/adr/)
> und, wo nötig, im Fließtext der Fachdokumente. Wer beim Codieren auf eine ungeklärte
> Frage stößt, **implementiert nicht auf Verdacht**, sondern hält an, schlägt eine ADR vor
> und lässt sie entscheiden.

## Erste Reflexe

- **⚠️ ADRs sind verbindlich.** [`docs/adr/`](docs/adr/) überschreibt Bauchgefühl,
  Framework-Defaults und Gewohnheit. Bei Konflikt gilt die ADR.
- **⚠️ Nur synthetische Bezeichner.** `to` und `from` niemals mit echten Vor- oder
  Nachnamen belegen. `GET /open/names` veröffentlicht jeden benutzten Namen im Internet
  ([ADR-0009](docs/adr/0009-nur-synthetische-bezeichner.md)).
- **⚠️ Keine undeklarierten Felder oder Query-Parameter.** Der Hub validiert strikt und
  antwortet mit `400 "property <x> should not exist"`. Ein ergänzter Filter bricht den
  Aufruf. Das gilt **auch für die angekündigte Absender-Filterung**: bis sie in der
  Spezifikation steht, wird sie nicht gesendet
  ([ADR-0010](docs/adr/0010-striktes-anfrage-schema.md)).
- **⚠️ Namen immer kleinschreiben.** Der Hub unterscheidet Groß-/Kleinschreibung, `anna` und
  `Anna` sind zwei Warteschlangen. Eingaben werden normalisiert; **geantwortet wird an das
  rohe `from`** ([ADR-0014](docs/adr/0014-namen-kleinschreiben.md)).
- **⚠️ Kein `credentials: "include"`.** Der Hub sendet `Access-Control-Allow-Origin: *`
  und braucht keine Credentials. Mit `include` verlangt der Browser einen konkreten Origin
  statt der Wildcard und der Aufruf scheitert, obwohl der Code korrekt aussieht
  ([ADR-0013](docs/adr/0013-cors-ohne-credentials.md)).
- **Vor dem Behaupten: verifizieren.** Der API-Vertrag steht in
  [`docs/api-messagehub.md`](docs/api-messagehub.md), der Schnappschuss der Spezifikation
  in [`docs/api/openapi.yaml`](docs/api/openapi.yaml). Keine Endpunkte, Felder oder
  Statuscodes aus dem Gedächtnis zitieren.
- **Bei Zielkonflikt zwischen Bequemlichkeit und Nachvollziehbarkeit** gewinnt in diesem
  Repo die Nachvollziehbarkeit. Das ist der Projektzweck, nicht ein Nebenaspekt.

## Doku-Karte

| Datei | Inhalt |
|---|---|
| [README.md](README.md) | Einstieg für Menschen |
| **CLAUDE.md** (diese Datei) | Verbindliche Agenten-Instruktionen, Quelle der Wahrheit |
| [AGENTS.md](AGENTS.md) | Tool-agnostischer Zeiger auf diese Datei |
| [.github/copilot-instructions.md](.github/copilot-instructions.md) | Zeiger für GitHub Copilot |
| [docs/architecture.md](docs/architecture.md) | Bausteine, Schichten, Datenfluss, Zustand |
| [docs/api-messagehub.md](docs/api-messagehub.md) | Vertrag des **offenen Pfades** und die Regeln seiner Nutzung |
| [docs/api-messagehub-v2.md](docs/api-messagehub-v2.md) | Vertrag der **v2-Stufe**: Basic Auth, Konten, Schlüsselverzeichnis |
| [docs/api/openapi.yaml](docs/api/openapi.yaml) | Eingefrorener Schnappschuss der Spezifikation |
| [docs/ux-bedienkonzept.md](docs/ux-bedienkonzept.md) | Bedienkonzept, Zustände, Sichtbarkeit |
| [docs/guardrails.md](docs/guardrails.md) | Was verboten ist und warum |
| [docs/conventions.md](docs/conventions.md) | Code- und Doku-Konventionen |
| [docs/adr/](docs/adr/) | Entscheidungen, einzeln begründet |
| [docs/confluence/](docs/confluence/) | Trainer-Material für den Entwicklertreff (Confluence-Vorlagen) — **nicht** verbindlich |
| [memory/](memory/) | Projektgedächtnis, versioniert und für alle Agenten lesbar |
| [PROMPTS.md](PROMPTS.md) | Prompt-Protokoll, generiert von `tools/collect_prompts.py` |

## Zwei Anwendungen

Der Workspace enthält **zwei** Anwendungen mit **getrennten Transporten**
([ADR-0015](docs/adr/0015-zwei-apps-getrennte-transporte.md)):

- **`apps/chat-open/`** — offener Pfad des MessageHub, ohne Nachweis. Vollständig
  spezifiziert, siehe [docs/](docs/).
- **`apps/chat-v2/`** — v2-Stufe des Hubs mit **Basic Auth**, seit `0.1.29+039ba26`
  (2026-09-03) in Betrieb. Vertrag in
  [docs/api-messagehub-v2.md](docs/api-messagehub-v2.md). Dort ist der Absender **aus dem
  Nachweis abgeleitet**, der Empfänger muss ein Konto sein, fremde Fächer sind unerreichbar,
  und `?from=` filtert nach Absender. Krypto: **asymmetrisch**
  ([ADR-0018](docs/adr/0018-app2-asymmetrisch-ecdh.md)).
- **`PUT` ist erlaubt** seit `0.1.34+69b185d` (verifiziert). Schlüsselwechsel über
  `PUT /v2/me/key` ist möglich — dabei gilt: **ausgemusterte Schlüssel bleiben in IndexedDB**
  und werden nur zum Entschlüsseln benutzt, und der Fingerabdruck muss **erneut mündlich**
  verglichen werden (ADR-0018).
- Geteilt werden `libs/domain`, `libs/payload`, `libs/store`, `libs/ui`. **`libs/domain` darf
  nichts über Nachweise wissen.**

## Festgelegter Stack

Verbindlich, Begründungen in den verlinkten ADRs:

- **Frontend:** Angular mit Angular Material 3, ITZ-Hausstandard
  ([ADR-0004](docs/adr/0004-frontend-angular-material3.md))
- **Kein eigenes Backend.** Der Client spricht direkt mit dem MessageHub
  ([ADR-0003](docs/adr/0003-nur-offener-pfad.md))
- **Angular `^21.2`** mit `@angular/build` (esbuild), TypeScript `~5.9.3`, npm mit
  `package-lock.json` ([ADR-0016](docs/adr/0016-browser-stack-angular21.md))
- **Tests:** Vitest (Unit/Component) + Playwright (E2E); die Guardrails der Stufe 2 sind als
  Tests zu schreiben ([ADR-0017](docs/adr/0017-teststack-vitest-playwright.md))
- **Krypto App 1:** WebCrypto, AES-GCM mit PBKDF2-Ableitung, umschaltbar gegen Klartext
  ([ADR-0007](docs/adr/0007-krypto-umschaltbar.md))
- **Krypto App 2:** asymmetrisch — ECDH P-256, HKDF-SHA-256, AES-GCM; privater Schlüssel
  **nicht exportierbar** in IndexedDB; Fingerabdruck mündlich vergleichen
  ([ADR-0018](docs/adr/0018-app2-asymmetrisch-ecdh.md))
- **Keine Stufen-Abstraktion.** Token und OIDC sind in diesem Release ignoriert
  ([ADR-0003](docs/adr/0003-nur-offener-pfad.md))
- **Lokale Persistenz:** IndexedDB, einzige Historie überhaupt
  ([ADR-0011](docs/adr/0011-lokale-persistenz-indexeddb.md))
- **Abruf:** adaptives Polling ([ADR-0008](docs/adr/0008-adaptives-polling.md))

## Die fünf Eigenschaften des Hubs, die alles bestimmen

Wer diese fünf nicht im Kopf hat, entwirft am Dienst vorbei. Herleitung in
[docs/api-messagehub.md](docs/api-messagehub.md).

1. **Keine Historie.** Der Hub ist eine Warteschlange je Empfängername, kein Chat. Verfall
   nach 60 Minuten, höchstens 20 Nachrichten je Name.
2. **Ansehen und Entnehmen sind getrennt.** `GET` ist folgenlos und wiederholbar,
   `DELETE /open/messages/{id}` entnimmt endgültig und genau einmal.
3. **Kein Absender-Filter — noch nicht.** `GET /open/messages` kennt **nur** `to`. Man holt
   immer den **ganzen Eingang** eines Namens, quer über alle Absender. Eine serverseitige
   Filterung ist angekündigt; vorbereitet ist die *Stelle*, nicht der *Aufruf*
   ([ADR-0005](docs/adr/0005-konversation-ist-client-konstrukt.md)).
4. **Kein Nachweis, für nichts.** Jeder darf jede Warteschlange lesen **und** entnehmen.
   `from` ist eine unbeglaubigte Behauptung.
5. **Die Nutzlast ist opak.** Der Hub interpretiert sie nicht. Vertraulichkeit entsteht
   ausschließlich daraus, dass der Client verschlüsselt einliefert.

## Schnellbefehle

```bash
# Prompt-Protokoll neu erzeugen (PROMPTS.md wird komplett überschrieben)
python tools/collect_prompts.py

# Läuft der Hub? Belegung und Grenzen der flüchtigen Ablage
curl -s https://utz-messagehub.itzcloud.de/health

# Aktuelle Spezifikation gegen den Schnappschuss im Repo prüfen
curl -s https://utz-messagehub.itzcloud.de/openapi.yaml | diff -u docs/api/openapi.yaml -
```

**Zu TLS:** Der Hub liefert ein Let's-Encrypt-Zertifikat. **Im ITZ-Netz** wird die
Verbindung aber vom Interception-Proxy `sofia.itz-rostock.de` aufgebrochen und neu
signiert — dann scheitert `curl` mit Exit 60. Abhilfe: `--cacert <pfad-zu-ITZ08-CA.crt>`.
**Nicht** `-k`, und die Wurzel **nicht global** trusten (sie beglaubigt auch jede
aufgebrochene Verbindung). Details in
[docs/api-messagehub.md](docs/api-messagehub.md).

## Was dieses Repo nicht enthält

- **Kein Code, solange die Entscheidungen nicht in ADRs stehen.** Der aktuelle Stand ist
  bewusst reine Dokumentation.
- **Keine Zugangsdaten, keine Schlüssel, keine Echtdaten.** Siehe
  [docs/guardrails.md](docs/guardrails.md).
- **Nichts zur Token- oder OIDC-Stufe.** In diesem Release ausdrücklich ignoriert: keine
  Anmeldung, kein Bearer-Header, kein Aufruf unter `/oidc/`, keine Abstraktion und kein
  UI-Element, das eine Stufe ankündigt. Die Nachrichten-Endpunkte der OIDC-Stufe existieren
  am Hub nicht; `/oidc/config` liefert `configured: false`. Die frühere Token-Stufe ist am
  2026-09-03 **aus der Spezifikation entfernt** worden
  ([ADR-0003](docs/adr/0003-nur-offener-pfad.md)).
