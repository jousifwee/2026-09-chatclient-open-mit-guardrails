# ADR-0009: Nur synthetische Bezeichner in `to` und `from`

**Status:** angenommen (2026-09-02)

## Kontext

Die Felder `to` und `from` sind Benutzernamen nach `^[A-Za-z0-9_-]{1,32}$`. Der Hub verlangt
keine Registrierung: ein Name entsteht beim ersten Einliefern.

Entscheidend ist, was mit diesen Namen passiert:

- **`GET /open/names` ist öffentlich** und listet jeden derzeit belegten Namen — als
  Empfänger, als behaupteter Absender oder beides.
- **`GET /open/messages?to=<name>` liefert jedem Fremden den vollständigen Eingang** eines
  Namens (verifiziert 2026-09-02).
- Der Dienst läuft auf einer **Demo-Box bei einem externen Anbieter in einer öffentlichen
  Cloud**.

Die Spezifikation des Dienstes sagt es selbst: Ein echter Vor- oder Nachname im Feld `to`
oder `from` steht über diese Operation im Internet.

Dazu die Richtlinie zur KI-Nutzung des ITZ Rostock: personenbezogene Daten gehören nicht in
solche Werkzeuge und Dienste — auch nicht zum Ausprobieren.

## Entscheidung

**In `to` und `from` stehen ausschließlich erkennbar erfundene Bezeichner.**

- Muster `^[A-Za-z0-9_-]{1,32}$`, validiert **während** der Eingabe.
- Konvention in diesem Projekt: sprechendes Präfix nach Zweck, etwa `anna_demo`,
  `bert_demo`, `etreff_probe_a`.
- Beim ersten Start **Pflichteingabe** des eigenen Namens — kein Vorschlag, keine
  Zufallsvergabe, keine Übernahme aus dem System.
- Über dem Feld dauerhaft der Hinweis: *„Dieser Name wird über `GET /open/names` öffentlich
  im Internet sichtbar. Nur erfundene Bezeichner verwenden — keine echten Vor- oder
  Nachnamen."*
- **Keine Heuristik, die echte Namen erkennen will.**
- Gilt gleichermaßen für Code, Tests, Beispiele in der Dokumentation und Commit-Nachrichten.

## Begründung

- **Der Name ist die eigentliche Datenschutzfrage dieses Dienstes**, nicht die Nutzlast. Die
  Nutzlast kann verschlüsselt werden ([ADR-0007](0007-krypto-umschaltbar.md)); der Name kann
  es nicht — er ist das Adressierungsmerkmal und steht zwingend im Klartext.
- **Eine Namenserkennung würde falsches Vertrauen schaffen.** Eine Prüfung, die `anna`
  durchlässt und `Anna Schmidt` ablehnt, sieht wie ein Schutz aus, ist aber keiner: `aschmidt`
  passiert sie ebenso. Klare Ansage plus Verantwortung beim Nutzer ist ehrlicher als eine
  Heuristik, die man für einen Filter hält.
- **Zufallsnamen wären bequem, aber lehrfrei.** Die Pflichteingabe mit Hinweis ist der
  Moment, in dem der Nutzer die Eigenschaft des Dienstes begreift.

## Folgen

- Namen sind nicht wiedererkennbar über Sitzungen hinweg, solange der Nutzer sie nicht notiert.
- Teilnehmer eines Entwicklertreffs müssen ihre Bezeichner untereinander austauschen.
- Auch Beispiele in dieser Dokumentation halten sich daran — die Namen `anna_demo`,
  `bert_demo` und `etreff_probe_*` sind bewusst gewählt.
- Eingegebene Namen werden kleingeschrieben ([ADR-0014](0014-namen-kleinschreiben.md)); das
  Muster erlaubt Großbuchstaben, der Client benutzt sie aber nicht.

## Verworfene Alternativen

- **Zufällig erzeugte Namen** (`user_7f3a`). Datenschutzrechtlich am sichersten, nimmt dem
  Nutzer aber die Entscheidung und damit die Lehre — und erschwert das Adressieren im Kurs.
- **Namenserkennung gegen eine Vornamensliste.** Erzeugt Scheinsicherheit, ist
  sprachabhängig, und Nachnamen sind ohnehin nicht abdeckbar.
- **Anzeigename getrennt vom technischen Namen.** Verlagert das Problem nur: ein Anzeigename
  wandert in die Nutzlast und liegt im Klartextmodus offen am Hub.
