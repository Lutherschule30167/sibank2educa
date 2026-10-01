# Ausgabeformat

Die Zieldatei ist eine CSV-Datei mit Komma als Trennzeichen; alle Felder stehen in Anführungszeichen, Zeilenende ist `CRLF`.

## Spalten

| Spalte | Inhalt |
|---|---|
| `recordUID` | `Schulnummer-ID-S` (Schüler) bzw. `Schulnummer-ID-L` (Lehrer) |
| `schools` | Schulnummer |
| `firstname` | Vorname |
| `lastname` | Nachname |
| `school_classes` | `Schulnummer-Schuljahr-Klasse`, Klasse mit führender Null (`8b` → `08b`); bei Lehrern leer |
| `user_role` | `student` bzw. `teacher` |
| `birthday` | `JJJJ-MM-TT`, fehlend als `NULL` |
| `birthplace` | Geburtsort (nur Schüler, abschaltbar) |
| `geschlecht` | kleingeschrieben: `m`, `w`, `d` |
| `abgang` | immer `NULL` |
| `zugang` | `JJJJ-MM-TT`, fehlend als `NULL` |
| `kuerzel` | Lehrerkürzel, sonst `NULL` |
| `akademischerTitel` | Titel, falls eine Spalte `Titel` vorhanden ist, sonst `NULL` |

## Beispiel

```
"recordUID","schools","firstname","lastname","school_classes","user_role","birthday","birthplace","geschlecht","abgang","zugang","kuerzel","akademischerTitel"
"611-2025010100000001-S","611","Max","Mustermann","611-2627-05a","student","2015-03-14","Hannover","m","NULL","2025-08-01","NULL","NULL"
"611-9001-L","611","Anna","Lehrerin","","teacher","1980-03-12","","w","NULL","2015-08-01","LEH","NULL"
```

## Datumsformate in der Eingabe

Akzeptiert werden `TT.MM.JJJJ` (Sibank-Standard) und `JJJJ-MM-TT`.

## Dateinamen

```
<Schulnummer>_<Schuljahr>_<SuS|LuL|SuS_LuL>_<JJJJMMTT>_<HHMM>.csv
```

Beispiel: `611_2627_SuS_LuL_20260929_1435.csv`

Existiert eine Datei mit gleichem Namen bereits, fragt das Programm vor dem Überschreiben nach.
