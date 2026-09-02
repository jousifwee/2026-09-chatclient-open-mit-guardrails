# 2026-09 Chatclient „open" — mit Guardrails

Entwicklertreff-Projekt des ITZ Rostock. Ein Chatclient gegen den
[UTZ MessageHub](https://utz-messagehub.itzcloud.de/), einen öffentlichen
Store-and-forward-Vermittlungsdienst.

## Worum es wirklich geht

Der Chatclient ist **Vehikel, nicht Ziel**. Geübt werden zwei Dinge:

- **Guardrails** — ausführbare und dokumentierte Grenzen für Agentenarbeit.
- **Agentenlesbare Projektdokumentation** — Architektur, Funktion und UX so vollständig
  festgelegt, dass ein Agent beim Codieren keine Freiräume mit eigenen Annahmen füllt.

Deshalb gilt hier: **Doku zuerst, Code danach.** Jede Architektur-, Funktions- und
UX-Entscheidung steht als ADR fest, bevor sie implementiert wird. Der aktuelle Stand des
Repos ist bewusst reine Dokumentation.

## Einstieg

| Wenn du … | dann lies |
|---|---|
| als Agent hier arbeitest | [CLAUDE.md](CLAUDE.md) — die Quelle der Wahrheit |
| verstehen willst, wie der Hub tickt | [docs/api-messagehub.md](docs/api-messagehub.md) |
| die Bausteine sehen willst | [docs/architecture.md](docs/architecture.md) |
| wissen willst, wie sich das anfühlt | [docs/ux-bedienkonzept.md](docs/ux-bedienkonzept.md) |
| wissen willst, was verboten ist | [docs/guardrails.md](docs/guardrails.md) |
| eine Entscheidung nachvollziehen willst | [docs/adr/](docs/adr/) |

## ⚠️ Nur synthetische Testdaten

Der Hub läuft auf einer Demo-Box bei einem externen Anbieter in einer öffentlichen Cloud,
und `GET /open/names` **veröffentlicht jeden benutzten Namen im Internet**. Keine
personenbezogenen Daten, keine Kundendaten, keine Zugangsdaten, keine Echtdaten aus
Produktivsystemen — auch nicht zum Ausprobieren. Das gilt ausdrücklich **auch für die Namen**
in `to` und `from`. Details in [docs/guardrails.md](docs/guardrails.md).

## Werkzeuge

```bash
# Prompt-Protokoll aus den Claude-Code-Transcripts neu erzeugen
python tools/collect_prompts.py
```

Ergebnis ist [PROMPTS.md](PROMPTS.md): alle Prompts dieses Projekts chronologisch, mit
Zeitstempel und genutztem Modell. Die Datei wird bei jedem Lauf komplett überschrieben —
nicht von Hand editieren.
