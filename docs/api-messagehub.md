# Der API-Vertrag des UTZ MessageHub — und die Regeln seiner Nutzung

Basis: `https://utz-messagehub.itzcloud.de` · Spezifikation `/openapi.json` und
`/openapi.yaml` · eingefrorener Schnappschuss in [`api/openapi.yaml`](api/openapi.yaml)
(Fassung `0.1.16+6afc10e`, geholt am 2026-09-02).

Dieses Dokument beschreibt **nur, was verifiziert ist**: aus der Spezifikation gelesen oder
am laufenden Dienst mit synthetischen Testdaten geprüft. Wo Verhalten geprüft wurde, steht
es dabei. Nichts hier ist geraten.

## Was der Dienst ist

Eine **Warteschlange je Empfängername**. Nutzlast unter einem Namen einliefern, unter
demselben Namen wieder abholen. Store-and-forward, mehr nicht — **kein Chat, keine Historie,
keine Zustellbestätigung**. Die Nutzlast ist für den Dienst **opak**: er interpretiert sie
nicht und erwartet keine Struktur.

Der Dienst wird in drei Schutzstufen mit **getrennten Endpunkten und getrennten Ablagen**
angeboten. Es gibt keinen Übergang: was unter einer Stufe eingeliefert wurde, ist über die
anderen nicht erreichbar.

| Stufe | Pfad | Nachweis | Ablage | Zustand |
|---|---|---|---|---|
| offen | `/open/...` | keiner | flüchtig, im Arbeitsspeicher, mit Verfall | **vollständig in Betrieb** |
| Token | `/token/...` | API-Token `X-API-Key` | dauerhaft | **nicht gebaut** |
| OIDC | `/oidc/...` | Bearer-JWT | dauerhaft | nur `whoami` + `directory`; Nachrichten-Endpunkte **nicht gebaut** |

`GET /oidc/config` liefert auf dieser Instanz **`configured: false`** (geprüft 2026-09-02) —
die OIDC-Stufe ist nicht einmal eingerichtet. Dieses Projekt nutzt daher ausschließlich den
offenen Pfad und **ignoriert Token- und OIDC-Stufe in diesem Release vollständig**: keine
Anmeldung, kein Aufruf unter `/oidc/` oder `/token/`, und ausdrücklich **keine**
Stufen-Abstraktion ([ADR-0003](adr/0003-nur-offener-pfad.md)).

## Die Endpunkte des offenen Pfades

### `POST /open/messages` — einliefern

Rumpf `SubmitMessageDto`, alle drei Felder erforderlich:

| Feld | Typ | Regel |
|---|---|---|
| `to` | string | `^[A-Za-z0-9_-]{1,32}$`, Groß-/Kleinschreibung wird unterschieden — der Client schreibt klein ([ADR-0014](adr/0014-namen-kleinschreiben.md)) |
| `from` | string | dasselbe Muster — **unbeglaubigte Behauptung**, der Dienst prüft nichts |
| `message` | string | mindestens 1 Zeichen, für den Dienst opak |

Antwort `201` mit `SubmissionAcceptedDto`: `{ id, expiresAt }`. Die `id` ist die einzige
Möglichkeit, die Nachricht später zu entnehmen.

Der Empfänger **muss nicht existieren** und sich nirgends registrieren. Der Benutzername ist
ein Fach, das beim ersten Einliefern entsteht.

Fehler: `400` Schemaverstoß · `413` Nutzlast über 64 KB · `429` entweder liegen für diesen
Namen bereits 20 Nachrichten oder der Aufrufer hat 60 Einlieferungen/Minute ausgeschöpft ·
`503` Gesamtspeicher erschöpft oder zu viele belegte Namen, `Retry-After` beachten.

### `GET /open/messages?to=<name>` — ansehen

**Der einzige Parameter ist `to`, und er ist erforderlich.** Antwort `200` mit einem
**flachen Array** aller bereitliegenden Nachrichten dieses Empfängers, **älteste zuerst**.
Je Element `MessageDto`: `{ id, to, from, message, receivedAt, expiresAt }`.

**`204` ohne Rumpf heißt: es liegt nichts bereit.** Das ist der Normalfall, kein Fehler, und
ausdrücklich **nicht** `404`.

Der Aufruf **verändert nichts** und ist beliebig wiederholbar. Entnommen wird mit einem
eigenen Aufruf. Die Trennung ist Absicht: `GET` ist in HTTP zustandsfrei, Clients wiederholen
es nach einem Timeout, und Crawler wie Link-Vorschauen rufen öffentliche URLs unaufgefordert
auf — würde Ansehen entnehmen, verschwänden Nachrichten, bevor der Empfänger sie sieht.

### `DELETE /open/messages/{id}` — entnehmen

Entnimmt genau diese Nachricht. Sie ist danach fort und wird kein zweites Mal ausgeliefert.
`204` entnommen · `404` gibt es nicht (mehr), bereits entnommen oder verfallen.

**Kein Nachweis nötig.** Jeder, der die `id` kennt, kann entnehmen.

