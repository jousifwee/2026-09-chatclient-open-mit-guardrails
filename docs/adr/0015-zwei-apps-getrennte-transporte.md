# ADR-0015: Zwei Anwendungen in einem Workspace, getrennte Transporte

**Status:** angenommen (2026-09-03) — **Vertrag inzwischen bekannt**, siehe „Nachtrag:
v2 ist live". Offen bleibt allein die Krypto-Entscheidung für Anwendung 2.

## Kontext

Bisher war eine Anwendung vorgesehen, gegen den offenen Pfad des UTZ MessageHub
([ADR-0003](0003-nur-offener-pfad.md)). Vorgesehen sind nun **zwei**: die zweite soll einen
**v2-Dienst mit Basic Auth** anbinden.

**Verifiziert am 2026-09-03, kurz vor 11:25 Uhr, am laufenden Hub (`0.1.24+ee364d0`) — der v2-Dienst
war dort nicht zu finden.** Er kam wenige Minuten später mit einem Redeploy; siehe
„Nachtrag: v2 ist live" am Ende. Die Bestandsaufnahme bleibt stehen, weil sie die
Strukturentscheidung begründet:

- `GET /health` meldet `0.1.24+ee364d0` (am Vortag `0.1.16+6afc10e`), also ein neuer Build.
- Die Endpunktmenge ist **identisch** zum Vortag: `/health`, `/open/messages` (POST, GET),
  `/open/messages/{id}` (DELETE), `/open/names`, `/oidc/config`, `/oidc/whoami`,
  `/oidc/directory`. Kein neuer Endpunkt, kein `v2`, kein Basic Auth.
- Die **Token-Stufe wurde entfernt** — samt Security-Schema `kurs-token` (`X-API-Key`). Es
  bleiben zwei Stufen: offen und OIDC.
- Das einzige verbleibende Security-Schema ist `oidc` (Bearer-JWT).
- `/v2`, `/v2/messages`, `/basic`, `/basic/messages`, `/token/messages` antworten mit `200
  text/html` — das ist die Catch-all-Route der Angular-Oberfläche, kein API-Endpunkt.
