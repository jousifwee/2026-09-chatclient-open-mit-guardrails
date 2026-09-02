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

## Harte Regeln

1. **Nur synthetische Bezeichner** in `to` und `from`. Keine echten Vor- oder Nachnamen —
   `GET /open/names` veröffentlicht jeden benutzten Namen im Internet. Muster:
   `^[A-Za-z0-9_-]{1,32}$`, Groß- und Kleinschreibung wird unterschieden.
2. **Keine undeklarierten Felder oder Query-Parameter.** Der Hub validiert strikt:
   `400 {"message":["property from should not exist"],...}`. Erfinde keine Filter-,
   Sortier- oder Paginierungsparameter — es gibt keine.
3. **`GET /open/messages` kennt nur `to`.** Der Aufruf liefert den **gesamten Eingang**
   eines Namens über alle Absender hinweg. Konversationen entstehen **clientseitig** durch
   Gruppieren nach `from` (ADR-0005). Niemals ein `GET` je Konversation.
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

## Grenzen des Hubs, die im Code auftauchen müssen

Nutzlast höchstens 64 KB (`413`) · höchstens 20 Nachrichten je Name (`429`) · höchstens 500
belegte Namen und 64 MB über alles (`503`, `Retry-After` beachten) · 60 Einlieferungen je
Aufrufer und Minute (`429`) · Verfall jeder Nachricht nach 60 Minuten.
