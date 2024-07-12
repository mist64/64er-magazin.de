# Musik lohnt sich

Es ist unverkennbar, daß es in der letzten Zeit einen richtigen Schub gegeben hat — was die Zahl der Musikprogramme für den 64 und vor allem ihre Qualität betrifft. Die interessanteste Software stellen wir in diesem Heft vor. Dabei ist es selbst für Fachleute auf dem Gebiet der elektronischen Musik erstaunlich, was man aus einem Heimcomputer und den vergleichsweise billigen Programmen herausholen kann.

Der Computer kann nicht nur als Musikinstrument dienen — er unterstützt auch das Lernen und Üben, erlaubt die Speicherung und Wiedergabe von Musik, ermöglicht das Zusammenstellen eigener »Sounds« ebenso wie Kompositionsversuche und nimmt keine Experimente übel.

Selbst das Noten-Schreiben kann man dem Computer beziehungsweise dem Drucker überlassen. Vieles, was jetzt jedermann selbst ausprobieren kann, blieb früher auch für musikalisch Interessierte trockene Lehrbuch-Theorie.

Natürlich macht ein 100-Mark-Programm aus einem 64 keinen Konzert-Synthesizer und aus einem schwerhörigen Anfänger kein musikalisches Wunderkind. Aber ein gutes Musikprogramm gehört heute wahrscheinlich zu den lohnendsten Anschaffungen die ein Heimcomputer-Besitzer machen kann — auch wenn die Beschreibungen meist furchtbar technisch und gar nicht melodisch klingen. Ein gutes Spielprogramm ist oftmals auch nicht billiger — wird aber in der Regel sehr viel schneller langweilig. Mit einem branchentypischen Problem müssen Interessenten allerdings rechnen: Die Programme bieten zum Teil schon so viele Möglichkeiten, daß sie wahrscheinlich nur von den wenigsten Verkäufern auch erschöpfend vorgeführt werden können.

Apropos Titelbild: Fragen Sie bitte nicht, wo man dieses Gerät kaufen kann — das ist natürlich eine Fotomontage.

Michael Pauly, Chefredakteur


# Eine neue Floppy für den C 64

> Eine Floppy, auf der mehr als ein MegaByte gespeichert werden kann und die zirka viermal schneller ist als die VC 1541, ist ein Traum für viele C 64/VC 20-Besitzer. Die neue Floppy SFD 1002 von Commodore hat jedoch auch ihre Schattenseiten.

Commodore hat ein neues Floppy-Laufwerk herausgebracht. Ihr Name ist SFD 1002. Eigentlich ist sie ja nichts Neues. Wenn man die große CBM 8250 in zwei Hälften teilt, und in ein anderes Gehäuse hineinsteckt, kommt die SFD 1002 heraus. Genauergesagt, die SFD 1001. Der Unterschied zwischen SFD 1002 und SFD 1001 besteht lediglich darin, daß die SFD 1001 mit einem zusätzlichem IEEE -488 Interface geliefert wird, das den C 64 mit der 1001 verbindet. Doch kommen wir zu einigen interessanten technischen Daten der SFD 1001/1002.

Nach dem Formatieren einer Diskette meldet die 1001/1002 fantastische 4133 freie Blöcke. Das entspricht umgerechnet 1033,25 KByte freiem Speicherplatz! Daten werden auf 77 Spuren bei 23 bis 29 Sektoren pro Spur gespeichert. Die Übertragungsgeschwindigkeit beträgt 1,2 KByte/sec (VC 1541 : 0,4 KByte/sec) Auch die Anzahl der gleichzeitig geöffneten Dateien ist gegenüber der VC 1541 höher. Es können gleichzeitig fünf sequentielle oder drei relative oder zwei sequentielle und zwei relative oder drei sequentielle und eine relative Datei geöffnet sein.

Die Tatsache, daß sie voll kompatibel zum CBM 8250 Format ist, bedeutet gleichzeitig deren Unverträglichkeit mit der VC 1541. Lassen sich denn Programme von der 1541 auf die 1002 übertragen?

Sie denken vielleicht: kein Problem. Man ändere einfach die Geräteadresse der VC 1541 auf 9, lädt ein Programm mit LOAD»NAME«,9 und speichere es mit SAVE»name«,8 auf der SFD 1001 wieder ab. Das geht aber nicht. Nicht etwa, daß die SFD 1002 die gewohnten Floppybefehle nicht beherrscht, das macht sie. Der Haken liegt woanders: Der serielle Bus ist gesperrt. Das heißt, es läuft weder die VC 1541 noch ein an den seriellen Port angeschlossener Drucker. Das ist schon ein harter Schlag. Nach einem Gespräch mit einem freundlichen Commodore-Fachmann erhielt ich zwei Tage später ein kleines Programm auf einer Diskette, das dieses Manko etwas lindert. Mit jeweils einem SYS-Befehl kann man auf einen anderen Port umschalten, entweder auf den seriellen oder auf den Expansion-Port. Sie können sich vorstellen, daß das Kopieren einer Diskette auf das SFD 1002 Format zur zermürbenden Prozedur wird.

Dieses Hilfsprogramm soll, so der Spezialist, zukünftig entweder auf der beigelegten Demodiskette gespeichert oder als abzutippendes Listing der Lieferung beigelegt werden.

## Spezialkabel nötig

Ein anderes Kapitel ist das Interface. Zusätzlich zum Interface benötigt man ein Spezialkabel vom Interface zur Floppy und ein anderes von der Floppy zu einem weiteren Peripheriegerät (Kosten pro Kabel: zirka 100 Mark; zusätzlich bestellen). Das Interface selbst besitzt oben einen Schacht, in dem Module eingesetzt werden können. An sich eine lobenswerte Einrichtung. Sie hat jedoch einen kleinen Schönheitsfehler: Sobald man ein Modul hineingesteckt hat, funktioniert nichts mehr. Ein echter Konstruktionsfehler. Auch mit Hilfe einer Steckplatzerweiterung, auf die das Interface und ein beliebiges Modul gesteckt werden, bleibt der Bildschirm dunkel und nichts läuft mehr.

Alles in allem kann ich dieses neue Gerät nicht bedingungslos empfehlen. Die Anpassung an den C 64 ist (noch) nicht optimal gelöst. Und für knapp 2000 Mark sollte man Kompatibilität und Portabilität erwarten können. Aber sicherlich werden dementsprechende Lösungen nicht allzulange auf sich warten lassen. Warten wir’s ab.

(gk)

# COMPUmask

Bei COMPUmask handelt es sich um eine Schablone, die auf den C 64 oder den VC 20 gelegt wird. Auf dieser abtrieb- und reinigungsmittelfesten Schablone sind die am häufigsten vorkommenden Daten, Funktionen, Befehle, Zeichen, POKEs, Tabellen und vieles mehr aufgeführt. Die Oberseite ist zweifarbig, wobei die auf den Bildschirm bezogenen Teile farbig unterlegt sind. So sind über 80 Basic-Befehle, Drucker- und Floppyoperationen, POKEs, Bildschirmausgabezeichen und 3 Demoprogramme zu finden. Diese kleine Übersicht kann nicht alles aufführen, was die Schablone beinhaltet. Für den Preis von 29,80 Mark dürfte die Schablone so für manchen C 64- oder VC 20-Neuling interessant sein, (rg)

Info: IDEE-SOFT, I.Dinkler, Am Schneiderhaus 7, 5760 Arnsberg 1, Tel. 02932/32947

# Komfort-Makroassembler für CBM und VC20/C 64

Für die Commodore-Geräte 3032, 4032, 8032, C 64 und VC20 ist das Makroassembler-Paket ASSI/M und ASSI/MC erhältlich. Es besteht aus drei Programmen, dem Fullscreen-Editor FSE, einem Makroassembler ASM für den 6502 oder — im Paket ASSI/MC - die CMOS CPU 65C02 und dem Debugger DEMON beziehungsweise DEMON/C sowie zwei Makrobibliotheken.

Der Assembler übersetzt von Floppy nach Floppy oder von der Floppy direkt in den Speicher, akzeptiert beliebig lange Sourcefiles (mit Verkettung und include) und kann das Listing auf ein beliebiges Gerät ausgeben oder ganz unterdrücken. Im Gegensatz zu anderen Assemblern kann man (wie zum Beispiel bei Pascal) eine Blockstruktur verwenden. Der ASM unterstützt rekursive Makroaufrufe beliebiger Tiefe sowie bis zu 255 Ebenen der Schachtelung bei bedingter Assemblierung. Weitere Eigenschaften: formatfreie Eingabe, lange Symbol-Namen, 23 Klartext-Fehlermeldungen und eine sehr umfangreiche Arithmetik. Der ASM kann Assemblerprogramme verarbeiten, die vom Basic-Compiler BASS der Firma gmb-Soft erzeugt wurden.

Der Editor FSE verwendet keine Zeilennummern, sondern erlaubt Textmanipulationen wie bei Textverarbeitungssystemen mit 2-Richtungs-Scroll, Blättern, frei definierbarem Tabulator und Rändern, Statuszeile, Such- und Austauschbefehlen mit vielen Optionen, Merker, Blockbefehle, arbeitet mit beliebiger Peripherie, auch Kassette, zusammen und bietet noch viele weitere Möglichkeiten.

Der Debugger DEMON bietet Line-Assemblierung, Disassemblierung, Single-Step (auch durch ROM-Bereiche), überwachte Ausführung ohne Anzeige der einzelnen Schritte, fünf Breakpoints, vollständige Kontrolle bei Trace durch frei programmierbare Überwachungsroutine, Arithmetik und Zahlenumwandlungen, Analyse von Programmen auf Verwendung von Zero-Page-Adressen, Verschiebbarkeit von Programmen und ist selbst voll verschieblich.

Die Makrobibliotheken erlauben die Verwendung von Befehlen für strukturierte Programmierung wie if/ then/else, repeat/until, while/endwhile und switch/ case/default/endswitch sowie von 16-Bit-Befehlen. Das Paket ist auf Disketten im Format 8050 oder 1541/4040 lieferbar und kostet 220 Mark für den 6502 und 250 Mark für den 65C02.

Info: D. Zabel, Stresemannstr. 50, 1000 Berlin 61,Tel. (0 30) 8 22 52 27

# Neue Single-Drive Floppy für Commodore

> Auf dem Markt der 5¼-Zoll-Floppylaufwerke für den C 64 und den VC 20 ist ein neuer Konkurrent aufgetaucht. Er heißt YL-55SU-CM. Auch ein neues Kassettenlaufwerk wird angeboten.

Diese neue Floppy ist mit einem Teac-Laufwerk ausgestattet, das für seine Zuverlässigkeit bekannt ist. Es ist voll kompatibel zur VC 1541. Das bedeutet, daß mit der VC 1541 bespielte Disketten auch von der neuen Floppy gelesen werden können. Die Geschwindigkeit, die mit diesem Laufwerk erreicht werden könnte, würde das Herz eines jeden VC 1541-Geschädigten höher schlagen lassen. Wenn da nicht noch das Commodore-kompatible DOS wäre. So bringt diese neue Floppy in diesem Punkt keinen Vorteil gegenüber der VC 1541. Laut Hersteller wird aber daran gearbeitet, die Geschwindigkeit, mit der das Laufwerk arbeitet, zu verbessern. Diejenigen, die sich die neue Floppy schon jetzt kaufen möchten, können später das alte DOS gegen einen geringen Aufpreis austauschen lassen. Doch die Übertragungsgeschwindigkeit bei einer Floppy ist nicht alles. Wer die Reparaturanfälligkeit der Commodore-Floppy kennt, wird ein zuverlässigeres Laufwerk schätzen. Der empfohlene Verkaufspreis liegt bei 798 Mark.

## 99-Mark-Recorder

Der Anbieter der neuen Floppy bringt auch ein Alternativprodukt für die Datasette auf den Markt. Das äußerlich ansprechende Produkt wird zum empfohlenen Richtpreis von 99 Mark erhältlich sein.

Info: Bezugsquelle: WM-Computer, St.-Anton-Str.31, 4150 Krefeld 1, 02151/801300 und Hertie.

# Commodore-Messe in Frankfurt

Vom 4. bis 8. September findet in der Halle 1 des Frankfurter Messegeländes die vierte »Internationale Commodore-Fachausstellung (CFA)« statt. Etwa 120 Aussteller präsentieren Hard- und Software rund um den Commodore. Laut Commodore werden beide Schwerpunkte berücksichtigt: kommerziell/professionelle Anwendungen und der Hobby-Bereich. Für »Freaks« gebe es eine spezielle Hard- und Softwarebörse, auf der Commodore-Computer und -Programme verkauft oder getauscht werden können. Übrigens: Die Redaktion des 64’er-Magazins steht während der CFA für Gespräche ihren Lesern zur Verfügung (Stand: Markt & Technik).

(kg)

# Computer-Bücher von Commodore

Bedienungshandbücher, die beim Kauf eines Computers mitgeliefert werden, sind oftmals nicht mehr als eine relativ lückenhafte Gebrauchsanweisung. Commodore will diese Lücken mit ihrer neuen Sachbuchreihe füllen. Bislang sind fünf Bände erschienen. Band 1: Alles über den Commodore 64 (59 Mark); Band 2: Alles über den VC 20 (24,90 Mark); Band 3: Logo, nur mit der Software erhältlich, Buch in deutsch, Programm in englisch (zusammen 159 Mark); Band 4: Das C 64-Spielebuch (29,80 Mark); Band 5: Das VC 20 Spielebuch (29,80 Mark). Die Reihe soll kontinuierlich fortgesetzt werden.

(kg)

# Modem als Bausatz

Als fertiges Gerät oder als Bausatz ist dieses neue Modem preiswert zu beziehen. Es hat allerdings keine FTZ-Nummer. Der Bausatz soll zirka 260 Mark kosten, das fertige Gerät dürfte um etwa 100 Mark teurer sein. Zirka 220 Einzelteile müssen Sie zusammenschrauben beziehungsweise löten, bevor Sie das Modem einsetzen können. Dann sollten Sie ein voll einsatzfähiges Gerät haben, das alle Voraussetzungen eines professionellen Modem besitzt.

Bezugsquelle: Software Express, Hugo-Vichoff-Str. 84, 4000 Düsseldorf 30

# Leserforum

Probleme mit Datasette?

Ich habe andauernd »LOAD ERROR« trotz Kassettenwechsel und einwandfrei justiertem Lese- und Aufnahmekopf der Datasette. Kann es am C 64 liegen? Wer kann helfen?

Peter Ritter

Schwierigkeiten mit Farbfernsehen und Interface?
Ich besitze einen C 64 und das Kassetteninterface von K. Jeschke. Früher hatte ich einen Schwarzweiß-Fernseher und das Interface arbeitete einwandfrei. Seit kurzem besitze ich einen kleinen Farbfernseher, doch jetzt tritt ein Problem auf. Das Speichern funktioniert weiterhin einwandfrei, doch beim Laden muß ich jetzt immer erst den Antennenstecker aus dem C 64 ziehen und Programme blind einladen, weil bei angeschlossenem Fernseher das Relais im Interface verrückt spielt und das Einladen nicht funktioniert. Woran kann die Unverträglichkeit zwischen Fernseher und Interface beim Laden liegen?

Andreas Heine

Das Problem liegt wahrscheinlich in einer mangelhaften Abschirmung des HF-Signals in Ihrem Fernseher. Mögliche Abhilfe: Standort des Interfaces verlagern, Anschlußkabel verdrillen. Besser abgeschirmtes Kabel vom Fernseher zum C 64 verwenden (75 Ohm Antennenkabel).

Probleme mit unseren Listings?

Was bedeuten im 64’er, Ausgabe 5, Seite 112 in Zeilennummer 50000 das Zeichen »^« und in Ausgabe 7 auf Seite 70 (Supervoc) in Zeile 420 IFA$=»T« das reverse T und wie gibt man dieses Zeichen ein? Gibt es einen Ersatz dafür?

Stefan Rolfes

Leider haben wir unseren Epson FX80 noch nicht dazu gebracht, sämtliche Zeichen des Commodore zu drucken. Vor allem bei dem Pfeil nach oben und Pfeil nach links weigert er sich bisher, sie richtig auf das Papier zu bringen. Der »^« bedeutet also Pfeil nach oben.

Das oben erwähnte reverse T steht für die DEL-Taste. Man kann das Zeichen so eingeben: ""(DEL)(INST)(DEL)". Also zuerst zwei Anführungszeichen, danach die DELete-Taste, die In-sert(INST)-Taste, wiederum die DELete-Taste und zum Schluß noch einmal ein Anführungszeichen. Allerdings kann man die DEL-Taste auch so abfragen: IF A$ = CHR$(20) THEN...

Programme direkt vom Fernseher?

Wie kann man die Datasette VC 1530 für direkte Aufnahme von Computer-Programmen vom Fernseher (Video-Recorder) umrüsten (siehe Computer-Club-Sendungen und so weiter)?

Wölfgang Schulte

Daten speichern ohne Datei zu laden?

Wie kann ich Daten auf Diskette speichern, ohne die Datei zu laden, umzuändern und neu zu speichern (das ist mir zu umständlich)?

The Dynamike, Emden

Mit einer relativen Datei ist das ohne Schwierigkeiten möglich. In Ausgabe 6/84 wurde sie ausführlich beschrieben. Und wem diese Methode noch zu umständlich erscheint, weil ja noch das Programm geladen werden muß, kann sich dieses Programm ja auf EPROM brennen. Dann genügt ein Einstecken des Moduls in den Expansionsport, Computer einschalten und schon können die ersten Daten am Bildschirm bearbeitet werden.

Rechenungenauigkeiten beim C 64?
Warum gibt der C 64 als Ergebnis der Aufgabe PRINT INT(3/0.03) nicht 100, sondern 99 an? Das gilt auch, wenn man schreibt A%=INT(3/0.03) und dann PRINTA%.

Oliver Treiber

Hardcopies mit MPS 802 und Simons-Basic?