- Neu ist eine Seite `/anbindung` („Muster für Client-Anbindung und Tokenerneuerung"). Auch
  sie ist eine Route dieser Oberfläche; im ausgelieferten JavaScript-Bundle kommen die
  Zeichenketten `basic`, `Authorization`, `btoa`, `X-API-Key` und `/v2` **nicht** vor.

Der v2-Dienst ist also entweder ein **anderer Dienst** unter anderer Adresse oder noch nicht
veröffentlicht. Entscheidbar ist damit heute die **Struktur**, nicht der Vertrag.

## Entscheidung

**Ein Angular-Workspace, zwei Anwendungen, getrennte Transporte.**

```
apps/
  chat-open/        Anwendung 1 — offener Pfad des MessageHub (ADR-0003)
  chat-v2/          Anwendung 2 — v2-Stufe des Hubs mit Basic Auth
libs/
  domain/           Konversationen, Nachrichtenzustände, Gruppierung, Namensregeln
  payload/          Umschlag und Krypto (ADR-0007)
  store/            IndexedDB-Historie (ADR-0011)
  ui/               gemeinsame Material-3-Bausteine
```

**Geteilt wird alles, was vom Nachweis unabhängig ist:** Umschlagformat und Krypto, die
lokale Historie, die Konversationsbildung, die Namensnormalisierung
([ADR-0014](0014-namen-kleinschreiben.md)), die Grenzwert-Konstanten und die UI-Bausteine.

**Nicht geteilt wird der Transport.** Jede Anwendung hat ihren **eigenen** — kein gemeinsames
Interface, keine Strategie-Klasse, kein Laufzeitschalter zwischen beiden.

**Zwei Anwendungen, keine Anwendung mit Umschalter.** Beide werden getrennt gebaut,
getrennt ausgeliefert und getrennt geöffnet.

### Was über Basic Auth heute schon festgelegt werden kann

Diese Punkte hängen nicht am Vertrag, sondern an Basic Auth und am Browser:

1. **Der Nachweis geht als selbst gesetzter Header** `Authorization: Basic <base64(user:pass)>`
   — nicht über den Zugangsdaten-Speicher des Browsers.
2. **`credentials: "include"` bleibt verboten**, auch hier
   ([ADR-0013](0013-cors-ohne-credentials.md)). Ein selbst gesetzter `Authorization`-Header
   braucht es **nicht**; `include` würde stattdessen den browsereigenen Zugangsdaten-Speicher
   einbeziehen und die CORS-Wildcard brechen. Die beiden Dinge werden regelmäßig verwechselt.
3. **Ein selbst gesetzter `Authorization`-Header macht die Anfrage cross-origin
   „non-simple"** — es gibt einen **Preflight** (`OPTIONS`). Der Dienst muss
   `Access-Control-Allow-Headers: Authorization` beantworten, sonst scheitert der Aufruf,
   bevor er gesendet wird. Das ist keine Client-Sache und im Zweifel beim Betreiber zu
   klären.
4. **`401` mit `WWW-Authenticate: Basic` löst den nativen Anmeldedialog des Browsers aus.**
   Der liegt außerhalb der Anwendung, sieht nach Fremdkörper aus und umgeht das eigene
   Bedienkonzept. Wenn der Dienst diesen Header sendet, ist das im Bedienkonzept zu behandeln
   und nicht zu ignorieren.
5. **Basic Auth sendet das Kennwort bei *jeder* Anfrage.** HTTPS ist damit nicht Kür sondern
   Pflicht — was der Secure Context für WebCrypto ohnehin erzwingt.
6. **Zugangsdaten sind Geheimnisse und leben nur im Arbeitsspeicher der laufenden Sitzung.**
   Nicht in IndexedDB, nicht in `localStorage`, nicht in `sessionStorage`, nicht in der URL,
   nicht im Repo, nicht in einer versionierten `.env`. Dieselbe Regel wie für die Passphrase
   ([ADR-0007](0007-krypto-umschaltbar.md), [guardrails.md](../guardrails.md)).
7. **Kein gemeinsames Kennwort im Code, auch nicht als Vorbelegung.** Der Nutzer gibt es ein.

## Begründung

- **Der Nachweis ist keine Konfiguration, sondern ein Wesensunterschied.** Er entscheidet,
  **woher der Absender kommt**: auf dem offenen Pfad ist `from` eine freie Behauptung
  ([ADR-0005](0005-konversation-ist-client-konstrukt.md)), bei einem Dienst mit Nachweis kann
  er aus dem Nachweis folgen. Davon hängen Konversationsbildung, Vertrauensanzeige und das
  Bedienkonzept ab — nicht nur ein Header.
- **Genau deshalb zwei Anwendungen und kein Umschalter.** Ein Laufzeitschalter zwängt beide
  Verhaltensweisen in einen Komponentenbaum und führt die Abstraktion wieder ein, die
  [ADR-0003](0003-nur-offener-pfad.md) verworfen hat. Zwei Ziele halten die Unterschiede
  sichtbar, statt sie in Bedingungen zu verstecken.
- **Zwei Anwendungen sind hier auch didaktisch der Punkt.** Der Kontrast „ohne Nachweis" gegen
  „mit Nachweis" ist nebeneinander vorführbar, wenn es zwei Fenster sind.
- **Ein Workspace statt zweier Repos**, weil Umschlag, Historie und Konversationslogik
  identisch sind. Zwei Repos würden sie duplizieren, und die Kopie veraltet.
- **Getrennte Transporte trotz gemeinsamer Bibliotheken**, weil nur der Transport sich
  wirklich unterscheidet. Alles andere kennt keinen Nachweis und soll ihn nicht kennen.

## Folgen

- Der Workspace bekommt zwei Build-Ziele und zwei Startbefehle; Anwendung 1 ist unabhängig von
  Anwendung 2 lauffähig und wird nicht durch deren offenen Vertrag blockiert.
- `libs/domain` darf **nichts** über Nachweise wissen. Wer dort ein Feld für Zugangsdaten
  einführt, verletzt diese ADR.
- Anwendung 2 braucht ein **eigenes Bedienkonzept**: dort folgt der Absender aus dem
  Nachweis, also entfällt die Anzeige „behauptet" — und es kommen Registrierung, Anmeldung
  und Schlüsselverzeichnis hinzu. Noch nicht geschrieben.
- Anwendung 1 bleibt auf dem Stand von ADR-0003: nichts zur OIDC-Stufe.

## Nachtrag: v2 ist live (2026-09-03, `0.1.29+039ba26`)

Der Dienst wurde um 11:25 Uhr neu ausgerollt und bringt die **v2-Stufe mit Basic Auth**
vollständig mit. Der Vertrag steht in [api-messagehub-v2.md](../api-messagehub-v2.md); hier
nur, was die offenen Punkte dieser ADR beantwortet:

| Frage von oben | Antwort |
|---|---|
| Basis-Adresse | derselbe Host, Pfadpräfix `/v2/...` |
| Spezifikation | `/openapi.json`, Schnappschuss im Repo |
| Folgt der Absender aus dem Nachweis? | **Ja.** `from` gibt es nicht; ein mitgeschicktes `from` wird mit `400` abgewiesen |
| Woher die Zugangsdaten? | **Selbstregistrierung** über `POST /v2/register`, je Teilnehmer ein Konto |
| `WWW-Authenticate` / CORS-Header | **noch nicht verifiziert**, beim ersten Aufruf zu prüfen |
| Gibt es Historie? | Die Ablage ist **dauerhaft**, Nachrichten verfallen aber weiterhin (`expiresAt`) |

**Damit ist diese ADR nicht überholt, sondern bestätigt.** Der Absender folgt auf v2 aus dem
Nachweis und ist auf dem offenen Pfad eine freie Behauptung — genau der Wesensunterschied,
der gegen einen Laufzeitschalter sprach. Dazu kommen drei weitere Unterschiede, die kein
Schalter überbrückt: der Empfänger muss ein Konto sein (`404` statt neues Fach), fremde
Fächer sind unerreichbar (kein `to`-Parameter), und es **gibt** einen Absender-Filter
(`?from=`), der auf dem offenen Pfad den Aufruf bricht.

### Was jetzt zusätzlich festgelegt ist

- **`apps/chat-v2/` bekommt seinen Transport gegen `/v2/...`.** Nicht mehr blockiert.
- **`libs/domain` bleibt nachweisfrei.** Dass der Absender auf v2 beglaubigt ist, ist eine
  Eigenschaft, die der Transport **als Feld mitliefert** — nicht eine Verzweigung in der
  Fachlogik. Die Anzeige „behauptet" gegen „nachgewiesen" ist ein Wert, keine Bedingung auf
  die Stufe.
- **Der Absender-Filter `?from=` gehört zu Anwendung 2 und nur dorthin.**
  [ADR-0010](0010-striktes-anfrage-schema.md) gilt für Anwendung 1 unverändert weiter: dort
  bricht dieser Parameter den Aufruf.
- **`/v2/open-directory` ist kein Bezugsweg für Schlüssel.** Die beiden Endpunkte sind
  erklärtermaßen dazu da, kaputt zu sein (jeder darf jeden Eintrag überschreiben). Wer von
  dort einen Schlüssel holt und damit verschlüsselt, führt den Mann-in-der-Mitte-Angriff aus,
  statt eine Anbindung zu bauen. Beglaubigt ist nur `GET /v2/directory`.
- **Kein hartkodierter Grenzwert für v2.** Die numerischen Grenzen der Spezifikation gelten
  ausdrücklich für den offenen Pfad; für v2 sind Nutzlastgrenze, Kontendeckel, Ratenlimit und
  Verfallsdauer **nicht genannt**, und `/health` hat keinen v2-Block. Der Client behandelt
  `413`, `429` und `503` ohne die Schwelle zu kennen und wertet `expiresAt` aus der Antwort
  aus.
- **Wegwerf-Kennwort.** Die Registrierung verlangt mindestens 8 Zeichen und sonst nichts; die
  Spezifikation bittet ausdrücklich um ein Kennwort, das nirgends sonst gilt. Der Client sagt
  das bei der Registrierung, statt es vorauszusetzen.

### Was noch offen ist

**Die Krypto-Entscheidung für Anwendung 2.** Die v2-Stufe hat ein beglaubigtes
Schlüsselverzeichnis (`PUT /v2/me/key`, `GET /v2/directory`) und die Spezifikation nennt
**JWK** als das im Kurs geltende Format — mit dem ausdrücklichen Hinweis, dass das Format
„im Leitplanken-Set" festgelegt wird, also hier. Damit wird asymmetrische Verschlüsselung
erstmals möglich, die [ADR-0007](0007-krypto-umschaltbar.md) für Anwendung 1 als eigenes
Projekt verworfen hatte — dort gab es keinen Vertrauensanker, hier gibt es einen.

Zu entscheiden ist, ob Anwendung 2 asymmetrisch verschlüsselt (und dann mit welchem
JWK-Format und welchem Fingerabdruckverfahren für den **mündlichen** Vergleich) oder die
Passphrasen-Variante aus ADR-0007 behält. Bis dahin wird für Anwendung 2 **keine** Krypto
implementiert.

## Verworfene Alternativen

- **Eine Anwendung mit Umschalter für den Nachweis.** Sieht sparsamer aus, führt aber die
  verworfene Stufen-Abstraktion wieder ein und verwischt genau den Unterschied, der gezeigt
  werden soll.
- **Zwei getrennte Repos.** Dupliziert Umschlag, Historie und Konversationslogik; die Kopie
  veraltet, und der Vergleich der beiden Varianten wird mühsam.
- **Anwendung 2 gegen die OIDC-Stufe des Hubs bauen** statt gegen einen v2-Dienst. Deren
  Nachrichten-Endpunkte existieren nicht, und `/oidc/config` liefert `configured: false`.
- **Basic Auth über den Zugangsdaten-Speicher des Browsers** (`credentials: "include"`, ohne
  eigenen Header). Löst den nativen Anmeldedialog aus, bricht die CORS-Wildcard und nimmt der
  Anwendung die Kontrolle über den Anmeldezeitpunkt.
- **Schon einen Transport für v2 schreiben und Endpunkte annehmen.** Genau der Freiraum, den
  [ADR-0001](0001-doku-zuerst.md) schließt. Ein geratener Vertrag kostet mehr als das Warten.
