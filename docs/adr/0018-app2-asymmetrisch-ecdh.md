# ADR-0018: Anwendung 2 verschlüsselt asymmetrisch — ECDH P-256, HKDF, AES-GCM

**Status:** angenommen (2026-09-03)

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

## ⚠️ Einschränkung: `PUT` ist im CORS nicht erlaubt

**Verifiziert am 2026-09-03** mit Preflight-Anfragen gegen `/v2/me/key`,
`/v2/open-directory/{name}` und `/v2/messages`:

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

Folgen, mit denen gebaut wird:

- **Der Schlüssel wird bei der Registrierung mitgegeben.** `POST /v2/register` nimmt ein
  optionales Feld `key`, und `POST` ist erlaubt. Anwendung 2 erzeugt das Paar also **vor** der
  Registrierung und veröffentlicht den öffentlichen Teil in demselben Aufruf.
- **Schlüsselwechsel ist aus dem Browser nicht möglich.** Das UI sagt das, statt einen Knopf
  anzubieten, der an CORS scheitert. Wer wechseln will, legt ein neues Konto an.
- **Der Verlust des privaten Schlüssels ist endgültig.** Er ist nicht exportierbar und liegt
  nur in diesem Browser; Browserdaten gelöscht heißt Konto unbrauchbar.
- **Der Angriff wird von der Kommandozeile vorgeführt**, nicht aus der Anwendung. Das ist
  didaktisch sogar ehrlicher: der Angreifer ist kein Knopf im Client des Opfers.

Bis auf Weiteres gilt der verifizierte Befund, nicht die Spezifikation — die kennt `PUT`, der
Browser bekommt ihn nicht.

### Offen: wie der `PUT`-Block aufgelöst wird

Zwei Wege, und sie sind nicht gleichwertig:

**a) Serverseitig `PUT` freigeben.** Der Dienst ist eine NestJS-Anwendung (erkennbar am
Fehlerrumpf `{"message":[…],"error":…,"statusCode":…}`). Die Methodenliste kommt aus der
CORS-Konfiguration; dort fehlt `PUT` einfach. Ein Eintrag mehr, und der Befund oben ist
erledigt — Entwicklung und Betrieb verhalten sich gleich, und CORS bleibt als echter
Mechanismus sichtbar. **Vorzuziehen.**

> Beim Nachprüfen zu beachten: Die Antwort setzt `Access-Control-Max-Age: 86400`. Ein Browser,
> der den alten Preflight schon zwischengespeichert hat, scheitert bis zu 24 Stunden weiter.
> Nach der Änderung in einem frischen Profil prüfen, nicht im offenen Fenster.

**b) Dev-Server-Proxy in Angular.** `ng serve` mit `proxy.config.json` macht die Aufrufe
gleicher Herkunft; CORS entfällt vollständig, `PUT` inbegriffen. Löst das Problem aber **nur
in der Entwicklung**: ein gebautes Bundle auf statischem Hosting hat keinen Proxy, und dann
ist der Befund zurück. Das ist genau die Sorte Unterschied zwischen Entwicklung und Betrieb,
die dieses Projekt sonst dokumentiert — und es nimmt dem Kurs die Gelegenheit, CORS überhaupt
zu sehen.

Ein Proxy wäre vertretbar, wenn er **auch im Betrieb** existiert (Reverse-Proxy vor dem
statischen Bundle, gleiche Herkunft für App und API). Dann ist es kein Dev-Trick, sondern eine
Architekturentscheidung — und gehört als solche in eine eigene ADR.

Solange nichts entschieden ist, baut Anwendung 2 nach dem Befund oben: Schlüssel bei der
Registrierung, kein Wechsel-Knopf.

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
