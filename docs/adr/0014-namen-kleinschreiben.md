# ADR-0014: Namen kleinschreiben, Kollisionen damit auflösen

**Status:** angenommen (2026-09-02)

## Kontext

Der Hub **unterscheidet Groß- und Kleinschreibung** in Benutzernamen. Das steht ausdrücklich
in der Spezifikation von `SubmitMessageDto` und in der Beschreibung von `GET /open/names`.

`anna` und `Anna` sind damit **zwei getrennte Warteschlangen**. Für einen Chatclient ist das
eine Falle mit mehreren Gesichtern:

- Wer sich beim eigenen Namen vertippt (`Anna` statt `anna`), sitzt vor einem leeren Eingang,
  während seine Nachrichten in einem anderen Fach liegen.
- Wer einen Empfänger falsch schreibt, liefert an ein Fach, das niemand abfragt — der Hub
  meldet keinen Fehler, denn jeder Name entsteht beim ersten Einliefern.
- Ein Eingang zeigt `Anna` und `anna` als zwei Konversationen.

Das ist keine graue Theorie: der laufende Dienst enthielt am 2026-09-02 die Namen `Heiko` und
`Robert` — großgeschrieben.

Diese Frage war in [ADR-0005](0005-konversation-ist-client-konstrukt.md) zunächst als offen
geführt und wird hiermit entschieden.

## Entscheidung

**Namen werden kleingeschrieben. Kollisionen durch Groß-/Kleinschreibung sind damit
aufgelöst.**

Genau geregelt, weil hier sonst geraten wird:

1. **Alles, was der Nutzer eingibt, wird an der Eingabegrenze kleingeschrieben** — der eigene
   Name und jeder selbst eingetippte Empfänger. `toLowerCase()` mit fester Locale
   (`toLocaleLowerCase("en-US")`), nicht der Systemsprache, damit das Ergebnis überall gleich
   ist. Das Feld zeigt sofort die kleingeschriebene Form; es gibt keinen Zustand, in dem der
   Nutzer etwas anderes sieht als das, was gesendet wird.
2. **Der Konversationsschlüssel ist immer der kleingeschriebene Name.** Gruppierung, Anzeige
   und der Schlüssel in IndexedDB benutzen ausschließlich diese Form.
3. **Bei eingehenden Nachrichten wird das rohe `from` zusätzlich aufbewahrt** — als
   `replyTo`. Für die Antwort wird **`replyTo` benutzt, nicht der kleingeschriebene
   Schlüssel.**
4. **Weicht `replyTo` von der kleingeschriebenen Form ab**, zeigt die Konversation einen
   Hinweis: *„Dieser Absender benutzt Großbuchstaben (`Heiko`). Antworten gehen an genau
   diese Schreibweise."*
5. Das Validierungsmuster bleibt `^[A-Za-z0-9_-]{1,32}$` — es ist das Muster des Dienstes.
   Der Client erzeugt daraus nur Kleinbuchstaben.

## Begründung

- **Kleinschreiben löst die drei häufigen Fälle vollständig**: eigener Name, eingetippter
  Empfänger, doppelte Konversation. Alle drei entstehen durch Tippen, und genau dort greift
  die Normalisierung.
- **Punkt 3 ist notwendig, nicht Zierde.** Würde auch das eingehende `from` kleingeschrieben
  *und für die Antwort benutzt*, ginge die Antwort an eine **andere Warteschlange** als die,
  die der Absender abfragt. Der Absender bekäme sie nie zu sehen, und niemand erhielte eine
  Fehlermeldung — der Hub nimmt jeden Namen an. Das ist der schlimmste Fehlertyp dieses
  Dienstes: lautlos.
- **Der Hinweis in Punkt 4 macht die Restunschärfe sichtbar**, statt sie zu verstecken. Er
  ist zugleich Lehrmaterial: hier wird begreifbar, warum ein Dienst ohne Registrierung
  Schreibweisen nicht vereinheitlichen kann.
- **Feste Locale**, weil `toLowerCase()` sprachabhängig ist — im Türkischen wird aus `I` ein
  `ı`, das vom Muster nicht erlaubt ist. Ein Client, der bei türkischer Systemsprache andere
  Namen erzeugt, ist unbrauchbar.

## Folgen

- Der Client kann **großgeschriebene Eingänge nicht mehr selbst anlegen**. Wer bewusst an
  `Anna` liefern will, kann es über diesen Client nicht. Bewusst in Kauf genommen.
- Zwei Namensfelder je Konversation: Schlüssel und `replyTo`. Sie fallen in fast allen Fällen
  zusammen; die Unterscheidung ist im Datenmodell trotzdem vorhanden
  ([architecture.md](../architecture.md)).
- Bereits am Hub liegende großgeschriebene Namen erscheinen kleingeschrieben in der Liste,
  mit Hinweis. `GET /open/names` liefert weiterhin die rohe Form — beim Anzeigen dieser Liste
  wird ebenfalls kleingeschrieben, sonst tauchen `Heiko` und `heiko` doppelt auf.
- **Offen und bewusst nicht entschieden:** ob der Client eine Warnung zeigen soll, wenn ein
  eingetippter Empfängername sich von einem bekannten nur in der Schreibweise unterscheidet.
  Braucht jemand das, schreibt er eine ADR.

## Verworfene Alternativen

- **Kleinschreiben ausnahmslos, auch fürs Antworten.** Die einfachste Regel und der klarste
  Text — aber sie erzeugt lautlos unzustellbare Antworten an jeden Absender mit
  Großbuchstaben. Am laufenden Dienst wären das heute zwei von drei belegten Namen.
- **Groß-/Kleinschreibung beibehalten und nur warnen.** Überlässt dem Nutzer eine
  Unterscheidung, die für ihn keinen Nutzen hat, und lässt doppelte Konversationen stehen.
- **Nur bei der Anzeige zusammenführen, technisch getrennt lassen.** Die Anzeige würde eine
  Einheit behaupten, die beim Senden wieder auseinanderfällt — die Verwirrung wäre größer als
  ohne Zusammenführung.
- **Namen serverseitig normalisieren lassen.** Nicht in unserer Hand; wäre eine Anfrage an
  den Betreiber und würde bestehende Fächer brechen.
