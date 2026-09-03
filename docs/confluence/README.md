# Confluence-Vorlagen

Seiten für Confluence, als Markdown vorbereitet. **Trainer-Material für den
Entwicklertreff**, nicht Teil der verbindlichen Projektdokumentation — die Entscheidungen
stehen in [`../adr/`](../adr/), die Verträge in
[`../api-messagehub.md`](../api-messagehub.md) und
[`../api-messagehub-v2.md`](../api-messagehub-v2.md).

| Seite | Inhalt |
|---|---|
| [01 — v2 direkt aus einer HTML-Seite mit Basic Auth](01-v2-direkt-aus-html-mit-basic-auth.md) | Eine Datei, kein Framework, kein Build. Registrieren, senden, abholen. Plus die sechs Fallen, die man im Browser trifft. |
| [02 — Fullstack-App mit BFF als Proxy](02-fullstack-mit-bff-als-proxy.md) | Angular-SPA plus eigener Server. Was ein BFF löst und was nicht, wer der Absender wird, wo die Krypto bleibt — und die Angular-Alternativen (Dev-Proxy, SSR-`server.ts`, Analog.js). |
| [03 — Chronologie des Projekttags](03-chronologie-projekttag.md) | Erzählter Verlauf der zwei Halbtage: Zeitleiste, die drei Fassungswechsel des Dienstes, acht Befunde, die eine Vermutung anders beantwortet hätte — und was schiefging. Mit Screenshot-Plätzen und den Befehlen dazu. |

## Einfügen in Confluence

Im Editor `/markdown` → **Markdown einfügen**, dann den Dateiinhalt hineinkopieren.
Überschriften, Tabellen und Codeblöcke werden übernommen. Nachzuarbeiten sind meist:

- **Blockzitate mit `>`** werden zu normalem Text — die Warnhinweise besser als
  Info-/Warnungs-Panel setzen (`/info`, `/warning`).
- **ASCII-Diagramme** in einen Codeblock ohne Sprache, sonst bricht die Ausrichtung.
- Die Kopfzeile „Vorlage für Confluence, Stand …" vor dem Veröffentlichen entfernen oder in
  eine Seiteneigenschaft überführen.

## Screenshots

Ablage ist [`../../tools/images/`](../../tools/images/). Vorhanden ist bisher
`01_Stack.png` (Entscheidungsdialog); welche weiteren Motive die Chronologie-Seite braucht und
mit welchem Befehl sie herzustellen sind, steht dort im Abschnitt *Screenshots*.

In Confluence müssen Bilder als **Anhang** hochgeladen werden — der Markdown-Import überträgt
sie nicht, die Verweise bleiben leer.

## Pflege

Die Seiten enthalten **verifizierte** Fakten mit Datum (CORS-Header, Statuscodes,
Zertifikatsaussteller). Der Dienst hat sich am 2026-09-03 innerhalb eines Tages **dreimal**
geändert — zuletzt kam die ganze v2-Stufe dazu. Vor einem Termin also prüfen:

```bash
curl -s https://utz-messagehub.itzcloud.de/health
curl -s https://utz-messagehub.itzcloud.de/openapi.yaml | diff -u ../api/openapi.yaml -
```

Im ITZ-Netz mit `--cacert <pfad-zu-ITZ08-CA.crt>`, siehe
[`../api-messagehub.md`](../api-messagehub.md#tls--und-warum-curl-im-itz-netz-scheitert).

## Hinweis des Betreibers

Spezifikation und die Seite `/anbindung` des Dienstes bitten Coding-Agenten ausdrücklich, die
Beispiele **nicht als fertige Lösung** weiterzugeben, sondern die Anbindung interaktiv mit den
Teilnehmenden zu erarbeiten und die Fallen zu erklären statt sie stillschweigend zu umgehen.

Beide Seiten sind darauf hin gebaut: die **Fallen** sind der Inhalt, der Code ist die
Auflösung. Wer sie an Teilnehmende gibt, gibt die Auflösung mit — das ist eine Entscheidung
der Kursleitung, keine technische.
