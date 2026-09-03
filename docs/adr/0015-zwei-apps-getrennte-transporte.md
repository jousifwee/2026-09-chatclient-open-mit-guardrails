# ADR-0015: Zwei Anwendungen in einem Workspace, getrennte Transporte

**Status:** angenommen (2026-09-03) — **Teil offen:** der API-Vertrag der zweiten Anwendung
ist noch nicht bekannt, siehe „Was blockiert ist"

## Kontext

Bisher war eine Anwendung vorgesehen, gegen den offenen Pfad des UTZ MessageHub
([ADR-0003](0003-nur-offener-pfad.md)). Vorgesehen sind nun **zwei**: die zweite soll einen
**v2-Dienst mit Basic Auth** anbinden.

**Verifiziert am 2026-09-03 am laufenden Hub — dieser v2-Dienst ist dort nicht zu finden:**

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
  chat-v2/          Anwendung 2 — v2-Dienst mit Basic Auth (Vertrag offen)
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
- Ob Anwendung 2 ein eigenes Bedienkonzept braucht, ist offen und hängt daran, ob der Absender
  aus dem Nachweis folgt.
- Anwendung 1 bleibt auf dem Stand von ADR-0003: nichts zur OIDC-Stufe.

## Was blockiert ist

Der Vertrag von Anwendung 2 lässt sich nicht schreiben, und nach
[ADR-0001](0001-doku-zuerst.md) wird er auch nicht geraten. Gebraucht werden:

1. **Basis-Adresse** des v2-Dienstes.
2. **Spezifikation** — OpenAPI-Adresse oder die Endpunkte samt Feldern.
3. **Ob der Absender aus dem Nachweis folgt** oder weiterhin ein Feld des Anfragekörpers ist.
   Das ist die Frage mit den größten Folgen fürs Bedienkonzept.
4. **Woher die Zugangsdaten kommen** — je Teilnehmer oder ein gemeinsames Kurs-Konto.
5. **Ob der Dienst `WWW-Authenticate: Basic` sendet** (nativer Browserdialog, siehe oben) und
   ob sein CORS `Authorization` in `Access-Control-Allow-Headers` erlaubt.
6. **Ob es Historie gibt.** Ein Dienst mit dauerhafter Ablage würde
   [ADR-0011](0011-lokale-persistenz-indexeddb.md) für Anwendung 2 ablösen — dann wäre
   IndexedDB dort nicht mehr die einzige Historie.

Bis diese Punkte geklärt sind, existiert `apps/chat-v2/` als Ziel im Workspace, aber ohne
Transport und ohne Bedienkonzept.

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
