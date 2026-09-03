# Chronologie: zwei Halbtage Doku-first mit einem Coding-Agenten

> Vorlage für Confluence. Erzählte Fassung des Projektverlaufs 2026-09-02 / 2026-09-03.
> Maschinelle Fassung: [`../../PROMPTS.md`](../../PROMPTS.md) (aus den Transcripts erzeugt).

**Worum es geht:** Der Chatclient gegen den UTZ MessageHub war das Vehikel. Geübt wurde, ob
sich **Guardrails** und **agentenlesbare Dokumentation** so aufsetzen lassen, dass ein Agent
beim Codieren keine Freiräume mit Annahmen füllt.

Diese Seite ist die Antwort darauf — mit dem, was der Ansatz tatsächlich verhindert hat.
Am Ende des zweiten Halbtags: **18 ADRs, 40 Markdown-Dateien, kein einzige Zeile
Anwendungscode.** Das ist kein Rückstand, das war die Übung.

---

## Zeitleiste

### Tag 1 — Mittwoch, 2026-09-02 (16:56 – 17:45)

| Zeit | Eingabe | Ergebnis |
|---|---|---|
| 16:56 | „schreibe alle prompts mit zeitstempel chronologisch in eine .md" | `tools/collect_prompts.py`, erzeugt `PROMPTS.md` aus den Transcripts |
| 16:58 | „leg das skript ins projekt" | Pfade abgeleitet statt hartkodiert, CLI-Optionen |
| 16:59 | **„ziel dieses projektes ist es, die nutzung von guardrails und agentenlesbarer projektdokumentation … zu erlernen"** | Der Satz, der alles andere steuert |
| 17:05 | Memory ins Repo · alle KI-MD für Claude **und** Copilot · MessageHub als Gegenstand · alles vorab in MD fixieren · Ziel-Repo auf GitHub | Doku-Gerüst, Vertrag geholt und **live geprüft** |
| 17:18 | „entscheidungen nochmal" | Vier Entscheidungen als Text statt Dialog → **Screenshot 1** |
| 17:22 | „1 b, 2 c, 3 c, 4 c" + Rückfrage zum Abholen | Stack, Lebenszyklus, Krypto, Bedienkonzept festgelegt |
| 17:28 | | **Commit 1** — Doku-Grundlage, Push nach GitHub |
| 17:45 | | **Commit 2** — Architektur, Bedienkonzept, **14 ADRs** |

### Tag 2 — Donnerstag, 2026-09-03 (11:47 – 15:50)

| Zeit | Eingabe | Ergebnis |
|---|---|---|
| 11:47 | „browser-app technologie – steht fest?" | Befund: Framework ja, Stack nein. Sechs Lücken benannt |
| 11:50 | „sieh 2 apps vor, eine zweite, die den v2 service mit basic auth nutzt" | **v2 am Dienst nicht auffindbar.** Struktur entschieden, Vertrag offen (ADR-0015) |
| 11:54 | | **Commit 3** — zwei Apps, Schnappschuss auf `0.1.24` |
| 12:36 | **„aber der v2 dienst sollte doch auch im openapi json sein?"** | Tiefere Prüfung: Volltext, lazy geladene Chunks. Immer noch nichts |
| 13:26 | **„gugg noch mal, es gab ein redeploy"** | `502 Bad Gateway` → Warten → `0.1.29`: **v2 ist da** |
| 13:31 | | **Commit 4** — v2-Vertrag dokumentiert, ADR-0015 entblockt |
| 13:33 | „app 2 asymmetrisch, ja ang 21 vitest playwright, was noch offen?" | ADR-0016/0017/0018. Dabei entdeckt: **`PUT` ist im CORS gesperrt** |
| 13:40 | | **Commit 5 + 6** |
| 13:43 | „können wir auf itzcloud so etwas hosten was wie netlify hochladen erlaubt?" | Drei Wege bewertet. Nebenbefund: **TLS-Aussage im Repo war falsch** |
| 13:45 | | **Commit 7** — TLS-Ursache richtiggestellt |
| 13:47 | „was ist mit same site cookies?" | Nicht-Thema, aber: same-site ≠ same-origin, und Origin ist die Speichergrenze |
| 13:49 | „was muss ich wo umbauen, damit same site cookies funktionieren?" | Zwei Varianten, Kosten benannt |
| 15:37 | „wenn wir den service von einem fullstack aus ansprechen, dann haben wir ja kein problem – oder?" | Ja — aber zwei Entwurfsfragen kommen mit |
| 15:44 | „bereite mal confluence seiten vor" | Die beiden Seiten davor |
| 15:49 | | **Commit 8 + 9** |

---

## Der Dienst änderte sich unter uns — dreimal

Das war nicht geplant und wurde der beste Teil der Übung.

