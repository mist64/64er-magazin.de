# 64er-magazin.de

Zum 40jährigen Jubiläum des *64'er Magazins* präsentieren wir das Kunstprojekt [www.64er-magazin.de](https://www.64er-magazin.de): eine Website, die so tut, als wäre 1984. Exakt 40 Jahre nach der ursprünglichen Veröffentlichung erscheint hier jeden Monat eine neue Ausgabe:

* 4/84: 20. März 2024 (Erstausgabe)
* 5/84: 19. April 2024
* 6/84: 18. Mai 2024
* 7/84: 22. Juni 2024
* 8/84: 20. Juli 2024
* 9/84: 17. August 2024
* 10/84: 21. September 2024
* 11/84: 19. Oktober 2024
* 12/84: 16. November 2024
* 01/85: 14. Dezember 2024
* 02/85: 18. Januar 2025
* 03/85: 15. Feburar 2025
* 04/85: 15. März 2025
* 05/85: 19. April 2025
* 06/85: 17. Mai 2025
* 07/85: 14. Juni 2025
* 08/85: 19. Juli 2025
* 09/85: 16. August 2025
* 10/85: 20. September 2025
* 11/85: 18. Oktober 2025
* 12/85: 15. November 2025
* 01/86: 13. Dezember 2025
* 02/86: 17. Januar 2026
* 03/86: 14. Februar 2026
* 04/86: 14. März 2026
* 05/86: 11. April 2026
* 06/86: 16. Mai 2026
* 07/86: 14. Juni 2026
* 08/86: 18. Juli 2026
* 09/86: 15. August 2026
* 10/86: 19. September 2026

usw.

* Sonderheft 1/85 (Tips & Tricks): 23. November 2024
* Sonderheft 2/85 (Abenteuerspiele): 25. März 1985 <!-- 8504/S.30 -->
* Sonderheft 3/85 (Spiele): ca. 14. Juni 2025 <!-- 8507/S.34 -->
* Sonderheft 4/85 (Grafik): *vor* 16. August 2025 <!-- 8509 --> <!-- bis 25.10.85, SH8506 -->
* Sonderheft 5/85 (Floppy, Datasette): ca. 20. September 2025 <!-- 8510 -->
* Sonderheft 6/85 (Top-Themen): ca. 18. Oktober 2025 <!-- 8511/S.139 -->
* Sonderheft 7/85 (Professionelle Anwendungen): Mitte November 2025 <!-- 8601/S.106 -->
* Sonderheft 8/85 (Assembler): ca. 13. Dezember 2025 <!-- 8601/S.106 -->
* Sonderheft 1/86 (PC 128): **weit vor** 14. Februar 2026 <!-- 8603/S.168 -->
* Sonderheft 2/86 (Tips & Tricks): **vor** 14. Februar 2026 <!-- 8603/S.168 -->
* Sonderheft 3/86 (C16, C116, Plus/4): **unbekannt**
* Sonderheft 4/86 (Abenteuerspiele): *vor* 14. März 2026 <!-- 8604/S.9 -->
* Sonderheft 5/86 (C64-Grundwissen): **weit vor** 16. Mai 2026 <!-- 8606/S.73 -->
* Sonderheft 6/86 (Grafik): zwischen 16. Mai und 14. Juni 2026 <!-- wegen 7/86 -->
* Sonderheft 7/86 (Peeks & Pokes): "Ende" Juni 2026 <!-- 8607/S.40 -->

usw.

Auf der modernen Homepage gibt es

* durchsuchbare PDF-Dateien der einzelnen Ausgaben
* alle Artikel im Web-Format mit Kommentar-Funktion
* alle Listings zum Download statt zum Abtippen
* Übersichtsseiten für alle Tests, alle Listings etc. über alle Ausgaben hinweg
* eine Suche über den Text aller Artikel
* einen RSS-Feed, der ab Veröffentlichung jeden Tag zwei Artikel liefert
* die Funktion, einen Artikel auf Mastodon zu teilen

