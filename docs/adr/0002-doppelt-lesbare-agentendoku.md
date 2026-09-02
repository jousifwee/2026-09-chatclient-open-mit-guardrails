# ADR-0002: Agentendoku für Claude und Copilot aus einer Quelle

**Status:** angenommen (2026-09-02)

## Kontext

Im Projekt werden mindestens zwei KI-Werkzeuge benutzt: Claude Code und GitHub Copilot. Beide
lesen Projektinstruktionen, aber an **unterschiedlichen** Stellen:

- Claude Code liest `CLAUDE.md`.
- GitHub Copilot liest `.github/copilot-instructions.md`.
- Werkzeugübergreifend hat sich `AGENTS.md` als offener Standort etabliert.

Naiv gelöst hieße das: dieselben Regeln dreimal pflegen. Nach der zweiten Änderung
widersprechen sich die Fassungen, und ein Agent handelt nach der veralteten.

## Entscheidung

**Eine Quelle, zwei Zeiger.**

- **`CLAUDE.md` ist die Quelle der Wahrheit.** Dort stehen Projektzweck, Doku-Karte, harte
  Regeln, festgelegter Stack und Schnellbefehle.
- **`AGENTS.md`** ist ein kurzer, tool-agnostischer Zeiger darauf, mit den vier Fallen, die
  einen fertig aussehenden Aufruf brechen.
- **`.github/copilot-instructions.md`** ist der Zeiger für Copilot. Weil Copilot Anweisungen
  knapp und direkt braucht, enthält diese Datei zusätzlich die harten Regeln als
  Aufzählung — inhaltlich deckungsgleich mit `CLAUDE.md`, nie abweichend.
- **Fachliche Tiefe steht in `docs/`** und wird von allen drei Dateien nur verlinkt.

Wer eine Regel ändert, prüft beide Zeiger im selben Commit.

## Begründung

- **Ein Zeiger veraltet sichtbar, eine Kopie veraltet unsichtbar.** Ein Verweis auf
  `CLAUDE.md` bleibt richtig, auch wenn sich der Inhalt dort ändert.
- **Copilot braucht etwas Redundanz.** Ein reiner Verweis wird in kurzen Kontexten
  unzuverlässig befolgt. Deshalb dort die harten Regeln ausgeschrieben — der einzige
  bewusste Duplikat-Punkt, und er ist als solcher benannt.
- **Menschen lesen `README.md`.** Die Trennung „Mensch gegen Agent" hält beide Texte kurz.

## Folgen

- Drei Dateien am Repo-Wurzelrand, die auf dasselbe zeigen. Gewollt.
- Die Regeln in `.github/copilot-instructions.md` sind bei jeder Regeländerung
  mitzupflegen — die einzige Stelle mit Pflegeaufwand.
- Weitere Werkzeuge bekommen weitere Zeiger, nie weitere Quellen.

## Verworfene Alternativen

- **Symlinks** von `AGENTS.md` und `.github/copilot-instructions.md` auf `CLAUDE.md`. Auf
  Windows ohne erweiterte Rechte unzuverlässig, und GitHub rendert sie nicht als Inhalt.
- **Generieren aus einer Quelle per Skript.** Löst das Problem, kostet aber einen
  Build-Schritt für drei kurze Dateien und erzeugt Dateien, die im Repo aussehen wie
  handgepflegt.
- **Nur `AGENTS.md`.** Claude Code und Copilot würden ihre erwarteten Dateien nicht finden;
  die Instruktionen wären zwar da, aber nicht automatisch im Kontext.
