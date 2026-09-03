# Guardrails

Was in diesem Projekt verboten ist, und warum. Verbindlich für Menschen **und** Agenten.

Guardrails sind hier nicht Beiwerk, sondern der Lerngegenstand: geübt wird, Grenzen so zu
formulieren, dass ein Agent sie beim Codieren nicht versehentlich überschreibt — und so zu
begründen, dass ein Mensch sie nicht aus Bequemlichkeit aufhebt.

## Stufe 1 — Daten: was niemals hineingeht

Gilt für den Hub, für Code, für Tests, für Beispiele in der Dokumentation, für Prompts an
KI-Werkzeuge und für Commit-Nachrichten.

**Verboten:**

- **Personenbezogene Daten** jeder Art — Bürger, Kunden, Kollegen. Ausdrücklich **auch
  Namen** in `to` und `from`.
- **Zugangsdaten, Secrets, Schlüssel, Passwörter.**
- **Echtdaten aus Produktivsystemen**, auch anonymisiert aussehende.
- **Vertrauliche Vertrags- und Vergabeunterlagen.**

**Warum beim Hub besonders:** Der Dienst läuft auf einer Demo-Box bei einem externen Anbieter
in einer öffentlichen Cloud, ohne Nachweis für irgendetwas. `GET /open/names` **listet jeden
benutzten Namen öffentlich auf**, und `GET /open/messages?to=<name>` liefert jedem Fremden
den vollständigen Eingang. Ein echter Nachname im Feld `from` steht damit im Internet.

**Im Zweifel: anonymisieren oder weglassen.** Wer versehentlich etwas Falsches eingegeben
hat: stoppen und an <tobias.haefner@itz-rostock.de> melden.

**Erlaubte Namensform:** erfundene Bezeichner nach `^[A-Za-z0-9_-]{1,32}$`, erkennbar
synthetisch. Konvention in diesem Projekt: Präfix nach Zweck, etwa `anna_demo`,
`bert_demo`, `etreff_probe_a`. Siehe
[ADR-0009](adr/0009-nur-synthetische-bezeichner.md).

## Stufe 2 — API: was den Aufruf bricht

Fallen, die einen fertig aussehenden Aufruf scheitern lassen. Vollständige Begründung in
[api-messagehub.md](api-messagehub.md).

| Verboten | Folge | Regel |
|---|---|---|
| Undeklarierte Query-Parameter oder Rumpffelder | `400 "property x should not exist"` | [ADR-0010](adr/0010-striktes-anfrage-schema.md) |
| `credentials: "include"` | CORS scheitert gegen `Allow-Origin: *` | [ADR-0013](adr/0013-cors-ohne-credentials.md) |
| Erfundener Absender-Filter, Paginierung, Sortierung | existiert nicht, siehe oben | [ADR-0005](adr/0005-konversation-ist-client-konstrukt.md) |
| Ein `GET` je Konversation | N-mal derselbe Aufruf für dieselben Daten | [ADR-0005](adr/0005-konversation-ist-client-konstrukt.md) |
| `204` als Fehler behandeln | leerer Eingang ist der Normalfall | [ADR-0012](adr/0012-fehler-und-grenzfaelle.md) |
| Automatisches `DELETE` nach dem Anzeigen | unwiederbringlicher Datenverlust | [ADR-0006](adr/0006-entnehmen-ist-nutzeraktion.md) |
| Fester Retry gegen `503` | ignoriert `Retry-After`, verschärft die Auslastung | [ADR-0012](adr/0012-fehler-und-grenzfaelle.md) |
| Ausnahme bei unlesbarer Nutzlast | ein Fremder macht den Client unbenutzbar | [ADR-0007](adr/0007-krypto-umschaltbar.md) |
| Behaupteten Absender als Identität behandeln | jeder kann jeden Namen angeben | [ADR-0005](adr/0005-konversation-ist-client-konstrukt.md) |
| An die kleingeschriebene Form antworten statt an das rohe `from` | lautlos unzustellbar | [ADR-0014](adr/0014-namen-kleinschreiben.md) |
| Etwas zur OIDC-Stufe einbauen | in diesem Release ignoriert | [ADR-0003](adr/0003-nur-offener-pfad.md) |
| Auf v2 ein `from` im Rumpf senden | Absender kommt aus dem Nachweis, `400` | [api-messagehub-v2.md](api-messagehub-v2.md) |
| Schlüssel aus `/v2/open-directory` beziehen | dort überschreibt jeder jeden Eintrag | [ADR-0015](adr/0015-zwei-apps-getrennte-transporte.md) |
| Grenzwerte des offenen Pfades auf v2 anwenden | für v2 nicht genannt | [api-messagehub-v2.md](api-messagehub-v2.md) |
| Krypto in `apps/chat-v2` implementieren | noch nicht entschieden | [ADR-0015](adr/0015-zwei-apps-getrennte-transporte.md) |
| Nachweise in `libs/domain` einführen | Schichtbruch, Nachweis ist Transportsache | [ADR-0015](adr/0015-zwei-apps-getrennte-transporte.md) |
| Zugangsdaten vorbelegen oder speichern | Geheimnis an Ruhe | [ADR-0015](adr/0015-zwei-apps-getrennte-transporte.md) |
| Den angekündigten Absender-Filter vorab senden | existiert nicht, `400` | [ADR-0010](adr/0010-striktes-anfrage-schema.md) |
| `-k` bei `curl` gegen den Hub | umgeht Zertifikatsprüfung; interne CA ist auch Interception-Wurzel | [api-messagehub.md](api-messagehub.md) |

