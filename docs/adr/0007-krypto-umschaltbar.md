# ADR-0007: Klartext und AES-GCM umschaltbar, selbstbeschreibender Umschlag

**Status:** angenommen (2026-09-02)

## Kontext

Die Nutzlast ist für den Hub **opak**: er interpretiert sie nicht und erwartet keine
Struktur. Die Spezifikation nennt als typischen Inhalt ein Chiffrat in Base64 und formuliert:
wer verschlüsselt einliefert, bekommt es verschlüsselt zurück.

Gleichzeitig ist der offene Pfad **welt-lesbar und welt-entnehmbar** (verifiziert): jeder
Eingang ist ohne Nachweis abrufbar, `GET /open/names` listet die belegten Namen öffentlich.
Vertraulichkeit kann also **ausschließlich** aus clientseitiger Verschlüsselung entstehen.

Für ein Lehrstück ist beides wertvoll: der Klartext zeigt, dass am offenen Pfad nichts
geschützt ist, das Chiffrat zeigt, wie man es trotzdem benutzen kann.

## Entscheidung

**Beide Betriebsarten, umschaltbar je Konversation** — und ein **selbstbeschreibender
Umschlag**, damit der Empfänger je Nachricht erkennt, was er vor sich hat.

Umschlag als JSON-Zeichenkette in `message`, **nicht** zusätzlich Base64-verpackt:

```json
{ "v": 1, "mode": "plain", "body": "Hallo" }
```

```json
{ "v": 1, "mode": "aes-gcm",
  "kdf": { "alg": "PBKDF2", "hash": "SHA-256", "iter": 250000, "salt": "<b64>" },
  "iv": "<b64>", "ct": "<b64>" }
```

Verfahren: **WebCrypto**, AES-GCM mit 256 Bit, Schlüssel per **PBKDF2** aus einer je
Konversation geteilten Passphrase, `SHA-256`, 250 000 Iterationen, Salt je Nachricht neu, IV
je Nachricht neu (12 Byte, aus `crypto.getRandomValues`).

**Deutung je Nachricht, nicht je Konversation** — vier Ausgänge, alle normal:

| Fall | Zustand |
|---|---|
| `mode: "plain"` | Klartext anzeigen |
| `mode: "aes-gcm"`, Entschlüsselung gelingt | Klartext anzeigen |
| `mode: "aes-gcm"`, Entschlüsselung scheitert | **nicht entschlüsselbar** |
| kein gültiger Umschlag | **Fremdformat**, Rohtext gekürzt, als unsicher markiert |

**Passphrasen leben ausschließlich im Arbeitsspeicher der laufenden Sitzung.** Nicht in
IndexedDB, nicht in `localStorage`, nicht in `sessionStorage`, nicht in der URL. Abgeleitete
Schlüssel werden ebenfalls nicht persistiert. Nach dem Neuladen wird erneut gefragt.

## Begründung

- **Der Kontrast ist die Lehre.** Im Klartextmodus ist am Hub direkt sichtbar, dass dort
  nichts geschützt ist — deshalb geht der Umschlag als lesbares JSON hinein und nicht
  Base64-verpackt.
- **Der Umschlag ist keine Zierde, sondern notwendig.** Weil jeder Fremde in jeden Eingang
  einliefern darf und die Betriebsart umschaltbar ist, ist die Form der Nutzlast eine
  Eigenschaft der **einzelnen Nachricht**. Ohne Selbstbeschreibung müsste der Client raten.
- **Fremdformat ist der Normalfall.** Ein `try/catch`, das hier eine Fehlermeldung wirft,
  macht den Client durch eine einzige fremde Nachricht unbenutzbar.
- **AES-GCM ist authentifiziert.** Ein fehlgeschlagener Integritätstest ist von einer
  falschen Passphrase nicht zu unterscheiden — beides führt zum Zustand „nicht
  entschlüsselbar", und genau das ist die ehrliche Aussage.
- **Passphrase nicht speichern**, weil eine gespeicherte Passphrase ein gespeichertes
  Geheimnis ist. Der Preis (erneute Eingabe nach dem Neuladen) ist im Lernkontext
  angemessen.
- **`v` von Anfang an**, damit ein zweites Format später unterscheidbar ist, ohne zu raten.

## Folgen

- Doppelte Zustandslogik im UI: Betriebsart fürs Senden, Umschlagdeutung fürs Empfangen. Sie
  sind unabhängig — eine verschlüsselte Konversation kann Klartext enthalten und umgekehrt.
- Der Umschlag kostet Platz. Bei 64 KB Grenze unkritisch, aber die effektive Textlänge ist
  kleiner als 64 KB und muss beim Senden berücksichtigt werden.
- Der Nutzer muss die Passphrase außerhalb dieses Clients austauschen. Ein
  Schlüsselaustausch ist **nicht** Teil dieses Projekts.
- Eine entnommene, nicht entschlüsselbare Nachricht ist endgültig unlesbar. Das UI muss
  diesen Zustand darstellen können ([architecture.md](../architecture.md)).

## Verworfene Alternativen

- **Nur AES-GCM.** Verliert den didaktischen Kontrast und die Möglichkeit, am Hub zu zeigen,
  was auf dem offenen Pfad wirklich passiert.
- **Nur Klartext.** Einfacher, aber der Client könnte nicht vorführen, wie man einen
  ungeschützten Vermittlungsdienst sinnvoll benutzt.
- **Asymmetrisches Verfahren** (Schlüsselpaare je Teilnehmer). Fachlich überlegen, braucht
  aber Schlüsselverteilung und Vertrauensanker — und der Hub bietet dafür keine Grundlage,
  weil er keine Identität kennt. Wäre ein eigenes Projekt.
- **Betriebsart global statt je Konversation.** Passt nicht zu einem Eingang, der Nachrichten
  verschiedener Absender mischt.
- **Passphrase in `sessionStorage` halten**, um Neuladen zu überleben. Verworfen: ein
  Geheimnis an Speicher, den jedes Skript im selben Origin lesen kann, für einen reinen
  Bequemlichkeitsgewinn.
