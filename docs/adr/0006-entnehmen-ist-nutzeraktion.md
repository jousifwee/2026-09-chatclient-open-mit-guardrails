# ADR-0006: Entnehmen ist eine bewusste Nutzeraktion

**Status:** angenommen (2026-09-02)

## Kontext

Der Hub trennt Ansehen und Entnehmen strikt:

- `GET /open/messages?to=<name>` ist **folgenlos** und beliebig wiederholbar.
- `DELETE /open/messages/{id}` entnimmt **endgültig**; die Nachricht wird kein zweites Mal
  ausgeliefert.
- Nachrichten verfallen ohnehin nach 60 Minuten, höchstens 20 je Empfängername.
- Es gibt **keinen** Nachweis: jeder, der die `id` kennt, kann entnehmen — und die `id` steht
  in der Antwort des Ansehens, das jedem offensteht.

Die Spezifikation begründet die Trennung ausdrücklich: `GET` ist in HTTP zustandsfrei,
Clients wiederholen es nach Timeouts, und Crawler rufen öffentliche URLs unaufgefordert auf.
Würde Ansehen entnehmen, verschwänden Nachrichten, bevor der Empfänger sie sieht.

Ein üblicher Chatclient würde nach dem Anzeigen automatisch entnehmen — das fühlt sich an wie
ein Messenger. Damit verschwindet aber genau die Eigenschaft, um die es hier geht.

## Entscheidung

**Anzeigen entnimmt nicht. Entnehmen ist eine ausdrückliche Nutzeraktion.**

- Knopf je Nachricht, dazu „Alle entnehmen" je Konversation.
- Vor dem ersten Entnehmen je Sitzung ein Dialog: *„Entnehmen ist endgültig. Die Nachricht
  ist danach nur noch auf diesem Gerät vorhanden."* Danach als Kurztext.
- Nach dem Entnehmen wechselt die Nachricht sichtbar von **am Hub** auf **nur lokal**,
  statt aus der Liste zu verschwinden.
- **Kein automatisches Entnehmen, und keine Einstellung, die es einschaltet.** Diese Regel
  ist ausdrücklich **nicht konfigurierbar**.
- Die Belegung des Eingangs (`n/20`) steht dauerhaft in der Kopfzeile, ab 16 mit Warnung.
- Entnehmen darf nicht durch Fokus- oder Hover-Ereignisse ausgelöst werden.

## Begründung

- **Es ist der Lerngegenstand.** Store-and-forward sichtbar zu halten, ist der Zweck dieses
  Clients. Automatisches Entnehmen würde die Semantik hinter einer Messenger-Fassade
  verstecken — bequemer, aber lehrfrei.
- **Entnehmen ist unwiderruflich, ohne zweite Chance.** Nach `DELETE` gibt es die Nachricht
  nur noch lokal. Ein Anzeigefehler, ein Neuladen zur falschen Zeit, ein zweites Gerät — und
  der Inhalt ist fort.
- **Automatisches Entnehmen macht Mehrgeräte-Betrieb unmöglich**, ohne dass der Nutzer
  erfährt, warum: das erste Gerät, das anzeigt, nimmt weg.
- **Die Belegungsanzeige ist Folgepflicht.** Wer nicht automatisch entnimmt, läuft in die
  Grenze von 20 — und ohne Anzeige ist der Grund für ausbleibende Nachrichten unsichtbar.

## Folgen

- Der Client fühlt sich weniger wie ein Messenger an. Beabsichtigt.
- Nutzer müssen aufräumen, sonst blockiert ihr Eingang Nachrichten **aller** Absender.
- Nachrichten können verfallen, bevor sie entnommen wurden. Die Restlaufzeit ist deshalb je
  Nachricht sichtbar.
- Ein Fremder kann entnehmen, bevor der Empfänger es tut. Nicht verhinderbar, aber im
  Zustand **fort** benannt — ohne Ursache zu behaupten, denn der Hub unterscheidet Entnahme
  und Verfall nicht.

## Verworfene Alternativen

- **Automatisch entnehmen nach dem Anzeigen** (Variante „echtes Chat-Gefühl"). Verworfen aus
  den Gründen oben; verliert zudem den Mehrgeräte-Betrieb.
- **Nie entnehmen, nur auf Verfall setzen.** Der Eingang läuft bei 20 voll und weist dann
  Einlieferungen aller Absender ab. Verlagert das Problem, statt es zu lösen.
- **Automatisch entnehmen ab einer Füllschwelle.** Versteckt eine zerstörende Aktion hinter
  einer Heuristik — der Nutzer kann nicht vorhersagen, wann sein Inhalt vom Hub verschwindet.
