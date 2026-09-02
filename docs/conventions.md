# Konventionen

Gilt für Doku und Code. Wer hiervon abweicht, begründet es in einer ADR.

## Dokumentation

- **Sprache Deutsch**, auch in Code-Kommentaren und Commit-Nachrichten. Fachbegriffe der
  HTTP- und Web-Welt bleiben englisch (`GET`, `Query-Parameter`, `Origin`).
- **Eine Aussage, eine Stelle.** Fakten stehen genau einmal; überall sonst wird verlinkt.
  Doppelt gepflegte Wahrheit ist nach zwei Wochen widersprüchlich.
- **Relative Links** zwischen Repo-Dateien, damit sie auf GitHub *und* lokal funktionieren.
- **Verifiziert oder gekennzeichnet.** Steht eine technische Aussage im Repo, wurde sie
  gelesen oder geprüft. Vermutungen werden als Vermutung ausgewiesen oder weggelassen.
- **Zeilenlänge etwa 96 Zeichen** in Markdown, damit Diffs lesbar bleiben.
- **Absolute Datumsangaben**, kein „letzte Woche". Format `YYYY-MM-DD`.
- **Zeitangaben aus der API** sind UTC (`expiresAt`, `receivedAt`). Im UI werden daraus
  Restlaufzeiten, keine Zeitstempel.

## ADRs

- Dateiname `NNNN-kurzer-titel.md`, vierstellig, aufsteigend, nie neu vergeben.
- Aufbau: **Status · Kontext · Entscheidung · Begründung · Folgen · Verworfene
  Alternativen**. Die verworfenen Alternativen sind Pflicht, nicht Zierde — sie halten fest,
  was schon geprüft wurde.
- Status: `angenommen`, `abgelöst durch ADR-NNNN`, `zurückgezogen`. Eine angenommene ADR
  wird **nicht editiert**, um eine Entscheidung zu ändern; sie wird abgelöst.
- Eine ADR beschreibt **eine** Entscheidung. Zwei Entscheidungen sind zwei ADRs.
- Index in [adr/README.md](adr/README.md) mitpflegen.

## Code (sobald es welchen gibt)

- **TypeScript strikt.** `strict: true`, kein `any` ohne Kommentar, der es begründet.
- **Angular:** Standalone-Komponenten, Signals für Zustand, `OnPush`. Angular Material 3 als
  Komponentenbibliothek — keine zweite UI-Bibliothek daneben.
- **Schichtgrenzen einhalten** ([architecture.md](architecture.md)). Eine Komponente ruft
  nie `fetch` und nie IndexedDB.
- **Keine magischen Zahlen.** Grenzwerte des Hubs und Poll-Intervalle stehen als benannte
  Konstanten an einer Stelle, mit Verweis auf die ADR, die sie festlegt.
- **Fehler sind Werte, nicht Ausnahmen**, wo es um erwartbare Lagen geht: `204`, `404` beim
  Entnehmen, nicht entschlüsselbare Nutzlast. Ausnahmen bleiben Programmierfehlern.
- **Namen im Code deutsch oder englisch, aber konsistent je Schicht.** Fachbegriffe des
  Bedienkonzepts (`entnehmen`, `eingang`) behalten ihr deutsches Wort, damit Doku und Code
  dasselbe Wort benutzen.

## Commits

- **Aussagesatz im Imperativ oder Präsens**, erste Zeile höchstens 72 Zeichen.
- Der Rumpf sagt **warum**, nicht was — das steht im Diff.
- Ein Commit ist eine abgeschlossene Aussage. Doku und zugehörige ADR gehören in **einen**
  Commit.
- Keine Geheimnisse, keine personenbezogenen Daten, keine echten Namen — auch nicht in der
  Nachricht.
