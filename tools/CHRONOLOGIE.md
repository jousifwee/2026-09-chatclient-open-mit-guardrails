Die vier offenen Entscheidungen als Text, damit du in Prosa antworten kannst — jeweils mit meiner Empfehlung:

1. Stack
- a) Vanilla TypeScript + Vite ← Empfehlung: Fokus bleibt auf Guardrails und Doku, nicht auf Framework-Konventionen
- b) Angular + Material 3 (Hausstandard, wie extended-angular-standard-template und die MessageHub-Seite selbst)
- c) React + Vite

2. Nachrichten-Lebenszyklus. Der Hub hat keine Historie: GET ist folgenlos und wiederholbar, DELETE entnimmt endgültig, Verfall nach 60 Minuten, max. 20 Nachrichten je Name.
- a) Automatisch entnehmen, Verlauf nur lokal (IndexedDB) — echtes Chat-Gefühl, aber gerätegebunden, zweiter Client sieht nichts mehr
- b) Nur ansehen, nie entnehmen — mehrere Geräte sehen dasselbe, aber Queue läuft bei 20 voll
- c) Anzeigen folgenlos, Entnehmen als bewusste Nutzeraktion ← Empfehlung: macht die Store-and-forward-Semantik im UI sichtbar, didaktisch am ehrlichsten

3. Krypto. Der Hub behandelt die Nutzlast als opak, /open/names ist öffentlich, jeder kann jede Queue lesen und entnehmen.
- a) AES-GCM, PBKDF2 aus geteilter Passphrase je Konversation, Chiffrat Base64 ← Empfehlung: entspricht dem Spec-Beispiel und führt vor, wozu der offene Pfad taugt
- b) Klartext-JSON
- c) Umschaltbar — zeigt den Unterschied, kostet doppelte Zustandslogik

4. Bedienkonzept für neue Nachrichten. Das Rate-Limit (60/min) betrifft nur POST, GET ist frei.
- a) Polling mit sichtbarem Intervall (z. B. 5 s), Pause-Schalter, Anzeige des letzten Abrufs
- b) Nur manuelle Aktualisierung ← Empfehlung: kein versteckter Hintergrundverkehr, jeder API-Aufruf nachvollziehbar
- c) Adaptives Polling

---

Diese Punkte fixiere ich ohne Rückfrage aus den Fakten, wenn du nicht widersprichst:

- Nur der offene Pfad /open/.... /oidc/config liefert live configured: false, die Nachrichten-Endpunkte der Token- und OIDC-Stufe existieren laut Spec noch nicht. Die Stufe wird aber als austauschbare Abstraktion modelliert, damit Token/OIDC später ohne Umbau andocken.
- Nur synthetische Namen in to/from. /open/names veröffentlicht jeden benutzten Namen im Internet — ein echter Vor- oder Nachname wäre ein Compliance-Verstoß. Das wird harte Guardrail inkl. Validierungsmuster ^[A-Za-z0-9_-]{1,32}$.
- from ist eine unbeglaubigte Behauptung und muss im UI als solche kenntlich sein, nicht als Identität.
- Doku-Layout nach Hausstandard: CLAUDE.md als Quelle der Wahrheit, AGENTS.md als tool-agnostischer Zeiger darauf, zusätzlich .github/copilot-instructions.md für Copilot, Detailtiefe in docs/architecture.md und docs/adr/.
- Fehlerbehandlung explizit für 413, 429, 503 (mit Retry-After) und 204 als Normalfall statt Fehler.
- credentials: "include" verboten — der Hub sendet Access-Control-Allow-Origin: *, mit Credentials scheitert der Aufruf trotz korrekt aussehendem Code. Steht so in der Spec und ist eine klassische Agenten-Falle.

Sag mir zu 1–4 deine Wahl (z. B. „1a, 2c, 3a, 4b"), dann schreibe ich das Doku-Set und lege das Memory ins Projekt.