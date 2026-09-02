# ADR-0011: IndexedDB als einzige Historie

**Status:** angenommen (2026-09-02)

## Kontext

Der Hub hat **keine Historie**. Er ist eine Warteschlange je Empfängername: Nachrichten
verfallen nach 60 Minuten, höchstens 20 liegen je Name bereit, und nach dem Entnehmen sind
sie fort. Gesendete Nachrichten sind für den Absender überhaupt nicht abrufbar — sie liegen
im Eingang des Empfängers.

Ein Client, der einen Gesprächsverlauf zeigen soll, muss ihn also **selbst** aufbewahren.
Es gibt kein eigenes Backend ([ADR-0003](0003-nur-offener-pfad.md)).

## Entscheidung

**IndexedDB im Browser ist die einzige Historie, die es gibt.**

Zwei Sammlungen:

- **`messages`** — `id`, `direction` (`in`/`out`), `ownName`, `peerName` (behauptetes `from`
  bzw. gewähltes `to`), Text, `receivedAt`, `expiresAt`, `hubState`, `payloadState`.
- **`identities`** — der eigene gewählte Name und die zuletzt benutzten Namen.

**Nicht** in IndexedDB:

- Passphrasen und daraus abgeleitete Schlüssel ([ADR-0007](0007-krypto-umschaltbar.md)).
- Klartext einer Nachricht, die verschlüsselt eintraf und deren Passphrase nicht vorlag.

Gesendete Nachrichten werden beim erfolgreichen `POST` (`201`) lokal abgelegt — sonst wären
sie nirgends. Sie tragen von Anfang an `hubState` = „am Hub" und wechseln nie zu „nur lokal",
weil der Absender das nicht feststellen kann.

## Begründung

- **Ohne lokale Ablage gibt es keinen Verlauf.** Das ist keine Optimierung, sondern die
  Voraussetzung dafür, dass der Client überhaupt wie ein Chat aussehen kann.
- **IndexedDB statt `localStorage`**, weil strukturierte Datensätze mit Indizes gebraucht
  werden (nach Konversation, nach Zustand) und `localStorage` nur Zeichenketten sowie ein
  knappes Kontingent bietet.
- **Keine Geheimnisse an Ruhe.** Eine gespeicherte Passphrase ist ein gespeichertes
  Geheimnis; der Bequemlichkeitsgewinn rechtfertigt das nicht.

## Folgen

- **Der Verlauf ist gerätegebunden.** Ein zweites Gerät sieht die Vergangenheit nicht. Das
  muss dem Nutzer klar sein und ist im Bedienkonzept benannt.
- Löschen der Browserdaten löscht den Verlauf endgültig — es gibt keine zweite Kopie.
- Der lokale Verlauf und der Zustand am Hub sind **zwei verschiedene Dinge**. Die Zahl neben
  einer Konversation zeigt, was **am Hub liegt**, nicht die Länge des Verlaufs
  ([architecture.md](../architecture.md)).
- Eine Nachricht kann „nur lokal" **und** „nicht entschlüsselbar" sein: entnommen und
  trotzdem unleserlich. Das UI muss diesen Zustand darstellen können.
- **Nicht entschieden:** Export und Import des Verlaufs. Wer das braucht, schreibt eine ADR.

## Verworfene Alternativen

- **Kein lokaler Verlauf, nur der aktuelle Eingang.** Ehrlich gegenüber dem Dienst, aber dann
  ist es kein Chatclient — und das explizite Entnehmen
  ([ADR-0006](0006-entnehmen-ist-nutzeraktion.md)) würde bedeuten, dass Inhalte beim
  Aufräumen ersatzlos verschwinden.
- **`localStorage`.** Zu knapp und ohne Indizes; erzwingt Serialisieren des gesamten Verlaufs
  bei jeder Änderung.
- **Eigenes Backend für die Historie.** Löst es sauber, verlagert aber den Lerngegenstand vom
  Umgang mit einem fremden, kargen Vertrag auf den Bau eines eigenen Dienstes — und würde
  Nachrichten an eine weitere Stelle kopieren.
- **Nachrichten am Hub liegen lassen als „Historie".** Bei 60 Minuten Verfall und 20 je Name
  keine Historie, sondern ein volllaufender Eingang.
