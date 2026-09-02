---
name: release-umfang-offener-pfad
description: Dieses Release nutzt nur den offenen Pfad des MessageHub; Token und OIDC sind ignoriert, eine Absender-Filterung ist angekündigt.
metadata:
  type: project
---

Am 2026-09-02 festgelegt für das erste Release des Chatclients:

- **Nur der offene Pfad** `/open/...`. **Token- und OIDC-Stufe ausdrücklich ignoriert** —
  keine Anmeldung, kein `X-API-Key`, kein Bearer-Header, kein Aufruf unter `/oidc/` oder
  `/token/`, und **keine** vorgebaute Stufen-Abstraktion.
- **Eine serverseitige Absender-Filterung ist vom Betreiber angekündigt.** Vorbereitet ist
  nur die *Stelle* (der Eingangsabruf liegt hinter genau einer Funktion), nicht der *Aufruf*.
  Solange der Parameter nicht in der Spezifikation steht, wird er nicht gesendet — der Hub
  weist undeklarierte Parameter mit `400` ab.
- **Namenskollisionen sind über Kleinschreibung aufgelöst.** Eingaben werden normalisiert,
  **geantwortet wird aber an das rohe `from`** — sonst landet die Antwort lautlos in einer
  anderen Warteschlange.

**Why:** Der Hub bietet drei Schutzstufen an, von denen nur eine gebaut ist; und er
unterscheidet Groß-/Kleinschreibung in Namen. Beides verleitet zu vorgebauter Allgemeinheit
bzw. zu stillen Fehlern. Die Unterscheidung „Stelle vorbereiten, Aufruf nicht" ist der Kern:
bei der Filterung ist die Form der Erweiterung bekannt, bei den Schutzstufen nicht.

**How to apply:** Verbindliche Fassung mit Begründung in `docs/adr/` — ADR-0003 (Stufen),
ADR-0005 (Konversationen und Filter-Vorbereitung), ADR-0010 (striktes Schema), ADR-0014
(Kleinschreibung). Vor Codeänderungen dort nachlesen, nicht hier. Siehe
[[projektziel-guardrails-lernen]] und [[doku-set-quelle-der-wahrheit]].
