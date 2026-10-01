# Meldungen und Fehlerbehebung

## Warnungen im Bereich „Meldungen“

Warnungen verhindern die Konvertierung nicht, sollten aber vor dem Import geklärt werden.

| Meldung | Bedeutung / Lösung |
|---|---|
| `keine IDENTNUMMER – übersprungen` | Der Datensatz hat keine ID und wird nicht übernommen. In Sibank ergänzen. |
| `Geburtsdatum ungültiges Datum '…' – als NULL ausgegeben` | Datum ist nicht im Format `TT.MM.JJJJ`. In Sibank korrigieren. |
| `Zugang ungültiges Datum '…' – als NULL ausgegeben` | wie oben, für das Zugangsdatum |
| `keine Klasse angegeben` | Schüler ohne Klasse; `school_classes` bleibt leer. |
| `unbekanntes Geschlecht '…'` | Erlaubt sind `m`, `w`, `d`. |
| `doppelte recordUID …` | Eine ID kommt mehrfach vor. In Sibank prüfen. |
| `Spalte '…' fehlt – das Feld bleibt leer` | Eine optionale Spalte fehlt im Export. Liste im Listengenerator prüfen. |

## Fehlermeldungen

| Meldung | Lösung |
|---|---|
| `Es fehlen Pflichtspalten` | Die Exportliste enthält nicht alle Pflichtfelder bzw. die Überschriften stimmen nicht. Siehe [Sibank-Export einrichten](Sibank-Export-einrichten). |
| `Die Datei ist leer.` / `Keine Kopfzeile in der Datei gefunden.` | Falsche Datei gewählt oder Export ohne Überschriften erstellt. |
| `Bitte eine Schulnummer (nur Ziffern) eingeben.` | Schulnummer ohne Buchstaben oder Leerzeichen eintragen. |
| `… Zeichen, die in der gewählten Kodierung nicht darstellbar sind` | Namen enthalten Sonderzeichen außerhalb von Windows-1252. Ausgabekodierung auf UTF-8 stellen. |
| `Der Zielordner existiert nicht` | Anderen Zielordner wählen. |
| `Es wurden keine gültigen Datensätze gefunden.` | Alle Zeilen wurden übersprungen oder herausgefiltert (z. B. nur Oberstufe und „Oberstufe ausschließen“ aktiv). |

## Häufige Fragen

**Umlaute werden in EDUCA falsch angezeigt.**
Eine andere Ausgabekodierung wählen (meist `UTF-8` oder `UTF-8 mit BOM`) und erneut importieren.

**Die Klassen der Oberstufe fehlen.**
Die Option „Oberstufe ausschließen“ ist standardmäßig aktiv. Haken entfernen.

**Windows blockiert den Start der EXE.**
Siehe [Installation](Installation) → Windows SmartScreen.

**Wie melde ich einen Fehler?**
Über [Issues](https://github.com/Lutherschule30167/sibank2educa/issues) – bitte **niemals echte Schülerdaten** anhängen, sondern das Problem mit erfundenen Daten nachstellen.