### `GET /open/names` — belegte Namen auflisten

`200` mit `NameUsageDto[]`: `{ name, waitingAsRecipient, waitingAsSender }`, alphabetisch.
Kein Verzeichnis von Konten — ein Name entsteht beim ersten Einliefern und verschwindet,
sobald seine letzte Nachricht entnommen oder verfallen ist. Wer hier fehlt, kann trotzdem
beliefert werden.

**Diese Liste ist öffentlich, und das ist der Punkt.** Sie zeigt, dass ein Name auf dem
offenen Pfad nichts verbirgt. `waitingAsSender` zählt, was in den Nachrichten *steht*, nicht
wer sie geschickt hat.

### `GET /health` — Betriebszustand

`200` mit Version, Belegung der flüchtigen Ablage und einer Bilanz der Einlieferungen.
`open.traffic.rejected` zählt Abweisungen **je Grund** — damit ist beantwortbar, *welche*
Grenze gegriffen hat. Zähler liegen im Arbeitsspeicher und beginnen bei jedem Neustart neu,
`since` sagt ab wann. Gezählt werden nur Summen, kein Vorgang je Name oder Adresse: die
Auskunft soll diagnostisch nutzbar sein, ohne ein Zugriffsprotokoll zu werden.

## Grenzen des offenen Pfades

| Grenze | Wert | Verstoß |
|---|---|---|
| Nutzlast je Nachricht | 64 KB | `413` |
| Nachrichten je Empfängername | 20 | `429` |
| Belegte Namen gesamt | 500 | `503` |
| Speicher über alles | 64 MB | `503` |
| Einlieferungen je Aufrufer und Minute | 60 | `429` |
| Verfall je Nachricht | 60 Minuten | stille Entfernung |

Das Rate-Limit betrifft **nur Einlieferungen**. `GET` ist nicht begrenzt.

## ⚠️ Das Abholen holt den *ganzen Eingang* — nicht eine Konversation

Das ist die Eigenschaft mit den meisten Folgen, und sie ist leicht zu überlesen.

**Verifiziert am 2026-09-02**, mit zwei synthetischen Absendern an einen synthetischen
Empfänger (danach beide Nachrichten wieder entnommen):

```
POST /open/messages  {"to":"etreff_probe_rx","from":"etreff_probe_a", ...}  -> 201
POST /open/messages  {"to":"etreff_probe_rx","from":"etreff_probe_b", ...}  -> 201

GET /open/messages?to=etreff_probe_rx                                       -> 200
  id=d6cf802a-...  from=etreff_probe_a  to=etreff_probe_rx
  id=f79f170d-...  from=etreff_probe_b  to=etreff_probe_rx
```

Beide Nachrichten kommen aus **einem** Aufruf zurück. Daraus folgt Punkt für Punkt:

**1. Ein Absender-Filter existiert nicht — und der Versuch scheitert hart.** Eine
serverseitige Filterung nach Absender ist vom Betreiber **angekündigt**; solange sie nicht in
der Spezifikation steht, gilt der folgende Befund unverändert. Die Operation
kennt genau einen Parameter. Wer `from` mitgibt, bekommt keinen ignorierten Parameter,
sondern einen Fehler (verifiziert):

```
GET /open/messages?to=etreff_probe_rx&from=etreff_probe_a               -> 400
{"message":["property from should not exist"],"error":"Bad Request","statusCode":400}
```

Der Hub validiert nach **Whitelist**: undeklarierte Query-Parameter und Rumpffelder werden
abgewiesen, nicht durchgelassen. Es gibt ebenso **keine** Paginierung, **keine** Sortier- und
**keine** Zeitfensterparameter. Ein Agent, der so etwas ergänzt, weil es plausibel wäre,
bricht den Aufruf ([ADR-0010](adr/0010-striktes-anfrage-schema.md)).

**2. Jeder Eingang ist von jedem lesbar.** `to` ist nicht auf den eigenen Namen beschränkt —
ein Abruf auf einen fremden Namen liefert `200` (verifiziert an einem bereits belegten,
fremden Namen). Zusammen mit dem öffentlichen `GET /open/names` ist der gesamte offene Pfad
**welt-lesbar und welt-entnehmbar**: `DELETE` braucht nur die `id`, und die steht in der
Antwort des Ansehens. Ein Fremder kann Nachrichten wegnehmen, bevor der Empfänger sie sieht,
und der Empfänger erfährt nicht, dass es sie gab.

**3. Ein Chat ist reine Client-Erfindung.** Der Hub kennt keine Konversation, keinen Thread,
keine Zuordnung von Frage und Antwort. Ein Verlauf entsteht ausschließlich dadurch, dass der
Client den geholten Eingang nach `from` gruppiert und selbst speichert
([ADR-0005](adr/0005-konversation-ist-client-konstrukt.md),
[ADR-0011](adr/0011-lokale-persistenz-indexeddb.md)).

