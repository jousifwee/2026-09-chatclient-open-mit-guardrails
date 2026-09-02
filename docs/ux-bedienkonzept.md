# Bedienkonzept

Verbindlich. Was hier steht, ist entschieden; was hier fehlt, ist **nicht** entschieden und
wird nicht beim Implementieren erfunden.

Grundlage: Angular Material 3 ([ADR-0004](adr/0004-frontend-angular-material3.md)),
explizites Entnehmen ([ADR-0006](adr/0006-entnehmen-ist-nutzeraktion.md)), umschaltbare
Krypto ([ADR-0007](adr/0007-krypto-umschaltbar.md)), adaptives Polling
([ADR-0008](adr/0008-adaptives-polling.md)).

## Die Leitidee

Der Client sieht aus wie ein Chat, **verspricht aber nichts, was der Dienst nicht hält**. Die
Store-and-forward-Semantik wird nicht versteckt, sondern gezeigt. Wer diesen Client benutzt,
soll danach verstanden haben, warum der offene Pfad kein Messenger ist.

Drei Dinge dürfen deshalb nie zusammengeschminkt werden:

1. **Liegt am Hub** ist nicht dasselbe wie **liegt bei mir**.
2. **Behaupteter Absender** ist nicht dasselbe wie **Absender**.
3. **Verschickt** ist nicht dasselbe wie **angekommen** — und Letzteres ist hier
   grundsätzlich unbekannt.

## Aufbau

```
┌───────────────────────────────────────────────────────────────────────┐
│  Ich bin: [ anna_demo ]  ✏     Eingang 3/20     ⟳ vor 4 s  ⏸  ⚙       │
├──────────────────────┬────────────────────────────────────────────────┤
│ Konversationen       │  bert_demo            ● unbestätigt   🔓 offen │
│                      │ ┌────────────────────────────────────────────┐ │
│ ● bert_demo      2   │ │ ← Hallo               am Hub   ⬇ entnehmen │ │
│   unbestätigt        │ │   verfällt in 41 min                       │ │
│                      │ │                                            │ │
│ ○ carl_demo      0   │ │ → Moin                nur lokal            │ │
│   🔒 verschlüsselt   │ │ ← ▨ nicht entschlüsselbar   ⬇ entnehmen    │ │
│                      │ └────────────────────────────────────────────┘ │
│ ○ fremd_xyz      1   │  Betriebsart: ( ) Klartext  (•) Verschlüsselt  │
│   ⚠ Fremdformat      │  [ Nachricht … ]                    [ Senden ] │
└──────────────────────┴────────────────────────────────────────────────┘
```

## Der eigene Name

- Beim ersten Start **Pflichteingabe**, kein Vorschlag und keine Zufallsvergabe.
- Validierung gegen `^[A-Za-z0-9_-]{1,32}$`, **während** der Eingabe.
- Über dem Feld steht dauerhaft: *„Dieser Name wird über `GET /open/names` öffentlich im
  Internet sichtbar. Nur erfundene Bezeichner verwenden — keine echten Vor- oder
  Nachnamen."* ([ADR-0009](adr/0009-nur-synthetische-bezeichner.md))
- **Keine Heuristik, die echte Namen erkennen will.** Eine Prüfung, die „anna" durchlässt und
  „Anna Schmidt" ablehnt, erzeugt Vertrauen, das sie nicht rechtfertigt. Stattdessen: klare
  Ansage, Verantwortung beim Nutzer.
- Genau **ein** eigener Name gleichzeitig. Wechseln ist möglich und wechselt den Eingang
  vollständig; die lokale Historie des alten Namens bleibt erhalten.
- **Das Feld schreibt klein.** Getipptes `Anna` erscheint sofort als `anna` — es gibt keinen
  Zustand, in dem der Nutzer etwas anderes sieht als das, was gesendet wird. Grund: der Hub
  unterscheidet Groß-/Kleinschreibung, `anna` und `Anna` wären zwei getrennte Eingänge
  ([ADR-0014](adr/0014-namen-kleinschreiben.md)). Dasselbe gilt für das Empfängerfeld.

## Konversationen

