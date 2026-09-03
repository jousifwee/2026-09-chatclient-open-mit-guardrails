# ADR-0017: Teststack — Vitest für Unit/Component, Playwright für E2E

**Status:** angenommen (2026-09-03)

## Kontext

Das Repo enthielt am 2026-09-03 **keine** Testentscheidung. Angular-CLI-Projekte wurden
historisch mit Karma und Jasmine aufgesetzt; Ende 2025 hat das Angular-Team **Karma
deprecated** und mit **Angular 21 Vitest zum stabilen Standard-Unit-Test-Runner** der CLI
gemacht. Protractor war schon vorher entfernt. Der ITZ-Hausstandard hat das in seiner
ADR-0010 nachgezogen: Vitest für Unit und Component, Playwright für E2E und visuelle Tests.

Für dieses Projekt kommt ein zweiter Grund hinzu. [guardrails.md](../guardrails.md) hält
selbst fest, dass die Guardrails bisher überwiegend **gelesen** und **begründet** sind, aber
kaum **erzwungen**. Tests sind die naheliegendste Stelle, das zu ändern.

## Entscheidung

**Vitest** für Unit- und Component-Tests, **Playwright** für E2E — Fassungen aus dem
Hausstandard (`vitest ^4.1`, `@playwright/test ^1.49`).

Dazu eine Festlegung, die über den Runner hinausgeht: **Die Guardrails aus
[guardrails.md](../guardrails.md) Stufe 2 werden zu Tests.** Wer eine solche Regel aufstellt,
schreibt den Test mit, der ihre Verletzung sichtbar macht. Verbindlich abgedeckt:

| Regel | Test |
|---|---|
| `204` ist „nichts da", nicht Fehler und nicht leeres Array | Transport-Test je Stufe |
| Fehlerabbildung `400`/`413`/`429`/`503` inkl. `Retry-After` | Transport-Test mit den beiden `429`-Ursachen getrennt |
| `message` ist ein **Array** | Test mit dem echten Fehlerrumpf des Dienstes |
| Nur deklarierte Felder und Parameter | Test, der die gesendete Anfrage gegen das DTO prüft; auf dem offenen Pfad **kein** `from` |
| Umschlag: vier Ausgänge, alle normal | `PayloadCodec`-Tests inkl. **Fremdformat** und **nicht entschlüsselbar** |
| Fremdformat macht den Client nicht unbenutzbar | Test mit Rohtext, der kein JSON ist |
| Namen kleinschreiben, aber an rohes `from` antworten | Test mit `Heiko` als eingehendem Absender |
| Kein automatisches `DELETE` nach dem Anzeigen | E2E: Nachricht bleibt nach dem Anzeigen „am Hub" |
| Kein privater Schlüssel im veröffentlichten JWK | Test, der `d` im Ergebnis ausschließt ([ADR-0018](0018-app2-asymmetrisch-ecdh.md)) |

**Der Transport wird gegen Attrappen getestet, nicht gegen den laufenden Hub.** Die Antworten
der Attrappen sind aus den Schnappschüssen unter [`api/`](../api/) abgeleitet.

**Playwright deckt die Abläufe ab, die der Lerngegenstand sind:** explizites Entnehmen,
Belegungswarnung, Umschalten der Betriebsart, Registrierung und Anmeldung auf v2, Vergleich
des Fingerabdrucks.

## Begründung

- **Karma ist abgekündigt**, Vitest ist in Angular 21 der Standard. Etwas anderes zu wählen
  hieße, gegen das Framework zu arbeiten.
- **Gleichlauf mit dem Hausstandard** — dieselbe Begründung wie in
  [ADR-0016](0016-browser-stack-angular21.md).
- **Tests sind hier die einzige erzwingende Guardrail, die wir selbst bauen können.** Eine
  Regel in einer Markdown-Datei wird gelesen; ein roter Test wird nicht übergangen. Das ist
  der Punkt, an dem dieses Projekt von „dokumentierten" zu „ausführbaren" Leitplanken kommt.
- **Attrappen statt Live-Dienst**, weil der Hub eine Demo-Box ist, jederzeit zurückgesetzt
  wird und sich innerhalb eines Tages zweimal geändert hat. Ein Test, der davon abhängt, ist
  kein Test.
- **Die Schnappschüsse im Repo machen die Attrappen prüfbar.** Ändert sich der Dienst, fällt
  es beim Vergleich auf, nicht durch rätselhaft rote Tests.

## Folgen

- `npm test` (Vitest) und `npm run e2e` (Playwright) als die zwei Befehle.
- Jede neue Regel in Stufe 2 der Guardrails zieht einen Test nach sich. Wer eine Regel ohne
  Test aufstellt, benennt das ausdrücklich.
- Playwright braucht Browser-Downloads; das gehört in die Einrichtungsanleitung.
- Ein E2E-Test gegen den echten Hub kann als **separater, ausdrücklich markierter** Lauf
  existieren — er ist nicht Teil von `npm run e2e`.

## Verworfene Alternativen

- **Karma und Jasmine.** Abgekündigt.
- **Jest.** Für Angular 21 nicht der CLI-Standard, mehr Konfiguration, kein Vorteil.
- **Nur E2E, keine Unit-Tests.** Genau die Regeln, die hier zählen (Statuscode-Abbildung,
  Umschlagdeutung, Namensnormalisierung) sind auf Einheitsebene billig und über E2E teuer und
  unzuverlässig zu prüfen.
- **Tests gegen den laufenden Hub.** Siehe Begründung; der Dienst ist bewusst flüchtig.
