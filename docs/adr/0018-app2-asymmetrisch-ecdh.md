# ADR-0018: Anwendung 2 verschlüsselt asymmetrisch — ECDH P-256, HKDF, AES-GCM

**Status:** angenommen (2026-09-03) · Nachtrag 2026-09-03: der `PUT`-Block ist serverseitig
aufgehoben, Schlüsselwechsel ist möglich

## Kontext

[ADR-0007](0007-krypto-umschaltbar.md) hatte asymmetrische Verfahren für Anwendung 1
**verworfen** — nicht aus fachlichen Gründen, sondern weil der offene Pfad keinen
Vertrauensanker bietet: er kennt keine Identität, und ein Schlüsselverzeichnis ohne Nachweis
ist keins.

Die **v2-Stufe** ([api-messagehub-v2.md](../api-messagehub-v2.md)) ändert genau das:

- Konten mit Basic Auth, und der Absender wird **aus dem Nachweis abgeleitet**.
- `GET /v2/directory` liefert Konten mit ihrem öffentlichen Schlüssel — **beglaubigt**, weil
  nur der Kontoinhaber seinen Eintrag setzen kann.
- Daneben `/v2/open-directory`, wo jeder jeden Eintrag überschreiben darf — erklärtermaßen,
  um den Mann-in-der-Mitte vorführbar zu machen.
- Der Dienst behandelt Schlüssel als **opake Zeichenketten**: kein Format, keine Prüfung, kein
  Fingerabdruck. Die Spezifikation sagt ausdrücklich, dass das Format „im Leitplanken-Set"
  festgelegt wird und **JWK** gilt — also hier.

## Entscheidung

Anwendung 2 verschlüsselt **asymmetrisch**, mit WebCrypto:

| Baustein | Festlegung |
|---|---|
| Schlüsselpaar | **ECDH, Kurve P-256** |
| Gemeinsames Geheimnis | ECDH zwischen eigenem privaten und dem veröffentlichten Schlüssel des Gegenübers |
| Schlüsselableitung | **HKDF-SHA-256**, Salt je Nachricht neu (16 Byte), `info` bindet an das Kontenpaar |
| Verschlüsselung | **AES-GCM 256**, IV je Nachricht neu (12 Byte, `crypto.getRandomValues`) |
| Veröffentlichtes Format | **JWK, nur öffentlich**: `{"kty":"EC","crv":"P-256","x":"…","y":"…"}` |
| Fingerabdruck | **SHA-256 über `exportKey("raw", publicKey)`**, angezeigt als erste 8 Byte in 4 Gruppen à 4 Hex-Zeichen |
| Privater Schlüssel | **nicht exportierbar**, `generateKey(…, extractable: false)`, als `CryptoKey` in IndexedDB |

Umschlag als neuer Modus im Format aus [ADR-0007](0007-krypto-umschaltbar.md):

```json
{ "v": 1, "mode": "ecdh-p256",
  "senderFp": "A1B2 C3D4 E5F6 0718",
  "salt": "<b64>", "iv": "<b64>", "ct": "<b64>" }
```

`senderFp` ist der Fingerabdruck des Schlüssels, mit dem der Absender abgeleitet hat. Er
unterscheidet „Schlüssel des Gegenübers hat sich geändert" von „nicht entschlüsselbar" —
sonst sind beide Fälle im UI nicht auseinanderzuhalten.

### Fünf Regeln, die daran hängen

1. **Nie den privaten Schlüssel exportieren.** `exportKey("jwk", keyPair.privateKey)` würde
   ein JWK **mit `d`** liefern — also den privaten Schlüssel im Klartext. Deshalb wird das
   Paar mit `extractable: false` erzeugt; der Aufruf schlägt dann fehl statt zu gelingen.
   Zusätzlich prüft der Code vor dem Veröffentlichen, dass das JWK **kein `d`** enthält, und
   sendet nur `kty`, `crv`, `x`, `y`. Dafür gibt es einen Test
   ([ADR-0017](0017-teststack-vitest-playwright.md)).
2. **Fingerabdruck über das rohe Schlüsselmaterial, nicht über das JWK.** Ein JWK ist JSON,
   und JSON hat keine feste Reihenfolge — zwei Clients würden verschiedene Fingerabdrücke
   für denselben Schlüssel berechnen. `exportKey("raw")` liefert den unkomprimierten Punkt
   (65 Byte) und ist damit kanonisch.
3. **Verglichen wird mündlich.** Der Fingerabdruck steht in der Konversation und wird
   ausgesprochen, nicht über den Kanal geschickt. Die Spezifikation nennt genau das das
   „echte Gegenmittel" — eine Gewohnheit, kein Endpunkt. Das UI sagt das auch so.
4. **`/v2/open-directory` ist kein Bezugsweg.** Schlüssel kommen ausschließlich aus
   `GET /v2/directory`. Das Spielfeld ist ausschließlich **Vorführmodus**, deutlich als
   unsicher gekennzeichnet.