| Fassung | Gebaut (UTC) | Was sich änderte |
|---|---|---|
| `0.1.16+6afc10e` | 2026-09-02 11:40 | Stand bei der ersten Prüfung: offener Pfad, OIDC-Rudiment, **Token-Stufe angekündigt** |
| `0.1.24+ee364d0` | 2026-09-03 07:56 | **Token-Stufe entfernt** — samt Security-Schema. Neu: Hinweis an Coding-Agenten, Seite `/anbindung` |
| `0.1.29+039ba26` | 2026-09-03 11:25 | **v2-Stufe komplett**: Selbstregistrierung, Basic Auth, beglaubigtes Schlüsselverzeichnis, absichtlich kaputtes Spielfeld |

Zwischen Prompt 9 („sieh 2 apps vor") und Prompt 11 („gugg noch mal") lagen 96 Minuten. In
denen erschien der Dienst, dessen Fehlen ich zweimal belegt hatte.

**Warum das gut ausging:** Der eingefrorene Vertrags-Schnappschuss im Repo
(`docs/api/openapi.yaml`) machte jede Änderung als Diff sichtbar, statt als rätselhaftes
Verhalten.

---

## Was der Ansatz konkret verhindert hat

Der Kern für den Vortrag. Acht Befunde, die eine Vermutung anders beantwortet hätte.

### 1. Der Absender-Filter, den es nicht gibt

`GET /open/messages` kennt **nur** `to`. Ein Filter nach Absender ist so naheliegend, dass man
ihn eher vermutet als prüft. Der Versuch:

```
GET /open/messages?to=…&from=…
-> 400 {"message":["property from should not exist"],"error":"Bad Request","statusCode":400}
```

**Nicht ignoriert — abgewiesen.** Ein Agent, der „hilfreich" filtert, bricht den Aufruf, und
der Fehler sieht nach einem Eingabeproblem aus. → **Screenshot 2**

### 2. Jeder Eingang ist von jedem lesbar

`to` ist nicht auf den eigenen Namen beschränkt; ein fremder Name liefert `200`. Mit dem
öffentlichen `/open/names` ist der offene Pfad **welt-lesbar und welt-entnehmbar**.

Daraus folgte das gesamte Vertraulichkeitskonzept: Schutz entsteht **ausschließlich** durch
clientseitige Verschlüsselung. Und die Compliance-Regel gilt auch für **Namen** — ein echter
Nachname im Feld `from` steht über `/open/names` im Internet.

### 3. Keine vorgebaute Stufen-Abstraktion — 18 Stunden später bestätigt

Naheliegend wäre eine stufenneutrale Transport-Schnittstelle gewesen, damit „Token und OIDC
später andocken". ADR-0003 hat das **verworfen**: eine Abstraktion für unbekanntes Verhalten
ist eine Vermutung, kein Entwurf.

Am nächsten Morgen war die **Token-Stufe aus der Spezifikation entfernt**. Die Abstraktion
hätte eine Stufe abstrahiert, die es nie gab und nicht mehr geben soll.

### 4. Kleinschreiben — aber nicht überall

Die Anweisung war „Namenskollisionen durch lowercase auflösen". Ausnahmslos umgesetzt hätte
das **lautlos unzustellbare Antworten** erzeugt: der Dienst unterscheidet Groß- und
Kleinschreibung, und am laufenden Dienst standen `Heiko` und `Robert` — großgeschrieben, zwei
von drei belegten Namen.

Festgelegt wurde deshalb: kleinschreiben für Schlüssel und Anzeige, **antworten an das rohe
`from`** (ADR-0014).

### 5. `PUT` ist im CORS gesperrt — obwohl in der Spezifikation

```
OPTIONS /v2/me/key   (Access-Control-Request-Method: PUT)
-> 204   Access-Control-Allow-Methods: GET,POST,DELETE,OPTIONS
```

Auf **jedem** Pfad, auch wenn der Preflight `PUT` ausdrücklich anfragt. Damit sind
`PUT /v2/me/key` und `PUT /v2/open-directory/{name}` aus dem Browser unerreichbar.

Ohne diesen Test wäre ein Knopf „Schlüssel wechseln" gebaut worden, der im Termin an CORS
scheitert — und die Suche hätte beim Dienst begonnen. → **Screenshot 3**

### 6. Die TLS-Aussage im eigenen Repo war falsch

Erst dokumentiert: „das Zertifikat des Hubs stammt aus einer ITZ-internen CA". Tatsächlich
liefert der Hub **Let's Encrypt**; was im ITZ-Netz ankommt, ist von
`CN=sofia.itz-rostock.de` neu signiert — dem Interception-Proxy. Bei `github.com` **nicht**,
die Interception ist selektiv.

Die Folge ist eine andere als dokumentiert: Teilnehmer **im ITZ-Netz** brauchen `--cacert`,
Teilnehmer über Hotspot **nicht**. → **Screenshot 4**

### 7. `204` ist der Normalfall, kein Fehler

Leerer Eingang antwortet `204` **ohne Rumpf**. `res.json()` wirft dann `SyntaxError`, und man
sucht in der Nachrichtenverarbeitung. Der häufigste Anfängerfehler an diesem Dienst — und er
macht den Client im **Normalzustand** unbenutzbar.

