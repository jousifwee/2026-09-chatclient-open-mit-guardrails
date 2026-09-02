# Architektur

Ableitung aus den Eigenschaften des Hubs ([api-messagehub.md](api-messagehub.md)) und den
Entscheidungen unter [adr/](adr/). Diese Datei beschreibt **Sollzustand**, nicht
Implementierungsstand — Code existiert noch nicht.

## Systemkontext

```
┌──────────────────────────┐          HTTPS, CORS *          ┌───────────────────────┐
│  Chatclient (Browser)    │ ──────────────────────────────> │  UTZ MessageHub       │
│  Angular + Material 3    │  POST/GET/DELETE /open/...      │  Warteschlange je     │
│                          │ <────────────────────────────── │  Empfängername        │
│  IndexedDB (Historie)    │          kein Nachweis          │  flüchtig, 60 min     │
└──────────────────────────┘                                 └───────────────────────┘
```

**Kein eigenes Backend.** Der Client spricht direkt mit dem Hub
([ADR-0003](adr/0003-nur-offener-pfad.md)). Es gibt keinen Server, der Zustand hält, keine
Sitzung, keine Anmeldung.

Damit ist der Client **die gesamte Anwendung** — und die einzige Stelle, an der Historie,
Konversationen und Vertraulichkeit überhaupt existieren.

## Schichten

Von außen nach innen. Jede Schicht kennt nur die nächste; keine Schicht darf eine
überspringen.

| Schicht | Aufgabe | Kennt nicht |
|---|---|---|
| **Ansicht** (Angular-Komponenten) | Darstellung, Nutzeraktionen | HTTP, Krypto, IndexedDB |
| **Zustand** (Signal-Store) | Konversationen, Nachrichtenzustände, Poll-Takt | HTTP-Details, Statuscodes |
| **Fachlogik** | Gruppieren nach `from`, Zustandsübergänge, Grenzwarnungen | Angular, DOM |
| **Nutzlast-Kodierung** (`PayloadCodec`) | Umschlag erzeugen und deuten, ver-/entschlüsseln | HTTP, Anzeige |
| **Transport** (`MessageTransport`) | Ein Aufruf je Endpunkt, Fehlerabbildung | Konversationen, Krypto |
| **Ablage** (`HistoryStore`) | IndexedDB lesen/schreiben | HTTP, Anzeige |

### Transport — `MessageTransport`

Dünn und dumm. Ein Verfahren je Endpunkt, keine Fachlogik. Aufgaben:

- **`200` gegen `204` unterscheiden** und diesen Unterschied nach oben tragen. `204` ist
  „nichts da", nicht „leeres Ergebnis" und nicht „Fehler".
- **Statuscodes in Fachfehler abbilden**: `413` zu groß · `429` mit Unterscheidung
  „Eingang voll" gegen „Rate-Limit" · `503` mit `Retry-After` · `400` Schemaverstoß, mit dem
  **Array** aus `message` als Detail.
- **Kein `credentials: "include"`** ([ADR-0013](adr/0013-cors-ohne-credentials.md)).
- **Keine undeklarierten Felder oder Parameter**
  ([ADR-0010](adr/0010-striktes-anfrage-schema.md)).

Die Schicht spricht den **offenen Pfad direkt** an. **Keine Stufen-Abstraktion:** Token- und
OIDC-Stufe sind in diesem Release ausdrücklich ignoriert, und eine Schnittstelle für
unbekanntes Verhalten wäre eine Vermutung, kein Entwurf
([ADR-0003](adr/0003-nur-offener-pfad.md)).

**Ein Naht ist trotzdem vorgesehen** — aber nur die, deren Form bekannt ist: Der Abruf des
Eingangs liegt hinter **genau einer Funktion**. Kommt die vom Betreiber angekündigte
serverseitige **Absender-Filterung**, ändert sich diese eine Stelle und sonst nichts. Bis der
Parameter in der Spezifikation steht, wird er **nicht gesendet** — auch nicht hinter einem
Schalter, auch nicht auskommentiert
([ADR-0005](adr/0005-konversation-ist-client-konstrukt.md),
[ADR-0010](adr/0010-striktes-anfrage-schema.md)).