5. **Ohne Schlüssel des Gegenübers wird nicht verschlüsselt.** Hat ein Konto keinen Eintrag,
   ist Verschlüsselung unmöglich — dann sagt das UI das und bietet ausdrücklich Klartext an
   (`mode: "plain"` bleibt gültig, die Nutzlast ist auch auf v2 opak). Kein stilles
   Zurückfallen auf Klartext.

## `PUT` war gesperrt — seit `0.1.34+69b185d` freigegeben

**Erledigt.** Der Befund unten stand einen halben Tag; am 2026-09-03 um 14:32 Uhr (UTC) wurde
der Dienst mit angepasster CORS-Konfiguration neu ausgerollt. Die Bestandsaufnahme bleibt
stehen, weil die Folgeregeln daraus hergeleitet sind — was jetzt gilt, steht im **Nachtrag**
am Ende dieses Abschnitts.

### Der Befund (2026-09-03, `0.1.29+039ba26`)

Preflight-Anfragen gegen `/v2/me/key`, `/v2/open-directory/{name}` und `/v2/messages`
ergaben:

```
OPTIONS /v2/me/key
  Access-Control-Request-Method: PUT
-> 204
   Access-Control-Allow-Methods: GET,POST,DELETE,OPTIONS
   Access-Control-Allow-Headers: Content-Type,Authorization,X-API-Key
```

`PUT` fehlt in `Access-Control-Allow-Methods` — auf **jedem** Pfad, auch wenn der Preflight
es ausdrücklich anfragt. Der Browser bricht den eigentlichen Aufruf danach ab. Damit sind aus
einer Browser-Anwendung **nicht erreichbar**:

- `PUT /v2/me/key` — den eigenen Schlüssel setzen oder **wechseln**
- `PUT /v2/open-directory/{name}` — den Angriff vorführen

Der Weg heraus war **serverseitig**, nicht per Dev-Proxy: die Methodenliste kommt aus der
CORS-Konfiguration des Dienstes, dort fehlte `PUT` einfach. Ein Eintrag mehr — Entwicklung und
Betrieb verhalten sich gleich, und CORS bleibt als echter Mechanismus sichtbar. Ein
Angular-Dev-Proxy hätte es nur bei `ng serve` behoben und im gebauten Bundle wieder gebrochen.

### Nachtrag (2026-09-03, `0.1.34+69b185d`) — was jetzt gilt

```
Access-Control-Allow-Methods: GET,POST,PUT,DELETE,OPTIONS
```

**Ende-zu-Ende verifiziert** mit einem synthetischen Wegwerf-Konto: `POST /v2/register` →
`201`, `PUT /v2/me/key` → `204`, der Schlüssel steht danach in `GET /v2/directory`, ein
zweites `PUT` ersetzt ihn (`204`, idempotent). Auch `PUT /v2/open-directory/{name}` → `204`.

- **Der Schlüssel kann weiter bei der Registrierung mitgegeben werden** (`key` im
  `RegisterDto`) — ein Aufruf statt zwei, und das Konto ist nie ohne Schlüssel sichtbar. Das
  bleibt der Weg beim Anlegen.
- **Schlüsselwechsel ist jetzt möglich** und gehört ins Bedienkonzept von Anwendung 2.
- **Das Spielfeld ist aus dem Browser vorführbar.** Ob Anwendung 2 das anbietet, ist eine
  UX-Entscheidung und **nicht** entschieden; der Angriff von der Kommandozeile bleibt die
  ehrlichere Vorführung, weil der Angreifer dort kein Knopf im Client des Opfers ist.

### Was am Wechsel hängt — und deshalb hier festgelegt wird

Ein Schlüsselwechsel ist bei statischem ECDH nicht folgenlos:

1. **Alte Nachrichten brauchen den alten privaten Schlüssel.** Wird er verworfen, sind alle
   bereits empfangenen Chiffrate endgültig unlesbar. Festlegung: **ausgemusterte Schlüssel
   bleiben in IndexedDB**, als `retired` markiert, und werden **ausschließlich zum
   Entschlüsseln** benutzt. Mit einem ausgemusterten Schlüssel wird **nie** verschlüsselt.
2. **Der Fingerabdruck ändert sich.** Nach einem Wechsel ist jede frühere mündliche
   Bestätigung ungültig. Das UI setzt den Zustand der betroffenen Konversationen auf
   **„Schlüssel geändert"** zurück und verlangt einen neuen mündlichen Vergleich — genau das,
   wofür `senderFp` im Umschlag steht.
3. **Ein Wechsel ist nicht von einem Angriff zu unterscheiden.** Für den Empfänger sieht ein
   legitimer Wechsel des Gegenübers genauso aus wie ein ausgetauschter Eintrag. Deshalb ist
   der Wechsel im UI keine stille Aktualisierung, sondern eine Meldung.

> **Beim Nachprüfen einer CORS-Änderung:** die Antwort setzt `Access-Control-Max-Age: 86400`.
> Ein Browser, der den alten Preflight zwischengespeichert hat, scheitert bis zu 24 Stunden
> weiter. In einem frischen Profil prüfen, nicht im offenen Fenster.