Wir haben den C 64 und den Drucker MPS 802 (Nachfolgegerät vom VC 1526), dazu Simons Basic. Ist es möglich, im Hires- beziehungsweise Low-col-Modus eine Kopie des Bildschirms zu erstellen?
Gerhard Schief
Das könnten Sie ja eigentlich selbst ausprobieren. Aber wenn Sie mit dem Befehl HRDCPY keine Hardcopy des normalauflösenden Bildschirms erhalten sollten, könnte der Drucker defekt sein. Eine Hardcopy des hochauflösenden Grafikbildschirms hingegen ist mit dem Simons-Basicbefehl COPY nicht möglich. Das gilt auch für den weitgehend baugleichen VC 1526.

Apple Joystick an C 64?

Gibt es ein Interface, das es ermöglicht, Apple-Joysticks an den Commodore 64 anschließen zu können? Alle Spiele, die für die Ports 1 und 2 geschrieben worden sind, sollten steuerbar sein.

Frank Zündorff

Erhöhte Lebensdauer bei Dauerbetrieb?

Wie lange kann man den C 64 laufen lassen, ohne daß er Schaden nimmt?

Burchard Laasch

Es gibt Computer-Benutzer, die ihren Computer niemals abschalten. Er läuft dort jahrelang, ohne das deswegen ein Defekt auftritt. Sie begründen das damit, daß bei jedem Ein- und Ausschaltvorgang die elektronischen Bauelemente warmwerden und wieder abkühlen. Da in vielen Bauelementen verschiedene Materialien verarbeitet werden, die sich bei einer Temperaturänderung unterschiedlich ausdehnen, können Spannungen auftreten. Diese andauernden thermischen Belastungen könnten die Lebensdauer vor allem der empfindlichen Halbleiter herabsetzen. Bei einem Dauerbetrieb treten diese Belastungen nicht auf. Wenn für ausreichende Belüftung gesorgt wird und der Computer nicht noch zusätzlich auf einer Heizung abgestellt wird und vor direkter Sonneneinstrahlung geschützt ist, dürften keine Probleme entstehen.

Darf man überhaupt eine Diskette in das Laufwerk legen?

Als wir uns mit dem deutschen und dem englischen Handbuch zur 1541 befaßten, stießen wir auf einige Widersprüche in bezug auf die Handhabung:

1.	Im englischen Handbuch wird auf Seite 8 unten ausdrücklich darauf hingewiesen, daß beim Leuchten der grünen LED nie eine Diskette ins Laufwerk hineingeschoben oder aus ihm hinausgenommen werden darf. Im deutschen Gegenstück ist jedoch auf Seite 5 Mitte zu lesen, daß auch im ausgeschalteten Zustand der Floppy keine Diskette darin sein darf.
2.	In der deutschen Fassung des Handbuches wird gesagt, daß erst der Computer, dann das Laufwerk eingeschaltet werden soll. Die Autoren des englischen Handbuches vermerken ausdrücklich auf Seite 7, daß man nie den Computer zuerst anschalten darf, da sonst nicht »everything OK« ist. Deshalb unsere Fragen:

a) Darf man überhaupt eine Disk ins Laufwerk legen?
b) Bei welcher Reihenfolge des Einschaltens ist denn »everything OK«?

Zusammenfassend: Welches der Handbücher ist maßgeblich oder kann man beide nicht ernst nehmen?

Gregor Fromme, Justus de Zeeuw

## VC 20/C 64-Tips

Manche Leserfrage zeigt deutlich, daß man doch von Zeit zu Zeit einen Blick in das mitgelieferte Handbuch werfen sollte. Auch wenn dieses Handbuch beim VC 20 nicht eben reichhaltige Informationen liefert, kann man doch auf der Seite 134 nachlesen, was Poke 36879,25 bedeutet. Mit diesem Befehl wird sowohl der Bildschirmrahmen als auch der -hintergrund auf die Farbe Weiß umgestellt. Selbstverständlich laufen Programme auch bei anderen Farbkombinationen (beim Einschalten Weiß/Hellblau) genauso gut. Wenn der Bildschirm bei R. Morgenthaler bei weißem Hintergrund ins Flackern gerät, so liegt das entweder am verwendeten Fernseher/Monitor, dann sollten Bildhelligkeit oder Kontrast etwas heruntergedreht werden. Ansonsten kann der Fehler nur im HF-Modulator liegen. Der Modulator muß dann vom Commodore-Systemhändler neu an den Computer angepaßt werden.

Wenn das Gerät auf dem grauen Markt gekauft wurde, dürfte sich das schwieriger gestalten. Ein Computer ist eben kein Gebrauchtwagen, der in jeder Hinterhofwerkstatt getestet werden kann. Hier hilft nur eines: Auf dem schnellsten Weg zum Fachhändler zu gehen und zu hoffen, daß der auch nicht bei ihm gekaufte Geräte einstellt (Selbstversuche rächen sich gerade beim HF-Modulator). Ebenso schnell sollte R. Morgenthaler das Handbuch zum VC 20 oder ein anderes Begleitbuch (die von Data Becker sind hilfreich, das von Hofacker weniger) anschaffen.

Die beiden anderen Fragen kann man zusammen beantworten. Der VC 20 läßt sich an einem gewöhnlichen Farb- oder S/W-Fernseher ohne Scart-Buchse nur mit dem HF-Modulator betreiben. Für den Betrieb mit einem Monitor oder einen Fernseher mit Spezial-(Scart)Anschluß braucht man ein Monitor-Kabel, das es für den Commodore-Farbmonitor bei jedem Systemhändler gibt. Da ich den Nordmende-Anschluß nicht kenne, kann ich nur den Rat geben, bei einem der Hardware-Drittanbieter (Data Becker oder Kingsoft etc.) oder bei Commodore Deutschland (Lyoner Str. 38, 6000 Frankfurt/M 71) anzufragen. Dort wird man gerne weiterhelfen. Ich bin gerne bereit, anderen VC 20-Anwendern — soweit ich kann — weiterzuhelfen. Meine Adresse: Adenauerallee 19, 5300 Bonn 1. Wer mir schreiben will, muß allerdings einen frankierten Rückumschlag beilegen.

Hans Altmeyer

Zur Frage von Günther Kyora: Der Anschluß von Commodore VC 20 und C64 an Fernseh-Empfänger mit Scartbuchse oder Videobuchse nach DIN ist nach folgendem Schaltplan vorzunehmen: VC 20:

Zu der punktierten Leitung: Manche Fernseh-Geräte haben einen Schalter zum Umschalten auf Monitorbetrieb (siehe Bedienanleitung). In diesem Fall kann die Verbindung entfallen. Andernfalls ist eine Schaltspannung von zirka 12 V zum Umschalten erforderlich. Dazu ist eine kleine Änderung im Computer erforderlich.

Am VC 20: Durch Umlöten von zwei Lötbrücken (E1-E3 unterbrechen, E1-E2 verbinden) wird Pin 1 des Video-Audio-Ports mit zirka 10 V belegt (vorher 5 V). Der Modulator kann nun nicht mehr ohne Änderung benutzt werden (5 V Regulator einbauen).

Am Commodore 64: Bei neueren Geräten ist eine 8polige DIN-Buchse als Video-Audio-Port eingebaut. Pin 6 bis 8 sind nicht belegt. Hier kann ein freier Anschluß (zum Beispiel 7) mit dem Ausgang des 12-V-Regulators Vr 1 des Computers verbunden werden. Bei Geräten mit 5poliger Buchse muß die Leitung direkt herausgeführt werden.

Manfred Lösch

---

Starten und Speichern von Spielprogrammen beim Commodore 64

Wenn ich ein Spielprogramm von Kassette geladen habe, starte ich es normalerweise durch die Eingabe des Wortes RUN nebst Drücken der RETURN-Taste. In einigen Fällen funktioniert das nicht, aber ich habe bisher folgende Verfahren kennengelernt:

1.	Eingabe von SYS mit Adreßzahl, wobei die Adreßzahl im meist nur einzeiligen LIST-Ausdruck steht.

2.	Eingabe von SYS 64738 und dann erst SYSmit der Adreßzahl aus dem Listing.

3.	Eingabe von SYS mit Adreßzahl, die nicht im Listing steht (wie kann ich diese finden, wenn ich sie nicht kenne oder vergessen habe?)

4.	Löschen der Programmzeilen mit SYS-Angaben.

5.	Drücken derRUN/STOP- und RESTORE-Taste.

Mich interessiert, wie diese Startroutinen zu erklären sind und ob sie bei einem neuen Abspeichern des Programmes zu eliminieren sind. Häufig kann man aus einem Spielprogramm nicht in den Normalzustand zurückkehren. Mir bleibt dann nichts anderes übrig, als den Commodore ab- und wieder einzuschalten. In manchen Fällen erscheint nach Drücken von RUN/STOP und RESTORE auf leerem Bildschirm das Wort READY und darunter der blinkende Cursor, aber nach Eingabe von Befehlen wie LOAD oder RUN wird nur die Eingabe gelöscht, und der Cursor springt zurück. Was bedeutet das? Wie kann ich hier den Commodore wieder zu sinnvoller Reaktion veranlassen?
Manchmal passiert mir folgendes: Ich möchte ein Spielprogramm von Kassette auf einer anderen Kassette abspeichern. Obwohl das Programm mit Namen auf der Kassette ist, kann ich es mit diesem Namen nicht saven. Der Commodore zeigt einen Error an. Lasse ich den Namen weg, funktioniert das Abspeichern einwandfrei. Wie ist das zu erklären und wie kann ich in solchen Fällen den Namen doch mitspeichern?

Werner Kiefert

Zu den Fragen zum Starten von Programmen:

1.	Hier handelt es sich um ein Maschinensprache-Programm, an das vorher eine Basic-Zeile gehängt wurde, die mit dem entsprechenden SYS-Befehl den Maschinenspracheteil startet. (Der Speicher des C 64 ist aufgeteilt in die Speicherzellen 0 bis 65535. In einer dieser Speicherzellen liegt der Beginn des Maschinenprogramms. Mit dem SYS-Befehl und der Angabe der Speicherzelle, wo das Maschinenprogramm beginnt, wird es gestartet.)

2.	Wenn man erst mit SYS 64738 den Computer in den Einschaltzustand bringt und dann den entsprechenden SYS-Befehl aus dem Listing eingibt, müßte eigentlich das gleiche herauskommen, wie wenn man den SYS 64738 wegläßt. Hier hat Ihnen jemand Humbug erzählt oder Ihnen ein ziemlich verpfuschtes Programm gegeben.

3.	Hier wurde ein Maschinenspracheprogramm abgespeichert, ohne eine Basic-Zeile mit dem entsprechenden SYS-Befehl vornedranzuhängen. Die Adresse für den Start des Programms läßt sich am besten so finden:

  * Maschinensprache lernen
  * Maschinensprache-Monitor laden
  * SUCHEN

4.	Ist uns nicht bekannt.

5.	Der sogenannte Restore-Vektor wurde vom Programmierer geändert, das heißt bei Drücken von RUN/STOP-RESTORE wird nicht mehr die normale Betriebssystem-Routine gestartet, sondern es wird zu der Adresse gesprungen, die der Programmierer angewählt hat, in diesem Fall die Startadresse des Programms.

Zur Frage, die das Zurückkehren aus Spielprogrammen in den Normalmodus betrifft:

Das war offensichtlich Absicht der Programmierer der Spiele (aus welchem Grund auch immer). Hier hilft meistens wirklich nur das Aus- und Anschalten des Computers.

Antwort auf die Frage, die das Speichern von Programmen betrifft:

Hier reicht offensichtlich der Speicher nicht mehr aus, um den Namen dort abzulegen. (Der Fehler ist dann wohl ein OUT OF MEMORY ERROR.) Man kann sich jedoch manchmal abhelfen, indem man den Variablenspeicher in einen freien Speicherbereich verlegt:
LOAD »Programm«
POKE 56,207
CLR
SAVE»Name«

Für das Funktionieren dieser Maßnahme kann nicht garantiert werden, da es doch immer sehr auf das einzelne Programm ankommt.

(gk)


Probleme mit Speichererweiterung

Frage: 3-KByte-Spiele funktionieren nicht mit dem 16-KByte-Modul?

Daniel Hüller
Ausgabe: 7/84

Programme, die für eine 3-KByte-Erweiterung gedacht sind, laufen auf dem VC 20, wenn man bei eingesteckter 16-KByte- und 3-KByte-Erweiterung (Modulbox) folgende Zeile im Direktmodus eingibt:
POKE 44,4: POKE 1024,0: POKE 56,30: POKE 648,30: NEW (RETURN). Nach Drücken der RE-TURN-Taste verschwindet der Cursor. Jetzt sind RUN/STOP und RESTORE zu drücken. Durch Eingabe von SYS 58238 erscheint das Anfangsbild und die Meldung: 6655 Bytes Free. So spart man sich das lästige Umstecken der Erweiterungen.

Oliver Eichhorn

»Alte« 64’er-Ausgaben

Bitte schicken Sie mir (gegen Nachnahme) Kopien des Kurses Grafikgrundlagen Teil 1 und Teil 2, da ich die entsprechenden 64’er-Ausgaben nicht mehr bekommen kann.

Martin Tobrock

Solche oder ähnliche Fragen werden nicht selten gestellt. Leider können diese Fragen nur noch negativ beantwortet werden. Alle Ausgaben 4, 5 und 6 sind mittlerweile ausverkauft! Aber wir geben auch ein Trostpflaster: Gegen Ende desJahres werden wir eine Sonderausgabe des 64'er herausbringen, in der unter anderem sämtliche bis dahin abgeschlossenen Kurse noch einmal veröffentlicht werden.

Ohne Kommentar

Ich habe da ein Programm, das heißt »Digi-Uhr«. Es macht aus dem C 64 nichts weiter als eine Digitaluhr, deren Zeitanzeige dann auf dem Bildschirm erscheint. Ich habe es geschenkt bekommen und viel mehr ist es wohl nicht wert. Es ist schade um die Mühe, die der unbekannte Programmierer sich damit gemacht hat. Denn das ist doch ein schlechter Witz: Eine Digitaluhr, deren Ganggenauigkeit sehr zu bezweifeln ist, für sage und schreibe 1750 Mark (Rechner plus Floppy plus Fernseher).

Eine drahtlose Nebenstelle der Braunschweiger Atomuhr bekommt man als Bausatz für 400 Mark. Und nun kommt in Ihrer Zeitung der zweite Witz dieser Art. — Das Blumengießen mit dem Commodore. Also wissen Sie, mit einer Billigschaltuhr und einem Verzögerungsrelais wäre es nämlich auch gegangen und dann auch noch so einfach, daß es jeder halbwegs begabte Schuljunge zusammenlöten kann!

Kommen wir nun zum Thema Spiele und als Aufhänger dazu diene uns der Q-Bernd. Da haben wir wieder mal eines der unzähligen Spiele, bei denen es mir einfach unbegreiflich ist, was deren Urheber wie Konsumenten eigentlich daran finden. Von vornherein steht fest, daß kein Erfolg möglich ist. Q-Bernd und mit ihm der Spieler sind auf der Verliererstraße.

Man verlange doch mal von einem gewöhnlichen Menschen, er solle auf einem Drahtseil einen Teich überqueren. Man sage ihm weiter, daß er nicht nur kein Geld dafür bekommt, sondern stattdessen auch noch bezahlen muß. Und man sage ihm weiter, daß man alles tun wird, um ihn da runterzuschmeißen, zum Beispiel das Seil mit Seife einschmieren, Windmaschinen aufzustellen und dergleichen. Er wird sich an die Stirn tippen und recht hat er. Aber man gebe ihm ein Computerspiel, bei dem er ebenfalls absolut keine Chance für ein Erfolgserlebnis hat und er wird zahlen und spielen und spielen und spielen — das begreife ich nicht. Mir hat man mal ein Spiel namens »Snokie« angeboten. Als der arme Vogel zum fünften Male auf die Schnauze fiel und starb, habe ich mir an die Stirn getippt und den Verkäufer gefragt, ob er mich für blöd hält. Genauso bescheuert finde ich Pacman, der kaum über die erste, aber ganz bestimmt nicht über die zweite Runde kommt. Und falls es doch ein Computerfreak schafft, sollte es mich nicht wundern, wenn der elektronische Heini dann eine Spielstufe zulegt und es ist wieder Essig. Ich habe sogar mal ein Programm erlebt, in dem der Computer jedesmal, wenn er den Spieler ausgetrickst hatte, auch noch höhnisch auf dem Bildschirm triumphierte »Got You!« In die Mentalität derer, die sowas machen, kann ich mich noch hineindenken: Sie treten gegen die Spieler an und wollen sich von diesen nicht schlagen lassen. Nur vergessen sie, daß sie sich dabei eines gewaltigen Verbündeten bedienen. Dem User bleibt so keine Chance.

Was aber sind das für Leute, die sowas benutzen? Ein normaler Mensch strebt doch nach Erfolgserlebnissen? Wer kauft sich eigentlich Mißerfolgserlebnisse oder tippt sie mühsam ein? Wie erfreulich ist doch dagegen so ein Spiel wie »Jawbreaker«, wenn man es mal wieder geschafft hat und es kommt die Zahnbürste! Und warum gibt es fast keine Spiele, bei denen zwei oder mehr Spieler gegeneinander auf dem Computer spielen, statt abwechselnd gegen den Computer, wo sie dann abwechselnd verlieren? Es war doch immer der Reiz des Spieles, zu gewinnen oder zu verlieren. Aber gegen einen Computer? Der dämliche Kerl ärgert sich doch nicht mal, wenn er wirklich verliert! Gerade das aber sollte man den Spielemachern als Tip geben: Der Computer muß auch von Anfängern zu besiegen sein und wenn man es mal geschafft hat, muß eine Printzeile ins Programm:
»Scheiße! Komm du mir noch mal ans Keyboard!«

