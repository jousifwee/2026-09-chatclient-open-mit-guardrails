# Der v2-Vertrag des UTZ MessageHub — Basic Auth, Konten, Schlüsselverzeichnis

Basis: `https://utz-messagehub.itzcloud.de` · Schnappschuss in
[`api/openapi.yaml`](api/openapi.yaml) (Fassung `0.1.34+69b185d`, geholt am 2026-09-03).

Gegenstück zu [api-messagehub.md](api-messagehub.md), das den **offenen Pfad** beschreibt.
Wieder gilt: hier steht **nur, was verifiziert ist** — aus der Spezifikation gelesen oder am
laufenden Dienst geprüft.

Die v2-Stufe ist die Grundlage von **Anwendung 2**
([ADR-0015](adr/0015-zwei-apps-getrennte-transporte.md)).

## Die drei Stufen des Dienstes

| Stufe | Pfad | Nachweis | Was der Dienst weiß | Ablage | Zustand |
|---|---|---|---|---|---|
| offen | `/open/...` | keiner | nichts | flüchtig, 60 min | in Betrieb |
| **v2** | `/v2/...` | **Basic Auth**, eigenes Konto | wer der Aufrufer ist — *auf sein Wort hin registriert* | **dauerhaft** | **in Betrieb** |
| OIDC | `/oidc/...` | Bearer-JWT | wer der Aufrufer ist — vom Haus-Anbieter bestätigt | dauerhaft | Nachrichten-Endpunkte fehlen |

> Ein Konto `anna` auf der v2-Stufe und ein Realm-Benutzer `anna` auf der OIDC-Stufe sind
> laut Spezifikation **zwei verschiedene Personen** mit zwei Postfächern, die einander nicht
> sehen. Getrennte Endpunkte, getrennte Ablagen, kein Übergang.

## Was v2 grundlegend anders macht als der offene Pfad

Vier Unterschiede. Sie sind der Grund, warum Anwendung 2 einen **eigenen** Transport hat und
kein Schalter genügt.

**1. `from` gibt es nicht.** Der Absender wird aus den Zugangsdaten abgeleitet. Ein
mitgeschicktes `from` wird **abgewiesen (400), nicht ignoriert**. Damit ist der Absender auf
dieser Stufe ein **Nachweis, keine Behauptung** — die zentrale Eigenschaft, an der auf dem
offenen Pfad alles hing.

**2. Der Empfänger muss ein Konto sein.** Es entsteht kein Fach durch Einliefern. Unbekannter
Name ergibt **404**. Auf dem offenen Pfad war jeder Name sofort belieferbar.

**3. Fremde Fächer sind nicht erreichbar.** `GET /v2/me/messages` hat **keinen
`to`-Parameter** — der Empfänger ist immer der Aufrufer. Eine fremde Nachrichten-Kennung
ergibt beim Entnehmen **404, auch wenn sie existiert**; die Antwort verrät nicht, ob es die
Nachricht gibt.

**4. Es gibt einen Absender-Filter.** `GET /v2/me/messages?from=<name>` — optional, und auf
dieser Stufe filtert er nach einem **nachgewiesenen** Absender. Auf dem offenen Pfad
existiert dieser Parameter nicht und bricht den Aufruf
([ADR-0010](adr/0010-striktes-anfrage-schema.md)).

## Endpunkte

### `POST /v2/register` — Konto anlegen · **ohne Nachweis**

Der **einzige** Endpunkt dieser Stufe ohne Nachweis: wer sich registriert, hat noch keinen.
Danach gelten Benutzername und Kennwort als Basic Auth für jeden weiteren Aufruf. **Der
Benutzername ist zugleich die Adresse.**

Rumpf `RegisterDto`:

| Feld | Regel |
|---|---|
| `username` | `^[A-Za-z0-9_-]{1,32}$`, erforderlich. Belegt → `409` |
| `password` | mindestens 8 Zeichen, erforderlich, keine weitere Regel |
| `key` | optional: öffentlicher Schlüssel gleich mit hinterlegen, opake Zeichenkette |

`201` angelegt · `400` Vorgabe verletzt · `409` Name belegt · `429` zu viele Registrierungen
von diesem Aufrufer · `503` Stufe nicht konfiguriert oder Gesamtzahl der Konten erreicht.

> **⚠️ Wegwerf-Kennwort, keines das anderswo gilt.** Sagt die Spezifikation selbst. Gespeichert
> wird nur ein scrypt-Hash, nie das Kennwort — aber der Dienst läuft auf einer Demo-Box bei
> einem externen Anbieter und wird jederzeit zurückgesetzt.

### `GET /v2/me` — eigenen Nachweis prüfen

Der billigste Weg zu prüfen, ob Zugangsdaten stimmen, **bevor** damit eingeliefert wird.
`200` mit `V2WhoamiDto` (`username`) · `401` falsch · `503` Stufe nicht konfiguriert.

**Nebenwirkung, die man kennen muss:** Der Aufruf setzt den Zeitpunkt der letzten Anmeldung —
**ein Konto, das benutzt wird, verfällt nicht.** Konten verfallen also bei Nichtbenutzung.

