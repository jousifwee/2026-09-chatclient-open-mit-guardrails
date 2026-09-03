# ADR-0016: Browser-Stack — Angular 21, `@angular/build`, TypeScript 5.9, npm

**Status:** angenommen (2026-09-03)

## Kontext

[ADR-0004](0004-frontend-angular-material3.md) legt Angular mit Material 3 fest, sagt aber
nichts über Fassung, Buildwerkzeug und Paketmanager. Eine Prüfung des Repos am 2026-09-03
ergab null Treffer für Angular CLI, esbuild, npm, pnpm — die eigentliche Browser-App-Technik
war also offen und wäre beim ersten `ng new` improvisiert worden.

Der ITZ-Hausstandard (`extended-angular-standard-template`) benutzt Angular `^21.2`,
TypeScript `~5.9.3`, rxjs `~7.8`, `zone.js ~0.15` und `@angular/build ^21.2` — den
esbuild-basierten Builder, nicht den alten Webpack-Builder. Einen Paketmanager legt auch der
Hausstandard nicht fest (`packageManager` fehlt in seiner `package.json`).

## Entscheidung

| Baustein | Festlegung |
|---|---|
| Angular | `^21.2` — Standalone, Signals, `OnPush` ([ADR-0004](0004-frontend-angular-material3.md)) |
| Angular Material | `^21.2`, Material-3-Tokens |
| Buildwerkzeug | **`@angular/build`** (esbuild), nicht `@angular-devkit/build-angular` |
| TypeScript | `~5.9.3`, `strict: true` |
| rxjs | `~7.8` — nur wo Streams wirklich gebraucht werden; Zustand läuft über Signals |
| Paketmanager | **npm**, mit versioniertem `package-lock.json` |
| Node | die von Angular 21 unterstützte LTS-Fassung, in `engines` festgeschrieben |
| Workspace | **eine** `angular.json` mit zwei Anwendungen und vier Bibliotheken ([ADR-0015](0015-zwei-apps-getrennte-transporte.md)) |

Versionen werden **exakt aus dem Hausstandard übernommen**, nicht neu gewählt. Ein Sprung auf
eine neuere Angular-Fassung ist eine eigene Entscheidung, keine Nebenwirkung eines
`npm update`.

## Begründung

- **Übernehmen statt entscheiden.** Der Hausstandard ist erprobt, und dieses Projekt ist kein
  Ort, um eine Angular-Fassung zu evaluieren. Abweichen würde Aufwand erzeugen ohne Ertrag.
- **`@angular/build` ist in Angular 21 der Standard.** Der Webpack-Builder ist Altlast; wer
  ihn heute wählt, tut es aus Gewohnheit.
- **npm, weil es keinen Grund für etwas anderes gibt.** pnpm wäre schneller und
  plattensparender, aber der Hausstandard setzt es nicht ein, und ein abweichender
  Paketmanager kostet jeden Mitleser eine Rückfrage. Das `package-lock.json` gehört ins Repo,
  damit zwei Rechner dasselbe bauen.
- **Signals für Zustand, rxjs nur wo nötig.** Die Zustandsschicht aus
  [architecture.md](../architecture.md) ist Signal-basiert; rxjs bleibt für den Poll-Takt und
  HTTP, wo es ohnehin auftritt.
- **Ein Workspace statt zweier**, weil die vier Bibliotheken von beiden Anwendungen benutzt
  werden.

## Folgen

- `npm ci` ist der reproduzierbare Installationsbefehl, `npm install` nur beim bewussten
  Ändern von Abhängigkeiten.
- Zwei Startbefehle (`ng serve chat-open`, `ng serve chat-v2`) und zwei Build-Ziele.
- Fassungssprünge sind ADR-pflichtig. Ein `^`-Bereich erlaubt Minor-Updates innerhalb von 21
  — Major-Sprünge nicht.
- Die Bibliotheken sind Angular-Bibliotheken im Workspace, **keine** veröffentlichten Pakete.

## Verworfene Alternativen

- **Neueste Angular-Fassung unabhängig vom Hausstandard.** Kostet Abweichung ohne Ertrag; der
  Lerngegenstand hängt nicht daran.
- **pnpm.** Technisch besser, aber abweichend vom Haus und damit erklärungsbedürftig.
- **Webpack-Builder.** In Angular 21 überholt.
- **Nx.** Für zwei Anwendungen und vier Bibliotheken Overkill; die Angular CLI kann
  Mehrprojekt-Workspaces von Haus aus.
- **Zwei getrennte Workspaces.** Würde die geteilten Bibliotheken duplizieren, siehe
  [ADR-0015](0015-zwei-apps-getrennte-transporte.md).