Eine Konversation ist ein **clientseitiges Konstrukt**: alle Nachrichten mit demselben
behaupteten `from` beziehungsweise demselben gewählten `to`
([ADR-0005](adr/0005-konversation-ist-client-konstrukt.md)).

- Neue Konversation entsteht **automatisch**, sobald ein unbekanntes `from` im Eingang
  auftaucht, und wird als **unbestätigt** markiert.
- Die Markierung verschwindet erst, wenn der Nutzer sie ausdrücklich bestätigt. Sie
  verschwindet **nicht** dadurch, dass mehrere Nachrichten desselben Namens kommen — das
  kann jeder herbeiführen.
- Neben jedem Namen steht die Zahl der Nachrichten, die **noch am Hub liegen**, nicht die
  Länge des lokalen Verlaufs.
- Der Titel einer Konversation trägt bei unbestätigten Namen den Zusatz **„behauptet"**.
  Nirgends im UI erscheint ein Absender ohne diese Einordnung als gesicherte Identität.
- **Großgeschriebene Absender:** Namen werden zur Anzeige kleingeschrieben, geantwortet wird
  aber an die rohe Schreibweise. Weichen beide ab, steht in der Konversation: *Dieser
  Absender benutzt Großbuchstaben (`Heiko`) — Antworten gehen an genau diese Schreibweise.*
  ([ADR-0014](adr/0014-namen-kleinschreiben.md))

## Nachrichtenzustände

Jede Nachricht zeigt beide Achsen aus [architecture.md](architecture.md):

| Anzeige | Bedeutung |
|---|---|
| **am Hub** + Restlaufzeit | liegt in der Warteschlange, jeder kann sie lesen und entnehmen |
| **nur lokal** | entnommen oder von mir gesendet; am Hub nicht mehr vorhanden |
| **fort** | beim Entnehmen kam `404` — bereits entnommen **oder** verfallen |
| ▨ **nicht entschlüsselbar** | gültiger Umschlag, falsche oder fehlende Passphrase |
| ⚠ **Fremdformat** | kein Umschlag dieses Projekts; Rohtext gekürzt, als unsicher markiert |

**„fort" behauptet keine Ursache.** Der Dienst unterscheidet Entnahme und Verfall nicht, also
tut der Client es auch nicht. Formulierung im UI: *„Nicht mehr am Hub — entnommen oder
verfallen."*