## Stufe 3 — Vorgehen: Doku zuerst

**Jede Architektur-, Funktions- und UX-Entscheidung wird vor der Implementierung in Markdown
fixiert** ([ADR-0001](adr/0001-doku-zuerst.md)).

Verboten ist damit ausdrücklich:

- **Implementieren auf Verdacht.** Wer beim Codieren auf eine Frage stößt, die keine ADR
  beantwortet, hält an und schlägt eine ADR vor. Er entscheidet nicht im Code.
- **Entscheidungen im Code verstecken.** Ein Wert wie „Poll-Intervall 5 s" gehört in eine
  ADR und ins Bedienkonzept, nicht nur in eine Konstante.
- **ADRs stillschweigend überholen.** Weicht der Code von einer ADR ab, ist entweder der Code
  falsch oder die ADR ersetzungsbedürftig — beides wird benannt, nicht ausgesessen.
- **Doku nachziehen statt vorziehen.** „Ich baue es erst und dokumentiere danach" ist genau
  der Modus, den dieses Projekt abstellen soll.

Die Liste **„Was bewusst offen ist"** in [architecture.md](architecture.md) ist die
verbindliche Stelle für ungeklärte Punkte. Wer dort etwas findet, das er braucht, schreibt
eine ADR.

## Stufe 4 — Geheimnisse und lokale Ablage

- **Nichts Geheimes im Repo.** Keine `.env`, keine Schlüssel, keine Zertifikatsschlüssel.
  `.gitignore` deckt `.env*`, `secrets/`, `*.pem`, `*.key` ab — das ist eine Hilfe, kein
  Ersatz für Aufmerksamkeit.
- **Passphrasen nur im Arbeitsspeicher.** Nicht in IndexedDB, nicht in `localStorage`, nicht
  in `sessionStorage`, nicht in der URL. Nach dem Neuladen wird erneut gefragt
  ([ADR-0007](adr/0007-krypto-umschaltbar.md)).
- **Zugangsdaten für Basic Auth genauso** — nur im Arbeitsspeicher, nie vorbelegt, nie im
  Repo, nie in einer versionierten `.env`. Basic Auth sendet das Kennwort bei *jeder*
  Anfrage, HTTPS ist damit Pflicht
  ([ADR-0015](adr/0015-zwei-apps-getrennte-transporte.md)).
- **Keine abgeleiteten Schlüssel persistieren.** Ein gespeicherter Schlüssel ist ein
  gespeichertes Geheimnis.
- **Die interne ITZ-CA nicht global trusten.** Sie ist gemeinsame Wurzel der internen
  Service-PKI **und** eines TLS-Interception-Proxys. Für Kommandozeilen-Aufrufe gezielt
  `--cacert` verwenden.

## Stufe 5 — KI-Nutzung

Die Richtlinie zur KI-Nutzung des ITZ Rostock gilt unverändert und geht individuellen
Vorlieben vor:

- KI-Werkzeuge sind für Code, Architektur, Konfiguration, Doku, Texte, Recherche und
  Problemlösung ausdrücklich erwünscht.
- **Tabu bleibt**, was unter Stufe 1 steht — auch als Prompt-Inhalt.
- **Output ist Entwurf, kein Ergebnis.** Vor produktivem Einsatz prüfen. Das gilt für jede
  Zeile in diesem Repo, einschließlich dieser Datei.

## Wie diese Guardrails wirken sollen

Drei Wege, absichtlich verschieden hart:

1. **Gelesen** — [CLAUDE.md](../CLAUDE.md) verweist auf diese Datei; Claude, Copilot und
   Mensch lesen dieselben Regeln über
   [AGENTS.md](../AGENTS.md) und
   [.github/copilot-instructions.md](../.github/copilot-instructions.md).
2. **Begründet** — jede Regel trägt ihren Grund. Eine Regel ohne Grund wird umgangen, sobald
   sie unbequem wird.
3. **Erzwungen** — soweit die Werkzeugkette es hergibt: `.gitignore` für Geheimnisse,
   Schema-Validierung im Client, Muster-Prüfung für Namen.

Stufe 3 ist noch dünn, und das ist bekannt. Ausführbare Guardrails (Hooks,
Permission-Allowlist, Lint-Regeln gegen die verbotenen Muster aus Stufe 2) sind ein
ausdrückliches Ziel dieses Projekts und noch nicht umgesetzt.
