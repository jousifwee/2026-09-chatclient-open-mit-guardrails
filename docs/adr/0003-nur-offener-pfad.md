# ADR-0003: Nur der offene Pfad; Token und OIDC in diesem Release ignoriert

**Status:** angenommen (2026-09-02)

## Kontext

Der UTZ MessageHub bietet Schutzstufen mit getrennten Endpunkten und **getrennten Ablagen**
an. Zwischen den Stufen gibt es keinen Übergang.

Geprüft am 2026-09-02 gegen den laufenden Dienst:

- Der **offene Pfad** ist vollständig in Betrieb.
- Von der **OIDC-Stufe** existieren nur `/oidc/whoami` und `/oidc/directory`; die
  Nachrichten-Endpunkte sind laut Spezifikation **nicht gebaut**. `GET /oidc/config` liefert
  auf dieser Instanz `configured: false` — die Stufe ist nicht einmal eingerichtet.
- Eine **Token-Stufe** (`/token/...` mit `X-API-Key`) war angekündigt und ebenfalls nicht
  gebaut.

Nachtrag 2026-09-03 (`0.1.24+ee364d0`): Die **Token-Stufe ist aus der Spezifikation
entfernt**, samt Security-Schema `kurs-token`. Es bleiben zwei Stufen: offen und OIDC. Diese
ADR wird dadurch **bestätigt, nicht abgelöst** — eine vorgebaute Stufen-Abstraktion hätte
jetzt eine Stufe abstrahiert, die es nie gab und nicht mehr geben soll.

Zusätzlich hält die Spezifikation fest, dass die Anmeldung im Kursbetrieb ohnehin keine
Person nachweist: alle Konten haben ein gemeinsames, dauerhaftes Kennwort.

## Entscheidung

Der Client nutzt **ausschließlich den offenen Pfad** `/open/...`.

**Token- und OIDC-Stufe werden in diesem Release ausdrücklich ignoriert.** Das heißt:

- Keine Anmeldung, kein `X-API-Key`, kein `Authorization`-Header, kein Aufruf unter `/oidc/`
  oder `/token/` — auch nicht `/oidc/config`.
- **Keine spekulative Stufen-Abstraktion.** Die Transport-Schicht spricht den offenen Pfad
  direkt an. Es gibt keine stufenneutrale Schnittstelle, keine Strategie-Klasse und keinen
  Konfigurationsschalter für eine Stufe, die es nicht gibt.
- Kein UI-Element, das eine Stufe erwähnt, anbietet oder als „demnächst" ankündigt.

Kommen die Stufen später, ist das ein **eigenes Release mit eigener ADR**.

## Begründung

- **Es gibt nichts anderes.** Ein Client gegen nicht existierende Endpunkte wäre nicht
  testbar und nicht ausführbar.
- **Der offene Pfad ist der interessantere Lerngegenstand.** Ohne Nachweis, welt-lesbar,
  welt-entnehmbar, mit unbeglaubigtem Absender — genau daran wird sichtbar, was Guardrails
  leisten müssen und wovor sie nicht schützen können.
- **Eine Abstraktion für unbekanntes Verhalten ist kein Entwurf, sondern eine Vermutung.**
  Auf der OIDC-Stufe wäre `from` kein Feld des Anfragekörpers mehr, sondern aus dem Nachweis
  abgeleitet — mit Folgen für Identität, Konversationsbildung und Vertrauensanzeige. Eine
  heute gebaute Schnittstelle würde diese Folgen erraten und die falsche Form vorgeben. Das
  ist teurer als der spätere Umbau.
- **Der Unterschied zur Absender-Filterung ist beabsichtigt:** dort ist die Erweiterung in
  Form und Wirkung bekannt und wird vorbereitet ([ADR-0005](0005-konversation-ist-client-konstrukt.md)),
  hier ist sie es nicht.

## Folgen

- Vertraulichkeit entsteht **ausschließlich** durch clientseitige Verschlüsselung
  ([ADR-0007](0007-krypto-umschaltbar.md)).
- Der Absender bleibt eine unbeglaubigte Behauptung; das UI muss das durchgehend zeigen
  ([ADR-0005](0005-konversation-ist-client-konstrukt.md)).
- Nachrichten sind flüchtig: 60 Minuten Verfall, 20 je Name. Historie nur lokal
  ([ADR-0011](0011-lokale-persistenz-indexeddb.md)).
- Der Umbau auf eine geschützte Stufe wird **teurer** als mit vorgebauter Abstraktion. Bewusst
  in Kauf genommen, weil die Form dieses Umbaus heute unbekannt ist.
- `/oidc/config` liefert auf dieser Instanz ohnehin `configured: false`; ein Abfragen dieser
  Auskunft würde nur einen Zustand anzeigen, auf den der Client nicht reagieren kann.

## Verworfene Alternativen

- **Stufenneutrale Transport-Schnittstelle vorbauen** (`submit`, `peek`, `take`, `names` mit
  austauschbarer Implementierung). Ursprünglich vorgesehen und am 2026-09-02 verworfen: Sie
  hätte Verhalten festgelegt, das nur die nicht gebauten Stufen kennen — vor allem die Frage,
  woher der Absender kommt. Eine Abstraktion, die die falsche Achse abstrahiert, muss beim
  ersten echten Bedarf ohnehin aufgebrochen werden.
- **Auf die OIDC-Stufe warten.** Unbestimmte Wartezeit, und der Lerngegenstand des Projekts
  hängt nicht daran.
- **OIDC-Anmeldung schon einbauen, Nachrichten weiter über `/open`.** Erzeugt den Anschein
  von Identität, ohne dass sie den Absender beglaubigt — die schlechteste aller Varianten
  für ein Projekt, das gerade das Gegenteil lehren will.
- **Eigenes Backend als Vermittler**, das Identität und Historie ergänzt. Verlagert den
  Lerngegenstand vom Umgang mit einem fremden, kargen Vertrag auf den Bau eines eigenen
  Dienstes.
