# ADR-0010: Nur deklarierte Felder und Parameter senden

**Status:** angenommen (2026-09-02)

## Kontext

Der Hub validiert Anfragen nach **Whitelist**. Verifiziert am 2026-09-02:

```
GET /open/messages?to=etreff_probe_rx&from=etreff_probe_a               -> 400
{"message":["property from should not exist"],"error":"Bad Request","statusCode":400}
```

Ein undeklarierter Parameter wird also **nicht ignoriert, sondern abgewiesen**. Dasselbe gilt
für Rumpffelder.

Das ist bemerkenswert, weil es eine verbreitete Erwartung bricht: Viele APIs ignorieren
Unbekanntes stillschweigend. Und es trifft genau die Stelle, an der ein Agent gern
„hilfreich" ergänzt — ein Absender-Filter, ein `limit`, ein `since`, ein `sort` erscheinen
bei einer Nachrichten-Ressource so naheliegend, dass sie eher vermutet als geprüft werden.

Tatsächlich existiert **keiner** dieser Parameter: `GET /open/messages` kennt genau `to`.

## Entscheidung

**Es werden ausschließlich Felder und Parameter gesendet, die in der Spezifikation stehen.**

- Keine erfundenen Filter, Sortierungen, Limits, Cursor oder Zeitfenster.
- Keine „harmlosen" Zusatzfelder im Rumpf von `POST /open/messages` — erlaubt sind genau
  `to`, `from`, `message`.
- Kein Ausprobieren gegen den laufenden Dienst in der Annahme, Unbekanntes werde ignoriert.
- Die Transport-Schicht baut Anfragen aus **typisierten** Objekten, die exakt den DTOs der
  Spezifikation entsprechen — nicht aus frei zusammengesetzten Objekten oder
  Query-Zeichenketten.
- Der Schnappschuss der Spezifikation liegt im Repo
  ([`docs/api/openapi.yaml`](../api/openapi.yaml)), damit die Prüfung ohne Netz möglich ist
  und Änderungen am Dienst auffallen.

## Begründung

- **Der Fehler sieht nicht wie ein Fehler aus.** Ein `400` auf einen sonst korrekten Aufruf
  wird leicht der Eingabe zugeschrieben statt dem hinzugefügten Parameter. Die Suche danach
  kostet unverhältnismäßig viel Zeit.
- **Es ist genau die Sorte Freiraum, die dieses Projekt schließen will.** Der Parameter wird
  nicht aus Nachlässigkeit hinzugefügt, sondern weil er plausibel ist. Plausibel ist hier
  aber nicht richtig, und das steht nur in der Spezifikation.
- **Typisierte DTOs machen die Regel erzwingbar**, nicht bloß erinnerbar.

## Folgen

- Filtern, Sortieren und Begrenzen geschieht **im Client**, nach dem Abruf des vollständigen
  Eingangs ([ADR-0005](0005-konversation-ist-client-konstrukt.md)).
- **Auch eine angekündigte Erweiterung wird nicht vorweggenommen.** Für den offen
  angekündigten Absender-Filter gilt diese ADR unverändert: solange der Parameter nicht in
  der Spezifikation steht, wird er nicht gesendet — auch nicht hinter einem Schalter, auch
  nicht auskommentiert. Vorbereitet wird die *Stelle*, nicht der *Aufruf*
  ([ADR-0005](0005-konversation-ist-client-konstrukt.md)).
- Der eingefrorene Schnappschuss ist zu vergleichen, wenn sich der Dienst ändert:
  `curl -s https://utz-messagehub.itzcloud.de/openapi.yaml | diff -u docs/api/openapi.yaml -`

## Verworfene Alternativen

- **Zusatzparameter senden und `400` abfangen.** Verschleiert den Fehler und erzeugt
  vermeidbare Aufrufe.
- **Auf Ignorieren durch den Dienst vertrauen.** Widerlegt, siehe Kontext.
- **Eine eigene Client-Abstraktion, die beliebige Parameter durchlässt.** Bequem beim
  Experimentieren, aber sie öffnet genau den Freiraum wieder, den diese ADR schließt.