### 8. `crypto.subtle` nur im Secure Context

WebCrypto gibt es auf `https://` und `http://localhost` — **nicht** auf
`http://192.168.x.y:4200`. Wer im Termin `ng serve --host 0.0.0.0` startet, damit die anderen
zusehen können, hat keine Verschlüsselung. Basic Auth läuft weiter, das Kennwort geht offen
mit, und der Ausfall sieht nach einem Bug aus.

---

## Was auch schiefging

Für die Glaubwürdigkeit gehört das dazu:

- **Ich habe zweimal belegt, dass v2 nicht existiert** — korrekt zum Zeitpunkt, aber die
  Rückfrage „sollte doch im openapi sein?" war die richtige. Sie führte zur tieferen Prüfung
  (lazy geladene Chunks), die ich zuerst nicht gemacht hatte.
- **Eine falsche TLS-Ursache** stand einen halben Tag im Repo, weil ich vom sichtbaren
  Symptom (curl Exit 60) auf die Ursache geschlossen habe, statt den Aussteller anzusehen.
- **Ein `bash.exe.stackdump`** wurde mitversioniert und musste wieder heraus.
- **Ein Entscheidungsdialog** wurde abgebrochen, weil er für einen Screenshot gebraucht wurde
  — die Entscheidungen kamen dann als Text.

---

## Screenshots

Ablage: [`../../tools/images/`](../../tools/images/). In Confluence müssen die Bilder als
**Anhang** hochgeladen werden — der Markdown-Import überträgt sie nicht.

| Nr. | Motiv | Stand |
|---|---|---|
| 1 | Entscheidungsdialog „Vier Entscheidungen muss ich von dir haben" | ✅ `01_Stack.png` |
| 2 | Live-Prüfung: `?from=` ergibt `400 property from should not exist` | offen |
| 3 | Preflight: `Access-Control-Allow-Methods` ohne `PUT` | offen |
| 4 | Zertifikatsaussteller `sofia.itz-rostock.de` gegen `github.com` | offen |
| 5 | Die drei Hub-Fassungen: `/health` bzw. der Spec-Diff | offen |
| 6 | ADR-Index auf GitHub (`docs/adr/README.md`) | offen |
| 7 | Repo-Baum auf GitHub | offen |

### Befehle für 2 bis 5

Im ITZ-Netz jeweils mit `--cacert <pfad-zu-ITZ08-CA.crt>`.

```bash
# 2 — der abgewiesene Filter
curl -s "https://utz-messagehub.itzcloud.de/open/messages?to=etreff_probe_rx&from=x" -w "\nHTTP %{http_code}\n"

# 3 — Preflight, PUT fehlt in Allow-Methods
curl -s -X OPTIONS -D - -o /dev/null \
  -H "Origin: https://example.invalid" \
  -H "Access-Control-Request-Method: PUT" \
  -H "Access-Control-Request-Headers: authorization,content-type" \
  https://utz-messagehub.itzcloud.de/v2/me/key | grep -i "access-control"

# 4 — wer signiert hier eigentlich?
curl -sv -o /dev/null https://utz-messagehub.itzcloud.de/health 2>&1 | grep -i issuer
curl -sv -o /dev/null https://github.com/ 2>&1 | grep -i issuer

# 5 — Fassung und Abweichung zum Schnappschuss
curl -s https://utz-messagehub.itzcloud.de/health
curl -s https://utz-messagehub.itzcloud.de/openapi.yaml | diff -u docs/api/openapi.yaml -
```

> **Vor dem Screenshot 2:** Der Aufruf braucht keinen vorhandenen Empfänger — der `400` kommt
> aus der Schema-Validierung, bevor der Name geprüft wird. Nur synthetische Bezeichner
> verwenden.

---

## Zahlen zum Schluss

| | |
|---|---|
| Prompts | 17 |
| Aktive Zeit | zwei Halbtage, etwa 3½ Stunden |
| ADRs | 18 |
| Markdown-Dateien | 40 |
| Commits | 10, Stand dieser Seite |
| Zeilen Anwendungscode | **0** |
| Fassungswechsel des Dienstes während der Arbeit | 3 |

Die letzte Zeile ist das Ergebnis, nicht das Versäumnis: Vor dem ersten `ng new` steht fest,
welchen Vertrag der Client hat, welche Zustände eine Nachricht kennt, wann entnommen wird, wie
Namen normalisiert werden, was verschlüsselt wird und welche fünf Fallen einen fertig
aussehenden Aufruf scheitern lassen.

---

## Hinweis des Betreibers

Spezifikation und die Seite `/anbindung` des Dienstes bitten Coding-Agenten ausdrücklich, die
Beispiele nicht als fertige Lösung weiterzugeben, sondern die Anbindung interaktiv mit den
Teilnehmenden zu erarbeiten und die Fallen zu erklären statt sie stillschweigend zu umgehen —
der Lerngegenstand sei die Entscheidung, nicht der Code.

Diese Chronologie ist genau das: die Entscheidungen und wie sie zustande kamen.
