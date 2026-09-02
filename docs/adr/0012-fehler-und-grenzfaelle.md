# ADR-0012: Fehler- und Grenzfallbehandlung

**Status:** angenommen (2026-09-02)

## Kontext

Der Hub benutzt HTTP-Statuscodes bedeutungstragend, und mehrere davon sind **erwartbare
Betriebszustände**, keine Störungen:

- **`204`** bei `GET /open/messages`: es liegt nichts bereit. Die Spezifikation sagt
  ausdrücklich, dass dies der Normalfall ist und **nicht** `404`.
- **`404`** bei `DELETE`: bereits entnommen **oder** verfallen — der Dienst unterscheidet das
  nicht.
- **`413`** Nutzlast über 64 KB.
- **`429`** zwei verschiedene Ursachen: Eingang voll (20 je Name) **oder** Rate-Limit (60
  Einlieferungen je Aufrufer und Minute).
- **`503`** Gesamtspeicher erschöpft oder zu viele belegte Namen, mit `Retry-After`.
- **`400`** Schemaverstoß, Rumpf `{"message":[...],"error":...,"statusCode":...}` — `message`
  ist ein **Array**.

Ein Client, der all das in einen generischen Fehlerpfad wirft, zeigt dem Nutzer „Fehler" für
einen leeren Eingang und lässt ihn im Dunkeln, wenn sein Eingang voll ist.

## Entscheidung

**Erwartbare Lagen werden als Werte behandelt, nicht als Ausnahmen** — und jede bekommt eine
eigene Aussage.

| Lage | Behandlung |
|---|---|
| `204` | „nichts da". **Kein** Fehler, **keine** Meldung, und nicht als leeres Array verkleidet — der Unterschied zu „Abruf fehlgeschlagen" bleibt erhalten. Poll-Takt verlangsamen. |
| `404` bei `DELETE` | Zustand **fort**: „Nicht mehr am Hub — entnommen oder verfallen." **Keine Ursache behaupten.** |
| `413` | „Zu lang. Der Hub nimmt höchstens 64 KB je Nachricht." Vorab prüfen, inklusive Umschlag-Aufschlag. |
| `429` Eingang voll | „Der Eingang von *name* ist voll (20). Der Empfänger muss erst entnehmen." |
| `429` Rate-Limit | „Zu viele Einlieferungen in kurzer Zeit. In einer Minute erneut." |
| `503` | `Retry-After` **auswerten und einhalten**, Anzeige „Hub ausgelastet, nächster Versuch in n s". |
| `400` | „Der Hub hat die Anfrage abgewiesen." Das `message`-**Array** in der Detailansicht zeigen. |
| Netzfehler | „Hub nicht erreichbar." **Kein** stiller Retry. |
| unlesbare Nutzlast | Anzeigezustand, keine Ausnahme ([ADR-0007](0007-krypto-umschaltbar.md)). |

Weitere Festlegungen:

- **Die beiden `429`-Ursachen werden unterschieden.** Die Statuszahl allein genügt nicht;
  Grundlage ist der Kontext des Aufrufs (Einlieferung an einen Namen mit bekannt vollem
  Eingang gegen eigene Aufrufrate) und die Meldung des Dienstes.
- **Kein Retry ohne Anlass.** Wiederholt wird nur bei `503` und genau nach `Retry-After`.
- **Statuscodes nicht im Endnutzertext**, aber in der Detailansicht sichtbar — das Projekt
  ist ein Lehrstück.
- **Belegung des Eingangs proaktiv anzeigen** (`n/20`, ab 16 Warnung), damit `429` beim
  Absender nicht die erste Information über einen vollen Eingang ist.

## Begründung

- **`204` als Fehler ist der häufigste Anfängerfehler an diesem Dienst** und macht den
  Client im Normalzustand — leerer Eingang — unbenutzbar.
- **Der Hub unterscheidet Entnahme und Verfall nicht.** Wer eine Ursache behauptet, erfindet
  Information. Das UI sagt beides oder keins.
- **Ein einziger `429`-Text für zwei Ursachen führt zur falschen Handlung.** „Warte eine
  Minute" hilft nicht, wenn der Eingang des Empfängers voll ist — dort muss *der Empfänger*
  handeln.
- **`Retry-After` zu ignorieren verschärft genau die Auslastung, die zum `503` geführt hat.**
- **Fehler als Werte** halten die Schichtgrenzen sauber: die Transport-Schicht bildet
  Statuscodes auf Fachlagen ab, die Ansicht kennt keine Statuscodes.

## Folgen

- Die Transport-Schicht braucht einen ausdrücklichen Ergebnistyp, der „nichts da" von
  „Ergebnis" und „Fehlschlag" unterscheidet.
- Fehlertexte sind Teil des Bedienkonzepts ([ux-bedienkonzept.md](../ux-bedienkonzept.md))
  und nicht frei formulierbar.
- Die Grenzwerte des Hubs stehen als benannte Konstanten an einer Stelle.

## Verworfene Alternativen

- **Ein generischer Fehlerpfad für alle Statuscodes.** Weniger Code, aber der Nutzer erfährt
  nie, was er tun kann — und `204` würde zur Störung.
- **`204` in ein leeres Array übersetzen.** Bequem, verliert aber die Unterscheidung zwischen
  „nichts da" und „Abruf fehlgeschlagen" und damit die Grundlage für den Poll-Takt.
- **Ursache bei `404` raten** (etwa „wahrscheinlich verfallen" anhand `expiresAt`). Eine
  Vermutung, die als Tatsache erscheint.