### Nutzlast-Kodierung — `PayloadCodec`

Der Hub behandelt `message` als opake Zeichenkette. Was darin steht, legt dieses Projekt
selbst fest: einen **selbstbeschreibenden Umschlag**
([ADR-0007](adr/0007-krypto-umschaltbar.md)), damit der Empfänger je Nachricht erkennt, was
er vor sich hat.

```json
{ "v": 1, "mode": "plain", "body": "Hallo" }
```

```json
{ "v": 1, "mode": "aes-gcm",
  "kdf": { "alg": "PBKDF2", "hash": "SHA-256", "iter": 250000, "salt": "<b64>" },
  "iv": "<b64>", "ct": "<b64>" }
```

Der Umschlag geht **als JSON-Zeichenkette** in `message`, nicht Base64-verpackt. Das ist
Absicht: im Klartextmodus ist am Hub direkt sichtbar, dass dort nichts geschützt ist — genau
die Lehre des offenen Pfades.

**Deutung je Nachricht, nicht je Konversation.** Drei Ausgänge, alle drei normal:

| Fall | Ergebnis |
|---|---|
| Umschlag `mode: "plain"` | Klartext anzeigen |
| Umschlag `mode: "aes-gcm"`, Entschlüsselung gelingt | Klartext anzeigen |
| Umschlag `mode: "aes-gcm"`, Entschlüsselung scheitert | Zustand **nicht entschlüsselbar** |
| kein gültiger Umschlag (`JSON.parse` scheitert oder `v` fehlt) | Zustand **Fremdformat**, Rohtext gekürzt und als unsicher markiert |

**Fremdformat ist der Normalfall, nicht der Ausnahmefall.** Jeder Dritte kann in jeden
Eingang einliefern, mit beliebigem Inhalt. Ein `try/catch`, das hier eine Fehlermeldung
wirft, macht den Client durch eine fremde Nachricht unbenutzbar.

### Ablage — `HistoryStore`

**IndexedDB ist die einzige Historie, die es gibt** ([ADR-0011](adr/0011-lokale-persistenz-indexeddb.md)).
Der Hub hat keine, und nach dem Entnehmen ist die Nachricht dort fort.

Zwei Sammlungen:

- **`messages`** — je Nachricht: `id`, `direction` (`in`/`out`), `ownName`, `peerKey`,
  `replyTo`, entschlüsselter oder roher Text, `receivedAt`, `expiresAt`, `hubState`,
  `payloadState`.
- **`identities`** — der eigene gewählte Name und die zuletzt benutzten Namen.

**Zu `peerKey` und `replyTo`:** Namen werden kleingeschrieben
([ADR-0014](adr/0014-namen-kleinschreiben.md)). `peerKey` ist die kleingeschriebene Form und
dient als Schlüssel für Gruppierung, Anzeige und Index. `replyTo` ist das **rohe `from`**, wie
es eintraf — und **nur damit wird geantwortet**. Beide fallen fast immer zusammen; weichen sie
ab, würde eine Antwort an `peerKey` in einer anderen Warteschlange landen als der, die der
Absender abfragt, und niemand bekäme eine Fehlermeldung.

**Nicht in IndexedDB:** Passphrasen, abgeleitete Schlüssel, Klartext zu einer Nachricht, die
im Umschlag verschlüsselt war und deren Passphrase der Nutzer nicht mehr eingegeben hat.
Passphrasen leben ausschließlich im Arbeitsspeicher der laufenden Sitzung
([guardrails.md](guardrails.md)).

## Zustandsmodell einer Nachricht

Zwei unabhängige Achsen. Sie zu vermischen ist der häufigste Entwurfsfehler an diesem Dienst.

**Achse 1 — Wo liegt sie? (`hubState`)**

```
                  POST 201
   (neu) ──────────────────────> am Hub ──── DELETE 204 ────> nur lokal
                                   │
                                   ├──── 60 min ohne Aktion ──> verfallen
                                   │
                                   └──── von Dritten entnommen ──> verfallen*
```