**4. Der Absender ist keine Identität.** `from` ist eine Behauptung, die jeder aufstellen
kann. In einem Eingang können jederzeit Nachrichten mit einem beliebigen, auch einem bereits
bekannten `from` auftauchen, ohne dass die behauptete Person beteiligt war. Eine Konversation
im Client ist damit **an einen behaupteten Namen** gebunden, nicht an ein Gegenüber.

**5. Die Grenze von 20 gilt je Empfängername, nicht je Konversation.** Ein einzelner
gesprächiger — oder böswilliger — Absender füllt den gesamten Eingang und blockiert damit
`POST` **aller** anderen Absender an diesen Namen mit `429`. Das ist ein Zustand, den der
Client sichtbar machen muss ([ADR-0006](adr/0006-entnehmen-ist-nutzeraktion.md)).

**6. Ein Eingang kann Klartext und Chiffrate mischen.** Da die Betriebsart umschaltbar ist
und jeder Fremde einliefern darf, ist die Form der Nutzlast eine Eigenschaft **der einzelnen
Nachricht**, nicht der Konversation. Erkennung und Entschlüsselung laufen je Nachricht, und
**Fehlschlag ist ein normaler Anzeigezustand**, keine Ausnahme
([ADR-0007](adr/0007-krypto-umschaltbar.md)).

## Festlegungen für die API-Nutzung

Verbindlich. Sie folgen aus den Eigenschaften oben, nicht aus Geschmack.

1. **Genau ein `GET /open/messages` je Poll-Zyklus**, mit dem eigenen Namen als `to`.
   Niemals ein Abruf je Konversation — das wäre N-mal derselbe Aufruf für dieselben Daten.
2. **Nach `from` clientseitig gruppieren.** Serverseitige Filterung nicht versuchen, auch
   nicht testweise.
3. **Nur deklarierte Felder und Parameter senden.** Keine erfundenen Filter, Sortierungen,
   Limits oder Cursor.
4. **`204` als Normalfall behandeln** — nicht als Fehler und nicht als leeres Array
   verkleidet. Der Unterschied zwischen „nichts da" und „Abruf fehlgeschlagen" muss im
   Client erhalten bleiben.
5. **`DELETE` nur auf ausdrückliche Nutzeraktion.** Unwiderruflich, ohne zweite Chance.
6. **Nachrichten mit unbekanntem `from` niemals stillschweigend zu einer vertrauten
   Konversation zusammenführen.** Ein behaupteter Name ist kein Nachweis.
7. **Belegung des eigenen Eingangs im Blick behalten** und dem Nutzer zeigen, wenn er sich
   der Grenze von 20 nähert — sonst schlägt sein nächster Empfang unbemerkt fehl.
8. **Nur synthetische Bezeichner** in `to` und `from`
   ([ADR-0009](adr/0009-nur-synthetische-bezeichner.md)).
9. **Namen kleinschreiben**, aber an das **rohe `from`** antworten — sonst landet die Antwort
   lautlos in einer anderen Warteschlange
   ([ADR-0014](adr/0014-namen-kleinschreiben.md)).
10. **Kein `credentials: "include"`** ([ADR-0013](adr/0013-cors-ohne-credentials.md)).
11. **`Retry-After` bei `503` respektieren**, nicht mit festem Intervall weiterhämmern.
12. **Nichts unter `/oidc/` oder `/token/` aufrufen** — in diesem Release ignoriert
    ([ADR-0003](adr/0003-nur-offener-pfad.md)).

## Aufrufe aus dem Browser

Der Hub setzt `Access-Control-Allow-Origin: *` und lässt Aufrufe aus beliebigen Origins zu.
Es werden **keine** Credentials gebraucht: kein Cookie, keine HTTP-Authentifizierung.

> **Falle:** Wird im Client `credentials: "include"` gesetzt, verlangt der Browser einen
> konkreten Origin statt der Wildcard, und der Aufruf scheitert — obwohl der Code korrekt
> aussieht. Diese Falle steht wörtlich in der Spezifikation des Dienstes.

## Fehlerform

Bei Validierungsfehlern antwortet der Hub mit einem NestJS-typischen Rumpf (verifiziert; die
Spezifikation nennt für `400` keinen Rumpf):

```json
{ "message": ["property from should not exist"], "error": "Bad Request", "statusCode": 400 }
```

`message` ist ein **Array** von Meldungen. Wer es als String behandelt, bekommt in der
Anzeige Buchstabensalat oder eine Ausnahme.

## TLS

Das Zertifikat des Hubs stammt aus einer ITZ-internen CA. Fehlt sie im lokalen Trust-Store,
scheitert `curl` mit Exit 60 („unable to get local issuer certificate"). Dann
`--cacert <pfad-zur-itz-ca>` verwenden.

**Nicht** `-k` benutzen und die interne Wurzel **nicht** global trusten: dieselbe CA ist
auch Wurzel eines TLS-Interception-Proxys — ein globaler Trust würde jede aufgebrochene
Verbindung mitbeglaubigen. Im Browser ist die CA in der Regel vorhanden; das Problem betrifft
Kommandozeilen-Werkzeuge.
