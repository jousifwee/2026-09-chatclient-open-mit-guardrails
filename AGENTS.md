# AGENTS.md

Diese Datei existiert für die tool-agnostische Auffindbarkeit (offener `AGENTS.md`-Standard).

**Die Quelle der Wahrheit für Agenten-Instruktionen ist [CLAUDE.md](CLAUDE.md).** Dort stehen
Projektzweck, Doku-Karte, die harten Regeln, der festgelegte Stack und die Schnellbefehle.
Bitte zuerst CLAUDE.md lesen. Diese Datei ergänzt nicht und weicht nicht ab.

Kurz: Ein **Chatclient gegen den UTZ MessageHub** (Angular + Material 3, kein eigenes
Backend). Der Projektzweck ist das Erlernen von **Guardrails** und **agentenlesbarer
Dokumentation** — der Chatclient ist Vehikel, nicht Ziel.

**Die eine Regel, die alles andere trägt:** Jede Architektur-, Funktions- und
UX-Entscheidung wird **vor** der Implementierung als ADR unter [`docs/adr/`](docs/adr/)
fixiert. Bei einer ungeklärten Frage wird nicht auf Verdacht implementiert, sondern eine ADR
vorgeschlagen.

Vier Fallen, die einen fertig aussehenden Aufruf scheitern lassen — Details in CLAUDE.md:

- **Zwei Stufen, zwei Anwendungen.** Auf dem **offenen Pfad** kennt `GET /open/messages`
  **nur** `to`, und ein `from` bricht den Aufruf mit `400`. Auf der **v2-Stufe** heißt der
  Abruf `GET /v2/me/messages`, hat **keinen** `to`-Parameter und **akzeptiert** `?from=`.
  Die beiden nicht verwechseln.
- Undeklarierte Felder oder Query-Parameter ergeben `400 "property <x> should not exist"`.
- `credentials: "include"` bricht CORS gegen `Access-Control-Allow-Origin: *`.
- `to`/`from` **niemals** mit echten Namen belegen — `GET /open/names` ist öffentlich.
- Namen kleinschreiben; geantwortet wird aber an das **rohe** `from`, sonst landet die
  Antwort lautlos in einer anderen Warteschlange.
- Die **OIDC-Stufe** ist ignoriert — nichts davon einbauen.
- Auf v2 gibt es **kein `from`** im Rumpf; der Absender folgt aus den Zugangsdaten.
- `/v2/open-directory` ist **erklärtermaßen kaputt** (jeder überschreibt jeden Eintrag) —
  **kein Bezugsweg für Schlüssel**. Beglaubigt ist nur `GET /v2/directory`.
