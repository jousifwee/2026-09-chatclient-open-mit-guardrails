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

- `GET /open/messages` kennt **nur** `to`. Es gibt **keinen** Absender-Filter.
- Undeklarierte Felder oder Query-Parameter ergeben `400 "property <x> should not exist"`.
- `credentials: "include"` bricht CORS gegen `Access-Control-Allow-Origin: *`.
- `to`/`from` **niemals** mit echten Namen belegen — `GET /open/names` ist öffentlich.