Nun zu dem Programm »Programm-Verwaltung«. Unter dem Namen kann man es natürlich nicht abspeichern, der ist zu lang. Wie wäre es mit »Filister«? Auf jeden Fall sollten Sie auf etwas hinweisen: In den Zeilen 2150 und 1520 findet man jedesmal einen Paragraphen §, der auf der C 64-Tastatur gar nicht vorkommt und den ich auch nur dank Beckers Textautomat jetzt schreiben kann. Mir ist erst nach geraumer Grübelei aufgegangen, daß er dort stellvertretend für den Klammeraffen steht.

Zu dem Programm hätte ich aber noch einiges zu sagen. Zunächst einmal grundsätzlich: Ich verstehe leider bitterwenig vom Programmieren und vieles in dem Programm ist mir glattes Chinesisch. Wenn ich jetzt Wünsche oder Verbesserungsvorschläge habe, so sei damit nichts gegen den Autor gesagt, denn ich weiß nicht, ob das, was ich gern hätte, machbar ist und ob es schwierig ist. Ein solches Programm fehlt mir schon lange, aber: Man müßte eingeben können, auf welcher Disk diese Files stehen, ob auf 12A oder 7B. Das wäre gewaltig, so aber muß man immer noch die Directory-Ausdrucke durchgeben, wenn man mal eins sucht.

Weiter: Der G 64 ist damit fürchterlich langsam. Um 165 Files alphabetisch zu sortieren, hat er etwa eine Stunde lang gebrütet. Das hätte ich nun selber schneller gekonnt. Da wünschte ich mir, daß der Computer sich akustisch meldet, daß er piept oder hupt, wenn er fertig ist oder pfeift wie ein Teekessel.

Heinrich Carstensen

Wollen Sie antworten?

Wir veröffentlichen auf dieser Seite auch Fragen, die sich nicht ohne weiteres anhand eines gutes Archivs oder aufgrund der Sachkunde eines Herstellers beziehungsweise Programmierers beantworten lassen. Das ist vor allem der Fall, wenn es um bestimmte Erfahrungen geht oder um die Suche nach speziellen Programmen beziehungsweise Produkten. Wenn Sie eine Antwort auf eine hier veröffentlichte Frage wissen - oder eine andere, bessere Antwort als die hier gelesene - dann schreiben Sie uns doch. Die Antworten werden wir in einer der nächsten Ausgaben publizieren. Bei Bedarf stellen wir auch den Kontakt zwischen Lesern her.


# Tips für den Umgang mit Sinnbildern von Programmablaufplänen

Für jemanden, der noch nichts mit Programmablaufplänen zu tun hatte, ist es meist sehr schwer, seine Ideen und Programme in Form von Programmablaufplänen darzustellen. Deshalb nun einige Tips, für den Umgang mit Programmablaufplänen.

1.	Operation: Dieses Sinnbild wird für Berechnungen, Zuweisungen und so weiter verwendet, ausgenommen für diejenigen Operationen, für die ein spezielles Sinnbild vorhanden ist.

2.	Verzweigung (Entscheidung): Das Sinnbild hat einen Eingang und zwei Ausgänge. Je nachdem ob die Bedingung, die im Sinnbild angegeben ist, erfüllt ist, wird der Programmlauf bei dem einen oder anderen Ausgang fortgesetzt. Man sollte die Ausgänge mit ja oder nein (+ oder —) kennzeichnen, um zu verdeutlichen, welcher Ausgang benutzt wird, wenn die Bedingung erfüllt ist oder nicht.

3.	Unterprogramm: Häufig benutzte Programmteile, die an verschiedenen Stellen des Programms benötigt werden, führt man meist als Unterprogramme aus. Im Programmablaufplan wird immer dann das Zeichen für ein bestimmtes Unterprogramm eingesetzt, wenn es benötigt wird. Wie Unterprogramme im einzelnen aussehen braucht man nur einmal gesondert aufzuführen.

4.	Programmodifikation: In vielen Programmen taucht das Bedürfnis auf, bestimmte Veränderungen an Indexregistern vorzunehmen, zum Beispiel: Abschalten der Tastatur oder Wahl eines anderen Zeichensatzes. Diese Veränderungen werden in Basic meist durch Poke-Befehle bewirkt. Am Sinnbild sollte deshalb ein sehr ausführlicher Text angebracht sein, aus dem deutlich hervorgeht, was ein derartiger Eingriff im Einzelnen bewirkt.

5.	Operation von Hand: Bei manchen Programmen ist es notwendig, daß der Bediener persönlich eingreift. Am Sinnbild sollte deshalb genau erläutert werden, welche Tätigkeiten vom Bediener ausgeführt werden müssen.

6.	Eingabe, Ausgabe: Aus der Beschriftung des Sinnbildes sollte außerdem deutlich hervorgehen, was durch wen und welche Geräte ein-beziehungsweise ausgegeben werden soll.

7.	Ablauflinie: Die Ablauflinie ist ein einfacher durchgehender Strich, der die Sinnbilder verbindet. Wenn es nicht ganz deutlich ist, wie die Ablaufrichtung verläuft, sollte sie durch Pfeile markiert werden.

Zusammenführung: Eine Ablauflinie, die in eine andere Ablauflinie einmündet, nennt man Zusammenführung. Um die Ablaufrichtung deutlich zu machen, empfiehlt es sich, Pfeile anzubringen.

8. Übergangsstelle: Damit es nicht zu einem chaotischen Wirrwarr an Ablauflinien kommt, empfiehlt es sich, Übergangsstellen einzusetzen. Zusammengehörende Übergangsstellen müssen die gleiche Bezeichnung tragen (siehe auch Beispiel 2).

9. Grenzstelle: Mit diesem Zeichen bezeichnet man den Beginn oder das Ende von Programmen und Unterprogrammen. Es wird damit deutlich gemacht, wo ein bestimmter Ablauf beginnt oder endet.
10. Bemerkung: Mit diesem Sinnbild sollte man nicht zu sparsam umgehen. Man kann damit jedem Sinnbild beliebig viele zusätzliche Informationen anfügen.

(B. Appel/rg)

# DOS 5.1 – Teil 2

> Das interessante Programm DOS 5.1 auf Ihrer Demo-Diskette bietet noch mehr als wir bisher gedacht hatten. Einige Leser schrieben uns: Sie entlockten dem DOS noch einige bemerkenswerte Geheimnisse. Außerdem wird das Programm noch um einige Befehle erweitert, zum Beispiel durch Merge.

Wie schon in der Ausgabe 5/84 des 64'er-Magazins berichtet (»Wie bitte, Sie besitzen ein tolles Programm und wissen es gar nicht?«), gab es zum DOS 5.1 nur sehr wenig Literatur. Daraufhin setzten sich einige Tüftler hin und versuchten anhand eines Assemblerlistings, ihm seine Geheimnisse zu entlocken. Einer von Ihnen ist Herbert Heise. Sein Bericht steht stellvertretend für alle anderen Zusendungen, die wir erhalten haben. Doch lesen Sie selbst.

### Geheimnisvolles DOS

Ich würde diesen Beitrag über das DOS gern fortsetzen und durch drei Programme abrunden. Denn das DOS hat noch folgende nützliche Eigenschaften:
(1)	%NAME bedeutet, ein Maschinenprogramm absolut laden.
(2)	@#9 ändert die Geräteadresse des DOS in 9.
(3)	@Q schaltet das DOS ab.
(4)	@$:*=PRG listet nur PRG-Files.
(5)	Das Auslisten mit @$ läßt sich über Space steuern.
(6)	DOS-Befehle funktionieren auch im Programmbetrieb.

Als ich mir das Diskettenlaufwerk gekauft hatte, wußte ich mit dem DOS wenig anzufangen. Dies liegt wohl hauptsächlich an der mangelnden Beschreibung im Handbuch. Mit der Zeit erfuhr ich durch Zufall und durch Bekannte, daß hinter dem DOS doch mehr steckt. Ich wurde neugierig und schaute mir das DOS genauer an. Damit das besser ging, erstellte ich mir zum DOS zuerst ein Assemblerlisting. Ich habe es gelesen und versucht, es zu verstehen. Was ich dabei herausgefunden habe, möchte ich hier beschreiben.

Später werde ich ein Programm 1 vorstellen, das es vereinfacht, das DOS zu kopieren.

Ein Programm 4 wird den Namen (=Einschaltmeldung) ändern.

Zum Schluß erweitere ich das DOS um den MERGE-Befehl. Über »+« kann damit ein Programm zugeladen werden.

Ich empfehle, zuerst das DOS zu laden.

### Erklärung der Befehle /,↑,%

Das DOS erlaubt, ein Programm auf drei verschiedene Arten zu laden.

Um die Beschreibung etwas zu vereinfachen, werde ich die Programme, die ich laden will, einfach »Test« nennen. Normalerweise soll ein Basicprogramm geladen werden. Über Basic gebe ich »LOAD ” TEST ”,8« ein. Beim DOS erspart man sich die Anführungszeichen und schreibt ganz kurz: /TEST. Soll nach dem LOADING sofort ein RUN ausgeführt werden, schreibt man einfach ↑ TEST.

Die dritte Möglichkeit besteht darin, ein <b>Maschinenprogramm absolut zu laden</b>. Da dies seltener vorkommt, wird dies meist verschwiegen. In Basic lautet der Befehl LOAD ” TEST ”,8,1.

Geschieht dies im Direktmodus, so teilt mir der Computer bald sein OUT OF MEMORY mit und ich muß ein NEW eingeben. Dies wird beim DOS mit %TEST vermieden. Um diesen Befehl testen zu können, wird natürlich ein Maschinenprogramm benötigt. Das DOS ist zwar ein solches, versucht man es aber mit zum Beispiel %DOS so erhält man eine  Fehlermeldung. Diejenigen, die von Data Becker »Profimat« oder »Profiass« besitzen, können dies damit probieren.

### Ein Tip am Rande

Man spart sich Tipparbeit, wenn man sich mit @$ das Inhaltsverzeichnis auf den Bildschirm holt. Danach fährt man mit dem Cursor hoch zum gewünschten Programmnamen und drückt die Tasten »/«, »↑«, »%« oder »←« und ein RETURN. Schon erscheint ein LOADING beziehungsweise SAVING des Programms.
Wer der Meinung ist, das DOS läßt sich nur mit einer Floppy einsetzen, den kann ich jetzt eines Besseren belehren. Soll das DOS zum Beispiel mit einem Kassettenrecorder arbeiten, genügt die Eingabe »@ # 1«. Dadurch adressieren wir Gerät 1. Es können nun die Abkürzungen /,↑,% benutzt werden. Natürlich kann man mit @ keinen Fehlerkanal lesen. Da nach jedem SAVE-Befehl mit »←« versucht wird, diesen zu lesen, kann auch diese Abkürzung nicht verwendet werden.

## DOS 5.1 arbeitet mit Disk oder Kassette

Die Glücklichen, denen zwei Diskettenlaufwerke zur Verfügung stehen, wählen zum Beispiel über: @#9 ihre Station aus.

### Anmerkungen:

Die Geräteadresse wird beim Aufruf mit »SYS 52224« festgelegt. Das DOS nimmt sich dabei den Wert aus derSpeicherstelle 186(=$ba). Demnach wird das Gerät adressiert, von dem das DOS geladen wurde.

Sicher kennen viele den ’RESET-Befehl' über ’SYS 64738’. Damit bringt sich unser Rechnergenie in den Einschaltzustand. Soll das DOS danach wieder arbeiten, müssen wir ihm die richtige Gerätenummer zuweisen (zum Beispiel @ # 8).

Wer hätte das gedacht: Das DOS kann sich abschalten. Die Syntax lautet »@Q«. Eine Kontrolle mit dem Klammeraffen »@« ergibt SYNTAX ERROR.
Dies ist nützlich bei Programmen, die sich mit dem DOS nicht vertragen wollen. Beispielsweise tun dies Simons Basic und manche BACKUP-Programme nicht. Natürlich kann ersatzweise auch kurz der »Saft« abgedreht werden (das heißt Computer ausschalten).

### DOS und das Inhaltsverzeichnis

Die Diskette hat viele Vorteile, unter anderem wird auf dieser automatisch ein Inhaltsverzeichnis angelegt. Dieses ist als Programm »$« gespeichert. Man kann es also über LOAD"$", 8 laden und mit LIST anschauen. Das DOS bietet diesen Befehl auch an. Er lautet »@$«. Dabei wird ein eventuell vorhandenes Programm nicht überschrieben. Zusätzlich kann das Auslisten gestoppt werden. Es genügt ein Druck auf die SPACE-Taste und das DOS verweilt in einer Warteschleife. Ein zweiter Tastendruck veranlaßt das DOS weiterzuarbeiten. Komfortabel wird das Ganze dadurch, daß man unter den Programmnamen auswählen kann. Dies geschieht durch Angabe von »*« oder »?«. Eine dritte Möglichkeit erlaubt Filetypen zu unterscheiden. »@$:*=PRG« listet alle vorhandenen PRG-Files aus. Entsprechendes gilt für »@$:T?S=SEQ« und »@$:TES*=USR«.

### DOS innerhalb von Programmen

Aus dem Beitrag über das DOS in der Ausgabe 5/84 geht hervor, daß man das DOS nur im Direktmodus benutzen kann. Dem muß ich widersprechen. Die Befehle haben allerdings eine andere Form. Allgemein ist es notwendig, <b>den Namen in Anführungszeichen</b> zu setzen. Die Befehle lauten dann zum Beispiel »@"$"«, »/"TEST"«, »←"TEST"« und »@" "«. So darf man auch im Direktmodus vorgehen. Ich denke aber, es wird sich keiner diese Mühe machen. Die Befehle werden ganz normal durch Doppelpunkt getrennt, zum Beispiel »@"S:TES*" :@" ":@"$"«.

### DOS als Programm ohne Lader

Als ich zum ersten Mal mit dem DOS Bekanntschaft machte, störte mich die Tatsache, daß es in Form zweier Programme abgespeichert war. Das DOS ließ sich außerdem ohne Kopierprogramme schlecht auf eine andere Diskette kopieren. Deshalb habe ich aus dem DOS eine Art Basicprogramm gemacht. Dieses kann ich mit LOAD laden und mit SAVE abspeichern. Wollen Sie es mir nachmachen?

Dann laden Sie bitte das DOS auf dem bisher üblichen Weg, falls es nicht ohnehin schon geschehen ist. Tippen Sie nun das Programm »DOS verschieben« ein (Listing 1 und 2). Mit einem RUN ohne Datafehler verschiebt sich das DOS direkt hinter das Programm. Dies erlaube ich nur einmal, da das Programm sonst doppelt so lang oder länger würde. Löschen Sie jetzt alle Programmzeilen außer Zeile 100. Es darf kein NEW eingegeben werden. Es können aber beliebig Zeilen hinzugefügt werden. Zum Beispiel könnte man die Bildschirmfarben festlegen und alle Tasten mit Repeatfunktion versehen (Listing 3). Damit ist meine DOS-Version fertig und kann abgespeichert werden.

### DOS unter neuem Namen

Tippen Sie das Programm »Neuer Name für DOS« (Listing 4) ein. Die Bezeichnung für das eigene DOS muß der Variablen Z$ zugeordnet werden. Hierfür werden die Zeilen 0 bis 99 verwendet. Der String darf bis zu 98 Zeichen enthalten und hat dieselbe Form wie beim PRINT-Befehl (PRINT Z$;). Ein RUN schreibt diesen String in das DOS. Jedes SYS 52224 erzeugt nun diesen Namen auf dem Bildschirm. Diese DOS-Version kann natürlich in ein Basicprogramm umgewandelt werden, wie ich es oben beschrieben habe.

### MERGE-Befehl für das DOS

Es wurden schon viele Methoden vorgestellt, die es ermöglichen sollten, ein Programm so zu laden, daß es an ein bestehendes angehängt wird. Ich erlaube mir nun, dem DOS diese zusätzliche Last aufzubürden.

Das Programm »DOS plus MERGE« (Listing 5 und 6) erzeugt diesen Befehl. Als Zeichen dient »+«. Ein MERGE-Befehl sieht dann aus wie »+TEST«. »+« und »/« arbeiten fast gleich. Sie unterscheiden sich nur in der Ladeadresse.

Ich sollte noch etwas anmerken. Hat das DOS das neue Zeichen »+« akzeptiert, so wird es vergeßlich. Denn das Zeichen »>« erfüllt seine Funktion nur noch im Direktbetrieb wie »+« auch.

Wie schon in der Ausgabe 5 angedeutet, lassen sich sämtliche Befehle, die normalerweise mit OPEN 15, 8, 15,".... übertragen werden, mit dem Klammeraffen abkürzen. Dazu gehören auch die Direktzugriffsbefehle wie B-R oder etwa B-W, und so weiter. Auch der im normalen Basic mögliche Replace-Befehl: SAVE"@:name", 8 läßt sich abkürzen mit ←@:name. Damit kann man ein Programm erneut unter gleichem Namen abspeichern, ohne daß es zu einem FILE EXIST ERROR kommt. Der Replace-Befehl funktioniert natürlich auch beim erneuten Schreiben von zum Beispiel sequentielle Dateien, die bereits unter gleichem Namen existieren. Allerdings wird dabei die alte Version überschrieben.

(Herbert Heise/gk)

# Flußdiagramme - eine Brücke zwischen Programmierern und Programmiersprachen?

> Wer hat sich als Programmierer nicht schon darüber geärgert, daß in einer Zeitschrift ein Listing eines interessanten Programms abgedruckt ist, aber ausgerechnet für einen anderen Computertyp als den eigenen? Flußdiagramme heNen, eventuelle Anpassungsprobleme auf ein Minimum zu beschränken.