### `POST /v2/messages` — einliefern

Rumpf `V2SubmitDto`: `to` (`^[A-Za-z0-9_-]{1,32}$`, **muss vorhandenes Konto sein**),
`message` (opak, mindestens 1 Zeichen). **Kein `from`.**

`201` mit `V2AcceptedDto` (`id`, `expiresAt`) · `400` Schema verletzt, *etwa ein
mitgeschicktes `from`* · `401` · `404` Empfänger ist kein Konto · `413` Nutzlast zu groß ·
`503`.

### `GET /v2/me/messages` — eigene Post ansehen

Ohne Nebenwirkung, beliebig wiederholbar, älteste zuerst. Optionaler Parameter `from`.
`200` mit `V2MessageDto[]` · **`204` keine Nachrichten (oder keine von diesem Absender)** ·
`401`.

`V2MessageDto`: `id`, `to`, `from`, `message`, `receivedAt`, `expiresAt` — alle erforderlich.

### `DELETE /v2/me/messages/{id}` — entnehmen

Genau eine Nachricht aus dem **eigenen** Fach, genau einmal. `204` · `401` · `404` nicht
(mehr) vorhanden, verfallen **oder fremdes Fach**.

Die Trennung von Ansehen und Entnehmen ist wie auf dem offenen Pfad begründet: der Dienst ist
öffentlich erreichbar, und Crawler, Link-Vorschauen oder Client-Wiederholungen würden
Nachrichten sonst verbrauchen, bevor der Empfänger sie holt.

### `PUT /v2/me/key` — eigenen öffentlichen Schlüssel setzen

Rumpf `KeyDto` (`key`, opak). Überschreibt, idempotent — ein Konto hat genau einen Eintrag.
`204` · `401`.

Ende-zu-Ende verifiziert am 2026-09-03 gegen `0.1.34`: `204`, der Schlüssel erscheint danach
in `GET /v2/directory`, ein zweites `PUT` ersetzt ihn.

> **Bis `0.1.29` war dieser Endpunkt aus dem Browser gesperrt**, weil `PUT` in
> `Access-Control-Allow-Methods` fehlte. Mit `0.1.34` ist das behoben. Die Folgen für den
> Schlüsselwechsel — ausgemusterte Schlüssel behalten, Fingerabdruck erneut mündlich
> vergleichen — stehen in [ADR-0018](adr/0018-app2-asymmetrisch-ecdh.md).

**Auf dieser Stufe ist der Eintrag beglaubigt:** nur der Kontoinhaber kann ihn setzen.

Der Dienst behandelt den Schlüssel als **opake Zeichenkette**: kein Format, keine Prüfung,
kein Fingerabdruck. Die Spezifikation sagt ausdrücklich, wer das festlegt: *„Welches Format im
Kurs gilt (JWK), steht im Leitplanken-Set, nicht in diesem Dienst."* — also **hier**, in
diesem Repo.

### `GET /v2/directory` — Konten und ihre Schlüssel · **mit Nachweis**

`200` mit `V2DirectoryEntryDto[]` (`username`, optional `key`), nach Benutzername sortiert ·
`401` (verifiziert: ohne Nachweis kommt `401`).

Braucht bewusst einen Nachweis — ein offenes Namensregister wäre auf einer Stufe mit Konten
ein Bruch: es verriete alle Kontonamen, während alles andere geschützt ist. (Auf dem offenen
Pfad ist `GET /open/names` dagegen absichtlich öffentlich.)

Fehlt der `key`, ist das Konto trotzdem erreichbar — **man kann ihm schreiben, nur nicht für
ihn verschlüsseln.**

## ⚠️ Das Spielfeld: `/v2/open-directory`

Zwei Endpunkte **ohne Nachweis**, deren erklärter Zweck es ist, kaputt zu sein:

- `GET /v2/open-directory` → `OpenKeyEntryDto[]` (`name`, `material`, `updatedAt`,
  `expiresAt`). Verifiziert: liefert derzeit `[]`.
- `PUT /v2/open-directory/{name}` → `204`. **Für JEDEN Namen, ohne Prüfung, ob er dir
  gehört.** Seit `0.1.34` auch aus dem Browser aufrufbar (verifiziert). Ob Anwendung 2 das
  anbietet, ist offen — von der Kommandozeile vorgeführt ist es ehrlicher, weil der Angreifer
  dort kein Knopf im Client des Opfers ist.
- Beobachtet: Einträge des Spielfelds tragen ein `expiresAt` von **etwa 48 Stunden** (gesetzt
  2026-09-03, verfällt 2026-09-05). Die Spezifikation nennt keine Dauer — also nicht darauf
  bauen.

Wörtlich aus der Spezifikation:

> Ein Dritter ersetzt den Eintrag von B durch seinen eigenen Schlüssel, A verschlüsselt für
> den Angreifer, B kann nicht entschlüsseln — und beide halten den Kanal für sicher.
> Mann-in-der-Mitte, vorführbar statt erzählt.
>
> Das echte Gegenmittel ist kein Endpunkt, sondern eine Gewohnheit: Fingerabdrücke
> **mündlich** vergleichen.