## Begründung

- **Der Vertrauensanker ist neu und macht den Unterschied.** ADR-0007 hatte Asymmetrie
  verworfen, weil Schlüsselverteilung ohne Anker sinnlos ist. Auf v2 gibt es einen
  beglaubigten Anker — und daneben das offene Gegenstück, an dem sich zeigen lässt, warum
  „beglaubigt" das entscheidende Wort ist. Das ist der stärkste Lehrsatz des Projekts.
- **ECDH statt RSA-OAEP**, weil P-256-Schlüssel klein sind, als JWK gut aussehen, in
  WebCrypto überall vorhanden sind und die Nutzlastgröße nicht begrenzen. RSA-OAEP könnte nur
  wenige hundert Byte direkt verschlüsseln und bräuchte ohnehin ein hybrides Verfahren.
- **HKDF mit Salt je Nachricht**, weil statisches ECDH sonst für jede Nachricht denselben
  Schlüssel liefert. `info` bindet zusätzlich an das Kontenpaar, damit ein abgeleiteter
  Schlüssel nicht in einem anderen Kontext wiederverwendbar ist.
- **`extractable: false` löst den Widerspruch zu den Guardrails.** „Keine Geheimnisse an
  Ruhe" verlangte für die Passphrase Arbeitsspeicher
  ([ADR-0007](0007-krypto-umschaltbar.md)). Ein privater Schlüssel muss aber Neuladen
  überleben, sonst ist das Konto nach jedem Reload unbrauchbar. Ein nicht exportierbarer
  `CryptoKey` in IndexedDB ist der Ausweg: er ist benutzbar, aber sein Material ist für
  JavaScript **nicht lesbar**. Das ist keine Umgehung der Regel, sondern ihre Erfüllung mit
  besseren Mitteln — und der Unterschied zur Passphrase ist genau der Punkt, den man daran
  lernt.
- **`senderFp` im Umschlag**, weil ein Schlüsselwechsel des Gegenübers sonst als „falsches
  Kennwort" erscheint und die Fehlersuche in die falsche Richtung schickt.

## Folgen

- Anwendung 2 braucht ein **eigenes Bedienkonzept**: Registrierung mit Schlüsselerzeugung,
  Anmeldung, Verzeichnis, Fingerabdruck-Anzeige und den Hinweis auf den mündlichen Vergleich.
  Noch nicht geschrieben.
- Die Anzeige „behauptet" aus [ADR-0005](0005-konversation-ist-client-konstrukt.md) entfällt
  auf v2 — der Absender ist nachgewiesen. Stattdessen gibt es den **Schlüssel**-Zustand:
  unbekannt, bekannt, geändert, mündlich bestätigt.
- `libs/payload` bekommt den Modus `ecdh-p256` zusätzlich zu `plain` und `aes-gcm`. Die
  Deutung bleibt **je Nachricht** ([ADR-0007](0007-krypto-umschaltbar.md)); ein Eingang kann
  alle drei mischen.
- **Keine Vorwärtsgeheimhaltung.** Statisches ECDH heißt: wer den privaten Schlüssel bekommt,
  entschlüsselt rückwirkend alles. Für ein Lehrprojekt vertretbar, wird aber im UI nicht
  verschwiegen.
- Ein Konto ohne Schlüssel bleibt erreichbar — man kann ihm schreiben, nur nicht für ihn
  verschlüsseln.
- **Schlüsselwechsel gehört ins Bedienkonzept**, seit `PUT` freigegeben ist: ausgemusterte
  Schlüssel bleiben zum Entschlüsseln liegen, der Fingerabdruck muss erneut mündlich
  verglichen werden, und ein Wechsel des Gegenübers wird gemeldet statt still übernommen —
  siehe Nachtrag oben.

## Verworfene Alternativen

- **Passphrasen-Variante aus ADR-0007 auch auf v2.** Würde den beglaubigten Anker ungenutzt
  lassen und den zentralen Kontrast zum offenen Verzeichnis verschenken.
- **RSA-OAEP.** Größere Schlüssel, Längenbegrenzung der Nutzlast, hybrides Verfahren trotzdem
  nötig.
- **Ephemeres ECDH (ECIES) für Vorwärtsgeheimhaltung.** Fachlich besser, aber der
  Sitzungsschlüssel müsste im Umschlag mitreisen, und die Authentizität des Absenders käme
  dann nicht mehr aus dem Schlüsselpaar. Für den Lerngegenstand zu viel auf einmal — wäre
  eine eigene ADR wert.
- **Privaten Schlüssel als JWK in IndexedDB.** Bequemer zu debuggen und ein Geheimnis an
  Ruhe, das jedes Skript im selben Origin lesen kann. Genau das verhindert
  `extractable: false`.
- **Fingerabdruck über das JWK.** Nicht kanonisch, siehe Regel 2.
- **Schlüssel aus `/v2/open-directory` beziehen.** Das ist der Angriff, nicht die Anbindung.