Vielen Computerfreaks wird es wohl schon so ergangen sein. Man sieht in einer Zeitschrift ein interessantes Programm, aber es wurde für einen anderen als den eigenen Computer geschrieben. Also versucht man sein Glück und fängt an das Programm auf den eigenen Computer anzupassen. Meistens reicht dann die Beschreibung nicht aus, um in Verbindung mit dem Listing die nötigen Änderungen vorzunehmen. Nach einigen Stunden mühsamen Eintippens stellt man dann bedrückt fest, Basic ist nicht gleich Basic und das für den Computer XY geschriebene Programm will einfach nicht auf dem eigenen Gerät laufen. Entweder kapituliert man dann, oder man versucht solange weiter bis ein lauffähiges Programm entsteht, welches dann unter Umständen kaum noch Ähnlichkeit mit dem Original hat. Jedenfalls erreicht man dann irgendwann einmal den Punkt, wo man sich fragt, warum nicht alle Programme in einer einheitlichen Programmiersprache geschrieben werden, die von allen Computern verstanden werden können. Es ist natürlich nur mit großem Aufwand möglich, eine einheitliche Programmiersprache für alle bestehenden Computersysteme zu schreiben und außerdem wäre der Aufwand höher als der effektive Nutzen.

Es stellt Sich also die Frage, ob es nicht eine Möglichkeit gibt, Programme so darzustellen, daß sie von der Hardware und der Programmiersprache weitgehend unabhängig sind. Hier stellen Flußdiagramme eine große Hilfe dar.

In der Datenverarbeitung kennt man schon lange verschiedene Möglichkeiten der Programmdarstellung. Einen besonderen Platz nimmt dabei der Ablaufplan ein. Er bietet mit seinen Sinnbildern (siehe Bild 1) die Möglichkeit ein Programm übersichtlich und detailliert darzustellen, ohne an einen bestimmten Computer gebunden zu sein.

Wie man von einer Problemstellung zu einer vollständigen Programmdokumentation kommt, soll nun an einem kurzen Beispiel erläutert werden.

Problem: Für Zahlen, die größer als 0 und kleiner oder gleich 100 sind, sollen die Quadratwurzeln berechnet werden. Um das Problem zu lösen, sollte für die einzelnen benötigten Programmteile ein Schema erstellt werden:

1.	Eingabe der Zahl x
2.	Überprüfung der Zahl x
3.	Berechnung der Wurzel
4.	Ausgabe des Ergebnisses

Ein Beispiel, das aus technischen Gründen auf Seite 15 abgedruckt werden mußte, zeigt wie das obige Schema als Programmablaufplan aussehen kann.

Anhand des ausführlichen Flußdiagramms sollte es den meisten Programmierern möglich sein, ein lauffähiges Programm zu schreiben. Die eben erwähnte Methode ist jedoch nicht die einzigste Möglichkeit einen Programmablaufplan zu dem gestellten Problem zu erstellen. In Anlehnung an die Programmiersprache Basic wurde hier die Beschriftung der Symbole geändert. Für diejenigen, die sich mit Basic auskennen, dürfte die gezeigte Version eine wesentliche Vereinfachung darstellen.

Das Beispiel zeigt, daß mehrere Möglichkeiten zur Verfügung stehen einen Programmablauf zu erstellen. Wie umfangreich die Diagramme ausfallen, hängt in erster Linie davon ab, ob man nur einen groben Überblick über das Programm vermitteln möchte, oder ob es anderen Programmierern die Möglichkeit geben soll, ein lauffähiges Programm zu erstellen.

Ein Programmablaufplan ist also, wenn genügend Informationen darin enthalten sind, eine nützliche Brücke zwischen Programmierern und Programmen. Wie stabil sie ist, hängt jedoch von einigen weiteren Faktoren ab. Eine möglichst ausführliche Programmdokumentation sollte noch Informationen enthalten, die benötigt werden, um entscheiden zu konnen, ob es überhaupt sinnvoll ist, das Programm auf das eigene System anzupassen.

(Burkhard Appe/rg)

# Dreidimensionale Kalkulationen

> Traditionelle Kalkulationsprogramme bestehen aus einer Seite mit 64 Spalten und 254 Reihen. Calc Result hat 32 solcher Seiten, und diese sind miteinander verknüpfbar. Doch das ist nicht der einzige Grund, warum man noch einen zweiten Blick riskieren sollte. Denn dieses Tabellenkalkulationsprogramm bietet die Möglichkeit, Balkendiagramme und formatierte Ausdrucke zu erzeugen, erleichtert die Bedienung durch jederzeit einblendbare Hilfsbildschirme, schützt einmal aufgestellte Formeln, und läßt schnelle Neuberechnungen zu. Wir haben Calc Result in einem ausführlichen Test genauer unter die Lupe genommen.

Calc Result wird in vier verschiedenen Versionen angeboten. Jeweils eine für den CBM 700 und den CMB 8000 sowie zwei Versionen für den Commodore 64. Die einfachste Ausführung »Calc Result Easy« kostet 295 Mark und besteht nur aus einem Modul, das in den Modul-Steckplatz des Commodore 64 geschoben wird. Die andere Version für den Commodore 64 heißt »Calc Result Advanced« und wird mit einem Modul und einer Diskette zu einem Preis von 495 Mark angeboten. Dieselbe Konfiguration ist auch für die beiden größeren Systeme erforderlich, deshalb wollen wir hier nur »Calc Result Advanced« betrachten, zumal die Leistungsmerkmale nahezu identisch sind.

Das auffälligste Merkmal von Calc Result ist die dreidimensionale Verarbeitung von Tabellen. Was ist darunter zu verstehen? Am besten ist es, sich ein Blatt Papier vorzustellen und das Papier in 64 Spalten und 256 Reihen zu unterteilen. Auf diesem Blatt kann man nun sämtliche Berechnungen und Verknüpfungen der Zahlenkolonnen vornehmen, wie man dies von anderen Kalkulationsprogrammen gewohnt ist. Nun hat man aber nicht nur dieses eine Blatt Papier zur Verfügung, sondern ganze 32 Blätter. Die Daten und Formate sind zwischen diesen 32 Seiten vollaustauschbar. Die letzte der 32 Seiten hat einen Sonderstatus. Auf ihr können gleichartige Tabellen quasi per Tastendruck addiert werden. Ein Beispiel soll das erläutern: Sie führen monatlich eine gleichbleibende Kostenübersicht. Lediglich die Werte ändern sich von Eintragung zu Eintragung. Am Jahresende wollen Sie die Gesamtkosten wissen. Sie geben den entsprechenden Befehl ein und das Ergebnis steht auf Seite 32. Die monatlichen Kosten und das Gesamtergebnis können Sie in Diagrammform sowohl auf den Bildschirm als auch auf den Drucker ausgeben (siehe auch Bild 1). Komplizierte Berechnungen können so durch Tastendruck grafisch dargestellt werden. In das Balkendiagramm sind lediglich eine Kopf- und zwei Fußzeilen für Erklärungen nachzutragen. Alle Berechnungen werden vom Kalkulationsprogramm ausgeführt. Dies dokumentiert bereits die Bedienungsfreundlichkeit von Calc Result.

## Berechnungen auf 32 Seiten

Als Kriterium für die leichte Bedienung eines Tabellenkalkulationsprogramms zählt auch die Art und Weise, wie die Befehle und Kommandos einzugeben und abzulesen sind. Neben dem Feld für die Dateneingabe sind besonders die ersten drei Zeilen von Bedeutung. Da wäre zunächst die sogenannte Befehlszeile. In dieser Zeile können Sie Befehle, den Inhalt der momentanen Cursorposition und verschiedene Funktionen wie Angaben zum Format der momentanen Position (maximale Genauigkeit, Integer, 2 Dezimalstellen, rechts- oder linksbündig) und den freien Hauptspeicherplatz ablesen. Die zweite, die Hilfszeile, zeigt folgende vier Funktionen an: GOTO (für direkte Sprünge mit dem Cursor auf dem Arbeitsblatt), HELP (darauf kommen wir später noch zu sprechen), HARDCOPY (für einen Ausdruck des Bildschirms) und CLEAR (löscht den Bildschirm). Daneben dient diese Zeile für den Dialog. Hier wird die Eingabe abgefragt sowie auf Antworten hingewiesen. Mit Ausnahme der Druckeditierung können alle Fragen mit einem Tastendruck beantwortet werden. In der dritten Zeile, der Eingabezeile, werden die eingegebenen Zeichen sowie die Fragen, die mit mehreren Tasten zu beantworten sind, angezeigt.

Nun aber zu der Help-Funktion. Hat man vom Eingabemodus in den Befehlsmodus umgeschaltet, erscheint in der Befehlszeile folgender Ausdruck: SYSTEM: B D E F G L O P Q R - (Bild 2)

## Die Help-Taste hilft weiter

Das soll übersichtlich und informativ sein? Diese Frage stellen Sie zunächst mit Recht. Drücken Sie doch einmal die Help-Taste. Es erscheint ein Hilfsbildschirm, auf dem die Auswirkung jedes einzelnen Befehls kurz erklärt wird (Bild 3). Sie erfahren, daß B für Blank steht und dadurch das Feld, in dem sich der Cursor befindet, gelöscht wird (Übrigens: Zahlenwerte in einer Zelle können einfach durch Überschreiben gelöscht werden, Formeln sind jedoch schreibgeschützt, deshalb dieser Befehl). Unter D finden Sie den Disk-Befehl mit der Erklärung: Diskettenoperationen und Systeminformationen. Sollte Ihnen das nicht ausreichen, hilft die Help-Funktion weiter. Ein zweiter Hilfsbildschirm gibt die nötigen Informationen. In Bild 4 sind die neun Unterbefehle der D-Anweisung aufgelistet. Wenn Sie sich die Erklärungen genau durchlesen, werden Sie bemerken, daß hier immer von Drive 0 und Drive 1 die Rede ist, obwohl wir in unserem Test Calc Result Advanced für den 64er verwenden, und hier das Vorhandensein von zwei Laufwerken in den seltensten Fällen realisiert sein dürfte. Im Handbuch (sehr gut, in deutscher Sprache, mit vielen Beispielen) wird zwar auf das Arbeiten mit einem Laufwerk kurz hingewiesen, aber sämtliche weiteren Erklärungen beziehen sich auf zwei Laufwerke. Hier hätte man besser etwas mehr an die Anwender gedacht, die gerne mit einem guten Tabellenkalkulationsprogramm arbeiten möchten, aber nur ein Laufwerk besitzen.

Die ersten acht Disk-Befehle dürften keine Verständnisprobleme bereiten. Der letzte Befehl U für User Register soll noch kurz erläutert werden. Mit diesem Befehl kann man die Sprache der Hilfsbildschirme bestimmen (acht verschiedene stehen zur Auswahl), die Farben und Geräteadressen einstellen sowie den Druckertyp und das Papierformat wählen. Welche Unterbefehle beim Edit-, Format-und Page-Befehl zur Verfügung stehen, kann ebenfalls Bild 4 entnommen werden.

## Flexible Druckformatierung

Ein weiteres wichtiges Kriterium für die Beurteilung eines Kalkulationsprogrammes stellt für den Anwender die Flexibilität der Ausgabe seiner Berechnungen dar. Calc Result ermöglicht es, das Zahlenmaterial noch während des Ausdrucks zu bearbeiten. So kann man wählen, in welcher Reihenfolge die Spalten ausgegeben werden sollen, wie breit die Spalte sein soll und wie oft die entsprechende Spalte im Ausdruck erscheinen soll. Diese und andere Ausgabeparameter können Sie abspeichern und bei Bedarf wieder einlesen. Man kann aber, wie bei den meisten Kalkulationsprogrammen üblich, das Zahlenmaterial auch so ausgeben, wie es auf dem Bildschirm zu sehen ist (siehe Bild 5).

Da wir gerade beim Bildschirm sind, gehen wir auf dessen Darstellungsmöglichkeiten ein. Eine Bildschirmseite kann sowohl horizontal als auch vertikal geteilt werden. Die Teilung muß aber mindestens drei Reihen von der x-Achse und drei Spalten von der y-Achse entfernt sein.

Damit ergibt sich für den 64er mit seinem 40-Zeichen-Bildschirm eine maximale Dreiteilung in vertikaler Richtung und es zeigt sich unter anderem, daß es problematisch sein kann, Tabellenkalkulation mit nur 40 Zeichen pro Zeile sinnvoll zu benutzen. Den Cursor kann man beliebig in diesem geteilten Bildschirm positionieren und sich einzelne Teilbereiche durch »Abrollen des Textes« anzeigen lassen. Schwieriger wird die Sache, wenn man sich noch ein sogenanntes Bildschirmfenster definiert hat. Befindet sich der Cursor nämlich in so einem Fenster, läßt er sich durch keine noch so gut gemeinten Befehle dort wieder herausholen (siehe Bild 6). Das schränkt natürlich den intensiven Einsatz von Bildschirmfenstern ein.

Sinnvoller ist da schon die Möglichkeit, bis zu vier Seiten gleichzeitig auf dem Bildschirm darzustellen. Auf diese Weise können Sie Ergebnisvergleiche zwischen Abteilungen oder Tochtergesellschaften anstellen, Sollabweichungen errechnen und so weiter.
Zur Mathematik: Calc Result rechnet nach den Regeln der korrekten mathematischen Priorität. Es sind somit alle Rechnungsarten einschließlich Potenzrechnung möglich. Ferner stehen zur Verfügung: Mittelwert, Minimum Maximum, Standardabweichung und trigonometrische Funktionen. Auch die Verwendung von Bedienungsfunktionen wie IF THEN ELSE und OR AND NOT ist möglich. Der Formelschutz wurde bereits erwähnt. Einmal aufgestellte Formeln sind gegen versehentliches Überschreiben oder Löschen geschützt.

Daß eine Datei in jeder beliebigen Entwicklungsphase mit einer oder mehreren Seiten abgespeichert werden kann, ist selbstverständlich. Als angenehm wurde beim Laden das vorherige Auflisten der gespeicherten Dateien mit den Dateinamen empfunden. Man muß nur mit dem Cursor auf die gewünschte Datei (beziehungsweise deren Namen) fahren um diese nach zweimaliger Betätigung der Return-Taste zu laden.

## Zusammenfassung

Calc Result gibt es in verschiedenen Versionen. Sie können also die Kombination wählen, die Ihnen am besten paßt. Benötigen Sie nur ein einfaches Kalkulationsprogramm, dann ist vielleicht Calc Result Easy die Lösung. Sie verzichten dabei auf die dritte Dimension, die globale Neuberechnung, die Seitenaddition und die Hilfsbildschirme. Sind die Anforderungen höher und möchten sie die oben angesprochenen Möglichkeiten nicht missen, so heißt der nächste Schritt Calc Result Advanced. Damit haben Sie ein mit einigen überzeugenden Merkmalen ausgestattetes Werkzeug für die Tabellenkalkulation zur Hand. Ihre Wahl wird auf die Versionen für den Commodore 700 oder Commodore Serie 8000 fallen, wenn Sie außer den Kalkulationsmöglichkeiten noch weitere Anforderungen (wie Verarbeitung von Visicalc-Dateien oder Kommunikationsfähigkeit) an Ihren Computer stellen.

(aa)

Der angekündigte Test von Multiplan mußte aus Platzgründen in eine der nächsten Ausgaben geschoben werden. Dann wird auch PractiCalc beschrieben.

# Gute Noten für gute Noten

> »Man müßte Klavier spielen können...«, tönte es einst durch die Gassen. Die Zeiten haben sich gewandelt. Glück bei den Frauen hat man heute auch ohne Fertigkeit im Klavierspiel. Denn mit dem Extended Synthesizer System ersetzt der Commodore 64 die Technik des Klavierspiels. Was jedoch nötig ist: eine gute Portion musikalisches Grundwissen.

Der Computermusiker würde das Extended Synthesizer System ein Komposerprogramm nennen. Lieder direkt über die Tastatur einspielen, das funktioniert nicht. Man tippt sie Ton für Ton, mittels diverser Befehle ein. Dies bedeutet zwar viel Arbeit, dafür haben jedoch hier auch Theoretiker ohne Übung im Klavierspiel eine Chance, eigene Kompositionen zum Klingen zu bringen.

Das Programm wird auf Diskette zum Preis von 138 Mark geliefert.

Die Bedienungsanleitung umfaßt zirka 50 Seiten. Klar und übersichtlich aufgebaut, erklärt sie alles Wichtige zu den einzelnen Bedienungsfunktionen. Schade, daß kein eigenes Kapitel die Grundlagen der allgemeinen Musiktheorie berücksichtigt. Dies hätte sicher vielen Nichtmusikern den Umgang mit dem Programm wesentlich erleichtert. Auch die Grundlagen der Klangerzeugung kamen etwas kurz weg. Ein paar kleine Grafiken mehr, und auch der Nicht-Synthesizer-Fach-mann wüßte anschließend besser Bescheid, über Wellenformen und Hüllkurvenverläufe. Sicher vermuteten die Autoren des Bedienungshandbuches, daß nur musikalisch vorgebildete Anwender mit dem Programm arbeiten. Doch das muß ja nicht immer sein. Es stimmt zwar, daß das Extended Synthesizer System in erster Linie für den musikalisch gut Vorgebildeten Nützliches bietet, doch hätte dieses Programm andererseits auch gerade für den Musikneuling großen pädagogischen Wert. Außerdem dürften sich unter den Commodore 64-Besitzern wesentlich mehr Musiklaien befinden als Musiker unter den Commodore 64-Usern. Nun denn, im Notfall hilft immer noch der Gang zum Musikalienhändler, der gerne mit Rat, Tat und Literatur zur allgemeinen Musiktheorie weiterhilft.

Nach dem Laden und Starten des Systems erscheint zunächst ein Titelbild. Mit »RETURN« aktivieren wir dann das Programm. Einige Sekunden später tauchen auf dem Bildschirm drei verschiedenfarbige Notenzeilen untereinander auf. So präsentiert sich das Extended Synthesizer System (siehe Bild) während wir mit ihm arbeiten.

