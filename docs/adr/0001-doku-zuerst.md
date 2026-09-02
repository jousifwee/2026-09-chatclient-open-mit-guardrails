# ADR-0001: Doku zuerst, Code danach

**Status:** angenommen (2026-09-02)

## Kontext

Das Projekt ist ein Lernprojekt. Geübt werden **Guardrails** und **agentenlesbare
Projektdokumentation** — der Chatclient ist Vehikel, nicht Ziel.

Das Problem, das dem zugrunde liegt: Ein Agent, der zu einer unklaren Frage keine Antwort in
der Dokumentation findet, hält nicht an. Er entscheidet plausibel und schreibt die
Entscheidung in Code — als Konstante, als Bedingung, als stillschweigende Annahme. Die
Entscheidung ist damit getroffen, aber nirgends begründet und für den nächsten Leser nicht
als Entscheidung erkennbar.

## Entscheidung

**Jede Architektur-, Funktions- und UX-Entscheidung wird vor der Implementierung in Markdown
fixiert** — als ADR unter `docs/adr/` und, wo es der Übersicht dient, im Fließtext der
Fachdokumente.

Stößt jemand beim Implementieren auf eine Frage, die keine ADR beantwortet, gilt:

1. **Nicht auf Verdacht implementieren.**
2. Die Lücke benennen und eine ADR vorschlagen.
3. Die Entscheidung einholen, dann bauen.

Ungeklärte Punkte werden in [architecture.md](../architecture.md) unter „Was bewusst offen
ist" geführt. Diese Liste ist die verbindliche Stelle für Offenes.

## Begründung

- **Entscheidungen im Code sind unsichtbar.** Ein Poll-Intervall von 5 Sekunden in einer
  Konstante sieht wie eine Implementierungsdetail aus, ist aber eine UX-Entscheidung mit
  Folgen für Last, Akku und wahrgenommene Geschwindigkeit.
- **Ein Agent ist nur so gut wie sein Kontext.** Wer Freiräume lässt, bekommt sie mit
  Annahmen gefüllt — vom Modell heute, von einem anderen Modell morgen, jedes Mal anders.
- **Der Zweck ist die Übung selbst.** Ein schnell gebauter Chatclient wäre kein Ergebnis
  dieses Projekts.

## Folgen

- Der Repo-Stand ist zunächst reine Dokumentation. Das ist beabsichtigt, kein Rückstand.
- Die Doku bremst kurzfristig. Sie ist der Gegenstand, nicht der Aufwand.
- Fehlt eine ADR, ist das ein Befund und keine Einladung zum Improvisieren.
- Weicht Code von einer ADR ab, ist entweder der Code falsch oder die ADR abzulösen. Beides
  wird benannt.

## Verworfene Alternativen

- **Code zuerst, Doku nachziehen.** Genau der Modus, den das Projekt abstellen soll. Die
  nachgezogene Doku beschreibt, was gebaut wurde, statt zu steuern, was gebaut wird — und
  hält die verworfenen Alternativen nicht fest.
- **Nur ein großes Architekturdokument, keine ADRs.** Fließtext verliert die Begründung und
  die geprüften Alternativen. Nach der dritten Änderung weiß niemand mehr, was warum
  entschieden wurde.
- **Entscheidungen in Issues.** Nicht im Repo, nicht offline lesbar, für einen Agenten ohne
  Netzzugriff unsichtbar.
