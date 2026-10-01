#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sibank2educa – wandelt Sibank-Exporte (Schüler / Lehrer) in das EDUCA-Importformat um.

Läuft unter Windows, macOS und Linux. Benötigt nur die Python-Standardbibliothek
(tkinter ist im offiziellen Windows-Installer von python.org enthalten).

Start:  python sibank2educa.py

Erstellt mit Unterstützung von Claude (KI-Assistent von Anthropic).

Marken: Sibank/SibankPLUS gehört Haneke Software (https://haneke.de/),
EDUCA der Digital Learning GmbH (https://digitallearning.gmbh/). Dieses Projekt
steht in keiner Verbindung zu den Herstellern.
"""

import csv
import io
import json
import re
from datetime import date, datetime
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

__version__ = "1.0.0"

APP_TITEL = f"sibank2educa {__version__}  –  Sibank → EDUCA"
CONFIG_DATEI = Path.home() / ".sibank2educa.json"
ALTE_CONFIG_DATEI = Path.home() / ".csv_zeugnis_konverter.json"  # frühere Version

PFLICHT_SPALTEN = ["IDENTNUMMER", "OFFIZIELLER VORNAME", "FAMILIENNAME"]
OPTIONALE_SPALTEN = {
    "S": ["KLASSE", "GEBURTSDATUM", "GEBURTSORT", "GESCHLECHT", "ZUGANG"],
    "L": ["GEBURTSDATUM", "GESCHLECHT", "ZUGANG", "KÜRZEL"],
}
# Alternative Spaltennamen, die auf die Standardnamen abgebildet werden
SPALTEN_ALIASE = {
    # Sibank Lehrer-Export
    "LEHRERID": "IDENTNUMMER",
    "VORNAME": "OFFIZIELLER VORNAME",
    "NAME": "FAMILIENNAME",
    "ZUGANGSDATUM": "ZUGANG",
    # weitere mögliche Schreibweisen
    "NACHNAME": "FAMILIENNAME",
    "KUERZEL": "KÜRZEL",
    "TITEL": "AKADEMISCHER TITEL",
}

ZIEL_SPALTEN = [
    "recordUID", "schools", "firstname", "lastname", "school_classes",
    "user_role", "birthday", "birthplace", "geschlecht", "abgang",
    "zugang", "kuerzel", "akademischerTitel",
]

TYPEN = ("S", "L")
ROLLEN = {"S": "student", "L": "teacher"}
BEZEICHNUNG = {"S": "Schüler", "L": "Lehrer"}
DATEI_TAG = {"S": "SuS", "L": "LuL"}
DATEI_TAG_BEIDE = "SuS_LuL"
OBERSTUFE = {11, 12, 13}

AUSGABE_KODIERUNGEN = {
    "UTF-8": "utf-8",
    "UTF-8 mit BOM": "utf-8-sig",
    "Windows-1252 (ANSI)": "cp1252",
}
NULL = "NULL"


class KonvertierungsFehler(Exception):
    """Fehler, der dem Benutzer als Meldung angezeigt wird."""


# --------------------------------------------------------------------------
# Konvertierungslogik (ohne GUI, separat testbar)
# --------------------------------------------------------------------------

def aktuelles_schuljahr(heute=None):
    """Schuljahr als 4-stelliger Code, Wechsel zum 1. August (z. B. 2026/27 -> '2627')."""
    heute = heute or date.today()
    start = heute.year if heute.month >= 8 else heute.year - 1
    return f"{start % 100:02d}{(start + 1) % 100:02d}"


def schuljahr_auswahl(zurueck=2, vor=2):
    heute = date.today()
    start = heute.year if heute.month >= 8 else heute.year - 1
    return [f"{j % 100:02d}{(j + 1) % 100:02d}" for j in range(start - zurueck, start + vor + 1)]


def datum_umwandeln(wert):
    """'09.10.2007' -> '2007-10-09'. Leerer Wert -> None."""
    wert = (wert or "").strip()
    if not wert:
        return None
    for fmt in ("%d.%m.%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(wert, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    raise ValueError(f"ungültiges Datum '{wert}'")


def klasse_formatieren(klasse):
    """'8b' -> '08b', '12' -> '12', '11d' -> '11d'."""
    klasse = (klasse or "").strip().replace(" ", "")
    treffer = re.match(r"^(\d+)(.*)$", klasse)
    if not treffer:
        return klasse
    return treffer.group(1).zfill(2) + treffer.group(2)


def jahrgang(klasse):
    """'11d' -> 11, '8b' -> 8, '' -> None."""
    treffer = re.match(r"^\s*(\d+)", klasse or "")
    return int(treffer.group(1)) if treffer else None


def nach_jahrgang_filtern(zeilen, ausgeschlossen):
    """Entfernt alle Zeilen, deren Klasse zu einem ausgeschlossenen Jahrgang gehört.

    Rückgabe: (behaltene_zeilen, anzahl_entfernt)
    """
    if not ausgeschlossen:
        return zeilen, 0
    behalten = [z for z in zeilen if jahrgang(z.get("KLASSE")) not in ausgeschlossen]
    return behalten, len(zeilen) - len(behalten)


def _sortiertext(text):
    """Deutsche Sortierung nach DIN 5007-1: Umlaute wie Grundbuchstaben, ß wie ss."""
    text = (text or "").casefold()
    for alt, neu in (("ä", "a"), ("ö", "o"), ("ü", "u"), ("ß", "ss")):
        text = text.replace(alt, neu)
    return text


def sortieren(ausgabe_zeilen, typ):
    """Schüler: nach Jahrgang, Klassenzusatz, Nachname, Vorname (ohne Klasse ans Ende).
    Lehrer: nach Nachname, Vorname."""
    def name(z):
        return (_sortiertext(z["lastname"]), _sortiertext(z["firstname"]))

    if typ == "L":
        return sorted(ausgabe_zeilen, key=name)

    def schluessel(z):
        klasse = z["school_classes"].split("-", 2)[2] if z["school_classes"] else ""
        stufe = jahrgang(klasse)
        zusatz = re.sub(r"^\d+", "", klasse)
        return (stufe is None, stufe or 0, _sortiertext(zusatz)) + name(z)

    return sorted(ausgabe_zeilen, key=schluessel)


def quelldatei_lesen(pfad, typ):
    """Liest eine Sibank-Export-CSV. Erkennt Kodierung und Trennzeichen automatisch.

    Rückgabe: (zeilen, kodierung, hinweise)
    """
    rohdaten = Path(pfad).read_bytes()
    text, kodierung = None, None
    for enc in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            text = rohdaten.decode(enc)
            kodierung = enc
            break
        except UnicodeDecodeError:
            continue

    if not text or not text.strip():
        raise KonvertierungsFehler("Die Datei ist leer.")

    erste_zeile = text.splitlines()[0]
    trenner = ";" if erste_zeile.count(";") > erste_zeile.count(",") else ","

    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=trenner)
    if reader.fieldnames is None:
        raise KonvertierungsFehler("Keine Kopfzeile in der Datei gefunden.")

    # Spaltennamen vereinheitlichen (Leerzeichen, Groß-/Kleinschreibung, Aliase)
    spalten = {}
    for name in reader.fieldnames:
        norm = (name or "").strip().upper()
        spalten[name] = SPALTEN_ALIASE.get(norm, norm)
    vorhanden = set(spalten.values())

    fehlend = [s for s in PFLICHT_SPALTEN if s not in vorhanden]
    if fehlend:
        raise KonvertierungsFehler(
            "Es fehlen Pflichtspalten:\n  " + "\n  ".join(fehlend)
            + "\n\nGefundene Spalten:\n  " + "\n  ".join(reader.fieldnames)
        )

    hinweise = [f"Spalte '{s}' fehlt – das Feld bleibt leer."
                for s in OPTIONALE_SPALTEN[typ] if s not in vorhanden]

    zeilen = []
    for roh in reader:
        zeilen.append({spalten[k]: (v or "").strip() for k, v in roh.items() if k in spalten})
    return zeilen, kodierung, hinweise


def konvertieren(zeilen, schulnummer, schuljahr, typ, geburtsort_uebernehmen=True):
    """Wandelt die gelesenen Zeilen ins EDUCA-Format um.

    Rückgabe: (ausgabe_zeilen, warnungen)
    """
    rolle = ROLLEN[typ]
    datei = f"{BEZEICHNUNG[typ]}-Datei"
    ausgabe, warnungen = [], []

    for nr, z in enumerate(zeilen, start=2):  # Zeile 1 = Kopfzeile
        if not any(z.values()):
            continue

        ident = z.get("IDENTNUMMER", "")
        name = f"{z.get('OFFIZIELLER VORNAME', '')} {z.get('FAMILIENNAME', '')}".strip()
        ort = f"{datei}, Zeile {nr} ({name or 'ohne Namen'})"
        if not ident:
            warnungen.append(f"{ort}: keine IDENTNUMMER – übersprungen.")
            continue

        try:
            geburtstag = datum_umwandeln(z.get("GEBURTSDATUM"))
        except ValueError as e:
            warnungen.append(f"{ort}: Geburtsdatum {e} – als NULL ausgegeben.")
            geburtstag = None

        try:
            zugang = datum_umwandeln(z.get("ZUGANG"))
        except ValueError as e:
            warnungen.append(f"{ort}: Zugang {e} – als NULL ausgegeben.")
            zugang = None

        klasse = klasse_formatieren(z.get("KLASSE"))
        if klasse:
            schulklasse = f"{schulnummer}-{schuljahr}-{klasse}"
        else:
            schulklasse = ""
            if typ == "S":
                warnungen.append(f"{ort}: keine Klasse angegeben.")

        geschlecht = z.get("GESCHLECHT", "").lower()
        if geschlecht and geschlecht not in ("m", "w", "d"):
            warnungen.append(f"{ort}: unbekanntes Geschlecht '{geschlecht}'.")

        ausgabe.append({
            "recordUID": f"{schulnummer}-{ident}-{typ}",
            "schools": schulnummer,
            "firstname": z.get("OFFIZIELLER VORNAME", ""),
            "lastname": z.get("FAMILIENNAME", ""),
            "school_classes": schulklasse,
            "user_role": rolle,
            "birthday": geburtstag or NULL,
            "birthplace": z.get("GEBURTSORT", "") if geburtsort_uebernehmen else "",
            "geschlecht": geschlecht,
            "abgang": NULL,
            "zugang": zugang or NULL,
            "kuerzel": z.get("KÜRZEL") or NULL,
            "akademischerTitel": z.get("AKADEMISCHER TITEL") or NULL,
        })

    gesehen = set()
    for zeile in ausgabe:
        uid = zeile["recordUID"]
        if uid in gesehen:
            warnungen.append(f"{datei}: doppelte recordUID {uid}")
        gesehen.add(uid)

    return ausgabe, warnungen


def zieldatei_schreiben(pfad, zeilen, kodierung):
    """Schreibt die Zieldatei: Komma-getrennt, alle Felder in Anführungszeichen."""
    nicht_darstellbar = []
    for z in zeilen:
        for feld in ZIEL_SPALTEN:
            try:
                z[feld].encode(kodierung)
            except UnicodeEncodeError:
                nicht_darstellbar.append(f"{z['firstname']} {z['lastname']} ({feld}: {z[feld]})")
                break
    if nicht_darstellbar:
        raise KonvertierungsFehler(
            "Folgende Einträge enthalten Zeichen, die in der gewählten Kodierung "
            "nicht darstellbar sind:\n  " + "\n  ".join(nicht_darstellbar[:15])
            + ("\n  …" if len(nicht_darstellbar) > 15 else "")
            + "\n\nBitte UTF-8 als Ausgabekodierung wählen."
        )

    with open(pfad, "w", encoding=kodierung, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ZIEL_SPALTEN, quoting=csv.QUOTE_ALL,
                                lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(zeilen)


def zieldateien_bestimmen(ordner, typen, zusammenfuegen, schulnummer, schuljahr, zeitpunkt=None):
    """Erzeugt die Dateinamen nach dem Muster
        <Schulnummer>_<Schuljahr>_<SuS|LuL|SuS_LuL>_<JJJJMMTT>_<HHMM>.csv
    z. B. 611_2627_SuS_LuL_20260929_1435.csv

    Rückgabe: Liste von (pfad, [typen])
    """
    zeitpunkt = zeitpunkt or datetime.now()
    stempel = zeitpunkt.strftime("%Y%m%d_%H%M")
    ordner = Path(ordner)

    def pfad(tag):
        return ordner / f"{schulnummer}_{schuljahr}_{tag}_{stempel}.csv"

    if len(typen) == 1:
        return [(pfad(DATEI_TAG[typen[0]]), list(typen))]
    if zusammenfuegen:
        return [(pfad(DATEI_TAG_BEIDE), list(typen))]
    return [(pfad(DATEI_TAG[t]), [t]) for t in typen]


def config_laden():
    for datei in (CONFIG_DATEI, ALTE_CONFIG_DATEI):
        try:
            return json.loads(datei.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
    return {}


def config_speichern(daten):
    try:
        CONFIG_DATEI.write_text(json.dumps(daten, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


# --------------------------------------------------------------------------
# GUI
# --------------------------------------------------------------------------

class KonverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITEL)
        self.geometry("1150x750")
        self.minsize(900, 600)

        self.cfg = config_laden()
        self.quellen = {t: None for t in TYPEN}   # je Typ: dict mit pfad/zeilen oder None
        self._after_id = None

        self.var_eingabe = {t: tk.StringVar() for t in TYPEN}
        self.var_ausgabe = tk.StringVar(value=self.cfg.get("zielordner", ""))
        self.var_schulnummer = tk.StringVar(value=self.cfg.get("schulnummer", ""))
        self.var_schuljahr = tk.StringVar(value=aktuelles_schuljahr())
        self.var_geburtsort = tk.BooleanVar(value=self.cfg.get("geburtsort", True))
        kod = self.cfg.get("kodierung", "UTF-8")
        self.var_kodierung = tk.StringVar(value=kod if kod in AUSGABE_KODIERUNGEN else "UTF-8")
        self.var_ohne_oberstufe = tk.BooleanVar(value=True)
        self.var_zusammenfuegen = tk.BooleanVar(value=True)
        self.var_ziel_hinweis = tk.StringVar()
        self.var_status = tk.StringVar(value="Bitte mindestens eine Sibank-Exportdatei auswählen.")

        self._oberflaeche_bauen()

        for var in (self.var_schulnummer, self.var_schuljahr, self.var_geburtsort,
                    self.var_ohne_oberstufe):
            var.trace_add("write", lambda *_: self._vorschau_planen())
        for var in (self.var_ausgabe, self.var_zusammenfuegen, self.var_schulnummer,
                    self.var_schuljahr):
            var.trace_add("write", lambda *_: self._zustand_aktualisieren())

        self._zustand_aktualisieren()
        self.protocol("WM_DELETE_WINDOW", self._beenden)

    # ---------- Aufbau ----------

    def _oberflaeche_bauen(self):
        pad = {"padx": 6, "pady": 4}
        haupt = ttk.Frame(self, padding=10)
        haupt.pack(fill="both", expand=True)

        # Dateien
        f_dat = ttk.LabelFrame(haupt, text="Dateien", padding=8)
        f_dat.pack(fill="x")
        f_dat.columnconfigure(1, weight=1)

        self.btn_entfernen = {}
        for zeile, typ in enumerate(TYPEN):
            ttk.Label(f_dat, text=f"Sibank {BEZEICHNUNG[typ]}-Exportdatei:").grid(
                row=zeile, column=0, sticky="w", **pad)
            ttk.Entry(f_dat, textvariable=self.var_eingabe[typ], state="readonly").grid(
                row=zeile, column=1, sticky="ew", **pad)
            ttk.Button(f_dat, text="Öffnen …", command=lambda t=typ: self._eingabe_waehlen(t)).grid(
                row=zeile, column=2, **pad)
            self.btn_entfernen[typ] = ttk.Button(
                f_dat, text="Entfernen", command=lambda t=typ: self._eingabe_entfernen(t))
            self.btn_entfernen[typ].grid(row=zeile, column=3, **pad)

        ttk.Label(f_dat, text="Zielordner für EDUCA:").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(f_dat, textvariable=self.var_ausgabe).grid(row=2, column=1, sticky="ew", **pad)
        ttk.Button(f_dat, text="Ordner wählen …", command=self._ausgabe_waehlen).grid(
            row=2, column=2, columnspan=2, sticky="ew", **pad)

        self.chk_zusammen = ttk.Checkbutton(
            f_dat, text="Schüler und Lehrer in einer Datei zusammenfügen",
            variable=self.var_zusammenfuegen)
        self.chk_zusammen.grid(row=3, column=1, sticky="w", **pad)
        ttk.Label(f_dat, textvariable=self.var_ziel_hinweis, foreground="gray40").grid(
            row=4, column=1, columnspan=3, sticky="w", padx=6)

        # Einstellungen
        f_ein = ttk.LabelFrame(haupt, text="Einstellungen", padding=8)
        f_ein.pack(fill="x", pady=(8, 0))

        ttk.Label(f_ein, text="Schulnummer:").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(f_ein, textvariable=self.var_schulnummer, width=12).grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(f_ein, text="Schuljahr:").grid(row=0, column=2, sticky="w", **pad)
        ttk.Combobox(f_ein, textvariable=self.var_schuljahr, values=schuljahr_auswahl(),
                     width=8).grid(row=0, column=3, sticky="w", **pad)

        self.chk_oberstufe = ttk.Checkbutton(
            f_ein, text="Oberstufe ausschließen (Jahrgänge 11, 12, 13)",
            variable=self.var_ohne_oberstufe)
        self.chk_oberstufe.grid(row=0, column=4, sticky="w", padx=(20, 6), pady=4)

        ttk.Checkbutton(f_ein, text="Geburtsort übernehmen", variable=self.var_geburtsort
                        ).grid(row=1, column=0, columnspan=2, sticky="w", **pad)

        ttk.Label(f_ein, text="Ausgabekodierung:").grid(row=1, column=2, sticky="w", **pad)
        ttk.Combobox(f_ein, textvariable=self.var_kodierung, values=list(AUSGABE_KODIERUNGEN),
                     state="readonly", width=20).grid(row=1, column=3, columnspan=2, sticky="w", **pad)

        # Vorschau
        f_vor = ttk.LabelFrame(haupt, text="Vorschau", padding=8)
        f_vor.pack(fill="both", expand=True, pady=(8, 0))
        f_vor.rowconfigure(0, weight=1)
        f_vor.columnconfigure(0, weight=1)

        self.tabelle = ttk.Treeview(f_vor, columns=ZIEL_SPALTEN, show="headings", height=10)
        for spalte in ZIEL_SPALTEN:
            self.tabelle.heading(spalte, text=spalte)
            self.tabelle.column(spalte, width=110, minwidth=60, stretch=False)
        sb_y = ttk.Scrollbar(f_vor, orient="vertical", command=self.tabelle.yview)
        sb_x = ttk.Scrollbar(f_vor, orient="horizontal", command=self.tabelle.xview)
        self.tabelle.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)
        self.tabelle.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")

        # Meldungen
        f_log = ttk.LabelFrame(haupt, text="Meldungen", padding=8)
        f_log.pack(fill="x", pady=(8, 0))
        self.log = tk.Text(f_log, height=6, wrap="word", state="disabled")
        sb_log = ttk.Scrollbar(f_log, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=sb_log.set)
        self.log.pack(side="left", fill="both", expand=True)
        sb_log.pack(side="right", fill="y")

        # Fußzeile
        f_fuss = ttk.Frame(haupt)
        f_fuss.pack(fill="x", pady=(8, 0))
        ttk.Label(f_fuss, textvariable=self.var_status).pack(side="left")
        ttk.Button(f_fuss, text="Konvertieren", command=self._konvertieren).pack(side="right")

    # ---------- Hilfsfunktionen ----------

    def _log(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _geladene_typen(self):
        return [t for t in TYPEN if self.quellen[t] is not None]

    def _parameter_pruefen(self):
        schulnummer = self.var_schulnummer.get().strip()
        schuljahr = self.var_schuljahr.get().strip()
        if not re.fullmatch(r"\d+", schulnummer):
            raise KonvertierungsFehler("Bitte eine Schulnummer (nur Ziffern) eingeben.")
        if not re.fullmatch(r"\d{4}", schuljahr):
            raise KonvertierungsFehler("Das Schuljahr muss 4-stellig sein, z. B. 2627.")
        if (int(schuljahr[:2]) + 1) % 100 != int(schuljahr[2:]):
            raise KonvertierungsFehler(f"Das Schuljahr '{schuljahr}' ist nicht plausibel (erwartet z. B. 2627).")
        return schulnummer, schuljahr

    def _zielpfade(self, zeitpunkt=None):
        """Liefert die zu schreibenden Dateien als Liste von (pfad, [typen])."""
        ziel = self.var_ausgabe.get().strip()
        typen = self._geladene_typen()
        if not ziel or not typen:
            return []
        try:
            schulnummer, schuljahr = self._parameter_pruefen()
        except KonvertierungsFehler:
            return []
        return zieldateien_bestimmen(ziel, typen, self.var_zusammenfuegen.get(),
                                     schulnummer, schuljahr, zeitpunkt)

    def _zustand_aktualisieren(self):
        beide = len(self._geladene_typen()) == 2
        self.chk_zusammen.configure(state="normal" if beide else "disabled")
        self.chk_oberstufe.configure(state="normal" if self.quellen["S"] else "disabled")
        for t in TYPEN:
            self.btn_entfernen[t].configure(state="normal" if self.quellen[t] else "disabled")

        pfade = self._zielpfade()
        if len(pfade) == 2:
            self.var_ziel_hinweis.set("Es werden zwei Dateien erzeugt:  "
                                      + "  und  ".join(p.name for p, _ in pfade))
        elif pfade:
            self.var_ziel_hinweis.set(f"Wird gespeichert als:  {pfade[0][0].name}")
        elif self._geladene_typen() and self.var_ausgabe.get().strip():
            self.var_ziel_hinweis.set("Dateiname wird angezeigt, sobald Schulnummer und Schuljahr gültig sind.")
        else:
            self.var_ziel_hinweis.set("")
        if pfade:
            self.var_ziel_hinweis.set(self.var_ziel_hinweis.get()
                                      + "   (Datum/Uhrzeit werden beim Speichern gesetzt)")

    def _ergebnis_berechnen(self, schulnummer, schuljahr):
        """Rückgabe: {typ: (zeilen, warnungen, anzahl_oberstufe_entfernt)}"""
        ergebnisse = {}
        for typ in self._geladene_typen():
            zeilen = self.quellen[typ]["zeilen"]
            entfernt = 0
            if typ == "S" and self.var_ohne_oberstufe.get():
                zeilen, entfernt = nach_jahrgang_filtern(zeilen, OBERSTUFE)
            ausgabe, warnungen = konvertieren(zeilen, schulnummer, schuljahr, typ,
                                              self.var_geburtsort.get())
            ergebnisse[typ] = (sortieren(ausgabe, typ), warnungen, entfernt)
        return ergebnisse

    # ---------- Aktionen ----------

    def _eingabe_waehlen(self, typ):
        pfad = filedialog.askopenfilename(
            title=f"Sibank {BEZEICHNUNG[typ]}-Exportdatei öffnen",
            initialdir=self.cfg.get("letzter_ordner") or str(Path.home()),
            filetypes=[("CSV-Dateien", "*.csv *.txt"), ("Alle Dateien", "*.*")],
        )
        if not pfad:
            return
        self.cfg["letzter_ordner"] = str(Path(pfad).parent)

        andere = "L" if typ == "S" else "S"
        if self.quellen[andere] and Path(self.quellen[andere]["pfad"]).resolve() == Path(pfad).resolve():
            messagebox.showwarning("Hinweis", f"Diese Datei ist bereits als {BEZEICHNUNG[andere]}-Datei geladen.")
            return

        try:
            zeilen, kodierung, hinweise = quelldatei_lesen(pfad, typ)
        except KonvertierungsFehler as e:
            messagebox.showerror("Fehler beim Einlesen", f"{Path(pfad).name}:\n\n{e}")
            self._log(f"Fehler ({BEZEICHNUNG[typ]}-Datei): {e}")
            return
        except OSError as e:
            messagebox.showerror("Fehler beim Einlesen", f"Datei konnte nicht gelesen werden:\n{e}")
            return

        self.quellen[typ] = {"pfad": pfad, "zeilen": zeilen}
        self.var_eingabe[typ].set(pfad)
        if not self.var_ausgabe.get().strip():
            self.var_ausgabe.set(str(Path(pfad).parent))

        self._log(f"{BEZEICHNUNG[typ]}-Datei eingelesen: {Path(pfad).name} – "
                  f"{len(zeilen)} Datensätze (Kodierung: {kodierung})")
        for h in hinweise:
            self._log("  Hinweis: " + h)
        self._zustand_aktualisieren()
        self._vorschau_aktualisieren()

    def _eingabe_entfernen(self, typ):
        if self.quellen[typ] is None:
            return
        self._log(f"{BEZEICHNUNG[typ]}-Datei entfernt.")
        self.quellen[typ] = None
        self.var_eingabe[typ].set("")
        self._zustand_aktualisieren()
        self._vorschau_aktualisieren()

    def _ausgabe_waehlen(self):
        aktuell = self.var_ausgabe.get().strip()
        ordner = filedialog.askdirectory(
            title="Zielordner für EDUCA wählen",
            initialdir=aktuell if aktuell and Path(aktuell).is_dir()
            else self.cfg.get("letzter_ordner") or str(Path.home()),
            mustexist=True,
        )
        if ordner:
            self.var_ausgabe.set(str(Path(ordner)))

    def _vorschau_planen(self):
        if self._after_id:
            self.after_cancel(self._after_id)
        self._after_id = self.after(300, self._vorschau_aktualisieren)

    def _vorschau_aktualisieren(self):
        self._after_id = None
        self.tabelle.delete(*self.tabelle.get_children())
        if not self._geladene_typen():
            self.var_status.set("Bitte mindestens eine Sibank-Exportdatei auswählen.")
            return
        try:
            schulnummer, schuljahr = self._parameter_pruefen()
        except KonvertierungsFehler as e:
            self.var_status.set(str(e))
            return

        ergebnisse = self._ergebnis_berechnen(schulnummer, schuljahr)
        teile, anzahl_warnungen = [], 0
        for typ, (zeilen, warnungen, entfernt) in ergebnisse.items():
            for zeile in zeilen:
                self.tabelle.insert("", "end", values=[zeile[s] for s in ZIEL_SPALTEN])
            text = f"{BEZEICHNUNG[typ]}: {len(zeilen)}"
            if entfernt:
                text += f" ({entfernt} aus der Oberstufe ausgeblendet)"
            teile.append(text)
            anzahl_warnungen += len(warnungen)

        status = "  ·  ".join(teile)
        if anzahl_warnungen:
            status += f"  –  {anzahl_warnungen} Warnung(en), werden beim Konvertieren angezeigt"
        self.var_status.set(status)

    def _konvertieren(self):
        if not self._geladene_typen():
            messagebox.showwarning("Hinweis", "Bitte zuerst mindestens eine Sibank-Exportdatei auswählen.")
            return
        try:
            schulnummer, schuljahr = self._parameter_pruefen()
        except KonvertierungsFehler as e:
            messagebox.showwarning("Eingabe prüfen", str(e))
            return

        if not self.var_ausgabe.get().strip():
            self._ausgabe_waehlen()
            if not self.var_ausgabe.get().strip():
                return

        if not Path(self.var_ausgabe.get().strip()).is_dir():
            messagebox.showerror("Fehler", "Der Zielordner existiert nicht:\n"
                                 f"{self.var_ausgabe.get().strip()}\n\nBitte einen anderen Ordner wählen.")
            return

        pfade = self._zielpfade(datetime.now())
        eingaben = {Path(self.quellen[t]["pfad"]).resolve() for t in self._geladene_typen()}
        if any(p.resolve() in eingaben for p, _ in pfade):
            messagebox.showerror("Fehler", "Eine Zieldatei darf nicht gleichzeitig eine Exportdatei sein.")
            return
        vorhanden = [p.name for p, _ in pfade if p.exists()]
        if vorhanden and not messagebox.askyesno(
                "Datei existiert", "Folgende Datei(en) existieren bereits:\n  "
                + "\n  ".join(vorhanden) + "\n\nÜberschreiben?"):
            return

        ergebnisse = self._ergebnis_berechnen(schulnummer, schuljahr)
        kodierung = AUSGABE_KODIERUNGEN[self.var_kodierung.get()]

        self._log("")
        for typ, (_, warnungen, entfernt) in ergebnisse.items():
            for w in warnungen:
                self._log("Warnung: " + w)
            if entfernt:
                self._log(f"Oberstufe ausgeschlossen: {entfernt} Schüler nicht übernommen.")

        geschrieben = []
        for pfad, typen in pfade:
            zeilen = [z for t in typen for z in ergebnisse[t][0]]
            if not zeilen:
                self._log(f"Keine Datensätze für {pfad.name} – Datei nicht erzeugt.")
                continue
            try:
                zieldatei_schreiben(pfad, zeilen, kodierung)
            except KonvertierungsFehler as e:
                messagebox.showerror("Fehler beim Speichern", f"{pfad.name}:\n\n{e}")
                return
            except OSError as e:
                messagebox.showerror("Fehler beim Speichern",
                                     f"{pfad.name} konnte nicht geschrieben werden:\n{e}\n\n"
                                     "Ist die Datei evtl. noch in Excel geöffnet?")
                return
            anzahl = " + ".join(f"{sum(1 for z in zeilen if z['user_role'] == ROLLEN[t])} "
                                f"{BEZEICHNUNG[t]}" for t in typen)
            self._log(f"Gespeichert: {pfad} ({anzahl})")
            geschrieben.append(f"{pfad.name}  ({anzahl})")

        self._einstellungen_merken()
        if not geschrieben:
            messagebox.showwarning("Hinweis", "Es wurden keine gültigen Datensätze gefunden.")
            return

        anzahl_warnungen = sum(len(e[1]) for e in ergebnisse.values())
        text = "Gespeichert:\n  " + "\n  ".join(geschrieben) + f"\n\nOrdner: {pfade[0][0].parent}"
        if anzahl_warnungen:
            text += f"\n\nEs gab {anzahl_warnungen} Warnung(en) – siehe Meldungsfenster."
        messagebox.showinfo("Fertig", text)

    def _einstellungen_merken(self):
        self.cfg.update({
            "schulnummer": self.var_schulnummer.get().strip(),
            "zielordner": self.var_ausgabe.get().strip(),
            "geburtsort": self.var_geburtsort.get(),
            "kodierung": self.var_kodierung.get(),
        })
        self.cfg.pop("typ", None)  # Einstellung aus älterer Version
        config_speichern(self.cfg)

    def _beenden(self):
        self._einstellungen_merken()
        self.destroy()


def main():
    # Scharfe Darstellung auf Windows-Bildschirmen mit Skalierung
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    app = KonverterApp()
    app.mainloop()


if __name__ == "__main__":
    main()
