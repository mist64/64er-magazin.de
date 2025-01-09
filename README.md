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
<!--
* 11/85: 
* 12/85: 
* 01/86:
* 02/86:
* 03/86:
* 04/86:
* 05/86:
* 06/86: 16. Mai 2026
* 07/86:
* 08/86: 18. Juli 2026
* 09/86: 
* 10/86: 
* 11/86: 
* 12/86: 
-->
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
brew install exiftool        # remove metadata from images

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
* Sonderheft 1/1985:
    * Abtippen der Listings
        * [Kalle861](https://www.forum64.de/wcf/index.php?user/18972-kalle861/)
        * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
        * [goloMAK](https://www.forum64.de/wcf/index.php?user/28439-golomak/)
        * [ClausS](https://www.forum64.de/wcf/index.php?user/28399-clauss/)
* Sonderheft 2/1985:
    * OCR
        * [Drachen](https://www.forum64.de/wcf/index.php?user/9125-drachen/)

![](screenshot1.png)

![](screenshot2.png)
