# Sibank-Export einrichten

Die Exportdateien werden in Sibank über den **Listengenerator** erzeugt. Dafür wird einmalig je eine Liste für Schüler und für Lehrer angelegt.

## Einstellungen für alle Felder (Reiter „Felder“)

| Einstellung | Wert |
|---|---|
| Breite | `0` |
| Summe | nicht angehakt |
| Ausrichtung | Links |
| Vor / Nach | leer |
| Spalte | fortlaufend (1, 2, 3, …) entsprechend der Reihenfolge unten |
| Zeile | `1` |
| Position | `1` |
| Gleiche Felder einfügen | nicht angehakt |

Die **Spaltenüberschrift** entspricht jeweils dem Feldnamen.

## Liste für den Schülerexport

| Spalte | Feld / Überschrift | Pflicht |
|---|---|---|
| 1 | Identnummer | ja |
| 2 | offizieller Vorname | ja |
| 3 | Familienname | ja |
| 4 | Klasse | |
| 5 | Geburtsdatum | |
| 6 | Geburtsort | |
| 7 | Geschlecht | |
| 8 | Zugang | |

## Liste für den Lehrerexport

| Spalte | Feld / Überschrift | Pflicht |
|---|---|---|
| 1 | LehrerID | ja |
| 2 | Vorname | ja |
| 3 | Name | ja |
| 4 | Geburtsdatum | |
| 5 | Geschlecht | |
| 6 | Zugangsdatum | |
| 7 | Kürzel | |

## Hinweise

- Die Listen als **CSV-Datei** exportieren.
- Groß- und Kleinschreibung der Überschriften spielt keine Rolle.
- Komma oder Semikolon als Trennzeichen sowie UTF-8 oder Windows-ANSI werden automatisch erkannt.
- Fehlt eine Pflichtspalte, bricht das Einlesen mit einer Meldung ab. Fehlt eine optionale Spalte, erscheint nur ein Hinweis und das Feld bleibt leer.
- Beispieldateien mit erfundenen Daten liegen im Repository im Ordner [`beispiele/`](https://github.com/Lutherschule30167/sibank2educa/tree/main/beispiele).
