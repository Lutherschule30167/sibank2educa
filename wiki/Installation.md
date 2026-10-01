# Installation

## Variante 1: Fertige EXE (Windows, empfohlen)

1. Auf der Seite [Releases](https://github.com/Lutherschule30167/sibank2educa/releases) die aktuelle `sibank2educa.exe` unter „Assets“ herunterladen.
2. Die Datei an einem beliebigen Ort speichern und per Doppelklick starten. Eine Installation ist nicht nötig.

**Windows SmartScreen:** Beim ersten Start kann Windows warnen, weil die EXE nicht signiert ist. Über **„Weitere Informationen“ → „Trotzdem ausführen“** lässt sie sich starten.

## Variante 2: Mit Python (Windows, macOS, Linux)

Voraussetzung ist Python 3.8 oder neuer von [python.org](https://www.python.org/downloads/). Weitere Pakete werden nicht benötigt; die grafische Oberfläche nutzt `tkinter`, das im Windows-Installer von python.org enthalten ist.

```
python sibank2educa.py
```

Unter Linux muss `tkinter` je nach Distribution separat installiert werden (z. B. Paket `python3-tk`).

## EXE selbst bauen

```
pip install pyinstaller
pyinstaller --onefile --noconsole --name sibank2educa sibank2educa.py
```

Die EXE liegt danach in `dist/`. Bei jedem auf GitHub veröffentlichten Release baut ein GitHub-Workflow die EXE automatisch und hängt sie an das Release an.

## Einstellungen

Schulnummer, Zielordner, Ausgabekodierung und die Einstellung zum Geburtsort werden für den nächsten Start gespeichert in:

```
%USERPROFILE%\.sibank2educa.json
```

Zum Zurücksetzen einfach diese Datei löschen.