`*` **Nicht unterscheidbar.** Ein `404` beim Entnehmen und ein Verschwinden aus dem Abruf
bedeuten „bereits entnommen **oder** verfallen" — der Hub sagt nicht, welches von beiden.
Der Client darf hier nichts behaupten, was er nicht weiß.

**Achse 2 — Kann ich sie lesen? (`payloadState`)** `klartext` · `entschlüsselt` ·
`nicht entschlüsselbar` · `fremdformat`.

Eine Nachricht kann „nur lokal" **und** „nicht entschlüsselbar" sein: entnommen, damit
unwiederbringlich, und trotzdem unleserlich. Das UI muss diesen Zustand darstellen können,
statt ihn für unmöglich zu halten.

## Datenfluss: ein Poll-Zyklus

```
1. GET /open/messages?to=<eigenerName>        genau EIN Aufruf, nie je Konversation
2. 204?  -> Zyklus endet, Takt verlangsamen. Kein Fehler.
3. 200:  Array, älteste zuerst
4. für jede Nachricht:
     a. unbekannte id?  -> in IndexedDB anlegen, hubState = "am Hub"
     b. PayloadCodec deuten -> payloadState setzen
     c. peerKey = from kleingeschrieben, replyTo = from roh
        nach peerKey einer Konversation zuordnen
        unbekannter peerKey -> neue Konversation, als UNBESTÄTIGT markiert
5. Belegung prüfen: Anzahl >= 16 von 20  -> Warnung im UI
6. KEIN automatisches DELETE. Entnehmen ist Nutzeraktion.
```

Schritt 6 ist der Kern von [ADR-0006](adr/0006-entnehmen-ist-nutzeraktion.md): der Client
holt beliebig oft, ohne etwas zu verbrauchen.

## Poll-Takt

Adaptiv ([ADR-0008](adr/0008-adaptives-polling.md)), mit festgelegten Werten — damit hier
niemand improvisiert:

| Lage | Intervall |
|---|---|
| Nach Senden oder eingegangener Nachricht | 3 s |
| Danach Verdopplung je leerem Zyklus | 3 → 6 → 12 → 24 → 48 s |
| Obergrenze im Leerlauf | 60 s |
| Tab nicht sichtbar (`visibilitychange`) | angehalten |
| `503` mit `Retry-After` | genau diese Wartezeit, dann Neustart bei 3 s |

Der Takt ist **sichtbar und übersteuerbar**: aktuelles Intervall, Zeitpunkt des letzten
Abrufs, Knopf für sofortiges Aktualisieren, Schalter zum Anhalten
([ux-bedienkonzept.md](ux-bedienkonzept.md)).

`GET` ist nicht rate-begrenzt, das Rate-Limit von 60/Minute betrifft nur `POST`. Der Takt ist
also keine technische Notwendigkeit, sondern Höflichkeit gegenüber einer Demo-Box — und wird
als solche begründet, nicht als Limit-Umgehung.

## Was bewusst offen ist

Kein Agent füllt diese Lücken selbst. Wer hier ankommt, schlägt eine ADR vor:

- **Mehrere eigene Namen gleichzeitig** (mehrere Eingänge in einer Sitzung) — nicht
  entschieden. Aktuell: genau ein eigener Name.
- **Export/Import der lokalen Historie** — nicht entschieden.
- **Zustellbestätigung** — vom Dienst nicht vorgesehen und **nicht nachbaubar**: ein
  Verschwinden aus dem Eingang kann Entnahme durch den Empfänger, Entnahme durch einen
  Dritten oder Verfall bedeuten.
- **Warnung bei ähnlichem Empfängernamen** (eingetippter Name unterscheidet sich von einem
  bekannten nur in der Schreibweise) — nicht entschieden
  ([ADR-0014](adr/0014-namen-kleinschreiben.md)).

Nicht offen, sondern **entschieden und abgeschlossen**: Token- und OIDC-Stufe sind in diesem
Release ignoriert ([ADR-0003](adr/0003-nur-offener-pfad.md)), Namenskollisionen durch
Groß-/Kleinschreibung sind über Kleinschreibung aufgelöst
([ADR-0014](adr/0014-namen-kleinschreiben.md)).
