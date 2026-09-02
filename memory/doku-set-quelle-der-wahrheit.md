---
name: doku-set-quelle-der-wahrheit
description: CLAUDE.md ist die Quelle der Wahrheit; AGENTS.md und .github/copilot-instructions.md sind Zeiger, damit Claude und Copilot dieselben Regeln lesen.
metadata:
  type: project
---

Der Nutzer will, dass **alle KI-relevanten Markdown-Dateien sowohl für Claude als auch für
GitHub Copilot funktionieren**. Umgesetzt am 2026-09-02 als **eine Quelle, zwei Zeiger**:

- `CLAUDE.md` — Quelle der Wahrheit für Agenten-Instruktionen.
- `AGENTS.md` — tool-agnostischer Zeiger (offener `AGENTS.md`-Standard).
- `.github/copilot-instructions.md` — Zeiger für Copilot, enthält die harten Regeln
  zusätzlich ausgeschrieben (bewusstes, benanntes Duplikat: Copilot befolgt reine Verweise
  in kurzen Kontexten unzuverlässig).
- Fachtiefe in `docs/` — `api-messagehub.md`, `architecture.md`, `ux-bedienkonzept.md`,
  `guardrails.md`, `conventions.md`, `docs/adr/`.

Das **Projektgedächtnis liegt im Repo** (`memory/`), nicht im Werkzeug-Verzeichnis unter
`~/.claude/projects/.../memory/` — versioniert und für jeden Agenten lesbar. Wird eine
Erinnerung angelegt oder geändert, gehört sie hierher und in `memory/MEMORY.md`.

**Why:** Dieselben Regeln dreimal zu pflegen führt nach zwei Änderungen zu widersprüchlichen
Fassungen, und ein Agent handelt dann nach der veralteten. Begründung als ADR-0002.

**How to apply:** Wer eine Regel ändert, ändert sie in `CLAUDE.md` **und** prüft im selben
Commit `.github/copilot-instructions.md` und `AGENTS.md`. Neue Fakten nicht in die Zeiger
schreiben. Siehe [[projektziel-guardrails-lernen]], [[release-umfang-offener-pfad]],
[[prompt-protokoll-tooling]].
