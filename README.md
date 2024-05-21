# 64er-magazin.de

Zum 40jährigen Jubiläum des *64'er Magazins* präsentieren wir das Kunstprojekt [www.64er-magazin.de](https://www.64er-magazin.de): eine Website, die so tut, als wäre 1984. Exakt 40 Jahre nach der ursprünglichen Veröffentlichung erscheint hier jeden Monat eine neue Ausgabe:

* 4/84: 20. März 2024 (Erstausgabe)
* 5/84: 19. April 2024
* 6/84: 18. Mai 2024
* usw.

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

Die Eingabe-Ausgaben werden aus `issues` gelesen, die Website wird nach `out` geschrieben. Befindet man sich gerade auf einem git-Branch (außer `main`), ist die Website in `out/pre/<Name des Branches>`.

* `/generate.py` generiert nur die Website.
* `./generate.py local` startet zudem einen lokalen Webserver.
* `./generate.py upload` lädt die Website auf den Server. Befindet man sich auf einem Branch, wird nach `/pre/<Name des Branches>` hochgeladen.

`local` und `upload` öffnen danach ein Browserfenster mit der Seite (nur macOS).

## Credits

* Script, HTML, CSS, Scan, Bildbearbeitung, OCR:
    * Michael Steil <mist64@mac.com>
    * [ellduin](https://github.com/ellduin)
* Abtippen der Listings aus Ausgabe 5/84:
    * [goloMAK](https://www.forum64.de/wcf/index.php?user/28439-golomak/)
    * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
    * [Drachen](https://www.forum64.de/wcf/index.php?user/9125-drachen/)
* Abtippen der Listings aus Ausgabe 6/84:
    * [goloMAK](https://www.forum64.de/wcf/index.php?user/28439-golomak/)
    * [Endurion](https://www.forum64.de/wcf/index.php?user/1964-endurion/)
    * [thierer](https://www.forum64.de/wcf/index.php?user/26370-thierer/)



![](screenshot1.png)

![](screenshot2.png)
