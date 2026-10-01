# sibank2educa

Kleines Windows-Tool mit grafischer Oberfläche, das die CSV-Exporte aus **Sibank** (Schüler und Lehrer) in das Importformat für **EDUCA** umwandelt.

Das Tool läuft vollständig lokal. Es werden keine Daten ins Internet übertragen.

> **Status: Testphase.** sibank2educa ist ein privates Projekt, das den Umstieg auf ein neues Zeugnisprogramm erleichtern soll. Es ist nicht im Auftrag einer Schule oder Schulleitung entstanden. Bitte die erzeugten Dateien vor dem Import sorgfältig prüfen.

## Funktionen

- Einlesen des Sibank-Schülerexports und/oder des Sibank-Lehrerexports
- Umwandlung in das EDUCA-Format (Datumsformat, Klassen mit führender Null, `recordUID`, `school_classes`, `user_role` usw.)
- Frei wählbare Schulnummer und Schuljahr (Vorbelegung automatisch, Wechsel zum 1. August)
- Oberstufe (Jahrgänge 11–13) optional ausschließen – standardmäßig aktiv
- Schüler und Lehrer wahlweise in einer gemeinsamen oder in getrennten Dateien
- Sortierung nach Klasse, innerhalb der Klasse nach Nachname und Vorname
- Vorschau der Ergebnisdaten vor dem Speichern
- Warnungen bei fehlenden oder fehlerhaften Angaben (z. B. ungültiges Datum, fehlende Klasse, doppelte IDs)
- Automatische Erkennung von Kodierung (UTF-8 / Windows-ANSI) und Trennzeichen (Komma / Semikolon)

## Installation

### Variante 1: Fertige EXE (Windows, ohne Python)

Unter [Releases](../../releases) die aktuelle `sibank2educa.exe` herunterladen und starten.

> Beim ersten Start kann Windows SmartScreen eine Warnung anzeigen, weil die EXE nicht signiert ist. Über „Weitere Informationen“ → „Trotzdem ausführen“ lässt sie sich starten.

### Variante 2: Mit Python (Windows, macOS, Linux)