In der obersten Zeile erhalten wir drei Informationen zum momentan gespielten Stück. Genauer gesagt, Tempo, Name des Stücks und der gerade gespielte Takt. Die Violinschlüssel in den drei Notenzeilen darunter wirken etwas verunglückt. Doch das soll uns hier nicht weiter stören. Das Extended Synthesizer System bietet, wie es mittlerweile unter den Musikprogrammen für C 64 zum guten Ton gehört, alle drei Stimmen des SID-Chips. Es entspricht insofern einem dreifingerigen Klavierspieler. Denn genau wie dieser vermag es drei Töne gleichzeitig zum Klingen zu bringen, nicht mehr. Vorausgesetzt natürlich, die

## Drei Notenzeilen am Bildschirm

Füße bleiben auf dem Pedal. Aber das sei der Fall. Eine Etage unterhalb der dritten Notenzeile, nochmals Text. Im Toneingabemodus teilt uns das Extended Synthesizer System in der oberen der zwei Zeilen mit, welche der drei Stimmen wir gerade bearbeiten. Darunter eine Input-Zeile. Hier spielt sich im folgenden die gesamte Kommunikation mit dem System ab. In der Kommandozeile erscheinen sämtliche über die Tastatur eingetippten Befehle, wie auch dezente Hinweise des Systems auf etwaige Bedienungsfehler.

Spätestens jetzt ist es Zeit, einen der Demosongs zu laden. Das gibt uns den besten Eindruck von den Möglichkeiten des Systems. Töne machen die Musik.

Zunächst will das Programm jedoch immer zwei Dinge wissen: Takt und Notenschlüssel. Genau wie diese beiden Grundfesten unserer westlichen Musikkultur jede Partitur eröffnen, stehen sie auch hier am Beginn der Arbeit.

Die Eingabe des Taktes erfolgt immer in der Form a/b, mit a von 1 bis 9 und b entweder 2, 4 oder 8. Wir können also zum Beispiel 4/4, 3/4, 9/8 oder auch einen 7/8 Takt eingeben. Tippen wir aus Versehen einen unzulässigen Wert ein, erkennt das System den Fehler sofort und ignoriert ihn. Gleiches gilt für alle anderen Befehlseingaben. Prinzipiell passieren nur korrekte Eingaben die Kommandozeile.

Die gewünschte Tonart teilen wir dem Extended Synthesizer System durch den entsprechenden Anfangsbuchstaben und gegebenenfalls das nötige Vorzeichen (Doppelkreuz beziehungsweise b) mit. Zum Beispiel c für C-Dur, c# für Cis-Dur, eb für ES-Dur und so weiter. Leider versteht die Software nur Dur-Tonarten. Moll-Tonarten müssen immer als Dur-Tonarten eingegeben werden. Dies läßt Vollblutmusikern natürlich die Haare zu Berge stehen.

Zu guter Letzt nun noch LOAD»DEMO«, 8 dann RETURN getippt und kurze Zeit später füllen sich unsere drei Notenzeilen. Ein Ausschnitt aus dem Musikstück erscheint notiert. Jetzt noch »PLAY« eingetippt und unser Extended Systhesizer System läßt sich nicht mehr halten. Flott trillert und flötet es dreistimmig vor sich hin. Noten flitzen über den Bildschirm. Auch optisch läßt sich mit dem Programm gewiß jeder Nachbar verblüffen. Nach zwei Minuten, Ruhe, der Spuk ist vorbei. Auf der Programmdiskette warten mehrere Demostücke auf Ihren Einsatz, alle recht passabel programmiert. Klanglich erlebt man jedoch hier weniger Überraschungen.

## Wenig Sound, aber viel Musik

Im Vergleich zu Synthimat 64 oder Musicalc hat man bei der Konzeption des Extended Synthesizer Systems weniger Wert darauf gelegt, alle Soundmöglichkeiten des SIDs auszuschöpfen. Dafür erhält man hier mit Abstand das beste Werkzeug, um mit Noten zu hantieren. Leider lassen sich die erstellten Kompositionen nicht ausdrucken. Schade, mit dieser Option zusätzlich, hätte man ein passables Notendrucksystem für dreistimmige Kompositionen.
Ringmodulation, Synchronisation, Filterung und LFO-Modulationen muß man hier vergessen. Auch den DCOs erlaubt man hier nur Dreieck, Rechteck, Sägezahn oder Noise zu produzieren, keine der Mischformen.

Die Sounds legt man hier in sogenannten Registern ab. Insgesamt sind jeweils zehn verschiedene Register ohne Diskettenoperation abrufbar. Diese Register könnte man natürlich auch Klangpresets oder Klangprogramme nennen.

Man sollte bereits vor Beginn der Songprogrammierung über die Struktur des Songs möglichst im Klaren sein. Wer gut notieren kann, ist am besten dran. Er kann die Notation vom Papier direkt in den Computer »abschreiben«. Andernfalls dauert es sicher länger bis man ein ganzes Stück wohltönend einprogrammiert hat. Trial and Error lautet die Devise für alle nicht der Musiksprache fähigen.

## Schnelles Komponieren dank sinnvoller Eingabe-erleichterungen

Wie funktioniert die Noteneingabe? Zunächst bestimmt man die Stimme, die programmiert werden soll, mit den Befehlen 01, 02 und 03. Dann gibt man Ton für Ton jeweils Notenlänge, Tonhöhe, Lautstärke, Anschlag und das gewünschte Klang-Register ein. Der gerade eingegebene Ton erscheint sofort als Note in der richtigen Notenzeile.

Gott sei Dank braucht man nicht für jeden Ton erneut alle Werte eintippen, nur die, die sich gegenüber der zuvor eingegebenen Note ändern. Im anderen Fall übernimmt das System die entsprechenden Werte des vorangegangenen Tones. Ganz ungeduldige Klangignoranten dürfen getrost auch auf die Eingabe von Lautstärke, Anschlag und Register verzichten. Dann nimmt die Software einfach gebräuchliche Ersatzwerte.

Eine vollständige Toneingabe sieht zum Beispiel so aus:
1.4 d5 : 9 : 1 : 3

Viertel Tonhöhe: Sustain: Anschlag Register Note: Oktave

Will man einen Wert nicht genau spezifizieren, gibt man statt dessen bei der ersten Noteneingabe ein »*« ein. Das System nimmt dann für diesen Parameter im gesamten Song einen Ersatzwert. Gibt man das Sternchen innerhalb eines Songs ein, übernimmt das System für diesen Parameter den Wert des vorangegangenen Tones.

Soll ein Ton in allen Parametern nochmals wiederholt werden, genügt ein Druck auf die RETURN-Taste. Dies erleichtert natürlich das Arbeiten ungemein.

Der Takt, der gerade eingegeben, bearbeitet oder gespielt wird, erscheint immer in seiner Umgebung, in allen drei Takten auf dem Bildschirm. Insgesamt kann das System 408 Takte pro Stimme im Speicher halten.

Die ersten acht Töne des bekannten »alle meine Entchen« erfordern einen doch recht hohen Programmieraufwand für eine Stimme.

Mit den Befehlen »+« und »-« kann man die Takte horizontal über den Bildschirm scrollen. Einige weitere nützliche Befehle dienen dazu, etwa einen schon eingegebenen Takt a gezielt auf den Bildschirm zu rufen (list a), bis zum Takt e zu löschen (del a-e) oder i-mal zu kopieren (copy a-e,i). Takt-Handling nennt man das. Auch die Funktionstasten f1, f3, f5 und f7 bieten interessante Arbeitserleichterungen. Ein einziger Tastendruck löscht den zuletzt eingegebenen Ton (f1) oder Takt (f3), kopiert den letzten Takt (f5), oder setzt einen ganzen Takt beziehungsweise den Rest des gerade Eingegebenen als Pause (f7). So geht die Eingabe der Kompositionen trotz komplexer Befehle relativ schnell vonstatten.

Mehrmaliges Wechseln von Tonart und Tempo innerhalb einer Komposition stellt kein Problem dar. Hierfür sind die Befehle »key« und »tempo«, mit nachfolgender Eingabe des Tonartsymbols beziehungsweise des Tempowertes zuständig. Sowohl Tempo- als auch Tonartänderungen beziehen sich nicht auf eine komplette Stimme sondern auf eine wählbare Anzahl von Takten. So sind mehrere Änderungen innerhalb eines Stückes möglich.

Die Einstellungen der einzelnen Klangregister gibt man numerisch ein. Wir können die Wellenformen und die ADR-Werte für jedes Register getrennt bestimmen. Die Wellenform legt man mit »t« für Dreieck, »p« für Rechteck, »s« für Sägezahn und »n« für Noise, fest. Als nächstes bestimmt man die ADR-Werte durch Eingabe des Buchstabens A, D beziehungsweise R und einer darauffolgenden Zahl von 0 für kurz, bis 9 für lang. Der Sustainwert steht nicht im Klangregister. Ihn gibt man bei der Toneingabe für jeden Ton getrennt ein. Was musikalisch natürlich gutzuheißen ist. Denn so lassen sich einzelne Töne mit unterschiedlicher Lautstärke spielen, dynamisch. Dies klingt weniger mechanisch als wenn alle Töne gleiche Lautstärke besitzen.

Das System läßt sich übrigens auch stimmen.

Obwohl der Extended Synthesizer weder die Ringmodulations-noch Synchronisationsmöglichkeiten des SIDs nutzt, erreicht man doch ganz interessante Soundabläufe. Jeder einzelne Ton läßt sich ja mit einem eigenen Sound versehen. Das gleicht das Fehlen besagter Effekte mehr als aus.

Die Lautstärkenwerte, Gate-Zeiten und angewählten Register der einzelnen Töne zeigt die Software, sofern gewünscht, auf dem Bildschirm.

Solange man mit dem System noch nicht so ganz hundertprozentig vertraut ist, passieren natürlich des öfteren Eingabefehler. In diesem Falle läßt uns das System nicht ratlos alleine, sondern hilft mit diversen Fehlermeldungen meist aus der Patsche. Dies gilt natürlich nur für falsch, beziehungsweise unvollständig eingegebene Kommandos. Klingt unser Lied am Schluß fürchterlich, so müssen wir das entweder mit unserem musikalischen Gewissen verantworten, oder tiefer in die Grundlagen der Harmonielehre einsteigen. Ein solches musikalisches Gewissen besitzt das Extended Synthesizer System nicht.

Will man sich seinen Song anhören, tippt man nur den Befehl PLAY ein und schon geht’s los. Auch einzelne Takte, sowie einzelne Stimmen spielt der Extended Synthesizer auf Wunsch vor. Sogar an eine Loop-Funktion, die einzelne Takte sowie eine oder mehrere Stimmen zyklisch wiederholt, hat man gedacht.

Für die Nachwelt können wir unsere Songs sowohl auf Diskette als auch auf Cassette aufbewahren. Zu jedem Song werden zugleich sämtliche Klangparameter mit abgespeichert.

Ein Aspekt, Extended Synthesizer einzusetzen, ist das Üben mehrstimmiger Notation. Wenn man nach dem Eintippen den Song abspielt, hört man sofort, ob man seine musikalische Imagination richtig zu »Papier« gebracht hat oder nicht.

Das Extended Synthesizer System ist vor allem für Notationsfetischisten und Composerfreaks gedacht, denen Effekte wie Ringmodulation und Synchronisation sowie viele LFOs und Realtimeeinspielung, nicht so wichtig sind. Man muß hier jedoch auch bemerken, daß die Notendarstellung nicht bis ins kleinste Detail der Hohen Schule der Notation entspricht. Doch an diesem Problem beißen sich momentan noch ungleich leistungsfähigere Computersysteme die Zähne aus. Das Programm kostet 138 Mark.

(Richard Aicher/aa)

# Übersicht der Musikprogramme für den C 64

TODO

# Quickcopy – das schnelle Kopierprogramm für den C 64

> Schon lange war bekannt, daß es Möglichkeiten gibt, die Floppy VC 1541 schneller zu machen. Beim gelegentlichen Laden und Speichern von Programmen störte die bekannte Trägheit des Laufwerks weniger. Wenn allerdings viel kopiert werden sollte, wurde sie zur Geduldsprobe. Jetzt gibt es ein schnelles Kopierprogramm, das zu einem erschwinglichen Preis erhältlich ist.

Schon seit einiger Zeit tauchten in allen möglichen Computerzeitschriften Anzeigen auf, die ein schnelles Kopieren von Programmen mit dem C 64 versprachen. Genauer gesagt waren die dort angegebenen Kopierzeiten sensationell. Selbst die unter der Hand herumgereichten schnellen Kopierprogramme von »Spezialisten« konnten nicht mit dieser Geschwindigkeit aufwarten. Als wir endlich eine Testversion bekamen, wurde alles liegengelassen um festzustellen, wo der Haken lag.

Um es vorwegzunehmen und ohne Schöntuerei: Es gibt keinen Haken. Quickcopy ist ein sehr schnelles und ausgereiftes Kopierprogramm (für den C 64, versteht sich).

Geliefert wird Quickcopy auf einer Diskette mit einer ausführlichen Beschreibung, die an sich gar nicht notwendig ist. Kopierprogramme sind ja normalerweise unkompliziert zu bedienen, vor allem diejenigen, die nicht einzelne Files kopieren, sondern komplette Disketten, sogenannte Backup-Versionen erstellen. Deren einzige Aufgabe ist es, ein Duplikat einer Diskette herzustellen. So lassen sich auch mit Quickcopy keine einzelne Files kopieren, sondern nur ganze Disketten. Trotzdem können einige Parameter eingestellt werden: Da Quickcopy wahlweise mit einem oder auch zwei Laufwerken arbeitet, kann deren Geräteadresse bestimmt werden. Anschließend wird der Kopiermodus festgelegt. Man kann wählen zwischen normalem und Utility- Modus. Im normalen Modus werden nur die als belegt gekennzeichneten Sektoren, im Utility-Modus alle Sektoren kopiert. Letzteres ist immer dann sinnvoll, wenn zum Beispiel die Block Availability Map (BAM) fehlerhaft ist oder um auch gelöschte Files mitzukopieren. Da im Normal-Modus nur die belegten Blöcke kopiert werden, ist eine Kopie je nach Belegungsgrad der Diskette langsamer oder schneller hergestellt. Für jeden Parameter werden Standardwerte vorgegeben, auch ob ein Verify gewünscht wird oder ob Lesefehler ignoriert werden sollen (wichtig bei beschädigten Disketten), so daß durch sechsmaliges Drücken der Returntaste sämtliche Standardwerte eingestellt werden und der Kopiervorgang anläuft. Falsch machen kann man eigentlich gar nichts. Fehler, etwa der Schreibschutz auf der Diskette werden abgefangen und lassen das Programm nicht abstürzen.

Bei einigen Kopierprogrammen wird während des Kopierens der Bildschirm abgestellt (nicht gelöscht), um schneller zu werden. Bei Quickcopy hingegen ist während des gesamten Kopiervorgangs der Bildschirm sichtbar. Interessant ist, daß angezeigt wird, welcher Track und Sektor gerade in Bearbeitung ist. Außerdem wird die Art der momentanen Tätigkeit angezeigt, ob Formatieren, Lesen, Schreiben oder Verifizieren. Interessant dabei ist die Reihenfolge der Bearbeitung: Jeder Block wird zuerst formatiert, dann beschrieben und zum Schluß verifiziert, anders als bei herkömmlichen Kopierprogrammen, bei denen zuerst die gesamte Diskette formatiert und erst danach mit dem Kopieren begonnen wird. Und alles geht mit einer bisher nicht gewohnten Geschwindigkeit vonstatten. Zwei extreme Beispiele:

1.	Die Quelldiskette ist formatiert aber leer: Kopierzeit = 27 Sekunden, einschließlich Formatieren, Verifizieren und Diskettenwechsel.

2.	Die Quelldiskette ist komplett voll: Kopierzeit 4,5 Minuten inklusive Formatieren, Verifizieren und dreimaligem Diskettenwechsel.

Ein Verzicht auf Formatierung lohnt sich nicht, der Vorteil liegt im Sekundenbereich. Der Verzicht auf ein Verify bringt ungefähr eine halbe Minute und darauf sollte aus Sicherheitsgründen auch nicht verzichtet werden.

Alles in allem ist Quickcopy ein Programm, das längst fällig war. Und auch die Tatsache, daß mit ihm die meisten kopiergeschützten Programme nicht dupliziert werden können (ich habe es ausprobiert), ist keine wesentliche Einschränkung, im Gegenteil, es zeugt von Verantwortungsbewußtsein.

Dieses Programm zeigt und läßt erwarten, daß es bald möglich sein wird, die Floppy VC 1541 insgesamt schneller zu machen. Und darauf kann man gespannt sein.

(gk)

# Musicalc – oder was wirklich im Commodore 64 steckt

> Musicalc ist eine elegante Methode, mit einem Commodore 64, Töne, Klänge, Kompositionen zu speichern und wiederzugeben. Noten erscheinen am Bildschirm — mit weiteren C 64 oder einem Elektronikschlagzeug bleiben wir stets im Takt. Wem die heimische Musik zu langweilig wird, der hoH sich eine der 50 exotischen Tonleitern in den Speicher und spieK zum Beispiel Bali Agung.

Die Disketten von Musicalc stecken nicht in den altbekannten, tristen schwarzen Hüllen, sondern präsentieren sich farbenprächtig, jede ein kleines grafisches »Kunstwerk« für sich. Jede ist über dies in einem ausgesprochenen hübsch gestalteten Umschlagskarton verpackt. Hier waren Optikspezialisten am Werk.

Zum Test lag mir leider nur der erste von drei Bänden, in der amerikanischen Version, vor. Band ist das passende Wort. Auf 65 Seiten großformatigem Druck erfährt man alles Wichtige über die Diskette Nummer 1, den Musicalc Sequenzer und Synthesizer. Grundlegende Themen der Synthesizer kommen zur Sprache. So können sich auch in diesem Gebiet noch völlig Unbedarfte ohne Probleme ins Reich des SID begeben. Für Fortgeschrittene oder Ungeduldige beinhaltet das Handbuch eine »Schnell-Anleitung« mit den wichtigsten Befehlen in Kurzform. Musicalc ist kein abgeschlossenes Programm, sondern ein ganzes Programmsystem, das ständig um weitere Soft- beziehungsweise Hardware erweitert wird. Dies verspricht zumindest der Hersteller, die amerikanische Firma Waveform. Sämtliche, auch in Zukunft erscheinende Softwaremodule, bleiben untereinander kompatibel. Problemlos lassen sich Daten innerhalb des Systems austauschen. Neben neuen Programmen erscheinen in Zukunft auch ständig neue Demostücke auf Disketten. So bringen auch Programmier- oder Spielfaule ihren Commodore 64 zum Tönen. Zwei dieser sogenannten Templates gibt es schon. Das African/Latin Rhythm Template und das New Wa-ve and Rock Template.

