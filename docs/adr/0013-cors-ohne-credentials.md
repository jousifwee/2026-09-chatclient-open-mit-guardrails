# ADR-0013: Kein `credentials: "include"`

**Status:** angenommen (2026-09-02)

## Kontext

Der Hub lässt Aufrufe aus beliebigen Origins zu und setzt dafür
`Access-Control-Allow-Origin: *`. Er braucht **keine** Credentials: kein Cookie, keine
HTTP-Authentifizierung, und auf dem offenen Pfad überhaupt keinen Nachweis.

Die Spezifikation des Dienstes warnt ausdrücklich: Wird im Client `credentials: "include"`
gesetzt, verlangt der Browser einen **konkreten** Origin in `Access-Control-Allow-Origin`
statt der Wildcard. Der Aufruf scheitert dann in der CORS-Prüfung — **obwohl der Code korrekt
aussieht**.

Das ist eine typische Verwechslung: `credentials: "include"` wirkt wie eine allgemeine
„auch Anmeldedaten mitsenden"-Vorsichtsmaßnahme und wird gern vorsorglich gesetzt.

## Entscheidung

**In diesem Projekt wird `credentials` bei Aufrufen an den Hub nicht auf `"include"`
gesetzt.** Es bleibt beim Standard (`"same-origin"`).

- Kein `withCredentials: true` an Angulars `HttpClient`.
- Kein globaler HTTP-Interceptor, der Credentials oder Authorization-Header ergänzt.
- Keine Cookies, keine `Authorization`-Header an `/open/...` — dort gibt es nichts zu
  beweisen.

## Begründung

- **Der Fehler ist teuer, weil er falsch aussieht.** Die Fehlermeldung des Browsers spricht
  von CORS und Origins; die Ursache ist eine Zeile im Client. Wer die Warnung nicht kennt,
  sucht beim Dienst oder beim Reverse-Proxy.
- **Es gibt keinen Grund dafür.** Der offene Pfad kennt keinen Nachweis; mitgesendete
  Credentials hätten keinen Empfänger.
- **Ein Interceptor, der pauschal Credentials setzt, ist die wahrscheinlichste Quelle** —
  deshalb ist auch er ausdrücklich untersagt, nicht nur der einzelne Aufruf.

## Folgen

- Kommt später die Token- oder OIDC-Stufe, wird der Nachweis über einen **Header**
  transportiert (`X-API-Key` bzw. `Authorization: Bearer`) — das ist von `credentials`
  unabhängig und ändert diese ADR nicht.
- Die Regel steht in [CLAUDE.md](../../CLAUDE.md), [AGENTS.md](../../AGENTS.md) und
  [.github/copilot-instructions.md](../../.github/copilot-instructions.md), weil sie beim
  Schreiben des ersten `fetch` gebraucht wird — nicht erst beim Debuggen.

## Verworfene Alternativen

- **`credentials: "include"` setzen und beim Betreiber einen konkreten Origin erbitten.**
  Löst ein Problem, das man nicht hat, und bindet den Client an eine Liste erlaubter Origins.
- **Einen Proxy davorschalten**, um CORS zu umgehen. Zusätzlicher Baustein ohne Nutzen; der
  Hub erlaubt Wildcard-Origins bereits.