Voraussetzung ist Python 3.8 oder neuer von [python.org](https://www.python.org/downloads/). Weitere Pakete werden nicht benötigt.

```
python sibank2educa.py
```

## Export aus Sibank vorbereiten

Die beiden Exportdateien werden in Sibank über den **Listengenerator** erzeugt. Dafür muss einmalig je eine neue Liste für Schüler und für Lehrer angelegt werden. Die Felder müssen genau in der unten angegebenen Reihenfolge ausgewählt werden.

Für alle Felder gelten auf dem Reiter **„Felder“** dieselben Einstellungen:

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

Die **Spalten-Überschriften** entsprechen jeweils dem Feldnamen, Ausrichtung Links.

### Liste für den Schülerexport

| Spalte | Feld / Überschrift |
|---|---|
| 1 | Identnummer |
| 2 | offizieller Vorname |
| 3 | Familienname |
| 4 | Klasse |
| 5 | Geburtsdatum |
| 6 | Geburtsort |
| 7 | Geschlecht |
| 8 | Zugang |

### Liste für den Lehrerexport

| Spalte | Feld / Überschrift |
|---|---|
| 1 | LehrerID |
| 2 | Vorname |
| 3 | Name |
| 4 | Geburtsdatum |
| 5 | Geschlecht |
| 6 | Zugangsdatum |
| 7 | Kürzel |

Die Listen werden anschließend als CSV-Datei exportiert. Groß- und Kleinschreibung der Überschriften spielt für sibank2educa keine Rolle.

## Bedienung

1. **Sibank Schüler-Exportdatei** und/oder **Sibank Lehrer-Exportdatei** über „Öffnen …“ laden.
2. **Zielordner für EDUCA** wählen (vorbelegt mit dem Ordner der Exportdatei).
3. **Schulnummer** und **Schuljahr** prüfen.
4. In der Vorschau kontrollieren und auf **Konvertieren** klicken.

Schulnummer, Zielordner, Kodierung und die Einstellung zum Geburtsort werden für den nächsten Start gespeichert (in `%USERPROFILE%\.sibank2educa.json`).

## Dateiformate

### Eingabe: Sibank-Schülerexport

```
"IDENTNUMMER","OFFIZIELLER VORNAME","FAMILIENNAME","KLASSE","GEBURTSDATUM","GEBURTSORT","GESCHLECHT","ZUGANG"
```

### Eingabe: Sibank-Lehrerexport

```
"LEHRERID","VORNAME","NAME","GEBURTSDATUM","GESCHLECHT","ZUGANGSDATUM","KÜRZEL"
```

Beispieldateien mit erfundenen Daten liegen im Ordner [`beispiele/`](beispiele/).

### Ausgabe: EDUCA-Import

```
"recordUID","schools","firstname","lastname","school_classes","user_role","birthday","birthplace","geschlecht","abgang","zugang","kuerzel","akademischerTitel"
"611-2025010100000001-S","611","Max","Mustermann","611-2627-05a","student","2015-03-14","Hannover","m","NULL","2025-08-01","NULL","NULL"
"611-9001-L","611","Anna","Lehrerin","","teacher","1980-03-12","","w","NULL","2015-08-01","LEH","NULL"
```

| Feld | Aufbau |
|---|---|
| `recordUID` | `Schulnummer-ID-S` (Schüler) bzw. `Schulnummer-ID-L` (Lehrer) |
| `school_classes` | `Schulnummer-Schuljahr-Klasse`, Klasse mit führender Null (`8b` → `08b`) |
| `user_role` | `student` bzw. `teacher` |
| `birthday`, `zugang` | `JJJJ-MM-TT`, fehlende Werte als `NULL` |
| `geschlecht` | kleingeschrieben (`m`, `w`, `d`) |

### Dateinamen

```
<Schulnummer>_<Schuljahr>_<SuS|LuL|SuS_LuL>_<JJJJMMTT>_<HHMM>.csv
```

Beispiel: `611_2627_SuS_LuL_20260929_1435.csv`

## Datenschutz

- Das Tool verarbeitet personenbezogene Daten ausschließlich lokal auf dem eigenen Rechner.
- **Echte Export- oder Importdateien niemals in dieses Repository hochladen.** Die `.gitignore` schließt deshalb alle `.csv`-Dateien außerhalb von `beispiele/` aus.
- Die Beispieldateien enthalten ausschließlich erfundene Personen.

## Windows-EXE selbst bauen

```
pip install pyinstaller
pyinstaller --onefile --noconsole --name sibank2educa sibank2educa.py
```

Die EXE liegt anschließend in `dist/`. Alternativ baut der GitHub-Workflow unter `.github/workflows/` die EXE automatisch, sobald auf GitHub ein Release veröffentlicht wird, und hängt sie dort unter „Assets“ an.

### Neue Version veröffentlichen

1. In `sibank2educa.py` die Versionsnummer `__version__` erhöhen und in `docs/index.html` die Angabe „Aktuelle Version“ anpassen.
2. Auf GitHub ein Release mit dem passenden Tag anlegen, z. B. `v1.0.2` für `__version__ = "1.0.2"`.

Der Workflow bricht ab, wenn Tag und `__version__` nicht übereinstimmen.

## Hinweis

Dieses Projekt steht in keiner Verbindung zu den Herstellern von Sibank oder EDUCA und wird von ihnen weder unterstützt noch geprüft. Die Nutzung erfolgt auf eigene Verantwortung – bitte die erzeugten Dateien vor dem Import stichprobenartig prüfen.

### Marken

Die Namen und Marken der genannten Programme gehören ihren jeweiligen Inhabern. Sie werden hier ausschließlich verwendet, um zu beschreiben, mit welchen Programmen sibank2educa zusammenarbeitet.

| Programm | Rechteinhaber | Homepage |
|---|---|---|
| Sibank / SibankPLUS | Haneke Software, Siegburg | [haneke.de](https://haneke.de/) |
| EDUCA (educa) | Digital Learning GmbH, Duderstadt | [digitallearning.gmbh](https://digitallearning.gmbh/) |

## Projektwebsite

Die Website liegt im Ordner [`docs/`](docs/) und wird über GitHub Pages veröffentlicht (Einstellungen → Pages → Branch `main`, Ordner `/docs`). Sie lädt keine externen Ressourcen und setzt keine Cookies.

## Entstehung

Programmcode, Dokumentation und Website wurden mit Unterstützung von [Claude](https://www.anthropic.com/claude), einem KI-Assistenten von Anthropic, erstellt. Anforderungen, Prüfung und Tests liegen beim Projektverantwortlichen.

## Lizenz

[MIT](LICENSE)