Ich möchte die ersten drei Programmodule des Musicalc-Systems (typischer Hardwareaufbau siehe Bild 1) besprechen, drei Disketten, randvoll mit Software, die Sequenzer und Synthesizer-Diskette Nummer 1, die Score-Writer-Disk Nummer 2 und schließlich Keyboardmaker, das Programmodul 3.

Die Sequenzer- und Synthesizerdiskette stellt den Grundbaustein im Musicalc-System dar, den Schlüssel zur Welt des Klangs und der Melodie.

Bei Musicalc symbolisiert die linke Bildschirmhälfte (Bild 2) das Einstellfeld eines ganz gewöhnlichen Synthesizers mit Schiebereglern und verschiedenen Schaltern, das Karofeld rechts einen Multisequenzer, der drei Stimmen gleichzeitig anzeigt. Bei beiden Einstellfeldem hielten sich die Softwareentwickler nahe an Vorbilder der klassischen Analogsynthesizertechnik. Dies macht es auch Musikern einigermaßen leicht, Musicalc Töne zu entlocken. Der vertraute Anblick eines Synthesizers und Analogsequenzers bleibt wenigstens in etwa am Bildschirm erhalten.

Unbedingt erforderlich ist ein Farbbildschirm. Verschiedene Hintergrundfarben signalisieren nämlich die diversen Bedienungsebenen, in denen die Commodore-Tastatur jeweils unterschiedliche Belegung aufweist.

Ordnung in die vielen verschiedenen Modi von Musicalc bringt das Hauptmenü. Ich möchte nur auf einige wichtige Optionen eingehen. Das genügt, um einen Eindruck von den vielen Möglichkeiten zu verschaffen.

32 verschiedene Soundeinstellungen und 32 verschiedene dreistimmige Melodielines können mittels »SAVE PRESETS« auf ein gemeinsames Preset-File abgelegt werden.

Erarbeitete Melodien und Klangeinstellungen können mittels »SAVE PRESETS« beziehungsweise »LOAD PRESETS« auf Diskette gespeichert oder in den Computer geladen werden. Auf jedem File haben 32 Sequenzen und 32 Sounds Platz. Zwei Demo-Preset-Files erhalten wir bereits gratis auf der Programmdiskette 1 mitgeliefert. Waveform hat sich sowohl mit der Auswahl der Demostücke als auch den Klangeinstellungen Mühe gegeben. Selbst ganz moderne Klänge tauchen hier und da auf. Andere Sound- und Sequenzereinstellungen erinnerten mich wiederum sehr an Klänge der altbekannten Elektronik-Rocker »Tangerine Dream«.

Für unsere ersten Versuche laden wir ein Demofile in den Arbeitsspeicher. Dann begeben wir uns mittels der Option »PRESETS« in den Preset-Spiel-Mode. Auf dem Bildschirm unser Bild 2. Grüner Hintergrund signalisiert: Presetmode! Jetzt wartet der Commodore auf unseren Einsatzbefehl. 32 verschiedene dreistimmige Sequenzen und 32 unterschiedliche Klangeinstellungen stehen abrufbar im Arbeitsspeicher bereit. Jeder von 32 QWERTYTasten ist jeweils eine Melodie und ein Sound zugeordnet. In der Melodieebene (Commodore Taste) rufen wir durch Druck auf einer Taste entweder die zugehörige Melodie, in der Soundebene (Shift-Taste) den zugehörigen Sound auf. Die Änderung erfolgt sofort, ohne Pause im Spiel. Jede der 32 Sequenzen läßt sich mit jedem der 32 Klänge versehen. Ohne Diskettenoperation stehen also momentan 1024 Kombinationen (32*32) von Sounds und Sequenzen abrufbereit zur Verfügung!

Demomelodien und -klänge abspielen ist bequem, aber auf die Dauer natürlich nicht beglückend. Irgendwann wächst der Wunsch, eigene Klänge und Melodien zu kreieren. Und jetzt kann man so richtig loslegen.

70 Schalter und Regler stehen zur Verfügung
Im Syntheziser-controlpanel, mit grauer Hintergrundfarbe, stellen wir die Klänge ein. Die Klangeinstellung funktioniert prinzipiell genau wie bei einem Analogsyntheziser mit Schiebereglern. Insgesamt regeln wir 70 verschiedene Klang-Parameter über das Panel. Es existierten sowohl »Schieberegler« als auch »Schalter«. Die Schieberegler erscheinen als vertikale schwarze Balken, die Schalter als kleine Vierecke im Bild. Mit unseren QWERTY-Tasten wählen wir die einzelnen Schieber und Schalter an. Entsprechend der Sound- und Melodiewahl rufen wir wieder jeweils einen Schieber und Schalter über eine Taste auf.

Mit den »Schiebereglern« stellen wir im Bereich ENV (linke obere Ecke im Bildschirm), die Hüllkurven ein. Hierzu wählen wir für jeden der drei Generatoren den entsprechenden Attack-, Decay-, Sustain- und Releasewert. Jede Stimme können wir mit einer anderen Hüllkurve versehen. Unter dem ENV-Bereich das PW-Einstellfeld. PW steht für Pulsweite. Wieder einen Stock tiefer, mit FILT gekennzeichnet, das Filter-Einstell-Feld. Jede der drei Stimmen verfügt über einen getrennt regelbaren Filtereinsatzpunkt, die Resonanz des Filters ist ebenfalls regelbar. Mit der untersten Reglerreihe können wir die Geschwindigkeiten der drei Sequenzerkanäle regeln.

Neben den »Schiebereglern« existieren noch zirka 30 Schaltfunktionen. So lassen sich für jeden der drei Oszillatoren getrennt verschiedene Kurvenformen auswählen: Dreieck, Sägezahn, Rechteck beziehungsweise Rauschen. In der obersten Zeile unseres Panels in Bild 2 lesen wir dreimal »TSPN«. Dies sind nichts anderes als die ersten zwölf Schalter, mit denen also Triangle (Dreieck), Sawtooth (Sägezahn), Pulse (Rechteck) und Noise (Rauschen) für jeden der drei Oszillatoren an-und ausgeschaltet werden. Im Einschaltzustand erscheint jeweils ein schwarzes Viereck unter dem entsprechenden Symbol. Mit einer weiteren Schaltserie (3 mal GSRT!) lassen sich Gate, Synchronisation und Ringmodulation ein- beziehungsweise ausschalten. Die letzte Schalterreihe ermöglicht die Auswahl der gewünschten Filtereinstellung. Insgesamt stehen acht verschiedene Filtereinstellungen zur Verfügung: Tiefpass, Bandpass, Hochpass und die bekannten Mischformen.

Das Motto: Probieren geht über studieren, gilt für die schier unzähligen Möglichkeiten der Modulation. Jeder Oszillator und Envelopegenerator kann so ziemlich jeden anderen Parameter modulieren. Dies eröffnet eine uferlose Anzahl von Klangvariationen. Die einzelnen Modulationsarten lassen sich durchschalten und sofort in ihrer Auswirkung auf den Sound überprüfen.

Hat man nach Stunden voller Mühe den richtigen Sound gefunden, geht’s ans Ausarbeiten einer Sequenz, Melodie, beziehungsweise Komposition. In der rechten Bildschirmhälfte unseres Hauptpanels (Bild 2): Das Sequenzersystem. Es besteht aus 15 waagrechten Reihen mit jeweils 16 Ton-Schritten. Jeden der 15 x 16 Kästchen entspricht ein bestimmter, frei wählbarer Ton. 240 Töne faßt jeder der 32 Sequenzer-Presets maximal. Drei farbige Quadrate entsprechen den drei Sequenzerstimmen. Sie durchlaufen nun Reihe für Reihe, Kästchen für Kästchen, das gesamte Feld oder auch nur Teile davon. Bei jedem Schritt erklingen maximal drei Töne im gewählten Sound. Keine Einschränkungen gibt es für die Art des Durchlaufs. Wir können die Kästchen entweder brav Reihe für Reihe laufen lassen. Aber auch wirre Sprünge von jeder beliebigen Stelle zu jeder anderen sind möglich. So können wir zum Beispiel Stimme 1 endlos Reihe 10 wiederholenlassen, während Stimme 2 die Reihen 1 bis 16 zyklisch durchläuft und Stimme 3 Reihe 3 von step 4 bis 8, dann Reihe 4 von step 1 bis 8 und schließlich Reihe 10 von step 8 bis step 12 spielt. Nichts ist unmöglich. Ein fast perfektes Sequenzersystem.

Welche Töne den 256 Kästchen entsprechen sollen, bestimmen wir in der Option SCORE. Hier entsteht quasi unsere Partitur. Das Score-Eingabefeld sehen wir in Bild 3.

Mit einem Cursor lassen sich hier in einer Art Balkendiagramm die Tonhöhen und Oktavlagen der jeweils 16 Töne einer Sequenzerzeile einstellen. Insgesamt existieren für jedes der 32 Sequenzerfelder eines Preset-Files 16 solche Scores. Das Komponieren von Songs sollten Ungeduldige lieber bleiben lassen, es erfordert Zeit.

Wem diese Art der Melodieentwicklung zu langsam vorangeht, der kann jedoch seine Sequenzen auch im Realtime-Verfahren, über Commodore 64-Tastatur, einspielen.

Hierzu wählt man im Hauptmenü die Option KEYBOARD. Drei weitere Unteroptionen stehen jetzt zur Wahl.

Im RECORDER MODE kann jeweils eine der drei Sequenzerstimmen per Hand eingespielt werden, die zwei restlichen hört man hierzu als Begleitung. Jeder Tastendruck wird registriert und überschreibt die ausgewählte Sequenzerspur an der bestimmten Stelle. Berührt man keine Taste, übernimmt der Sequenzer die ursprünglichen Töne.

Im STEP MODE lassen sich bestimmte, einzelne Steps innerhalb der Sequenz gezielt verändern, und zwar durch Eingabe des gewünschten Tones über das Keyboard.

Im sogenannten VOICE MODE können wir eine der drei Stimmen des Sequenzers abschalten und per Hand über das C 64-Keyboard spielen. So spielen wir dann ein Solo zu unserem zweistimmigen, vorher programmierten Begleitorchester.

Noch viele weitere Modi existieren. Auf alle hier einzugehen, würde den Rahmen doch erheblich sprengen. Eines möchte ich noch erwähnen. Im Mode EXTERNAL können einige externe Programme geladen werden. Mit einem hiervon lassen sich zum Beispiel die Oszillatoren des Commodore 64 in weitem Bereich stimmen. Der jeweilige Frequenzbereich erscheint numerisch, auf vier Stellen genau, im Bildschirm. Musicalc als Stimmgerät.

Die Diskette 2 nennt sich Score Maker. Sie dient zur Übersetzung der im Sequenzer befindlichen Songs in Notenschreibweise. So erscheinen Noten am Bildschirm. Mit einem VC 1525 Grafikdrucker oder über einen Epson mit Cardco Centronics-Interface lassen sich diese ausdrucken. Bei meiner Testversion gab es hier jedoch einige Schwierigkeiten. Ein perfekter Ausdruck gelang nicht.

Mir lag für diesen Teil von Musicalc allerdings noch keine schriftliche Bedienungsanleitung vor. Da sich das gesamte Programm mittels ausführlicher Help-Texte (Bild 4) von selbst erklärt, ist diese normalerweise auch nicht nötig. Vielleicht fehlen jedoch hier genauere Hinweise auf diverse Druckkommandos.

Sämtliche Programme auf dieser Diskette funktionieren natürlich nur in Verbindung mit der Diskette 1. Denn nur ausschließlich mit der Synthesizer- und Sequenzerdiskette erstellte Kompositionen versteht der Scorer.

Nach dem Start liest man von der Diskette 1 oder einer anderen Diskette mit erstellten Presetfiles ein gewünschtes Preset ein, gibt an, welchen der 32 Songs man notieren will, wartet, bis der Song geladen ist und legt dann wieder die Score-Writer-Diskette ein. Das Score-Writer-Programm wird nun wieder geladen. Das Arbeiten mit diesen Programmen verlangt leider viele Wartepausen und öfteres Diskettenwechseln. Als nächstes bestimmen wir, ob der Ausdruck im 2/4, 3/4 oder 4/4 Taktschema erfolgen oder ob alle oder nur einzelne der drei Stimmen auf dem Papier erscheinen, welche Farben diese, beziehungsweise der Bildschirm und Hintergrund besitzen sollen.

Dann geht’s ab in den Printmode. Zwei verschiedene Druckmodi existieren. Einmal der sogenannte AUTO PRINT-Mode, in dem die gesamte Sequenz Zeile für Zeile bis zum Schluß ausgedruckt wird. Daneben gibt es den MANUAL PRINT-Mode. Hier können einzelne Sequenzteile ausgedruckt werden. Der Druckvorgang stoppt nach jeder fertigen Doppelzeile.

Hat man den Printvorgang angewählt, beginnt auf dem Bildschirm ein flackerndes Farbenspiel aus schnell wechselnden Hintergrundfarben. »Ich bin vollauf beschäftigt«, signalisiert die Software. Die Berechnung einer Doppelzeile dauert zirka eine Minute. Dann erscheint Bild 5 am Schirm.

Kurze Zeit später sollte der Drucker die Zeilen ausdrucken. Wie gesagt, tat er dies, trotz mehrmaligen Versuchen mit diversen Druckern, nicht.

Auf der Score-Writer-Diskette befinden sich noch weitere sehr wichtige Programme.

Das erste ist ein Synchronisationsprogramm, das den Commodore 64 mit weiteren C 64 oder auch einer Rhythmusmaschine synchronisiert. Dies ist bisher ein Novum im Bereich der Musiksoftware für den Commodore 64. So läßt er sich nun endlich in weiteres Equipment integrieren. Denn ohne Synchronisation spielt das Schlagzeug schon längst auf »und«, während die 64-Sequenz noch mit der »Eins« zu tun hat. Das »C 64-Quartett« wird sicher nicht mehr lange auf sich warten lassen. Dieses Programm heißt E. SYNC. Es kann nur als externes Programm über die Musicalc-1-Diskette aufgerufen werden. Man kann dann entweder den C 64 mit einem extern eingegebenen, zum Beispiel von einem Elektronik-Schlagzeug stammenden, Sync-Impuls synchronisieren, oder ein TTL-Clock-Signal vom C 64 an eine externe Einheit abgeben. Die Signale werden über den User-Port eingeschleust, beziehungsweise dem Expansion-Port ausgegeben. Doch Vorsicht beim Hantieren an den Ports! Bei unsachgemäßem Vorgehen können Baugruppen des Computers leicht ihren Geist aufgeben.

Das zweite wichtige externe Programm nennt sich LIST MAKER. Es erweitert den Sequenzer der Musicalc-1-Diskette, macht längere und komplexere Sequenzen möglich. LIST MAKER kann man als »Sequenz-Sequenzer« bezeichnen. Er bildet ganze Kompositionen aus den 32 Sequenzen und Sounds eines Presets. 64mal lassen sich Klang und Melodie hintereinander wechseln, wobei man noch jeweils bestimmen kann, wie viele 16er-Zyklen einer Sequenz-Sound-Kombination er hintereinander durchläuft, ehe LIST MAKER zur nächsten Kombination wechselt. So bilden wir durch Aneinanderhängen von einzelnen Sequenzen komplexe Musikstücke mit vielen Sound- und Melodieabschnitten. Die fertigen Kompositions-Listen speichern wir, mit Namen versehen, auf Diskette und spielen sie nach Belieben automatisch ab. Das Orchestrion von heute. Ein wirklich komfortables Sequenzersystem. In Bild 6 sehen wir eine der vier Listen, hier Step 49 bis 64, die den Ablauf der Komposition bestimmen.

Keyboardmaker (Bild 7) nennt sich die dritte bisher im Musicalc-System erschienene Programmdiskette.
Dies ist das Programm für alle Liebhaber der Musik fremder Kulturkreise. Hiermit spart man sich das Auswendiglernen und Einüben von Tonleitern. Diese Aufgabe übernimmt ab sofort der Commodore 64.

Die erste Option des Hauptmenüs heißt VISUAL.

Im oberen Bildschirmteil befindet sich ein Bedienungsmenü, darunter die QWERTY-Tastatur des Commodore 64, versehen mit der aktuellen Tonbelegung. Drückt man eine Taste, erscheint auf dem Bildschirm im zugehörigen Feld ein blinkender Cursor. Der entsprechende Ton klingt aus dem Lautsprecher. Soweit nichts Neues — das gab es schon oft. Die Tastenbelegung ist jedoch hier nicht fix, sondem beliebig wählbar. Im Bereich von sieben Oktaven können wir jeder Taste einen beliebigen Ton zuweisen. Die gewünschte Oktavlage gibt man mittels SHIFT plus 1,2,3... ein, die Töne mittels SHIFT plus C, D, E ... Der Ton »Des« läßt sich nur durch Erhöhung eines »C« darstellen. Es existiert kein Erniedrigungszeichen. Ein Manko in diesem Programmteil: Im Live-Spielmodus arbeitet es zu langsam. Spielt man zwei aufeinanderfolgende Töne etwas schneller, hinkt die Tonerzeugung meist etwas nach. Deshalb ist dieser Programmteil zum Spielen von schneller Melodik unbrauchbar. Die Keyboard-Layout-Daten lassen sich jedoch in das Sequenz-Programm der Diskette 1 transferieren. Spielt man hier dann im VOICE-Modus eine Melodie auf der QWERTY-Tastatur, klingen die einzelnen Töne entsprechend dem neuen Tastaturlayout und ohne Verzögerung.