Alle Artikel sind mit dem Text im gedruckten Magazin identisch, Schreibfehler und sachliche Fehler sind also unverändert. Errata aus späteren Ausgaben ("Fehlerteufelchen") werden den Artikeln allerdings angehängt, und später dokumentierte Fehler in Software sind in den Downloads bereits behoben.

## CMS

Das Projekt verwendet ein einfaches in Python geschriebenes "CMS". Es nimmt HTMLs (mit zusätzlichen Metadaten) und ein paar andere Dateien und erstellt eine vollständig statische Seite.

* Für lokale Kommentare verwenden wir [Isso](https://isso-comments.de).
* Die lokale Suche ist [Lunr](https://lunrjs.com).

Das Skript braucht (macOS):
```
brew install imagemagick     # to convert PNG to JPG
brew install vice            # to generate PRG from TXT (via petcat)

python3 -m pip install -r requirements.txt
# pip3 install beautifulsoup4    # to work with HTML
# pip3 install python-dateutil   # to work with dates
# pip3 install pytz              # ...and timezones
# pip3 install PyPDF2            # to cut PDFs
```

Die Python-Packages können auch in eine virtuelle Umgebung installiert werden:
```
python3 -m venv .venv                       # create a virtual environment
source .venv/bin/activate                   # activate it
python3 -m pip install -r requirements.txt  # install the required packages
```

Die Eingabe-Ausgaben werden aus `issues` gelesen, die Website wird nach `out` geschrieben.

* `/generate.py` generiert nur die Website.
* `./generate.py local` startet zudem einen lokalen Webserver.
* `./generate.py upload` lädt die Website auf den Server.
* Das Argument `--future` vor `local`/`upload` bezieht auch Ausgaben mit ein, deren Veröffentlichungsdatum in der Zukunft liegt. Beim Upload landen die Daten in einem Unterverzeichnis namens `test/`.

`local` und `upload` öffnen danach ein Browserfenster mit der Seite (nur macOS).

## Credits

* Script, HTML, CSS, Scan, Bildbearbeitung, OCR:
    * [Michael Steil](https://github.com/mist64) &lt;mist64@mac.com&gt;
    * [ellduin](https://github.com/ellduin)
* Ausgabe 5/84:
    * Abtippen der Listings
        * [goloMAK](https://www.forum64.de/wcf/index.php?user/28439-golomak/)
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
        * [Drachen](https://www.forum64.de/wcf/index.php?user/9125-drachen/)
* Ausgabe 6/84:
    * Abtippen der Listings
        * [goloMAK](https://www.forum64.de/wcf/index.php?user/28439-golomak/)
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
* Ausgabe 7/84:
    * Erfassen diverser Tabellen, Eintragen der Index-Kategorien und -Titel
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * Abtippen der Listings
        * [Dekay](https://www.forum64.de/wcf/index.php?user/1038-dekay/)
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
        * [goloMAK](https://www.forum64.de/wcf/index.php?user/28439-golomak/)
        * [marvin](https://www.forum64.de/wcf/index.php?user/10141-marvin/)
        * [pgeorgi](https://www.forum64.de/wcf/index.php?user/28405-pgeorgi/)
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
        * [vicjack](https://www.forum64.de/wcf/index.php?user/15999-vicjack/)
* Ausgabe 8/84:
    * Erfassen diverser Tabellen, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * Abtippen der Listings
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
* Ausgabe 9/84:
    * Formatierung, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * Abtippen der Listings
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
        * [goloMAK](https://www.forum64.de/wcf/index.php?user/28439-golomak/)
        * [64erGrufti](https://www.forum64.de/wcf/index.php?user/30650-64ergrufti/)
        * [ClausS](https://www.forum64.de/wcf/index.php?user/28399-clauss/)
* Ausgabe 10/84:
    * Formatierung, Metadaten
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * OCR-Fixes
        * [vicjack](https://www.forum64.de/wcf/index.php?user/15999-vicjack/)
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * Abtippen der Listings
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
        * [darkvision](https://www.forum64.de/wcf/index.php?user/21031-darkvision/)
* Ausgabe 11/84:
    * Formatierung, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * Abtippen der Listings
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
        * [goloMAK](https://www.forum64.de/wcf/index.php?user/28439-golomak/)
        * [ClausS](https://www.forum64.de/wcf/index.php?user/28399-clauss/)
* Ausgabe 12/84:
    * Formatierung, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * Abtippen der Listings
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
* Ausgabe 1/85:
    * Formatierung, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * Abtippen der Listings
        * [pgeorgi](https://www.forum64.de/wcf/index.php?user/28405-pgeorgi/)
        * [goloMAK](https://www.forum64.de/wcf/index.php?user/28439-golomak/)
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
* Ausgabe 2/85:
    * Formatierung, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * Abtippen der Listings
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
* Ausgabe 3/85:
    * Formatierung, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * Abtippen der Listings
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
* Ausgabe 4/85:
    * Formatierung, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * OCR-Fixes
        * [vicjack](https://www.forum64.de/wcf/index.php?user/15999-vicjack/)
    * Abtippen der Listings
        * [pgeorgi](https://www.forum64.de/wcf/index.php?user/28405-pgeorgi/)
* Ausgabe 5/85:
    * Formatierung, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * Abtippen der Listings
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
        * [goloMAK](https://www.forum64.de/wcf/index.php?user/28439-golomak/)
* Ausgabe 6/85:
    * Formatierung, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * OCR-Fixes
        * [vicjack](https://www.forum64.de/wcf/index.php?user/15999-vicjack/)
* Ausgabe 7/85:
    * Formatierung, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * OCR-Fixes
        * [vicjack](https://www.forum64.de/wcf/index.php?user/15999-vicjack/)
* Ausgabe 8/85:
    * Formatierung, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * OCR-Fixes
        * [vicjack](https://www.forum64.de/wcf/index.php?user/15999-vicjack/)
* Ausgabe 9/85:
    * Formatierung, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * Abtippen der Listings
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
        * [pgeorgi](https://www.forum64.de/wcf/index.php?user/28405-pgeorgi/)
* Ausgabe 10/85:
    * Formatierung, Metadaten, OCR-Fixes
        * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)
    * Abtippen der Listings
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
        * [goloMAK](https://www.forum64.de/wcf/index.php?user/28439-golomak/)

* Sonderheft 1/1985:
    * Abtippen der Listings
        * [Kalle861](https://www.forum64.de/wcf/index.php?user/18972-kalle861/)
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
        * [goloMAK](https://www.forum64.de/wcf/index.php?user/28439-golomak/)
        * [ClausS](https://www.forum64.de/wcf/index.php?user/28399-clauss/)
* Sonderheft 2/1985:
    * Zeitschrift zum Scannen geliehen
        * [pgeorgi](https://www.forum64.de/wcf/index.php?user/28405-pgeorgi/)
    * Umschlag (inkl. Titelbild) zum Scannen geliehen
        * [docbobo](https://www.forum64.de/wcf/index.php?user/26944-docbobo/)
    * OCR
        * [Drachen](https://www.forum64.de/wcf/index.php?user/9125-drachen/)
* Sonderheft 3/1985:
    * OCR-Fixes
        * [vicjack](https://www.forum64.de/wcf/index.php?user/15999-vicjack/)
    * Abtippen der Listings
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
* Sonderheft 4/1985:
    * Abtippen der Listings
        * [goloMAK](https://www.forum64.de/wcf/index.php?user/28439-golomak/)
        * [ClausS](https://www.forum64.de/wcf/index.php?user/28399-clauss/)
* Sonderheft 5/1985:
    * Abtippen der Listings
        * [hiTCH-HiKER](https://www.forum64.de/wcf/index.php?user/30694-hitch-hiker/)
        * [64erGrufti](https://www.forum64.de/wcf/index.php?user/30650-64ergrufti/)
        * [pgeorgi](https://www.forum64.de/wcf/index.php?user/28405-pgeorgi/)

![](screenshot1.png)

![](screenshot2.png)
