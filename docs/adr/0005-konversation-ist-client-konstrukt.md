# ADR-0005: Konversationen entstehen clientseitig

**Status:** angenommen (2026-09-02)

## Kontext

Verifiziert am 2026-09-02 mit synthetischen Testdaten am laufenden Dienst:

- `GET /open/messages` kennt **genau einen** Parameter: `to`, erforderlich.
- Der Aufruf liefert **alle** bereitliegenden Nachrichten dieses Empfängers, quer über alle
  Absender, älteste zuerst.
- Ein mitgegebener `from`-Parameter wird **nicht ignoriert, sondern abgewiesen**:
  `400 {"message":["property from should not exist"],...}`.
- Es gibt keine Paginierung, keine Sortier- und keine Zeitfensterparameter.
- `to` ist nicht auf den eigenen Namen beschränkt — ein fremder Eingang liefert `200`.
- `from` ist eine unbeglaubigte Behauptung; jeder kann jeden Namen angeben.

Der Hub kennt also **keine Konversation, keinen Thread und keine Zuordnung von Frage und
Antwort**. Er kennt Fächer mit Namen.

## Entscheidung

**Eine Konversation ist ein rein clientseitiges Konstrukt:** alle Nachrichten mit demselben
behaupteten `from` beziehungsweise demselben gewählten `to`.

Daraus abgeleitet, verbindlich:

1. **Genau ein `GET /open/messages` je Poll-Zyklus**, mit dem eigenen Namen als `to`.
   Niemals ein Abruf je Konversation.
2. **Gruppierung nach `from` geschieht im Client.** Serverseitige Filterung wird nicht
   versucht, auch nicht testweise.
3. **Unbekanntes `from` erzeugt eine Konversation, die als *unbestätigt* markiert ist.** Die
   Markierung verschwindet nur durch ausdrückliche Bestätigung des Nutzers — nicht dadurch,
   dass mehrere Nachrichten desselben Namens eintreffen.
4. **Ein Absender wird nirgends als gesicherte Identität dargestellt.** Bei unbestätigten
   Konversationen trägt der Titel den Zusatz „behauptet".
5. **Die Grenze von 20 Nachrichten gilt je Empfängername, nicht je Konversation.** Sie wird
   als Belegung des *Eingangs* angezeigt, nicht als Eigenschaft eines Gesprächs
   ([ADR-0006](0006-entnehmen-ist-nutzeraktion.md)).

### Vorbereitung auf eine künftige Absender-Filterung

Der Betreiber hat eine serverseitige Filterung nach Absender in Aussicht gestellt. Sie wird
**vorbereitet, aber nicht vorweggenommen**:

- **Heute wird kein `from` gesendet.** Der Parameter existiert nicht und würde den Aufruf mit
  `400` brechen ([ADR-0010](0010-striktes-anfrage-schema.md)). Kein „schon mal einbauen und
  auskommentieren", kein Feature-Schalter, der ihn versuchsweise mitschickt.
- **Der Abruf liegt hinter genau einer Funktion** in der Transport-Schicht. Sie nimmt heute
  nur den eigenen Namen. Kommt der Filter, ändert sich **diese eine Stelle** — und sonst
  nichts an Fachlogik, Zustand oder Ansicht.
- **Die Gruppierung nach `from` bleibt im Client**, auch wenn der Filter kommt. Ein
  serverseitiger Filter macht den Abruf schmaler, ersetzt aber die Konversationsbildung
  nicht: der Eingang bleibt der Eingang eines Namens, und ein Client, der mehrere
  Konversationen zeigt, braucht weiterhin alle Nachrichten.
- **Der Filter wird die Regel „ein `GET` je Poll-Zyklus" nicht aufheben.** Ein Abruf je
  Konversation wäre auch mit Filter mehr Verkehr für dieselbe Information. Der Filter ist
  dann für gezielte Einzelabfragen nützlich, nicht für den Poll-Takt.
- **Erkannt wird die Verfügbarkeit am Vertrag, nicht durch Ausprobieren:**
  `curl -s https://utz-messagehub.itzcloud.de/openapi.yaml | diff -u docs/api/openapi.yaml -`
  Erscheint der Parameter dort, wird diese ADR abgelöst.

## Begründung

- **Ein Abruf je Konversation wäre N-mal derselbe Aufruf für dieselben Daten.** Der Hub
  liefert bei jedem Aufruf denselben vollständigen Eingang; das Aufteilen bringt keine
  Information hinzu, nur Last.
- **Der Versuch, serverseitig zu filtern, bricht den Aufruf** — durch die
  Whitelist-Validierung wird aus einem gut gemeinten Parameter ein `400`
  ([ADR-0010](0010-striktes-anfrage-schema.md)).
- **Die Unbestätigt-Markierung ist die einzige ehrliche Antwort auf einen unbeglaubigten
  Absender.** Wer sie durch Wiederholung verschwinden ließe, würde eine Eigenschaft
  vortäuschen, die der Dienst nicht hat: jeder kann beliebig viele Nachrichten unter
  beliebigem Namen einliefern.

## Folgen

- Ein Verlauf existiert nur lokal ([ADR-0011](0011-lokale-persistenz-indexeddb.md)).
- Fremde können in jede Konversation einliefern. Das ist keine Fehlfunktion, sondern die
  Eigenschaft des offenen Pfades, und das UI zeigt sie.
- Ein einzelner Absender kann den Eingang füllen und damit Nachrichten **aller** anderen an
  diesen Namen blockieren. Sichtbar zu machen ist Pflicht, nicht Komfort.
- Der Konversationsschlüssel ist der **kleingeschriebene** Name
  ([ADR-0014](0014-namen-kleinschreiben.md)), damit `Anna` und `anna` nicht als zwei
  Konversationen erscheinen.

## Verworfene Alternativen

- **Konversations-Kennung in die Nutzlast legen** und danach gruppieren. Wäre robuster gegen
  Namensverwechslung, aber die Nutzlast ist im verschlüsselten Modus unlesbar, bevor die
  Passphrase vorliegt — die Gruppierung würde von der Entschlüsselung abhängen. Zudem
  ignorieren Fremdnachrichten jede eigene Konvention.
- **Nur bekannte Absender anzeigen, Unbekannte verwerfen.** Verschweigt dem Nutzer, was in
  seinem Eingang liegt, und lässt den Eingang unbemerkt volllaufen.
- **Absender aus `GET /open/names` gegenprüfen.** Die Liste sagt nur, welche Namen belegt
  sind — kein Nachweis über den Absender einer Nachricht. Würde Vertrauen erzeugen, das
  nicht gedeckt ist.