Alle Keyboardlayouts lassen sich natürlich auf Disketten ablegen.

Ein hervorragender Einfall der Waveform-Leute war, zirka 50 Tonleitern aus allen möglichen Kulturbereichen als fertige Keyboardlayouts mitzuliefern. Dies stellt wirklich eine wahre Fundgrube für alle Liebhaber der Musik ferner Völker dar. Einen Teil der mitgelieferten Tonleitern sehen wir in Bild 8 und 9.

Leider wurde nicht berücksichtigt, daß nicht alle Völker mit unserem Intervallsystem arbeiten. Es hat eigentlich nicht sehr viel Sinn, einen der indischen Musikphilosophie entstammenden Raga Todi in unser Intervallsystem zu pressen. Waveform sollte in einer späteren Softwareerweiterung auch die unterschiedlichen Intonationen mit berücksichtigen. Dann wäre das System perfekt.

Zwanzig der erstellten Keyboardlayouts lassen sich zu einer sogenannten Scratch-Page zusammenfassen. Ein Preset mit 20 verschiedenen Keyboard-Belegungen gewissermaßen. Aus diesem Scratch-Page können wir dann ohne Diskettenoperationen einzelne Layouts abrufen, studieren beziehungsweise spielen. Diese Zusammenstellungen sind natürlich editierbar.

Musicalc ist ein Programmsystem für den Anspruchsvollen unter den Commodore 64-Musikern. Da man jeweils nur eine Stimme auf der Tastatur spielen kann, eignet es sich nicht zum polyphonen Spiel. Es ist mehr als Kompositions- und Abspielsystem gedacht. Bisher ein Novum: Es unterstützt den, der seinen Computer zusammen mit anderen Rhythmusinstrumenten beziehungsweise einem oder mehrerer weiterer C 64 synchron betreiben will. Sollte demnächst auch der Notenausdruck funktionieren, ist Musicalc in meinen Augen, momentan jedenfalls, eines der bestdurchdachten Musik-Software-Pakete.

(Richard Aicher/aa)

# TEXTOMAT – Büroanwendung zum kleinen Preis

> Gute Textverarbeitungs-Programme kosten häufig mehrere hundert Mark. Aber es geht auch billiger. Beim Textomat von Data Becker stimmt der Preis, und er kann auch mit den Leistungen wesentlich teuerer Programme konkurrieren.

Oft muß der Commodore 64 die Aufgaben eines Personal Computers übernehmen. So erfreut er sich beim Einsatz in der Textverarbeitung zunehmender Beliebtheit. Einen wesentlichen Beitrag dazu haben die Entwickler spezieller Textverarbeitungsprogramme, wie Textomat, geleistet. Die Textverarbeitung, eine der sinnvollsten und nützlichsten Anwendungen des Computers, birgt aber ein Handicap in sich: Sie läßt kaum Kompromisse zu.

Sinnvolles Arbeiten ist mit solchen Programmen nur dann möglich, wenn einige Grundvoraussetzungen erfüllt werden:

— Ein deutscher Zeichensatz auf dem Bildschirm, leicht zu handhabende, deutsche Benutzerführung — Umfangreiche Textformatierungsbefehle für den Ausdruck und den Bildschirm
— Die Möglichkeit zur Diskettenverwaltung
— Umfangreiche Anpassungsmöglichkeiten an verschiedene Drucker.
— Verschiebe,- Ersetz,- und Kopierfunktionen.
— und möglichst eine Schnittstelle zu einem Datenverwaltungsprogramm.

Alle diese Anforderungen zu erfüllen, verspricht der Textomat. Seine Geschichte ist eigentlich einen eigenen Artikel wert, denn angeboten wird das Programm schon seit über einem Jahr. In dieser Zeit reifte der Textomat von Version zu Version — nicht immer zur Freude der Käufer. Zum Test stand aber die bislang neueste Auflage dieses Programms zur Verfügung.

Textomat wird komplett mit Diskette und umfangreichem deutschen Handbuch geliefert. Das gesamte Programm ist ebenso wie das Handbuch ganz in Deutsch verfaßt. Sehr erfreulich, denn immer noch geistert in manchen Softwarehäusern die Vorstellung herum, daß professionelle Anwenderprogramme in englischer Sprache verfaßt sein müssen. Das insgesamt vorbildliche Handbuch macht selbst dem Computerneuling den Einstieg in die Textverarbeitung leicht. Es ist in einen Übungsteil, in dem alle Befehle schrittweise erklärt sind und einen Anwenderteil, der nochmals genauer auf alle Befehle eingeht, gegliedert.

Der Weg, der mit dem Textomat bei der Art der Textbehandlung beschritten wurde, hebt sich in einigen Punkten von anderen Konkurrenzprodukten ab. Der Textomat unterscheidet zwischen Schreib-, Kommando- und Menümodus. Texte werden im Schreibmodus erstellt.

Dazu stehen alle Buchstaben und Sonderzeichen sowie die Grafikzeichen, die sich mit der Commodore-Taste erreichen lassen, zur Verfügung. Im Kommandomodus werden alle Steuerzeichen in den Text eingegeben, die bei der Ausgabe auf den Drucker wirksam werden. Verschiedene Schriftarten lassen sich auswählen, Texte formatieren oder Zeilenabstände verändern. Wiederkehrende Redewendungen oder das aktuelle Datum können als Textbausteine definiert und problemlos aneinandergekettet werden; aber dazu später mehr. Der umfangreichste der drei Modi ist der »Menümodus«. In der untersten Bildschirmzeile sind die vier Hauptmenüs »Edit, Formular Ausgabe und Dienst« abgebildet. Nach dem Anwählen eines dieser Punkte beginnt der Kampf durch die Menülandschaft, die aus bis zu drei Untermenüs besteht (Bild 1). Soll beispielsweise der Inhalt einer Diskette eingelesen werden, so ist zuerst das Dienstmenü zu wählen, von da aus der Unterpunkt »Floppy« und dort angelangt wiederum der Punkt »Disketteninhalt zeigen«. Leider führt der Weg durch die Menüs nicht nur von oben nach unten, sondern auch von unten nach oben.

Eines der größten Handicaps des C 64 wurde beim Textomat elegant umgangen. Eine Textverarbeitung fordert in der Regel eine Darstellung von 80 Zeichen pro Zeile auf dem Bildschirm, denn ein Ausdruck hat ja meistens auch dieses Format. Da der C 64 aber nur mit einer 80-Zeichen-Karte oder mit einem entsprechenden Programm 80 Zeichen darstellen kann (wobei die Leserlichkeit bei der Software-Methode in Verbindung mit einem Fernseher stark leidet), wurden die Zeichen in ihrer Originalgröße belassen. Die Darstellung von mehr als 40 Zeichen wird durch automatisches horizontales Verschieben des Textes bewerkstelligt. Der Text kann dann ohne Rücksicht auf Textformatierung als zusammenhängende Folge von Wörtern eingegeben werden. Leider werden am definierten Zeilen-ende die Wörter unterbrochen und in der nächsten Zeile fortgesetzt. Diese Tatsache stört etwas, kann aber mit dem Prinzip des bildschirmorientierten Aufbaus erklärt werden. Die notwendige Formatierung des Textes wird erst kurz vor dem Ausdruck vorgenommen. Der Vorteil dieses Konzepts liegt darin, daß Texte allen Eventualitäten angepaßt werden können. Dazu stellt der Textomat eine nützliche Hilfsfunktion bereit. Alle häufig gebrauchten Formatbefehle können in Form von Formularen zusammengefaßt und abgespeichert werden. Ein einziger Text kann so durch einfaches Nachladen der Formatbefehle ein unterschiedliches Bild annehmen.

Wer aber lieber den Text schon auf dem Bildschirm formatiert haben will, kann dies durch Verwendung von »Fest-Zeichen« erreichen (Bild 2). Nun zur Praxis. Die erste Überraschung erlebt der Anwender kurz nach dem Laden. Er wird gefragt, welchen Schrifttyp er für die Bildschirmdarstellung wählt. Zur Auswahl stehen Standard-Deutsch/Amerikanisch und Alt-deutsch/Amerikanisch, sowie ein individueller Zeichensatz. Der Unterschied zwischen den Standard- und den Alt-Zeichensätzen ist lediglich eine etwas verschnörkelte Darstellung auf dem Bildschirm (nicht auf dem Drucker!). Eine hübsche, aber nicht notwendige Funktion. Interessant ist die individuelle Zeichendarstellung. Mit ihr ist es möglich, besondere wissenschaftliche oder sogar japanische Zeichen auf dem Bildschirm darzustellen (Bild 3). Sinnvoll anwendbar ist diese Funktion allerdings nur dann, wenn gleichzeitig ein Drucker mit ladbarem Zeichensatz, wie der Epson FX-80, zur Verfügung steht. Erst dann werden die auf dem Bildschirm dargestellten Sonderzeichen auch ausgedruckt. Ansonsten bleibt die Wahl des Zeichensatzes eine hübsche Spielerei. Leiderwird im Handbuch auf diese Funktion nicht genügend eingegangen. Beim Test gelang es deshalb erst nach mehreren Stunden, einen neuen Zeichensatz auszudrucken. Im einzelnen ist es notwendig, einen Zeichensatz zu entwerfen — ohne geeignetes Hilfsprogramm ein fast aussichtsloses Unterfangen. Außerdem muß der gesamte Vorgang für den Drucker wiederholt werden, denn Bildschirmdarstellung und Druckbild (Bild 4) sind zwei grundverschiedene Angelegenheiten. Der fertige Zeichensatz wurde dann vor den Textomat geladen und in den Zeichenspeicher des FX-80 übertragen.

Der Textomat kann auch den deutschen Zeichensatz darstellen. Nach der Wahl des deutschen Zeichensatzes werden einige Tasten des C 64 umbelegt, das »Z« und das »Y« werden vertauscht und die deutschen Umlaute definiert. Der erste Versuch, diese Zeichen auch auszudrucken, wurde mit dem Epson-Drucker vorgenommen, der ja bekanntlich über einen deutschen Zeichensatz verfügt. Leider ist es vorher notwendig, jedem einzelnen Zeichen einen eigenen, im Druckerhandbuch beschriebenen, Wert zuzuordnen; ein langwieriges und fehlerträchtiges Unterfangen. Andererseits wird dadurch sichergestellt, daß größte Flexibilität erhalten bleibt. Die fertige Einstellung wird zusammen mit den ebenfalls definierbaren Steuercodes auf einer sogenannten Parameterdiskette abgespeichert.

Dadurch entfällt die erneute Eingabe aller Werte. Wünschenswert wäre allerdings, wenn eine solche Einstellung für die gängigen Schnittstellen und Drucker bereits auf der Diskette mitgeliefert würde. Denn nicht jeder Anwender ist mit den innersten Geheimnissen der Zeichendarstellung vertraut.

Zurück zum deutschen Zeichensatz. Nach den vorgenommenen Einstellungen druckte der Textomat mit einem Epson FX-80 ordnungsgemäß den gesamten Zeichensatz aus. Lediglich beim Görlitz-Interface älterer Bauart kam es zu gar keinem Ausdruck, da erst die neueren Versionen mit Textomat zusammenarbeiten. Wie verhielten sich aber Commodore-Drucker, namentlich der 1526 oder MPS 802, die ja keinen deutschen Zeichensatz kennen? Das Ergebnis war verblüffend und erfreulich zugleich, der angeschlossene MPS 802 stoppte bei jedem Umlaut kurz, druckte dann aber das gewünschte Zeichen. Ein kleiner Programmiertrick mit großer Wirkung! Das beim MPS 802 (früher VC 1526) mögliche, eine frei definierbare Zeichen wird durch ständiges Umdefinieren zur Darstellung der Umlaute verwendet. Auch die grafikfähigen Commodore-Drucker wie der MPS 801 (VC 1525) ließen keinen Umlaut aus. Kein anderes uns bekanntes Textverarbeitungssystem verfügt über diese Besonderheit. Der Ausdruck dauert zwar etwas länger, aber er erfüllt alle Anforderungen an einen sauberen Ausdruck. Nur wer ganz genau hinschaut, erkennt, daß die Umlaute nicht exakt zwischen den anderen Buchstaben stehen.

Einer der Hauptvorteile der computergestützten Textverarbeitung ist die Möglichkeit, den Text beliebig zu verschieben, zu editieren und zu korrigieren, ohne dabei Zeit zu verlieren und kiloweise Altpapier zu produzieren. Der Textomat ist in diesem Bereich mit einigen sehr interessanten Befehlen ausgestattet. Die sogenannten Blockoperationen erlauben es, einzelne Textblöcke zu markieren und diese nach Belieben zu verschieben, zu löschen, oder zu kopieren.

Leider muß ein Block immer nur aus ganzen Zeilen bestehen, so daß nach dem Blockkommando immer noch etwas nachgebessert werden muß. Aber auch hierzu sind eine Reihe von Tastenfunktionen vorgesehen. Wer den Commodore-Editor gewöhnt ist, muß allerdings eine kleine Änderung berücksichtigen. Bei einem Druck auf die DEL-Taste wird das Zeichen gelöscht, an dem der Cursor steht und nicht wie üblich, das Zeichen links von ihm. Nach Betätigen der Taste »INS« wird in der Informationszeile am oberen Bildschirmrand »Einf.« für »Einfügen« angezeigt. Alle nachfolgend eingegebenen Zeichen werden nun in den bereits bestehenden Text eingeschoben.

Die Funktionstasten f3 bis f6 machen ein wortweises Vor- und Zurückspringen, aber auch Sprünge an den Textanfang und das Textende möglich.

Eigentlich wäre der Textomat jetzt schon ein gutes Textverarbeitungsprogramm, aber er bietet noch mehr. Einfache arithmetische Operationen sind ihm nichts Unbekanntes. Im Kontrollmodus können beliebig viele Zahlen zur Berechnung herangezogen werden. Die Genauigkeit ist hinreichend, denn sogar Nachkommastellen werden berücksichtigt. Eine hilfreiche Funktion, die noch dadurch verbessert werden könnte, wenn die Verknüpfungsoperanten definierbar wären.

Wesentlich wichtiger, da häufiger gebraucht, ist die Schnittstelle zu einem Datenverwaltungsprogramm. Der Sinn dieser Funktion liegt in dem Erstellen von Formbriefen und Rundschreiben. Im Handbuch wird auf das Datenverwaltungsprogramm aus gleichem Hause verwiesen, dem Datamat. Leider konnten wir diese Funktion nicht in befriedigendem Maße testen, da uns dieses Programm nur in einer veralteten, viel zu langsamen Version vorlag. Mit etwas Übung und Geduld kann es aber gelingen, den richtigen Datensatz aus dem entsprechenden Datenfeld zu lesen. Sie merken schon, ganz einfach ist diese Funktion nicht zu handhaben.

Wer glaubt, jetzt das Ende der Fähigkeiten von Textomat erreicht zu haben, irrt. Beim Test gefielen noch zwei Dinge besonders. Die Diskettenoperationen und die Suchfunktion. Erstere beginnen mit der Wahl des entsprechenden Laufwerkskonstellation (Bild 5). In einem einfachen Wählmenü kann eingestellt werden, wieviele Laufwerke (1 oder 2) und mit welchem Interface (IEEE 488 oder serieller IEC-Bus) sie angeschlossen sind. Der Einsatz zweier 1541 oder einem 4040 Doppellaufwerk wird somit unterstützt. Natürlich sind auch alle Kommandobefehle des Laufwerkes verfügbar. Die Besitzer eines Kassettenlaufwerkes werden allerdings enttäuscht. Denn weder das Programm noch seine Dateien arbeiten mit der Kassette zusammen.

»Suchen und Ersetzen« ist die Aufgabe der Suchfunktion. Beliebige Textstrings können hiermit entweder einzeln oder global durch einen anderen ersetzt werden. Dies ist ein anderer Weg, Serienbriefe zu erzeugen, indem der Name eines Adressaten durch den eines anderen im gesamten Text ersetzt wird. Das ist zwar etwas umständlicher, aber es erspart den Kauf des Datamat jedenfalls in dieser Beziehung).

Der Textomat stellt ein leistungfähiges Textverarbeitungsprogramm mit leichten Verbesserungsmöglichkeiten dar. Mit ihm ist ein durchaus sinnvolles und komfortables Arbeiten in vielen Bereichen möglich, auch wenn die Steuerung der vielen Funktionen manchmal etwas gewöhnungsbedürftig ist. Eine einzige Funktion konnte im Test leider gar nicht überzeugen: Das Ausdrucken. Nach dem Start des Ausdrucks ist kein Anhalten und keine Korrektur mehr möglich. Dies ist besonders widrig, wenn das gesamte System noch nicht optimal ist. Wer vergessen hat, seine Drucker anzustellen oder wer in Verbindung mit einem Epson-Drucker vergessen hat, die Parameterdiskette zu komplettieren, wird nichts erhalten. Auch nicht seinen Text zurück. Deshalb Vorsicht beim Ausdruck, erst abspeichern, dann drucken! Es wäre schön, wenn die Anpassung an die verschiedenen Drucker etwas komfortabler gestaltet werden könnte, denn die Umrechnung und die Eingabe von hexadezimalen Zahlen ist nicht jedermanns Sache.

Einen Bereich gibt es allerdings, in dem der Textomat »noch« nicht zu schlagen ist: Der Textomat ist jede seiner 99 Mark wert und es wäre wünschenswert, wenn auch andere Softwarehäuser ähnlich gute Programme in dieser Preisklasse anbieten würden.

(Arnd Wängler/aa)

# Das Piano für den Aktenkoffer

> Ein Konzert für drei Stimmen, live gespielt auf einer Schreibmaschinentastatur — aufgenommen mit einer zum Tonbandgerät umfunktionierten Diskettenstation. Das Programm Synthimat 64 macht’s möglich.

