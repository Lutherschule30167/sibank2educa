# Bedienung

## Ablauf

1. **Exportdateien laden:** Im Bereich „Dateien“ über **„Öffnen …“** die Sibank-Schülerexportdatei und/oder die Lehrerexportdatei wählen. Mit **„Entfernen“** wird eine Datei wieder abgewählt.
2. **Zielordner wählen:** Unter „Zielordner für EDUCA“ wird der Ordner der Exportdatei vorbelegt; über **„Ordner wählen …“** lässt er sich ändern.
3. **Einstellungen prüfen** (siehe unten), vor allem Schulnummer und Schuljahr.
4. **Vorschau und Meldungen kontrollieren.**
5. Auf **„Konvertieren“** klicken. Am Ende zeigt das Programm an, welche Dateien geschrieben wurden.

## Einstellungen

| Einstellung | Bedeutung |
|---|---|
| Schulnummer | Nur Ziffern. Wird in `recordUID`, `schools` und `school_classes` verwendet. |
| Schuljahr | Vierstelliger Code, z. B. `2627` für 2026/27. Vorbelegt mit dem aktuellen Schuljahr (Wechsel zum 1. August). |
| Schüler und Lehrer in einer Datei zusammenfügen | Wenn beide Dateien geladen sind: eine gemeinsame Datei (`SuS_LuL`) statt zwei getrennter. |
| Oberstufe ausschließen (Jahrgänge 11, 12, 13) | Standardmäßig aktiv. Schüler dieser Jahrgänge werden nicht übernommen. |
| Geburtsort übernehmen | Bei deaktivierter Option bleibt das Feld `birthplace` leer. |
| Ausgabekodierung | `UTF-8` (Standard), `UTF-8 mit BOM` oder `Windows-1252 (ANSI)`. |

## Sortierung

- **Schüler:** nach Jahrgang, Klassenzusatz, Nachname, Vorname. Schüler ohne Klasse stehen am Ende.
- **Lehrer:** nach Nachname, Vorname.
- Umlaute werden wie ihre Grundbuchstaben sortiert, `ß` wie `ss`.

## Vor dem Import

Bitte die erzeugte Datei stichprobenartig prüfen, z. B. in einem Texteditor oder in Excel (beim Öffnen in Excel nicht speichern, da Excel Datums- und Zahlenformate verändern kann).