Eigene Ablage — was hier passiert, kann die beglaubigten Schlüssel unter `/v2/directory`
nicht beschädigen. `updatedAt` sagt, wann überschrieben wurde; **von wem, weiß der Dienst
nicht.**

**Regel für dieses Projekt:** `/v2/open-directory` ist **kein Bezugsweg für Schlüssel**. Ein
Client, der von dort einen Schlüssel holt und damit verschlüsselt, ist der Vorführfall des
Angriffs, nicht eine Anbindung. Wenn Anwendung 2 das Spielfeld benutzt, dann als
**ausdrücklich als unsicher gekennzeichneter Vorführmodus**.

## Grenzen — teils unbekannt, und das ist relevant

Die numerischen Grenzen in der Spezifikation (64 KB, 20 Nachrichten je Name, 500 Namen, 64 MB,
60 Einlieferungen/Minute, 60 Minuten Verfall) sind **ausdrücklich die des offenen Pfades**.

Für v2 nennt die Spezifikation:

| Grenze | Angabe |
|---|---|
| Nutzlast | Größengrenze vorhanden (`413`), **Wert nicht genannt** |
| Registrierungen | ratenbegrenzt (`429`), **Wert nicht genannt** |
| Gesamtzahl Konten | gedeckelt (`503`), **Wert nicht genannt** |
| Nachrichten je Konto | **nicht genannt** |
| Verfall der Nachrichten | `expiresAt` je Nachricht, Dauer **nicht genannt** |
| Verfall der Konten | bei Nichtbenutzung; `GET /v2/me` setzt den Zeitpunkt zurück |

`GET /health` enthält **keinen** v2-Block — die Belegungszahlen des offenen Pfades gibt es
dort, die der v2-Stufe nicht.

**Folge für den Client:** Er muss `413`, `429` und `503` behandeln, **ohne die Schwelle zu
kennen**. Keine hartkodierte Byte-Grenze für v2, kein „ab 16 von 20" wie auf dem offenen Pfad
— stattdessen `expiresAt` aus der Antwort auswerten und die Fehler als Fakten nehmen.
Vermutete Werte gehören nicht in den Code
([ADR-0001](adr/0001-doku-zuerst.md)).

## Basic Auth im Browser

Das gilt unabhängig vom Vertrag und ist in
[ADR-0015](adr/0015-zwei-apps-getrennte-transporte.md) festgelegt:

- Nachweis als **selbst gesetzter** Header `Authorization: Basic <base64(user:pass)>`.
- **Kein `credentials: "include"`** — für einen selbst gesetzten Header nicht nötig; es würde
  stattdessen den browsereigenen Zugangsdaten-Speicher einbeziehen und die CORS-Wildcard
  brechen ([ADR-0013](adr/0013-cors-ohne-credentials.md)).
- Der Header macht die Anfrage cross-origin **„non-simple"** → **Preflight**. **Verifiziert
  am 2026-09-03:** der Dienst antwortet
  `Access-Control-Allow-Headers: Content-Type,Authorization,X-API-Key` — der Nachweis darf
  also mitgeschickt werden.
- **Kein `WWW-Authenticate` bei `401`** (verifiziert): der native Anmeldedialog des Browsers
  erscheint **nicht**. Die Anwendung behält die Kontrolle über den Anmeldezeitpunkt.
- **`PUT` ist erlaubt** — seit `0.1.34+69b185d`. `Access-Control-Allow-Methods` liefert
  `GET,POST,PUT,DELETE,OPTIONS` (verifiziert). Bis `0.1.29` fehlte `PUT`, und
  `PUT /v2/me/key` war aus dem Browser unerreichbar; die Geschichte samt Folgen für den
  Schlüsselwechsel steht in [ADR-0018](adr/0018-app2-asymmetrisch-ecdh.md).
- `Access-Control-Max-Age: 86400` — ein zwischengespeicherter Preflight gilt 24 Stunden.
  Nach einer serverseitigen CORS-Änderung in einem frischen Browserprofil prüfen.
- `Access-Control-Expose-Headers: Retry-After` — `Retry-After` ist aus JavaScript lesbar.
- Das Kennwort geht bei **jeder** Anfrage mit. HTTPS ist Pflicht.
- **Zugangsdaten nur im Arbeitsspeicher**, nie vorbelegt, nie im Repo
  ([guardrails.md](guardrails.md)).

## Hinweis des Betreibers an Coding-Agenten

Spezifikation und die Seite `/anbindung` enthalten eine ausdrückliche Bitte: Beispiele **nicht
abschreiben**, die Anbindung **interaktiv mit dem Kursteilnehmer** erarbeiten, die Fallen
**erklären** statt sie stillschweigend zu umgehen — der Lerngegenstand sei die Entscheidung,
nicht der Code.

Das deckt sich mit [ADR-0001](adr/0001-doku-zuerst.md). In diesem Repo landen daher die
**Entscheidungen und ihre Begründungen**, nicht kopierte Muster von dort.
