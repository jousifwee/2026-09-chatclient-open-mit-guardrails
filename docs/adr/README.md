# Architekturentscheidungen (ADRs)

Jede Architektur-, Funktions- und UX-Entscheidung dieses Projekts steht hier — **bevor** sie
implementiert wird ([ADR-0001](0001-doku-zuerst.md)). ADRs sind verbindlich und überschreiben
Framework-Defaults, Gewohnheit und Bauchgefühl.

Aufbau und Regeln: [../conventions.md](../conventions.md).

| Nr. | Entscheidung | Status |
|---|---|---|
| [0001](0001-doku-zuerst.md) | Doku zuerst, Code danach | angenommen |
| [0002](0002-doppelt-lesbare-agentendoku.md) | Agentendoku für Claude und Copilot aus einer Quelle | angenommen |
| [0003](0003-nur-offener-pfad.md) | Nur der offene Pfad; Token und OIDC in diesem Release ignoriert | angenommen |
| [0004](0004-frontend-angular-material3.md) | Frontend: Angular mit Material 3 | angenommen |
| [0005](0005-konversation-ist-client-konstrukt.md) | Konversationen entstehen clientseitig | angenommen |
| [0006](0006-entnehmen-ist-nutzeraktion.md) | Entnehmen ist eine bewusste Nutzeraktion | angenommen |
| [0007](0007-krypto-umschaltbar.md) | Klartext und AES-GCM umschaltbar, selbstbeschreibender Umschlag | angenommen |
| [0008](0008-adaptives-polling.md) | Adaptives Polling mit festen Werten | angenommen |
| [0009](0009-nur-synthetische-bezeichner.md) | Nur synthetische Bezeichner in `to` und `from` | angenommen |
| [0010](0010-striktes-anfrage-schema.md) | Nur deklarierte Felder und Parameter senden | angenommen |
| [0011](0011-lokale-persistenz-indexeddb.md) | IndexedDB als einzige Historie | angenommen |
| [0012](0012-fehler-und-grenzfaelle.md) | Fehler- und Grenzfallbehandlung | angenommen |
| [0013](0013-cors-ohne-credentials.md) | Kein `credentials: "include"` | angenommen |
| [0014](0014-namen-kleinschreiben.md) | Namen kleinschreiben, Kollisionen damit auflösen | angenommen |
| [0015](0015-zwei-apps-getrennte-transporte.md) | Zwei Anwendungen im Workspace, getrennte Transporte | angenommen, Vertrag von App 2 offen |

## Angekündigte Änderungen am Dienst

Der Betreiber hat eine **serverseitige Filterung nach Absender** in Aussicht gestellt. Bis
sie in der Spezifikation steht, gilt unverändert: **kein `from` senden**
([ADR-0010](0010-striktes-anfrage-schema.md)). Vorbereitet ist die Stelle, an der sie
andockt, nicht der Aufruf ([ADR-0005](0005-konversation-ist-client-konstrukt.md)).

Ein **v2-Dienst mit Basic Auth** ist für die zweite Anwendung angekündigt, am Hub aber am
2026-09-03 nicht auffindbar. Struktur entschieden, Vertrag offen — die gebrauchten Angaben
listet [ADR-0015](0015-zwei-apps-getrennte-transporte.md) unter „Was blockiert ist".

Bereits eingetreten am 2026-09-03 (`0.1.16` → `0.1.24`): die **Token-Stufe**
(`/token/...`, `X-API-Key`) ist aus der Spezifikation **entfernt**. Endpunktmenge
unverändert. Das bestätigt [ADR-0003](0003-nur-offener-pfad.md).

Prüfen mit:

```bash
curl -s https://utz-messagehub.itzcloud.de/openapi.yaml | diff -u docs/api/openapi.yaml -
```
