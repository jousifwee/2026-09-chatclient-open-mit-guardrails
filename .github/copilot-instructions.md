# GitHub Copilot — Repository-Instruktionen

**Die Quelle der Wahrheit für Agenten-Instruktionen ist [../CLAUDE.md](../CLAUDE.md).**
Diese Datei ist der Zeiger für GitHub Copilot und weicht inhaltlich nicht ab. Bitte
CLAUDE.md lesen, dazu [../docs/api-messagehub.md](../docs/api-messagehub.md) und die
Entscheidungen unter [../docs/adr/](../docs/adr/).

## Projekt

Chatclient gegen den **UTZ MessageHub** (<https://utz-messagehub.itzcloud.de/>), einen
öffentlichen Store-and-forward-Dienst ohne Historie und ohne Nachweis. Zweck des Projekts ist
das Erlernen von **Guardrails** und **agentenlesbarer Dokumentation**; der Chatclient ist
Vehikel, nicht Ziel.

## Arbeitsregel

**Doku zuerst, Code danach.** Jede Architektur-, Funktions- und UX-Entscheidung wird vor der
Implementierung als ADR unter `docs/adr/` fixiert. Stößt du beim Vorschlagen von Code auf
eine ungeklärte Frage, implementiere **nicht auf Verdacht** — benenne die Lücke und verweise
auf die fehlende ADR.

## Festgelegter Stack — nicht abweichen

- Angular mit Angular Material 3, ITZ-Hausstandard (ADR-0004)
- Kein eigenes Backend; der Client spricht direkt mit dem Hub (ADR-0003)
- WebCrypto AES-GCM mit PBKDF2, umschaltbar gegen Klartext (ADR-0007)
- IndexedDB als einzige Historie (ADR-0011)
- Adaptives Polling (ADR-0008)
- **Keine** Stufen-Abstraktion: Token und OIDC sind in diesem Release ignoriert (ADR-0003)

## Harte Regeln

1. **Nur synthetische Bezeichner** in `to` und `from`. Keine echten Vor- oder Nachnamen —
   `GET /open/names` veröffentlicht jeden benutzten Namen im Internet. Muster:
   `^[A-Za-z0-9_-]{1,32}$`, Groß- und Kleinschreibung wird unterschieden.
2. **Keine undeklarierten Felder oder Query-Parameter.** Der Hub validiert strikt:
   `400 {"message":["property from should not exist"],...}`. Erfinde keine Filter-,
   Sortier- oder Paginierungsparameter — es gibt keine.
3. **`GET /open/messages` kennt nur `to`.** Der Aufruf liefert den **gesamten Eingang**
   eines Namens über alle Absender hinweg. Konversationen entstehen **clientseitig** durch
   Gruppieren nach `from` (ADR-0005). Niemals ein `GET` je Konversation. Eine serverseitige
   Absender-Filterung ist angekündigt — bis sie in der Spezifikation steht, wird sie **nicht
   gesendet**, auch nicht hinter einem Schalter oder auskommentiert.
4. **Kein `credentials: "include"`** in `fetch`. Der Hub antwortet mit
   `Access-Control-Allow-Origin: *` und braucht keine Credentials.
5. **`204` ist der Normalfall, kein Fehler** — leerer Eingang. Nicht als `404` oder
   Ausnahme behandeln.
6. **`DELETE` ist endgültig und unwiderruflich.** Nur auf ausdrückliche Nutzeraktion, nie
   automatisch nach dem Anzeigen (ADR-0006).
7. **Keine Zugangsdaten, Schlüssel, Passwörter, personenbezogenen oder Echtdaten** — weder
   im Code, noch in Tests, noch als Nutzlast an den Hub.
8. **Fehlgeschlagenes Entschlüsseln ist ein normaler Anzeigezustand**, keine Ausnahme.
   Ein Eingang kann Klartext und Chiffrate verschiedener Absender mischen (ADR-0007).
9. **Namen kleinschreiben** mit `toLocaleLowerCase("en-US")` — der Hub unterscheidet
   Groß-/Kleinschreibung, `anna` und `Anna` sind zwei Warteschlangen. **Aber geantwortet
   wird an das rohe `from`**, nie an die kleingeschriebene Form: sonst landet die Antwort
   lautlos in einer anderen Warteschlange (ADR-0014).
10. **Nichts zur OIDC-Stufe** — keine Anmeldung, kein Bearer-Header, kein Aufruf unter
   `/oidc/` (ADR-0003).
11. **Die beiden Stufen nicht verwechseln.** Offener Pfad (`apps/chat-open`):
   `GET /open/messages?to=<name>`, **kein** `from` — es bricht mit `400`. v2-Stufe
   (`apps/chat-v2`): `GET /v2/me/messages`, **kein** `to`, dafür optionales `?from=`;
   Einliefern über `POST /v2/messages` **ohne** `from` (Absender kommt aus Basic Auth);
   unbekannter Empfänger ergibt `404`. Vertrag in `docs/api-messagehub-v2.md`.
12. **`/v2/open-directory` ist kein Bezugsweg für Schlüssel** — dort darf jeder jeden Eintrag
   überschreiben, das ist der vorgeführte Mann-in-der-Mitte. Beglaubigt ist nur
   `GET /v2/directory` (ADR-0015).
13. **Keine hartkodierten Grenzwerte für v2.** Die Zahlen der Spezifikation (64 KB, 20, 500,
   64 MB, 60/min, 60 min) gelten ausdrücklich für den **offenen Pfad**. Für v2 sind sie nicht
   genannt: `413`, `429`, `503` behandeln, ohne die Schwelle zu kennen.
14. **Krypto in `apps/chat-v2` ist asymmetrisch**: ECDH P-256 + HKDF-SHA-256 + AES-GCM,
   Schlüsselpaar mit `extractable: false`, privater Schlüssel als `CryptoKey` in IndexedDB.
   **Niemals** `exportKey` auf den privaten Schlüssel, und vor dem Veröffentlichen prüfen,
   dass das JWK **kein `d`** enthält — gesendet werden nur `kty`, `crv`, `x`, `y`.
   Fingerabdruck über `exportKey("raw", publicKey)`, nicht über das JWK (ADR-0018).
15. **`PUT` ist im CORS des Hubs nicht erlaubt** (`Access-Control-Allow-Methods:
   GET,POST,DELETE,OPTIONS`, verifiziert 2026-09-03). Also keinen Aufruf von
   `PUT /v2/me/key` bauen: der Schlüssel geht bei `POST /v2/register` mit (ADR-0018).
16. **Stack:** Angular `^21.2` mit `@angular/build`, TypeScript `~5.9.3`, npm (ADR-0016).
   Tests mit Vitest und Playwright; jede Guardrail-Regel bekommt einen Test (ADR-0017).

## Grenzen des Hubs, die im Code auftauchen müssen

Nutzlast höchstens 64 KB (`413`) · höchstens 20 Nachrichten je Name (`429`) · höchstens 500
belegte Namen und 64 MB über alles (`503`, `Retry-After` beachten) · 60 Einlieferungen je
Aufrufer und Minute (`429`) · Verfall jeder Nachricht nach 60 Minuten.
