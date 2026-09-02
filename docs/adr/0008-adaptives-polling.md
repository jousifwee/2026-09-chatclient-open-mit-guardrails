# ADR-0008: Adaptives Polling mit festen Werten

**Status:** angenommen (2026-09-02)

## Kontext

Der Hub bietet **keine** Benachrichtigung: keine Server-Sent Events, keine WebSockets, kein
Webhook. Neue Nachrichten sind nur durch Abrufen feststellbar.

Randbedingungen:

- `GET /open/messages` ist **nicht** rate-begrenzt. Das Limit von 60 Aufrufen pro Minute
  betrifft ausschließlich Einlieferungen (`POST`).
- Der Aufruf ist folgenlos und beliebig wiederholbar.
- Der Dienst läuft auf einer Demo-Box; `503` mit `Retry-After` ist ein vorgesehener Zustand.
- Nachrichten verfallen nach 60 Minuten — sehr lange Intervalle verpassen nichts, verzögern
  aber die Anzeige.

## Entscheidung

**Adaptives Polling mit festgelegten Werten** — damit hier niemand improvisiert:

| Lage | Intervall |
|---|---|
| Nach Senden oder eingegangener Nachricht | 3 s |
| Verdopplung je leerem Zyklus | 3 → 6 → 12 → 24 → 48 s |
| Obergrenze im Leerlauf | 60 s |
| Tab nicht sichtbar (`visibilitychange`) | angehalten |
| `503` mit `Retry-After` | genau diese Wartezeit, danach Neustart bei 3 s |

Der Takt ist **sichtbar und übersteuerbar**:

- Kopfzeile zeigt den Zeitpunkt des letzten Abrufs („⟳ vor n s"); Klick holt sofort.
- Schalter zum Anhalten, im angehaltenen Zustand deutlich erkennbar.
- Nach dem Zurückkehren zu einem pausierten Tab sagt die Kopfzeile, dass pausiert war.
- Bei `503`: Anzeige „Hub ausgelastet, nächster Versuch in n s" — kein stilles
  Weiterhämmern.

## Begründung

- **Der Takt ist keine technische Notwendigkeit, sondern Höflichkeit** gegenüber einer
  Demo-Box. Das wird auch so begründet und nicht als Limit-Umgehung getarnt — `GET` hat
  kein Limit.
- **Kurz bei Aktivität, lang im Leerlauf** trifft die Erwartung: während eines Gesprächs
  soll es sich flüssig anfühlen, ein offener Tab über Nacht soll nicht dauerhaft Verkehr
  erzeugen.
- **Feste Werte in der ADR statt „adaptiv" als Absicht.** Ein Agent, der nur „adaptiv" liest,
  erfindet eine eigene Kurve. Genau das soll dieses Repo verhindern
  ([ADR-0001](0001-doku-zuerst.md)).
- **Sichtbarkeit ist Pflicht.** Verstecktes Hintergrundverhalten ist in einem Lehrprojekt der
  falsche Default; wer den Takt sieht, versteht, dass es Polling ist.
- **Pause bei unsichtbarem Tab** ist der größte Einspareffekt für den geringsten Aufwand.

## Folgen

- Im Leerlauf bis zu 60 s Verzögerung bis zur Anzeige. Vertretbar bei 60 min Verfall.
- Zustandsmaschine für den Takt gehört in die Zustandsschicht, nicht in eine Komponente
  ([architecture.md](../architecture.md)).
- Die Werte sind benannte Konstanten an **einer** Stelle, mit Verweis auf diese ADR
  ([conventions.md](../conventions.md)).
- `Retry-After` muss ausgewertet werden ([ADR-0012](0012-fehler-und-grenzfaelle.md)).

## Verworfene Alternativen

- **Fester Takt, etwa 5 s.** Vorhersagbar und einfacher, erzeugt aber im Leerlauf dauerhaft
  Verkehr gegen eine Demo-Box, ohne dass jemand hinsieht.
- **Nur manuelle Aktualisierung.** Am sparsamsten und macht jeden Aufruf nachvollziehbar,
  fühlt sich aber im Gespräch zäh an und lässt den Eingang unbemerkt volllaufen.
- **Long Polling.** Der Hub unterstützt es nicht; `GET` antwortet sofort mit `204`.
- **`503` mit festem Retry beantworten.** Ignoriert `Retry-After` und verschärft genau die
  Auslastung, die zum `503` geführt hat.