Die Restlaufzeit wird als **verbleibende Dauer** gezeigt („verfällt in 41 min"), nicht als
Zeitstempel: `expiresAt` ist UTC, und eine Zeitzonenverwechslung wäre hier besonders
irreführend.

## Entnehmen

Der bewusste Kern des Bedienkonzepts ([ADR-0006](adr/0006-entnehmen-ist-nutzeraktion.md)).

- **Anzeigen entnimmt nicht.** Eine gelesene Nachricht bleibt am Hub liegen, bis der Nutzer
  handelt oder sie verfällt.
- Knopf **⬇ Entnehmen** je Nachricht, dazu **„Alle entnehmen"** je Konversation.
- Vor dem Entnehmen ein Hinweis, beim ersten Mal je Sitzung als Dialog, danach als Kurztext:
  *„Entnehmen ist endgültig. Die Nachricht ist danach nur noch auf diesem Gerät vorhanden."*
- Kein automatisches Entnehmen. Keine Einstellung, die es einschaltet. **Diese Regel ist
  nicht konfigurierbar** — sie ist der Lerngegenstand.
- Nach dem Entnehmen wechselt die Nachricht sichtbar von „am Hub" auf „nur lokal", statt aus
  der Liste zu verschwinden.

## Belegung des Eingangs

Der Hub nimmt höchstens **20 Nachrichten je Empfängername** an — über alle Absender
zusammen. Läuft der Eingang voll, scheitert jede weitere Einlieferung **an diesen Namen** mit
`429`, egal von wem.

- Dauerhafte Anzeige **„Eingang n/20"** in der Kopfzeile.
- Ab **16** Warnfarbe und Hinweis: *„Eingang fast voll. Weitere Nachrichten an dich werden
  abgewiesen, bis du entnimmst."*
- Bei **20** deutlicher Hinweis mit direktem Weg zum Entnehmen.

Das ist kein Komfortdetail: ohne diese Anzeige ist der Grund für ausbleibende Nachrichten für
den Nutzer unsichtbar.

## Betriebsart Klartext oder verschlüsselt

Umschaltbar **je Konversation** ([ADR-0007](adr/0007-krypto-umschaltbar.md)), sichtbar am
Schloss-Symbol.

- **🔓 Klartext:** die Nutzlast steht lesbar am Hub. Beim Umschalten einmal je Konversation
  der Hinweis: *„Im Klartext kann jeder mit deinem Namen die Nachricht lesen — der Eingang
  ist ohne Nachweis abrufbar."*
- **🔒 Verschlüsselt:** Passphrase je Konversation, Eingabe beim Öffnen. Die Passphrase lebt
  **nur im Arbeitsspeicher der laufenden Sitzung** und wird nirgends gespeichert; nach dem
  Neuladen wird sie erneut verlangt.
- Die Betriebsart gilt fürs **Senden**. Beim **Empfangen** entscheidet der Umschlag jeder
  einzelnen Nachricht — eine verschlüsselte Konversation kann Klartext enthalten und
  umgekehrt.
- Kein stiller Fehlschlag: gelingt die Entschlüsselung nicht, steht die Nachricht als
  **nicht entschlüsselbar** in der Liste, mit Knopf „Passphrase erneut eingeben".

## Aktualisieren

Adaptiver Takt ([ADR-0008](adr/0008-adaptives-polling.md)), aber **nie verdeckt**:

- Kopfzeile zeigt **„⟳ vor n s"** — Zeitpunkt des letzten Abrufs.
- Klick darauf holt sofort.
- **⏸** hält das Polling an; im angehaltenen Zustand ist das deutlich sichtbar.
- Bei nicht sichtbarem Tab pausiert der Takt und die Kopfzeile sagt das nach dem
  Zurückkehren.
- Bei `503` mit `Retry-After`: Anzeige *„Hub ausgelastet, nächster Versuch in n s"* — kein
  stilles Weiterhämmern.

## Fehlermeldungen

Jede Meldung nennt **was passiert ist** und **was der Nutzer tun kann**. Keine Statuscodes im
Text für Endnutzer, aber der Code in der Detailansicht — das Projekt ist ein Lehrstück.

| Lage | Text |
|---|---|
| `413` | „Zu lang. Der Hub nimmt höchstens 64 KB je Nachricht." |
| `429` Eingang voll | „Der Eingang von *name* ist voll (20). Der Empfänger muss erst entnehmen." |
| `429` Rate-Limit | „Zu viele Einlieferungen in kurzer Zeit. In einer Minute erneut." |
| `503` | „Der Hub ist ausgelastet. Nächster Versuch in n s." |
| `400` | „Der Hub hat die Anfrage abgewiesen." + `message`-Array in der Detailansicht |
| Netzfehler | „Hub nicht erreichbar." + Hinweis auf Erreichbarkeit, **kein** stiller Retry |
| `404` beim Entnehmen | „Nicht mehr am Hub — entnommen oder verfallen." |

`204` ist **keine** Fehlermeldung und erzeugt keine. Leerer Eingang ist der Normalzustand.

## Compliance-Hinweis im UI

Dauerhaft erreichbar, nicht wegklickbar versteckt, beim ersten Start als Dialog:

> Dieser Dienst läuft auf einer Demo-Box bei einem externen Anbieter in einer öffentlichen
> Cloud. Nur erfundene Testdaten eingeben. Keine personenbezogenen Daten, keine Kundendaten,
> keine Zugangsdaten, keine Echtdaten aus Produktivsystemen — auch nicht zum Ausprobieren.
> Das gilt **auch für die Namen**: `GET /open/names` veröffentlicht jeden benutzten Namen.

## Barrierefreiheit und Darstellung

- Zustände **nie allein über Farbe**. Jeder Zustand hat Text oder Symbol.
- Hell und dunkel gleichwertig; der Hub selbst folgt `prefers-color-scheme`, der Client
  ebenso.
- Bedienbar ohne Maus: Konversationswechsel, Senden und Entnehmen über die Tastatur.
- Entnehmen ist eine zerstörende Aktion und darf **nicht** auf einem Fokus- oder
  Hover-Ereignis ausgelöst werden.