Willkommen im »Wunderland der synthetischen Musik«, beginnt das Bedienungshandbuch und das ist nicht zuviel versprochen. Aber auch das »Handbuch« ist ein Wunder, es erinnert eher an Fotokopie, als an Buchdruckerkunst von heute. Auch mit der grafischen Gestaltung hat man sich so gut wie keine Mühe gegeben. Vielleicht sollte man sich hier doch endlich von der Ansicht lösen, diese Handbücher würden nur Freaks lesen, denen es nur um Informationsvermittlung geht. Musiker, und sicher viele davon wollen Synthimat einsetzen, sind kreative Leute, denen meist auch die Form wichtig ist.

## Die Bedienungsanleitung: Mäßiger Druck, aber guter Inhalt

So mäßig das Aussehen, so gut der Inhalt. Der Autor hat sich viel Mühe gegeben und selbst schwierige Sachverhalte anschaulich erklärt. So erfährt man nicht nur alles wesentliche zu den einzelnen Bedienungsbefehlen, sondern auch das Wichtigste über Klangsynthese, Filterung, Hüllkurven, Schwingungsformen, Funktionsweise des SIDs und so weiter.

Das Programm bietet Möglichkeiten, von denen manch »echter« Synthesizer nur träumt. Insgesamt stellt es elf Oszillatoren zur Verfügung. Zwei getrennt spielbare »Tastaturen« erlauben, Begleitung und Melodiestimme mit unterschiedlichen Sounds unabhängig voneinander, zu spielen. Bis zu 256 verschiedene Klänge merkt sich Synthimat 64 softwaremäßig. Ein komplettes Lied kann in Realtime auf Diskette gespielt werden, als wäre die Diskette ein Tonband. Insgesamt finden auf einer Diskette 9x256 Soundprogramme und neun verschiedene Lieder Platz.

Das Programm schöpft alle Möglichkeiten des SIDs voll aus. Synthimat 64 stellt alle drei DCOs des SID-Chips, mit allen acht möglichen Kurvenformen zur Verfügung. Die DCOs lassen sich einzeln in % Ton-Schritten stimmen. Auch alle Filterparameter, die der Chip bietet, stehen zur Verfügung. Gleiches gilt für die ADSRs. Sämtliche Parameter lassen sich für jede der drei Stimmen separat einstellen.

## Elf Oszillatoren

Zusätzlich zu den Features des SIDs, realisierten die Entwickler softwaremäßig noch 8 LFOs. Diese verfügen genau wie die Oszillatoren über 8 verschiedene Wellenformen. Jeweils 2 LFOs modulieren bei Bedarf einen DCO, und zwar einer die Pitch, der andere die Pulsbreite. Von den 2 verbleibenden LFOs kann man mit einem den Filter, mit dem zweiten die Lautstärke der drei Stimmen beeinflussen. Die Geschwindigkeit jedes LFOs läßt sich separat bestimmen.

Recht komfortabel gerieten auch die Ringmodulations- und Syncmöglichkeiten. Acht verschiedene Arten der Beeinflussung der DCOs untereinander stehen zur Auswahl. Zu guter letzt hat man auch einen Pitch-bender nicht vergessen.

An Möglichkeiten mangelt es Synthimat sicher nicht.

Der wunde Punkt am Ganzen, zumindest für jeden klaviergewohnten Musiker, ist, wie üblich, die Tastatur selbst. Es erfordert schon etwas Umgewöhnungszeit und Geduld, bis man auf den Schreibmaschinentasten annähernd so flüssig spielen kann wie auf einer Klaviertastatur. Vor allem bei beidhändigem Spiel auf den übereinanderliegenden Tastaturbereichen, kann es schon einmal passieren, daß man sich die Finger verknotet. Doch mittlerweile gibt es hier Abhilfe. Zwei ordentliche Klaviertastaturen kamen in jüngster Zeit auf den Markt. Angeschlossen an den Commodore 64 wird dieser dann wirklich zum Musikinstrument.

Nun soll es aber losgehen. Wir legen die Diskette ein und tippen auf der Tastatur des Commodore 64: LOAD ”*”,8,1 dann RUN. Der Ladevorgang startet, und nach kurzer Zeit erscheint ein farbiges Bild auf dem Schirm (Bild 1).

Spätestens jetzt hat der Computer vergessen, daß er ein Computer ist. Man sollte ihn ab sofort auch besser »Synthi« nennen. Alle Tastenfunktionen sind jetzt neu definiert und speziell auf das Programm zugeschnitten. Dies wird höchstens den Computerfan anfangs irritieren, der Musiker kann so jedoch getrost vergessen, daß er es mit einem Computer zu tun hat.

## Getrennte Keyboards, für Solo und Begleitung

Drückt man jetzt auf eine Taste der oberen zwei Buchstabenreihen, so klingt ein Ton aus dem Lautsprecher. Wir spielen gerade auf dem sogenannten Solokeyboard. Die dritte und vierte Tastenreihe stellen die zweite Klaviatur, das Begleitkeyboard dar. Drei Töne können wir maximal gleichzeitig auf den zwei Tastaturen spielen. Bei beiden Klaviaturen entspricht jeweils die obere Tastenreihe den schwarzen Halbtontasten, die untere, den weißen Ganztontasten einer »richtigen« Klaviertastatur.

Einen gespielten Ton meldet Synthimat 64 grafisch mittels weißem Punkt beziehungsweise Balken, auf der entsprechend symbolisierten Taste am Bildschirm. Drückt man auf die Shift-Taste, so schreibt Synthimat 64 die Buchstabenbezeichnung der Commodore 64-Tastatur in die Tastengrafik des Bildschirms.

Betrachten wir das Arbeitspanel unseres Synthimat 64 (Bild 1). Hier sind die einzelnen Funktionsbereiche des Schirmbildes zu sehen. Zusammengehörige erkennt man jeweils leicht an der gemeinsamen Farbe. Diese Bildschirmgrafik bleibt übrigens während des gesamten Arbeitens mit Synthimat 64 erhalten. Sie bildet sämtliche veränderbare Funktionen mit den jeweils eingestellten Werten ab. Mühsames Hin- und Herschalten diverser Menüs bleibt also erspart.

Der obere, von rotbraunen Linien eingeschlossene Teil des Bildschirms, zeigt die für die Tonerzeugung wichtigen Parameter. Im unteren Bildschirmbereich erkennen wir die beiden Tastaturdiagramme, die Anzeigenfelder für die Stimmung der Oszillatoren und die aktuelle Bedienungsfunktion.

Bewegung bringen zwei Anzeigen ins Bild. Eine Uhr (unter der weißen Schrift Synthimat 64), die auf Ortszeit gestellt werden kann sowie die SYS-Uhr im rechten unteren Bildabschnitt. Letztere zeigt an, wie schnell das Programm gerade abläuft.

Wie arbeitet man nun mit Synthimat? Zunächst will die Software wissen, was man überhaupt mit ihr anzustellen gedenkt. Sounds einstellen, die VCOs den Keyboards zuordnen, Songs aufnehmen oder abspielen, Glides und Tunes einstellen, oder Sound und Songprogramme von der Diskette in den Computer laden beziehungsweise speichern.

## 13 verschiedene Bedienfunktionen bringen Ordnung in das System

Insgesamt warten 13 verschiedene Bedienungsfunktionen auf ihren Einsatz. Die jeweils gültige zeigt Synthimat 64 mit weißer Schrift auf dem Bildschirm, oberhalb der Melodietastatur, an. Die einzelnen Funktionen rufen wir mit den vier Funktionstasten auf. fl dient zum Durchblättern der einzelnen Funktionen, f3 startet die jeweilige Funktion und mit f7 verläßt man sie wieder.

Betrachten wir kurz die einzelnen Bedienungsfunktionen. Mit SET REAL-TIME CLOCK stellen wir die eingebaute Echtzeituhr. Mit der Funktionstaste f3 wählen wir den einzustellenden Bereich (Std., Min., Sec., %o Sec.); jeder Druck auf f3 schaltet dann automatisch einen Bereich weiter. Dieses praktische »Step-Prinzip« wird für alle wählbaren Einstellungen beibehalten. Mit f5 läßt sich nun der gewünschte Wert einstellen. Ein Druck auf f7 und die Uhr startet. Damit hat man die Funktion SET REAL-TIME qLOCK wieder verlassen. Wir können nun einen anderen Funktionsbereich anwählen.

Mit der Funktion SET VCOS TO KEYBOARD ordnen wir die drei Oszillatoren den beiden Keyboards zu. Jede der drei Stimmen, die jeweils aus einem Oszillator mit zugehöriger Klangeinstellung bestehen, läßt sich entweder auf das Solo- oder das Begleitkeyboard legen. Die betreffenden Stimmen werden sofort durch inverse Darstellung der entsprechenden Ziffern 1, 2 oder 3, links neben den Keyboards, am Bildschirm gekennzeichnet.

Während das Einstellens kann man übrigens weiterspielen. Man hört bei allen Einstellarbeiten sofort die Auswirkung einer Parameteränderung auf den Sound. Auch im Schirmbild zeigt Synthimat 64 jede Parameteränderung sofort grafisch an. Entweder numerisch oder mittels Hintergrundeinfärbungen beziehungsweise mit Symbolen. Diese Methode wird im ganzen Programm beibehalten und vereinfacht das Arbeiten ungemein. Deshalb kann man den Bildschirm wirklich als das Bedienfeld eines komfortablen Synthesizers betrachten, der ständig alle gültigen Werte und ^Zuordnungen anzeigt.

Will man mit anderen Instrumenten zusammenspielen, müßen wir Synthimat 64 erst einmal stimmen. Dies geht mit der Funktion SET TUNE FOR VCO. Die Stimmung kann in Ys Tonschritten über den Bereich einer Oktave verändert werden. Da sich die einzelnen Oszillatoren getrennt stimmen lassen, lassen sich auf diese Weise Phasingklänge erzielen (Schwebung). Dies ist wichtig für Streichereinstellungen. Hat man sich jedoch beim Durchsteppen der Tuningeinstellungen einmal um einen Step geirrt, müssen alle nachfolgenden 99 Werte brav durchschritten werden. Rückwärts schreiten ist leider nicht möglich. Das Tuning der drei Oszillatoren wird auf dem Schirm numerisch angezeigt, ganz rechts unten.

SET GLIDE TO VCO ermöglicht gleitenden Tonverlauf zwischen zwei aufeinanderfolgend gespielten Tönen. Musiker nennen diesen Effekt auch Portamento. Die Glide-Zeiten können für jede Stimme unabhängig eingestellt werden. Die kleinste Abstufung ist jedoch bereits etwas groß gewählt.

EQUALIZE VCOS BY erlaubt das Kopieren sämtlicher Parametereinstellungen einer Stimme auf eine andere, mit einem einzigen Befehl. Das erspart viel Zeit und wird vor allem benötigt, wenn Akkorde gespielt werden sollen, deren Töne gleich klingen.

SOLO/MULTI PLAY MODE: In der Solostellung spielt nur ein VCO jeweils einen Ton, im Multiplaymode hingegen spielen alle verfügbaren Oszillatoren den gleichen Ton. Bei harmonisch verstimmten Oszillatoren erklingt so mittels einem Tastendruck ein ganzer Akkord auf einmal.

Mit der ACCOM: MELODY-CHORD-Funktion können im Chord-Modus auf der Begleittastatur Arpeggios gespielt werden. Drückt man zwei oder mehrere Tasten gleichzeitig, wird — angefangen mit dem tiefsten zum höchsten — zyklisch ein Ton nach dem anderen durchgespielt. Ähnlich der Begleitautomatik älterer Heimorgeln.

## Die Floppy 1541 als Tonbandgerät

Zum Tonbandgerät wird die Floppy in den beiden Bedienfunktionen ENGAGE DIRECT TO DISK und ENGAGE DIRECT FROM DISK. Im ersten Modus, dem Aufnahmemodus, wird alles was man auf der Tastatur spielt, direkt auf die laufende Diskette gespeichert. Das Ganze ähnelt deshalb einer Tonbandaufnahme, mit dem Unterschied, daß hier digitale Daten aufgenommen werden. Hat man sich einmal verspielt, was bei der Schreibmaschinen-Tastatur leicht vorkommen kann, muß man noch einmal von vorne beginnen. Einzelne Teile des Stückes lassen sich nicht löschen und neu einspielen. Synthimat 64 ist das einzige Programm, das Songs auf diese Art und Weise direkt auf die laufende Diskette speichert, ohne Umweg über den Arbeitsspeicher des Computers.

Die Sequenzen können nur in Realtime über das »Keyboard« eingespielt werden. Leider existiert keine Composerfunktion für weniger virtuose Softwarefreaks.

Insgesamt haben auf einer Diskette 9 Lieder Platz. Sie werden als sogenannte Soundfiles gespeichert. Welche Soundfilenummer ein Song bekommen soll, können wir in der Bedienungsfunktion SET DISK FILE bestimmen.

Neben den Song-Directfiles existieren noch sogenannte Registerfiles. In diesen legt man die Klangparameter ab. Insgesamt haben in jedem Registerfile 256 verschiedene Klangeinstellungen, also komplette Synthiprogrammierungen, Platz.

## 256 verschiedene Klangprogramme im Arbeitsspeicher

Recht einfach geht die Soundprogrammierung in der Bedienfunktion SET SID 6581 REGISTER, vonstatten. Insgesamt existieren 44 voneinander unabhängig einstellbare Klangparameter (Bild 2).

Mit den zwei Funktionstasten f1 (vorwärts) und f2 (rückwärts) dirigiert man einen Cursorpfeil von Parameter zu Parameter. Am gewünschten Parameter angelangt, erhöht ein Druck auf Taste f5 den Parameter um einen Wert. Die Taste RETURN erniedrigt denselben jeweils um einen Wert. In Bild 2 erkennen wir, welche Parameter im einzelnen veränderbar sind und in welchen Abstufungen. Es lassen sich dann in jedem Feld die möglichen Werte in aufsteigender oder abfallender Reihenfolge durchschreiten. Die Klangveränderung hört man sofort. Es handelt sich also um einen echten Editmodus.

Synthimat stellt alle drei DCOs des SID-Chips, inklusive aller acht möglichen Kurvenformen, zur Verfügung. Man nennt die eigentlich digital gesteuerten Oszillatoren hier, aus historischen Gründen, VCOs. Die jeweils angewählte Kurvenform erscheint, im zugehörigen VCO-Anzeigefeld, in Zeile 1 unseres Bildschirms. Die Kurvenformen werden mit Symbolen angezeigt. Direkt daneben die Fußlage des jeweiligen Oszillators. Fußlagen sind Oktavbezeichnungen der Orgelkunde. Die tiefste hier spielbare Fußlage ist 64 Fuß, die höchste 1 Fuß. Insgesamt stehen 8 Oktaven zur Verfügung. Hat man die Rechteckform für einen Oszillator angewählt, kann man auch dessen Pulsbreite variieren, angezeigt neben der Fußlage. Die Pulsbreite kann in 4096 Schritten verändert werden. Sämtliche Parameter lassen sich für jede der drei Stimmen separat einstellen.

Zusätzlich zu 3 VCOs des SIDs realisierten die Entwickler softwaremäßig noch 8 langsamschwingende Oszillatoren (LFOs). Diese verfügen, genau wie die Oszillatoren, über 8 verschiedene Wellenformen. Jeweils 2 LFOs modulieren einen DCO und zwar einer die Pitch, der andere die Pulsbreite. Ihre Parameter stehen in der zweiten Zeile des Bildschirms, jeweils unter dem zugehörigen VCO-Einstellfeld. Die ausgewählte Kurvenform wird mit einem Symbol, die Modulationsfrequenz numerisch angezeigt. Die Modulationstiefe kann nur für alle drei Oszillatoren gemeinsam bestimmt werden und zwar mit dem roten Balken unter der Realtime-Uhr. Von den 2 verbleibenden LFOs kann man mit einem Filter, mit dem zweiten die Lautstärke der drei Stimmen beeinflussen. Mit der Zuordnung von Kurvenformen und LFOs muß man etwas experimentieren. Die Geschwindigkeit jedes LFOs läßt sich separat bestimmen. LFO 7 wirkt, wie schon gesagt, auf den Filter, LFO 8 auf den DCA.

Die Hüllkurvengeneratoren (ADSRs), bestimmen den zeitlichen Verlauf der Lautstärke des Klanges. Bei Synthimat 64 ist pro Stimme ein ADSR vorhanden. Alle vier Hüllkurvenbereiche, also Attack, Decay, Sustain und Release lassen sich getrennt bestimmen. Die Emstellzeiten reichen von zwei Millisekunden bis acht Sekunden bei Attack, von sechs Millisekunden bis 24 Sekunden jeweils bei Decay und Release.

Auch die Filtermöglichkeiten wurden alle verwirklicht: Tiefpaß, Bandpaß, Hochpaß sowie fünf Mischformen. Filterfrequenz und Gütefaktor sind regelbar. Die Werte werden in der vierten Zeile links am Bildschirm dargestellt.

Komfortabel gerieten auch die Ringmodulations- und Syncmöglichkeiten. Acht verschiedene Arten der Beeinflussung der DCOs untereinander stehen zur Auswahl. Und hiermit erschließt sich Synthimat 64 das weite Feld von Ufo- und Flipperklängen, Gongs und Meeresbrandung.

Es dauert gewiß einige Zeit, bis man sich durch die Vielzahl der Möglichkeiten, die auch verwöhnten Ansprüchen genügen, hindurchprobiert und gelernt hat, bestimmte Sounds mit dem Commodore 64 zu programmieren. Doch dies geht Musikprofis mit weit teureren Anlagen noch viel schlimmer. Durchhalten lautet die Devise!

An Möglichkeiten mangelt es Synthimat 64 sicher nicht. Manch ordentlicher Synthi mit weit höherem Preis bietet weit weniger! Das Programm kostet ganze 99 Mark.

(Richard Aicher/aa)
























































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































