# ADR-0004: Frontend: Angular mit Material 3

**Status:** angenommen (2026-09-02)

## Kontext

Der Client ist die gesamte Anwendung — es gibt kein eigenes Backend
([ADR-0003](0003-nur-offener-pfad.md)). Zu entscheiden war der verbindliche Stack.

Umfeld: Das ITZ Rostock pflegt Angular-Vorlagen als Hausstandard
(`angular-standard-template`, `extended-angular-standard-template` mit Angular Material 3).
Auch die Schnittstellenseite des MessageHub selbst ist eine Angular-Anwendung.

Zur Wahl standen Angular mit Material 3, Vanilla TypeScript mit Vite und React mit Vite.

## Entscheidung

**Angular mit Angular Material 3**, entsprechend dem ITZ-Hausstandard.

Präzisierungen, damit hier nichts improvisiert wird:

- **Standalone-Komponenten**, keine `NgModule`-Struktur.
- **Signals** für Zustandshaltung, `ChangeDetectionStrategy.OnPush`.
- **Angular Material 3 als einzige Komponentenbibliothek.** Keine zweite UI-Bibliothek und
  kein zusätzliches CSS-Framework daneben.
- Theming über Material-3-Tokens, hell und dunkel gleichwertig, `prefers-color-scheme`
  folgend.

## Begründung

- **Konsistenz mit dem Hausstandard wiegt hier mehr als Sparsamkeit.** Was im
  Entwicklertreff geübt wird, soll auf die reale Arbeit übertragbar sein; dort wird Angular
  eingesetzt.
- **Ein Framework mit starken Konventionen passt zum Projektzweck.** Wo das Framework
  Struktur vorgibt, gibt es weniger Freiraum, in dem ein Agent frei entscheidet — dieselbe
  Logik wie bei den ADRs, eine Ebene tiefer.
- **Material 3 liefert die gebrauchten Bausteine fertig** — Listen, Zustandschips, Dialoge,
  Snackbars, Formularvalidierung — und zwar barrierefrei und in beiden Themes.

## Folgen

- Deutlich mehr Gerüst als für die Sache nötig. Bewusst in Kauf genommen.
- Angular-Konventionen sind einzuhalten und in [conventions.md](../conventions.md) zu
  präzisieren, wo sie mit den Schichtgrenzen aus [architecture.md](../architecture.md)
  zusammenspielen.
- Die Schichtgrenzen gelten **trotz** Framework: eine Komponente ruft nie `fetch` und nie
  IndexedDB.

## Verworfene Alternativen

- **Vanilla TypeScript mit Vite.** Sachlich angemessen — die Anwendung ist klein, und der
  Fokus wäre stärker auf Guardrails und Doku statt auf Framework-Konventionen geblieben.
  Verworfen, weil die Übertragbarkeit auf die reale Arbeit im Haus höher gewichtet wurde.
- **React mit Vite.** Kein Vorteil gegenüber Angular in diesem Umfeld, aber Abweichung vom
  Hausstandard ohne fachlichen Grund.
