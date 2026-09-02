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
  antwortet mit `400 "property <x> should not exist"`. Ein „hilfreich" ergänzter Filter
  bricht den Aufruf ([ADR-0010](docs/adr/0010-striktes-anfrage-schema.md)).
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
| [docs/api-messagehub.md](docs/api-messagehub.md) | Der API-Vertrag und die Regeln seiner Nutzung |
| [docs/api/openapi.yaml](docs/api/openapi.yaml) | Eingefrorener Schnappschuss der Spezifikation |
| [docs/ux-bedienkonzept.md](docs/ux-bedienkonzept.md) | Bedienkonzept, Zustände, Sichtbarkeit |
| [docs/guardrails.md](docs/guardrails.md) | Was verboten ist und warum |
| [docs/conventions.md](docs/conventions.md) | Code- und Doku-Konventionen |
| [docs/adr/](docs/adr/) | Entscheidungen, einzeln begründet |
| [memory/](memory/) | Projektgedächtnis, versioniert und für alle Agenten lesbar |
| [PROMPTS.md](PROMPTS.md) | Prompt-Protokoll, generiert von `tools/collect_prompts.py` |

## Festgelegter Stack

Verbindlich, Begründungen in den verlinkten ADRs:

- **Frontend:** Angular mit Angular Material 3, ITZ-Hausstandard
  ([ADR-0004](docs/adr/0004-frontend-angular-material3.md))
- **Kein eigenes Backend.** Der Client spricht direkt mit dem MessageHub
  ([ADR-0003](docs/adr/0003-nur-offener-pfad.md))
- **Krypto:** WebCrypto, AES-GCM mit PBKDF2-Ableitung, umschaltbar gegen Klartext
  ([ADR-0007](docs/adr/0007-krypto-umschaltbar.md))
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
3. **Kein Absender-Filter.** `GET /open/messages` kennt **nur** `to`. Man holt immer den
   **ganzen Eingang** eines Namens, quer über alle Absender
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

**Zu TLS:** Das Hub-Zertifikat kommt aus einer ITZ-internen CA. Ist sie im lokalen
Trust-Store nicht vorhanden, scheitert `curl` mit Exit 60. Dann
`--cacert <pfad-zur-itz-ca>` verwenden — **nicht** `-k` und **nicht** die CA global
trusten (sie ist auch Wurzel eines TLS-Interception-Proxys).

## Was dieses Repo nicht enthält

- **Kein Code, solange die Entscheidungen nicht in ADRs stehen.** Der aktuelle Stand ist
  bewusst reine Dokumentation.
- **Keine Zugangsdaten, keine Schlüssel, keine Echtdaten.** Siehe
  [docs/guardrails.md](docs/guardrails.md).
- **Keine Implementierung der Token- oder OIDC-Stufe.** Die Nachrichten-Endpunkte dieser
  Stufen existieren am Hub nicht; `/oidc/config` liefert derzeit `configured: false`.
