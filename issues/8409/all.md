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

# Computer-Music – Komponieren leicht gemacht

> Mit dem VC 20 Music-Composer können Sie auf einfache Weise bis zu dreistimmige Partituren programmieren.

Das Programm arbeitet nicht etwa mit Zahlen oder Buchstaben, sondern benutzt die gewohnte Standardnotenschrift.

Im Compose-Modus fordert Sie der Computer auf, zwischen drei Stimmen zu wählen:
Voice 1 (Alt)
Voice 2 (Tenor)
Voice 3 (Sopran)

Haben Sie sich nun für eine der drei Stimmen entschieden, wird nach der gewünschten Tonart gefragt. Wie jeder Musiker weiß, gehört zu einer vernünftigen Komposition auch ein Takt. Bei der Takteingabe werden allerdings auch äußerst seltsame Takte akzeptiert (zum Beispiel 3/7 Takt, 1/9 Takt etc.).

Nach der Taktwahl erscheint auf dem Bildschirm die Komponier- beziehungsweise Bearbeitungsseite (EDIT-PAGE). Mit den Cursor-Tasten können Sie nun die gewünschte Note (ganze Note bis 1/32 Note) anwählen und diese in eine Notenzeile setzen. Auf Wunsch kann diese Note nun er--höht, erniedrigt oder punktiert werden. Entsprechend lassen sich auch beliebig lange Pausen setzen. Die Taktstriche müssen Sie sich leider selber setzen.

Wie laut eine Passage gespielt werden soll, wird jeweils in italienischen Begriffen angegeben. Es stehen sechs Lautstärken, von pianissimo (= sehr leise) bis fortissimo ( = sehr laut) zur Verfügung.

Die Editiermöglichkeiten des Programms sind gut. Noten lassen sich bequem einfügen oder löschen.

Da sich alle drei Stimmen unabhängig voneinander programmieren lassen, können auch polyphone (= mehrstimmige) Partituren gespielt werden. Dies geschieht im PLAY-Modus. Nach der Frage DISPLAY WHICH VOICE? kann die Notation der gewünschten Stimme parallel zur Melodie verfolgt werden. Das Tempo läßt sich stufenweise von 1 (= sehr schnell) bis 9 (= sehr langsam) anwählen.

Damit Sie nicht jedesmal das 4. Brandenburgische Konzert von Johann Sebastian Bach neu eingeben müssen, können Sie jedes Stück wahlweise auf Kassette oder Diskette abspeichern und später erneut laden.

### Fazit

Sowohl für den musikalischen Anfänger als auch für den Fortgeschrittenen bietet der VC 20 Music-Composer zahlreiche Möglichkeiten, musikalische Ideen zu verwirklichen.

‚Computer Music' von Thorn Emi Video ist als Steckmodul für den VC 20 erhältlich.

(C.Q. Spitzner/B.Carli)

# Brandaktuell aus USA: Musik Neuigkeiten

> Ein weiteres Musik-Keyboard für den Commodore 64

Auch in den USA präsentierte man ein Keyboard für den Commodore 64. Das Colortone Synthesizer Keyboard. Drei Oktaven besitzt das von Waveform (Musi-calc!) entwickelte Keyboard und ein futuristisch anmuten-des Design, das auch jedem wirklichen Synthesizer alle Ehre machen würde. Mit dem Keyboard können Melodien per Klaviatur in die Musicalc I Software eingespielt werden, was bisher nicht möglich war. Die Songs lassen sich dann wie bekannt mit Musicalc bearbeiten oder in Notenschrift ausdrucken. Somit wäre das System Commodore 64, Floppy 1541, Monitor, Colortone-Keyboard und Musicalc-Software ein komplettes Musiksystem, das auch Keyboarder spielen können, ohne sich die Finger auf einer QWERTY—Tastatur zu verrenken. Der Preis des Colortone-Keyboards wird sich in den USA zwischen 200 Dollar und 300 Dollar bewegen.

Ein weiteres dreistimmiges, vier Oktaven umfassendes Musik-Keyboard, mit dem man die drei Soundgeneratoren des SID-Chips kontrollieren kann, ist seit kurzem in England erhältlich. Es besitzt zwei Slide-Regler, deren Funktion man per Software selbst definieren kann. Hiermit lassen sich zum Beispiel Vibrato-, Pitch-bend- oder ähnliche Effekte bequem regeln. Zu diesem Keyboard wird passende Musiksoftware mit Sequenzer und Realtime-Spielmöglichkeiten geliefert. Man arbeitet momentan an einer Softwareerweiterung, mit der dann zirka 0,8 Sekunden Naturklang aufgenommen, gespeichert und per Keyboard über vier Oktaven gespielt werden. Das Microsound 64-Keyboard ist bisher leider nur in England erhältlich. Ich werde sobald als möglich darüber berichten.

## MIDI-Interface- und Software auch in einer C 64-Version erhältlich

Roland vertreibt ein intelligentes MIDI-Interface mit eigenem Mikroprozessor, das mittels Interface-Karte an Apple II und IBM PCs angeschlossen werden kann.

In Kürze erscheint nun auch eine Version für den Commodore 64. Das Interface verfügt über diverse Synchronisationsmöglichkeiten (Tape Sync, Sync von Roland-Drumy-Units) und erspart durch seine eigene Intelligenz dem externen Computer viel Arbeit. Die C 64-MIDI-Software existiert momentan ebenfalls nur in einer Apple II- und IBM-Ver-sion, man schreibt aber gerade fleißig auf den C 64 um. Diese Roland MIDI-Recorder-Software für den Commmodore 64 wird dann, genau wie die bisherigen Versionen, acht Tracks zur Verfügung stellen, die 16 Kanäle ansprechen können. Timing-Fehler lassen sich nach der Aufnahme automatisch korrigieren. Vor jeder Aufnahme kann man die Anzahl der aufzunehmenden Takte und der Vorzähl-Takte bis zum Aufnahmebeginn bestimmen.

## Microsound 64 — Keyboard mit Musiksoftware für den Commodore 64

Weitere Features: Metronom Temporegelung, Pitchbend. Das Interface kostet zirka 600 Mark, die zugehörige Software mit Interfaceadapter voraussichtlich zirka 300 Mark.

## IMA, die Internationale MIDI Association bietet Mitgliedschaft an

Alle an der Entwicklung des MIDI-Systems Interessierte, können in der International Midi Association (IMA) Mitglied werden. Die IMA ist eine nichtkommerzielle Einrichtung. Sie verfügt über sämtliche Informationen zum aktuellen Stand des MIDI-Geschehens. Die Gesellschaft versucht, ein weltweites Forum des Gedankenaustausches zu sein. Die Mitglieder unterteilt man in drei Gruppen: Hersteller, Händler und Anwender. Für jede Kategorie werden spezifisch zugeschnittene Informationen angeboten.

Der Mitgliedsbeitrag beläuft sich für Anwender auf jährlich 40 Dollar, zuzüglich 5 Dollar Postgebühren. Dafür erhält man das »MIDI Specification Manual« kostenlos. Diese Fundgrube für MIDI-Technik-Freaks kann man auch als Nichtmitglied, zum Preis von 10 Dollar zuzüglich 5 Dollar Postgebühren, beziehen.

Daneben existieren noch eine Reihe anderer interessanter Angebote, die Mitglieder kostenlos oder zumindest ermäßigt erhalten. Zum Beispiel, das monatlich erscheinende »IMA Bulletin« vollgepackt mit den allerneuesten Informationen zum MIDI-Standard, Produktinformationen, Kontaktadressen anderer Mitglieder, Seminarpläne und Termine, der 36 mal jährlich erscheinende »IMA Update Service« und jährlich herausgegebene »IMA Sourcer« mit Nachrichten über MIDI Equipment. Detailliertere Informationen bietet die »IMA Membership Information Brouchure«. Diese erhält man über: IMA — The International MIDI Association, 8426 Vine Valley Drive, Sun Valley, CA 91352

(Richard Aicher/aa)

# MIDI – Glanz und Elend eines Interfaces

> Für die meisten Profi-Keyboarder ist der Computer mittlerweile zum unentbehrlichen Begleiter auf den Bühnen der Wert geworden. 1983 haben sich fast alle Synthesizerhersteller auf ein einheitliches Keyboard-Bus-System, das Midi, geeinigt. Seither ist es auch ohne Lötkolben möglich, mehrere Keyboards, Rhythmusmaschinen und Effektgeräte, Takt für Takt synchron, durch einen Song zu jagen. Und wenn man will, nimmt einem der Computer sogar das Spielen ab. Doch war die Einführung dieses Systems auch mit Schwierigkeiten verbunden.

Noch vor einem Jahrzehnt war ein Synthesizer ein riesiges Klangmonster, vollgestopft mit Analog-Elektronik. Dank moderner Mikroprozessortechnik hat sich dies jedoch innerhalb weniger Jahre grundlegend gewandelt. Synthesizer von heute sind klein und handlich, kaum noch größer als die Tastatur und voll polyphon, also vielstimmig spielbar. Alle Klangparameter lassen sich heute problemlos abspeichern und stehen nach einem Druck auf ein Knöpfchen sofort und jederzeit wieder zum Spiel bereit. Zeit ist kostbar, vor allem auf der Bühne.

Die Arrangements moderner Popsongs konnten dank moderner Studiotechnik unheimlich verfeinert werden. Mit einer 24-Spur-Maschine, einem guten Techniker und viel Zeit, läßt sich heute aus einer Fünf-Mann-Combo ein vielstimmiges Orchester zaubern. Die einzelnen Stimmen spielt man hintereinander auf das Bandgerät.

Doch wie realisiert man solche Meisterwerke moderner Studiotechnik auf der Bühne, live, möglichst ohne Playback? Hier sind wir an dem Punkt, der Keyboarder, die etwas auf sich halten wollen, wohl oder übel zu Computerfreaks werden läßt — denn auch ein Keyboarder hat nur zwei Hände. Dank Midi genügen ihm diese nun auch, die Stimmen, die er nicht mehr selbst zu spielen schafft, übernimmt der Computer. Wenn ein Konzert abläuft, hat der Midi-Keyboarder die Hauptaufgabe schon zu Hause erledigt, nämlich das Einprogrammieren der Songs. Theoretisch könnte der Computer den Keyboarder natürlich voll ersetzen. Doch das wäre unfair, wo bliebe dann noch die Show?

Midi hilft nicht nur, komplexe Studiomusik live auf der Bühne zu realisieren. Das Inventar eines modernen Tonstudios geht heutzutage in die Millionen. Entsprechend hoch sind auch die Mieten. Midi hilft auch, teure Studiozeit zu sparen. Zumindest Keyboards und Elektronikdrums programmieren viele weniger betuchte Musikgruppen heute per Computer und Midi bereits zu Hause fertig ein. Im Studio spielt dann der Computer fehlerfrei sämtliche Stimmen gleichzeitig auf das Band. Mühseliges und zeitraubendes Spur-für-Spur-Aufnehmen wird so hinfällig. Midi ist also quasi notwendig geworden. Immer komplizierter werdende Technik erfordert meist noch mehr Technik, um sie wieder in Griff zu bekommen.

So, genug des Lobs. Selbst Computermusiker, habe ich mich wieder einmal in Begeisterung geschrieben. Es wäre mittlerweile allerdings sehr wichtig, die anfängliche Begeisterung von Musikern, Herstellern und Presse, über das neue Wunderkind, das alles möglich zu machen versprach, gegen eine kritischere Betrachtungsweise auszuwechseln; Midi, nach einem Jahr auf dem Markt, als das zu betrachten, was es eigentlich wirklich ist, — lediglich ein genormtes Bus-System. Genau wie RS232 oder Centronics, oder S-100 oder wie sie alle heißen. Ein Standard wie viele andere, behaftet mit genau den gleichen Unzulänglichkeiten und Vereinfachungen. In der Entwicklung behindert durch Fehlinterpretationen und dem Konkurrenzverhalten vieler Industriefirmen. Das ist das Fazit nach einem Jahr Midi.

## Wie sich alles entwickette

Sehen wir uns an, wie sich alles entwickelte.

Die Idee, ein genormtes Bussystem für Synthesizer-Keyboards zu entwickeln, kam erstmals im Juni 1981 auf der berühmten NAMM (National Association of Music Merchants) Show in Anaheim, USA auf. Diese größte Musikmesse der Welt findet jährlich statt, — hier werden meist sämtliche Neuentwicklungen der Musikindustrie erstmals vorgestellt. Die Präsidenten der bekannten Synthesizerfirmen Sequential Circuits, Oberheim Electronics und Roland (Dave Smith, Tom Oberheim, Kahehashi) unterhielten sich erstmals über die Möglichkeiten eines Standard-Digital-Interface für ihre Keyboards. Die nächsten Monate arbeitete man an ersten Vorschlägen. Ein weiteres Gespräch im Oktober 1981; der Kreis der Interessenten war mittlerweile gewachsen — Yamaha, Korg und Kawai, drei japanische Hersteller, hatten sich mittlerweile dazugesellt. Im Oktober 1981 stellte dann Sequential Circuits (SCI) auf der AES (Audio Engineering Society) in New York den ersten Versuch eines solchen Interfaces vor. Es hieß USI (Universal Synthesizer Interfaces) und war ein schnelles serielles Interface. Der Effekt: wenig Interesse von seiten anderer Hersteller. Doch der Stein war damit ins Rollen gekommen. Bei der NAMM-Show im Januar 1982 zählten bereits 15 Synthesizer-Hersteller zum Kreis der Interface-Interessenten: Oberheim, E-mu, Yamaha, Korg, Roland, Kawai, Moog, Fairlight, GDS, CBS-Rhodes, MusicTechnologie Inc., Octave Plateau, Passport Design, Alpha Syntauri und noch einige mehr. Für Keyboarder alles bekannte und wohlklingende Namen. Viele Streitpunkte tauchten auf, man fand keine Einigung, SCI und die Firmen, Yamaha, Roland, Korg, Kawai waren die einzigen, die nach diesem Treffen zunächst weitermachten. Es war mittlerweile klar, daß es kein optimales Interface geben würde, jedes müßte ein Kompromiß sein. Ein Kompromiß zwischen dem Wunsch jedes Herstellers nach wie vor Keyboards zu entwickeln, die sich möglichst von allen anderen in den meisten Features unterscheiden und andererseits dem Wunsch, alle Instrumente unter einen Hut zu bringen. So verwundert es nicht, daß trotz vieler Bemühungen, bis zum heutigen Tage wirklich 100 prozentig mit Midi nur eines machbar ist: die Ansteuerung eines zweiten Keyboards von einem ersten aus. Das heißt: drückt man auf eine Taste von Keyboard 1, klingt der Ton gleichzeitig von beiden Keyboards. Hier treten nie Schwierigkeiten auf, unabhängig davon, welchen Markennamen die gekoppelten Keyboards tragen.

Im folgenden Jahr machten nun die Japaner einige Vorschläge zur Abänderung des USI-Interfaces und Roland erfand den Namen Midi (Musical Instrument Digital Interface).

Im Januar 1983, wieder einmal NAMM, war es dann soweit. SCI stellte das erste Midi-Keyboard vor, den Prophet 600. Auch die Roland-Leute waren fleißig gewesen und hatten ebenfalls ein Midi-Keyboard entwickelt, den JP-6. Und, welch ein Wunder, obwohl die Instrumente unabhängig voneinander entwickelt wurden, verstanden sie sich. Keyboarddaten ließen sich austauschen. Doch das war auch schon alles. Tonhöhe und Anschlagsdauer wurden zwar korrekt übermittelt, SCI übermittelte jedoch zusätzlich Arpeggiator-Daten, Roland nicht.

## Nach anfänglicher Begeisterung regte sich bald Mißtrauen unter den Musikern

Erst im Nachhinein wurde man sich leider klar, daß es gewisse Richtlinien geben müsse, welche Daten übertragen werden sollen und wie. So entstand die erste Midi-Spezifikation 1.0. Leider waren zu diesem Zeitpunkt schon Keyboards auf dem Markt, die ihr noch nicht entsprachen. Überdies hatten sich unter den Musikern mittlerweile die unglaublichsten Gerüchte aufgebauscht, was Midi alles könne: nämlich alles. Sie stellten jedoch bald fest, daß dies weit gefehlt war. Die Enttäuschung war groß, die Unsicherheit wuchs. Musiker ahnen eben nicht, welche Schwierigkeiten sich hinter einer so einfach aussehenden Entwicklung verbergen.

Mittlerweile jedoch hatte die anfängliche Begeisterung von seiten der Musiker viele Hersteller, die zunächst der Spezifikation skeptisch gegenüberstanden, in Zugzwang gebracht. Sie befürchteten, ihre Keyboards ohne Midi-Anschluß nicht mehr los zu werden. Die Folge: Mittlerweile sind bis auf vereinzelte Ausnahmen alle neueren Keyboards mit Midi ausgerüstet.

Die Geister waren hiermit gerufen. Es bleibt nur noch, das Beste aus dem Anfang zu machen. Alle Hersteller haben sich mittlerweile geeinigt, bis März dieses Jahres die gültige Midi-Spezifikation 1.0 in allen Punkten zu befolgen. Die Hoffnung bleibt.

## Die technischen Details der Midi-Spezifikation 1.0

Wenden wir uns nach diesem historischen Abriß den technischen Details der Midi-Spezifikation 1.0 zu.
Um die Verkabelung der Instrumente einfach zu halten, hat man sich für eine serielle Datenübertragung entschlossen. Diese Tatsache stößt nach wie vor auf viel Widerspruch. Viele halten die Datenübertragungsgeschwindigkeit für zu niedrig. Sie würden lieber mit paralleler Datenübertragung arbeiten. Bei sehr komplexen Systemen, in denen viele Instrumente gleichzeitig mit sehr vielen Daten versorgt werden sollen, können Verzögerungen aufgrund der langsamen seriellen Datenübertragung Delays auftreten, das heißt, die Toninformationen erscheinen am Ende der Leitung mit Verzögerung. Der Streit ist groß, ob dieser Effekt nun hörbar ist oder nicht. Einige wollen Delays störend bemerkt haben, andere entgegnen, daß dieselben Zeitunterschiede für einen Hörer auftreten, der lediglich einige Meter vom Keyboard entfernt steht. Unser Schall ist ja auch nicht der schnellste. Und wer hat hier schon störende Delays bemerkt? Sei es wie es sei. Immerhin arbeiten Midi-Interfaces mit fast der doppelten Geschwindigkeit des in der Computerindustrie weit verbreiteten RS232 Busses, nämlich mit 31,25 KBaud. Diese Frequenz wählte man, da sie hardwaremäßig leicht durch Teilung eines l-MHz-Taktes durch 32 zu erhalten ist. Jedes Daten-Byte besteht aus einem Start-Bit, acht Daten-Bits und einem Stop-Bits (siehe Bild 2).

In jedem mit Midi ausgerüsteten Instrument sowie in allen Midi-Interfaces befindet sich nun eine Baugruppe, die parallele Daten des internen Keyboardprozessors in serielle wandelt und auf die Reise in das Midi-Verbindungskabel schickt, beziehungsweise von einem externen Computer ankommende serielle Daten in parallele rückwandelt. Diese Einheit heißt ACIA (Asynchronous Communications Interface Adapter Bild 3).

Von außen unterscheidet sich ein Midi-Keyboard nur durch drei Buchsen — Midi-Input, Midi-Output und Midi-Durchgangsbuchse (Midi Thru) — von einem anderen. Laut Spezifikation dürfen lediglich 5-Pin/180-Grad-DIN- beziehungsweise XLR-Buchsen Verwendung finden. Verbindungskabel zwischen Midi-Systemen dürfen nicht länger als 15 m sein, man muß eine zweipolige Leitung, abgeschirmt und verdrillt, verwenden.

Will man Keyboards nicht bloß verbinden, sondern von einem Computer ansteuern, benötigt man ein externes Midi-Interface, das die parallelen Daten des Computers in serielle wandelt, die unser Keyboard versteht. Den prinzipiellen Aufbau eines Midi-Interfaces erkennen wir in Bild 4.

Solch externe Interfaces gibt es mittlerweile in den verschiedensten Modifikationen. Viele passen nur an einen Rechner, einige mittels zusätzlicher Adapter-Karten an mehrere. Für den Commodore 64 existieren momentan die meisten Midi-Inter-faces und, was noch wichtiger ist, sehr viel Software. Auch im Midi-Sektor scheint der C 64-Konkurrenten mittlerweile weit abzuschlagen.

## Welche Daten sollen übertragen werden? Diese Frage ließ Köpfe rauchen

Das Problem des Midi-Standards lag bisher jedoch weniger in der Normung der Hardware. Ungleich schwerer fiel die Entscheidung, welche Daten nun eigentlich übertragen werden können beziehungsweise müssen, um das System für den Musiker interessant zu machen.

Optimal wäre, alle Features eines Instruments per Midi auf ein anderes Instrument übertragen zu können.

Dieser Wunsch scheitert jedoch sofort an den unterschiedlichen technischen Möglichkeiten diverser Geräte. Midi kann lediglich auf dem niedrigsten gemeinsamen Level aller angeschlossenen Instrumente wirken. So lassen sich zwar auf einen vierstimmigen Synthesizer Daten für acht Stimmen, also eine achtstimmige Komposition, übertragen, gleichzeitig spielen wird er aber nur vier hiervon. Ebenso werden einen Synthi, der keine Anschlagsdynamik aufweist, diesbezügliche Daten kalt lassen. Die erste Lektion lautet folglich: Midi erweitert niemals die technischen Möglichkeiten angeschlossener Instrumente!

Zweitens: Jedes Instrument interessieren nur ganz bestimmte Informationen; Keyboards ganz andere als zum Beispiel eine elektronische Rhythmuseinheit oder einen Sequenzer. Um Synthesizer sinnvoll zu koppeln, müssen mindestens die Keyboardinformationen, Tonhöhe, Gate on time und die Anschlagsgeschwindigkeit beziehungsweise -dynamik codiert übertragen werden.

Polyphone Sequenzer können mit denselben Daten arbeiten, nicht aber monophone Sequenzer. Letztere registrieren nur einzelne Melodiestimmen. Rhythmusmaschinen wiederum sind überhaupt nicht an Ton-, sondern nur an Synchronisationsinformationen interessiert.

Noch schwieriger vorhersehbar als diese Punkte ist die Frage, in welcher Konfiguration von Geräten das Midi-Interface dann jeweils tatsächlich vom Benutzer eingesetzt werden wird. Will man zum Beispiel mehrere verschiedene Synthis ansteuern und auf jedem eine andere Stimme einer mehrstimmigen Komposition mit anderem Klang ausgeben, so erfordert dies sicher eine ganz andere Zuordnung, als wenn alle Instrumente dieselbe Stimme spielen sollen. Deshalb führte man drei unterschiedliche Zuordnungsmodi ein, den OMNI-, POLY- und MONOmodus. Da die Verkabelung der einzelnen Instrumente möglichst einfach sein soll, müssen softwaremäßig Kanäle geschaffen werden, um die Instrumente mit den unterschiedlichen Stimmen der Komposition zu versorgen. Jedes Instrument muß für es bestimmte Daten gezielt erkennen. So führte man neben den drei Modi noch 16 Kanäle (Channels) ein. Mit geeigneter Software ließen sich deshalb auch maximal 16 Instrumente gleichzeitig und polyphon ansprechen — angesteuert von einem Computer.

Was für Möglichkeiten bieten die einzelnen Modi? Im OMNImodus spielen alle Instrumente, die am Bus hängen, parallel und polyphon. Die angeschlossenen Instrumente empfangen sämtliche über den Bus geleitete Daten, unabhängig vom jeweiligen Kanal, auf dem diese übermittelt werden. Sollen die gekoppelten Synthis jedoch verschiedene Stimmen spielen, wechselt man in den POLYmodus. Hier lassen sich die einzelnen Instrumente unterschiedlich adressieren. Kanal 1 spricht dann zum Beispiel nur Synthi 1 an. Man könnte auf diesem Kanal eine Baßstimme programmieren, über Kanal 2 einen zweiten Synthesizer ansprechen und diesen Begleitakkorde spielen lassen. Eine Melodiestimme über Kanal 3 auf Synthi 3 gelegt und zu guter Letzt eine Rhythmusmaschine synchronisiert, über Kanal 4 — schon hat man das Orchester fertig. Auf jedem Kanal können theoretisch unbegrenzt viele Stimmen gleichzeitig übermittelt werden; das angeschlossene Keyboard spielt natürlich nur so viele, wie es Stimmen besitzt. Bei modernen Keyboards sind das mittlerweile bis zu 16, wie der Yamaha DX-7 zeigt. Hätte man 16 DX-7, könnte man eine 16 x 16, also 256stimmige Komposition mit Top-Sound, von einem Commodore 64 gesteuert, über diese Maschinerie ausgeben! Da die jüngsten Tendenzen der Synthesizerindustrie wieder in Richtung Modultechnik gehen, steht dies auch nicht mehr in allzu weiter Ferne. So erscheinen demnächst von den Firmen Roland und Yamaha 19-Zoll-Synthiracks, in denen jeweils acht komplette Synthesizer untergebracht sind, per Midi und Computer steuerbar. Dann braucht man nur noch ein Klaviatur-Modul und los geht’s.

Im dritten und letzten Modus, dem MONOmodus wird schließlich je Kanal nur eine einzige Stimme übertragen. Jedes angeschlossene Instrument empfängt so viele Kanäle, wie es Stimmen besitzt, beginnend bei dem Kanal, mit dem es adressiert wurde. Verfügt es über keinen Adreßschalter, wird es automatisch mit Kanal 1 adressiert. Letzteres gilt übrigens für alle Modi. Besitzt man zum Beispiel den Six-Track von Sequential Circuits, einen Synthesizer, der sechs verschieden klingende Stimmen gleichzeitig spielen kann, lassen sich diese Stimmen im MONOmodus mit unterschiedlichen Melodien belegen. So spielt dann ein Synthi gleichzeitig stampfendes Baßfundament, Bläserbegleitung, Fuzzsolo und vielleicht noch drei Percussionstimmen — was will man mehr.

Prinzipiell sind zwei verschiedene Arten der Verkabelung angeschlossener Geräte möglich, sternförmig und kettenförmig. Wir sehen dies in Bild 5.

## Alle Midi-Features funktionieren meist nur im Idealfall

Midi bietet also ungeheure Möglichkeiten. Doch das Ganze funktioniert tadellos nur im Idealfall.

Vor dem Kauf jeglichen Midi-Equipments sollte man sich zunächst immer möglichst genau informieren, ob das Gerät auch in Zusammenhang mit den anderen, die man schon besitzt, funktionieren wird. Schwierigkeiten treten meistens auf, wenn Equipment verschiedener Hersteller gekoppelt werden soll. Die meisten Möglichkeiten und wenigsten Probleme ergeben sich, wenn man nur Equipment eines Herstellers nutzt. Dies ist prinzipiell nicht anders als in der Computerszene. Andernfalls werden zwar viele Features funktionieren, aber nicht alle.

Was man dann mit dem Computer und seinem Equipment tatsächlich für Möglichkeiten hat, bestimmt die Qualität der verwendeten Software. Midi-Software für den Commodore 64 gibt es mittlerweile in Hülle und Fülle. Tunlichst sollte man sich auch hier vor dem Kauf genau über deren Möglichkeiten informieren. Sich wenn möglich alles praktisch demonstrieren lassen. Hier liegt jedoch meist der Hund begraben. Man versuche einmal, in einem Musikgeschäft bestimmte Midi-Software vorgeführt zu bekommen. Die meisten werden passen. Mangels Kenntnis im Umgang mit dem Computer oder überhaupt in Ermangelung eines solchen. Entsprechend wird man ebenso verzweifelt in Computershops nach Midi-Keyboards Ausschau halten. Hier bleibt nur die Hoffnung, daß sich demnächst einiges ändert.

(Richard Aicher/aa)

# Die Index-sequentielle Datei

> Das Arbeiten mit einer relativen Datei ist gar nicht so komfortabel wie man es eigentlich möchte. Der Zugriff auf Datensätze nur über die Datensatznummer ist nicht besonders benutzerfreundlich und in der Regel auch praxisfremd. Unter Zuhilfenahme einer sequentiellen Datei wird dieser Nachteil jedoch aufgehoben.

In den letzten beiden Ausgaben des 64’er wurden Ihnen die Grundzüge der sequentiellen und der relativen Datei vorgestellt und erläutert. Ich deutete auch schon an, daß erst die Verbindung dieser beiden Dateiformen zu einer befriedigenden Lösung führt. Aber auch hier muß man Abstriche machen. Durch diese Vermischung werden leider nicht nur die Vorteile, sondern auch ein Teil der Nachteile mit übernommen. Ich möchte diese noch einmal kurz anreißen.

Das Wesen der sequentiellen Datei liegt in der aufeinanderfolgenden (eben sequentiellen) Anordnung der Daten. Um mit dieser Datei arbeiten zu können, muß sie vollkommen in den Speicher des Computers geladen werden. Bei großen Datenbeständen kann das eine ganze Zeit lang dauern. Andererseits wird die maximale Größe durch den zu Verfügung stehenden Speicherplatz im Computer selbst bestimmt. Sind jedoch alle Datensätze erst einmal geladen, ist ein Bearbeiten der Daten sehr einfach und auch schnell. Dann können alle Änderungen, Ergänzungen und sonstige Manipulationen im Computer selbst durchgeführt werden. Und für zeitkritische Funktionen wie Sortieren und Suchen kann man die Maschinensprache sehr wirkungsvoll einsetzen.

Die relative Datei hingegen benötigt außer dem eigentlichen Programm nur sehr wenig Speicherplatz, nämlich nur noch denjenigen für die internen Variablen und für einen Datensatz. Der Rest aller Daten befindet sich auf Diskette. Und dort stehen einem fast 170 KByte zur Verfügung. Allerdings ist das Arbeiten mit einer rein relativen Datei nur in speziellen Fällen sinnvoll und praktisch, da bei ihr ein Datensatz nur über die Datensatznummer angesprochen werden kann. Ein weiteres Merkmal ist, daß die Datensatzlänge vorher festgelegt werden muß und eine Floppy unbedingt notwendig ist.

## Indizierung als Lösung

Durch die Verbindung einer relativen Datei mit einer sequentiellen wird ein Kompromiß geschlossen. Einerseits wird die Suche nach einem Datensatz, beispielsweise nach einer Adresse, jetzt direkt über den Namen möglich. Andererseits muß gleich nach dem Programmstart die sequentielle Datei geladen und am Ende wieder gespeichert werden. Allerdings fällt sie wesentlich kürzer aus. In ihr braucht lediglich ein Feld der Datensätze enthalten zu sein, nämlich das Indexfeld, im Beispiel die Nachnamen, und nicht, wie bei der puren sequentiellen Form, alle Felder.

Gehen wir einmal von folgender Voraussetzung aus: Auf der Diskette sind bereits eine Anzahl von Adressen gespeichert. Im RAM des Computers befindet sich das Programm und in einem eindimensionalen Feld (im Beispiel die Variable IN$) alle bisher eingegebenen Nachnamen. Indem wir diese Variable mittels einer FOR-NEXT-Schleife durchsuchen, können wir auch einen gespeicherten Namen finden. Allerdings kommen wir damit noch nicht an seine Adresse heran, da diese ja in diesem Moment nicht im Computer sondern auf Diskette gespeichert steht. Mit einem kleinen Kniff schaffen wir aber auch diese Hürde. Wir speichern bei der Eingabe einer neuen Adresse einfach die Datensatznummer vor dem Nachnamen in die Variable IN$. Und zwar reservieren wir vor jedem Nachnamen vier Stellen für die zugehörige Datensatznummer. Ab der 5. Stelle beginnt also der jeweilige Nachname. Wollen wir nun einen Namen suchen, so müssen wir mit der MID$-Funktion die Feldvariable IN$ ab dem fünften Buchstaben durch-kämmen. Sobald der gesuchte Name gefunden wurde, trennen wir die ersten vier Zeichen ab und erhalten damit die zugehörige Datensatznummer. Mit dieser Nummer können wir jetzt direkt auf die relative Datei auf der Diskette zugreifen und holen uns die komplette Adresse.

## ... und so wird’s gemacht

Anhand eines Beispiels soll das noch einmal gezeigt werden:
Inhalt der ersten Elemente von IN$:
IN$(1) =»1... MEIER«
IN$(2) =»2... MUELLER«
IN$(3) =»3... ANDERMANN«
IN$(4) =»*«

Gesuchter Name = Mueller, er steht in der Variablen N$ (Zeile 3060)
3060 INPUT"NACHNAME";N$
3070 N = LEN(N$) Länge des eingegebenen Namens

Die folgenden Programmzeilen suchen den Namen.
3090 FOR 1 = 1 TO DATEIENDE
3100 IF IN$(I) = ”*” THEN 3120
3110 IF MID$(IN$(I),5,N)=N$ THEN gefunden
3120 NEXT I

Zur Zeile 3100 kommen wir später noch. Angenommen, wir haben nicht den ganzen Namen eingegeben, sondern lediglich die ersten drei Buchstaben MUE. Dann werden in der Variable IN$ nur die 5.,6. und 7. Zeichen, das entspricht den ersten drei Buchstaben eines jeden Namens, verglichen. Dafür sorgt die Zeile 3070 und in 3110 das »,N« als letzter Parameter der MID$-Funktion. Somit könnte mit dieser Eingabe auch der Name MUECKE gefunden werden. Im Extremfall, wenn nichts eingegeben, also RETURN gedrückt wird, findet diese Funktion jeden Namen. Das heißt, man kann mit der Suchfunktion sich nicht nur einzelne Adressen holen, sondern auch die gesamte Datei, oder zum Beispiel alle Adressen, die mit M anfangen. Damit würde der Menüpunkt »G = Anzeigen gesamte Datei« überflüssig. Ich habe ihn nicht entfernt, da hier unabhängig von der sequentiellen Datei alle Datensätze direkt von der Diskette aus der relativen Datei gelesen werden. Man könnte diese Funktion benutzen, um eine eventuell (zum Beispiel durch Stromausfall) teilweise zerstörte sequentielle Datei zu reorganisieren.

Die Zeile 3100 wird dann verständlich, wenn man sich den Programmteil »Neue Datei anlegen« ab 11000 anschaut. In den Zeilen 11320 bis 11350 wird jedes Element der Variablen IN$ mit einem »*« vorbesetzt. Der Stern kennzeichnet einen leeren Datensatz. Damit kommen wir auch gleich zum Programmteil »Löschen Datensatz« ab 4000. Auch dort wird ein zu löschender Datensatz in IN$ mit einem »*« gekennzeichnet und zusätzlich der entsprechende Datensatz auf der Diskette mit Hex FF (= Dezimal 255 = das Zeichen PI). Auch das wollen wir uns anhand eines kleinen Beispiels näher betrachten:

Wir wollen den Herrn Mueller aus unserer Datei entfernen. Nachdem wir seine Adresse mit der Suchfunktion gefunden haben, geben wir ein »L« für Löschen ein. Danach springt das Programm nach 4000, schreibt in die Variable IN$ das »*« , überschreibt den Datensatz auf der Diskette mit CHR$(255)(=PI), löscht die einzelnen Datensatzfelder (NN$, NV$, und so weiter) und springt zurück nach 3350. Die Variable IN$ sieht jetzt so aus:
IN$(1) =»1... MAIER«
IN$(2) =»*«
IN$(3) =»3... ANDERMANN«»
IN$(4) =»*«

Der zweite Datensatz ist nun mit »*« als gelöscht und leer gekennzeichnet. Das bedeutet auch, daß er wieder mit einer neuen Adresse belegt werden kann. Sehen wir uns dazu den Programmteil »Neueingabe Adresse« ab 1800 an.

Nachdem wir eine neue Adresse eingegeben haben (die einzelnen Programmteile, die in 1830 bis 1850 aufgerufen werden, kennen Sie ja bereits aus den letzten beiden 64'er Ausgaben), muß jetzt ein leerer Platz gefunden werden, auf dem wir die neue Adresse abspeichern können. Wichtig sind jetzt die Zeilen 1880 bis 1910. In diesem Abschnitt wird IN$ so lange durchsucht, bis ein mit »*« gekennzeichnetes Element gefunden wird (1910). In unserem Beispiel ist das bereits das zweite Element (IN$(I) = »*«, bei I = 2). Somit wird die neue Adresse als zweiter Datensatz auf Diskette gespeichert. In Zeile 1930 und 1940 wird die Variable IN$ auf den neuesten Stand gebracht. Zuerst wird die Datensatznummer (I) in einen String umgewandelt (1920). Dabei wird immer das (unsichtbare positive) Vorzeichen mit berücksichtigt. Da wir dieses nicht brauchen, wird es abgeschnitten (MID$(I$,2) und die Zahl mit Leerstellen auf insgesamt vier Zeichen Länge erweitert. Zeile 1940 verbindet dann die Datensatznummer mit dem Namen.

Vielleicht ein Wort noch zur MID$-Funktion. Normalerweise gehören zu dieser Funktion drei Parameter. So steht es auch kurz erläutert im Commodore-Handbuch. Der letzte Parameter gibt an, wieviele Zeichen ab einer definierten Stelle des Strings genommen werden sollen. Wird dieser Parameter weggelassen, werden ab der definierten Stelle alle restlichen Zeichen des Strings übernommen.

## Probleme, dfe sich ergeben können

Es könnte sein, daß Ihnen die Dateistruktur nicht gefällt. Zum Beispiel möchten Sie die Länge der Datenfelder ändern. Das dürfen Sie nur machen, wenn die Datei neu eingerichtet werden soll. Bei einer bestehenden geht es nicht! Beim Verkürzen gibt es keine Probleme, auch keine beim Verlängern bis zu 88 Zeichen. Zu verändern sind dann die Zeile 30040 sowie die Längenangaben zwischen den Zeilen 5000 und 7100. Bedenken Sie dabei, daß die Variable BL$ mindestens so viele Leerstellen haben muß, wie das längste Datenfeld.

Schwieriger wird es, wenn Sie infolge einer Vergrößerung der Datensatzlänge über 88 Zeichen hinwegkommen. Das Problem hierbei ist der INPUT#-Befehl. Mit ihm kann man nämlich nur maximal 88 Zeichen aus einer Datei lesen. Es gibt zwei Methoden, diese Hürde zu überwinden. Erstens eine Maschinensprache-Routine, die den INPUT#-Befehl erweitert, so daß auch Datensätze mit bis zu 255 Zeichen gelesen werden können (schauen Sie doch einmal in das Floppy-Buch von Data Becker, dort finden Sie eine entsprechende Routine). Die zweite Möglichkeit ist die Verwendung des GET#-Befehls anstelle des INPUT#-Befehls. Dann ist die Zeile 9070 INPUT#1,RC$ durch folgende Zeilen zu ersetzen:
9068 RC$ = " "
9070 GET#1,W$
9072 RC$ = RC$+W$
9074 IF W$ = CHR$(255) THEN 9090
9076 IF W$ = CHR$(13) THEN 9070

Den GET#-Befehl kann man natürlich auch dann einsetzen, wenn die Satzlänge kleiner als 88 Zeichen ist. Dann werden die Zeichen jedoch um einiges langsamer eingelesen als mit dem INPUT#-Befehl. Aber es ist mit dem GET#-Befehl möglich, bis zu 255 Zeichen in eine Variable einzulesen.

Ein Problem ganz anderer Art kann auftauchen, wenn Sie eine Floppy besitzen, die vor Dezember 1983 gekauft beziehungsweise hergestellt wurde und gleichzeitig mit einem VC 1526 drucken. Es kann möglich sein, daß bei Benutzung einer relativen Datei Fehler auftauchen, sobald dieser Drucker eingeschaltet ist. Probieren Sie das vorher aus! Abhilfe schafft meines Wissens nur ein neues DOS für die alte VC 1541.

## Anregungen für Programmierer

Dieses Programm ist — bis auf die Druckerroutine, die sich jeder für seinen eigenen Drucker selber schreiben sollte — komplett und funktionsfähig. Sicherlich lassen sich noch eine ganze Reihe von Schönheitsreparaturen machen. Auch eine Erweiterung des Programms ist durchaus sinnvoll. Zum Beispiel könnte man ein Unterprogramm schreiben, das, ähnlich einem professionellen Dateiprogramm, es ermöglicht, sich die Datenfelder selbst zu definieren. Auch die Suche nach mehr als einem Feld ist durchaus sinnvoll. Wenn erwünscht, kann auch eine Sortierroutine eingefügt werden. Der modulare Aufbau erlaubt dies ohne Schwierigkeiten. So kann sich jeder, der etwas Programmiererfahrung hat, eine Dateiverwaltung aufbauen, die sogar professionellen Programmen etwas voraus hat: Sie ist auf die persönlichen Bedürfnisse abgestimmt und läßt sich auch jederzeit ändern. Wer das Programm kompiliert, kann auch bei sehr großen Dateien noch mit guten Suchgeschwindigkeiten rechnen. Dieses Beispielprogramm enthält alle Voraussetzungen für eigene Erweiterungen. Ich selbst habe obengenannte Funktionen für meine eigene Dateiverwaltung bereits realisiert.

(gk)

# Hard and Soft: eine kleine Marktübersicht

> Von der Qualität und leichten Bedienbarkeit der Programme hängt die Qualität der Keyboardarrangements immer mehr mit ab. Nichts-desto-trotz sollte man immer daran denken, daß ein schlechter Song auch mit der ausgefeiltesten Software nicht besser wird. Hier ein kurzer Überblick über Midi-Software und -Interfaces für den Commodore 64.

### Steinberg Research: 16-Spur-Midi-Recorder, Interface und Drum to Midi Converter

Vom Keyboarder für Keyboarder entwickelt wurde die Steinberg-Midi-Software: Einer der beiden Entwickler ist selbst Keyboarder in der Gruppe um die Rock-Lady Inga Rumpf. Dieselbe Firma verteibt auch ein Mini-Midi-Interface mit einem Midi-Input und zwei Outputs. Das Interface selbst besteht aus einer Platine mit festgelöteten Buchsen. Die Platine wird direkt in den User-Port des C 64 gesteckt. Leider hat man, wahrscheinlich aus Kostengründen, auf ein Gehäuse verzichtet. Hier empfiehlt es sich, auf jeden Fall selbst Hand anzulegen. Preis zirka 120 Mark.

Die Software kann man als 16 Spur-Multitrack-Recorder bezeichnen. 16 Sequenzen verschiedener Länge haben im Arbeitsspeicher Platz. Die einzelnen Sequenzen spielt man Spur für Spur ein. Jede faßt bis zu 16 polyphone Spuren und unterschiedliche Parameter. Pitchbending und Modulation, Dynamik und After Touch sowie Sound-Änderungen werden mit aufgezeichnet. Natürlich nur, wenn das Instrument dazu in der Lage ist. Jede Spur kann dabei so viele Stimmen aufnehmen, wie das Einspielkeyboard zur Verfügung stellt. Längere Kompositionen bildet man durch Verknüpfen der 16 Sequenzen, wobei die Reihenfolge frei wählbar ist. Die 16 Sequenzen und 16 Spuren erscheinen recht musikerfreundlich in einer Art Songtable am Bildschirm. Man arbeitet ausschließlich mit diesem Bild (Bild 1). Bereits während der Aufnahme werden etwaige Timingfehler korrigiert, wobei die Korrektur für jede Spur individuell anwählbar ist. (Korrektur auf %-&Ji6,%2- und Yw-Werte möglich). Ein Metronom hilft während des Einspielens, das richtige Tempo zu halten.

Bis zu 16 Midi-Instrumente spricht das Interface im Playmode an. Die 16 Recorder-Spuren lassen sich natürlich beliebig auf die 16 Channels und somit verschiedenen Instrumente verteilen. Die Software ist für OMNI-, POLY- und MONOmode ausgelegt.

Ein Farbbildschirm ist unbedingt nötig. Die einzelnen Betriebsmodes, wie Aufnahme, Play und so weiter, erkennt man durch verschiedene Hintergrundfarben. Bespielte Spuren lassen sich in jede beliebige Sequenz und dort an jeden Platz kopieren, sowie in einem Bereich von + 32 bis +32 Halbtönen transportieren. Preis 290 Mark.

Für schwierige Synchronisations-Aufgaben in größeren Midi-Systemen, stellt Steinberg eine auf die Midi-Multitrack-Recorder-Software und den C 64 abgestimmte Synchronisier-Platine her. Mit dieser läßt sich dann eine Band-Maschine synchronisieren (Tape Sync) oder der Midi-Recorder extern triggern. Umgekehrt kann man ihm diverse Glock-Signale und einen Start-Impuls zur Steuerung externer, noch nicht Midi-kompatibler Elektronik-Drums entnehmen. Preis zirka 98 Mark.

Demnächst erscheint im Programm von Steinberg ein Drum-to-Midi-Converter. Dies wäre das erste Gerät dieser Art. Mit diesem Gerät kann man dann endlich Percussion-Impulse direkt in die Midi-Software einspielen. Hierzu ist zusätzlich Hardware nötig. Die Impulse können entweder von einem Pad-Set (Simmons oder ähnliches) oder über Mikrofon von einem »echten« Schlagzeugset abgenommen werden.

### Jellinghaus Music Systems: Midi-Interfaces und Software

Jellinghaus, einer der deutschen Pioniere auf dem Gebiet der Midi-Technik, bietet zwei verschiedene Interface-Versionen an. Ein sogenanntes Mini-Interface, zum Preis von 115 Mark, daß sich ausschließlich an den Commodore 64 anschließen läßt, sowie eines mit mehr Features, das sich sowohl mit 6502 als auch Z80-Prozessoren ansprechen läßt, zum Preis von 330 Mark. Das Mini-Interface verfügt lediglich über einen In- und zwei Outputs. Die größere Version bietet zusätzlich eine Midi-Thru-Buchse sowie Drum Sync-Möglichkeit.

Jellinghaus bietet diverse Software für den Commodore 64 an. Vor allem Yamaha-DX-7-Besitzer kommen hier auf ihre Kosten. Der Sound-Editor DX-7/DX-9 zeigt alle Soundparameter dieser Keyboards übersichtlich auf dem Bildschirm an. Dies weiß jeder zu schätzen, der sich schon an der Programmierung der beiden Keyboards versucht hat. Die einzelnen Parameter lassen sich nun bequem über die C 64-Tastatur editieren und anschließend ausdrucken.

Überdies entkommt man auf diese Weise auch den teuren RAM-Cartridges, denn mit dieser Software lassen sich sämtliche Sounddaten auch auf die Commodore-Diskette speichern. Preis zirka 185 Mark.

Auch eine Multitracker-Software gibt es hier, den sogenannten Multitrack Live-Sequenzer für den Commodore 64 (Bild 2).

Er stellt 12 Spuren zur Verfügung, natürlich wieder voll polyphon. 10000 Events (note on/note off) haben insgesamt im Speicher Platz. Ein Metronom sorgt für den richtigen Takt, die Aufnahme startet mit einem wählbaren Ereignis, zum Beispiel der ersten gespielten Note, einem Druck auf die Programmwechseltaste oder durch Drehen am Pitch-Bender. Für jede Aufnahme-Spur läßt sich getrennt festlegen, welche Parameteränderungen gespeichert werden sollen, zum Beispiel Keyboarddaten, Anschlagsdynamik, Programmwechsel, Pitch Bender und andere. Die Auswahl erfolgt in einem Filter-Menü. Diese Bezeichnung erscheint mir hier allerdings etwas fehl am Platze. Beim Arbeiten mit einer Drum-Box kann entweder diese den Recorder, oder der Recorder diese synchronisieren. Das Tempo läßt sich im Bereich von 40 bis 200 regeln, die Taktart kann von 2/2 bis 11/2, 2/4 bis 11/4, 2/8 bis 11/8 gewählt werden. Natürlich auch hier alle drei Midimodes und wählbare Zuordnung von Spuren auf Channels. Einzigartig bisher: Die gespeicherten Songs lassen sich listen und editieren. Auf dem Bildschirm erscheint hierbei ein korrektes Zeitprotokoll der Reihenfolge, in der bestimmte Tasten gedruckt und wieder losgelassen wurden, mit Angabe der zusätzlich aufgenommenen Parameter. Außerdem lassen sich alle Spuren nachträglich im Timing korrigieren, in 1/4 bis 1/32-Werten, sowie 1/4- bis 1/32-Triolen. Weitere Features: Endlos-Wiedergabe (loops), Fuß-Schalter-Anschluß, Transponierung und Loudness-Skalierung jedes Tracks und die Möglichkeit, mehrere Tracks auf einen abzumischen (Mix-Down). Das Jellinghaus Midi-Recording-Studio kostet 250 Mark.

Eine weitere interessante Midi-Software: das Master-Keyboard (Bild 3). Dieses Programm ist interessant, wenn man viele Instrumente an seinem Midi-System angeschlossen hat und live darauf spielen will. Die Einspielklaviatur läßt sich dann in verschiedenen Weisen zur Steuerung der anderen Synthis einsetzen. So lassen sich zum Beispiel auf dem Einspiel-Keyboard (Master Keyboard) sechs Splitpunkte bestimmen. Mit den so entstandenen Klaviaturabschnitten kann man dann die restlichen Synthis gezielt vom Master-Keyboard aus live spielen. Außerdem können für die angeschlossenen Keyboards oder Effektgeräte 80 Presets programmiert werden, so daß sie bei Anwahl eines dieser Presets durch einen Tastendruck auf die bestimmten Klangbeziehungsweise Effektprogramme geschaltet werden. Ein drittes Feature ermöglicht zu jedem gespielten Ton andere hinzumischen. Diese Software kostet 200 Mark.

Passport Design: Midi-Interface und Software
Passport Design ist in Computermusik-Kreisen durch ihr System für den Apple II, das Mountain Board Music System, wohlbekannt. Mittlerweile wurde auch Midi-Software und ein Interface für den C 64 von dieser Firma entwickelt. Auf der Midi-Interface-Karte sind drei 5-Pol-DIN-Buchsen vorhanden. Einmal Midi-In, einmal Midi-Out und eine dritte Buchse, für die Synchronisation einer Drum-Maschine (Drum Sync). Die Midi-Interfacecard überträgt und empfängt sämtliche Standard-Midi-Daten. Sie kostet in Deutschland 590 Mark.

Mit dem Midi-Recorder Midi/4 kann man bis zu 16 Stimmen Real-Time einspielen, beliebig über vier Aufnahmespuren verteilt. Hierbei speichert die Software alle für die Komposition wichtigen Informationen, also Tonhöhe, Dauer, Anschlagsdynamik, Pitch-Bend, Presetänderungen und After Touch. Sollte man sich einmal verspielt haben, können einzelne Stellen mit der »Punch-In«-Funktion während des Abspielens korrigiert werden, — so, als hätte man eine der guten alten Vier-Spur-Bandmaschinen vor sich. Natürlich lassen sich alle Midikompatiblen Rhythmusmaschinen synchronisieren. Auch Geräte ohne Midi-Bus, wie zum Beispiel ältere Electronic-Drums der Firmen Roland und Korg, kann man anschließen, sofern sie einen 5-Pol-DIN-Stecker zur Synchronisation besitzen. Das Schlagzeug wird durch die Software gestoppt und gestartet. Weitere Features von Midi/4 sind eine »Loop«-Funktion, »Clicktrack on/off«, die die Synchronisation des Midi-Sequenzers mit einer Bandmaschine erlaubt und »Transposition«. Der Preis beträgt in Deutschland zirka 295 Mark.

### Sequential Circuits: Model 64-Sequenzer für den Commodore 64

Der Model 64 Midi-Sequenzer Sequential Circuits ist als Cartridge entwickelt, die in den Memory-Expansion-Port des C 64 gesteckt wird. Um ihn voll ausnutzen zu können, benötigt man ein sechsstimmig polyphones, Midi-fähiges Keyboard. Der Sequenzer zeichnet dann exakt das auf, was von der Tastatur her eingespielt wird. Insgesamt können bis zu 4000 Noten gespeichert werden. Verfügt das benutzte Keyboard über Anschlagsdynamik, so wird auch diese mit aufgezeichnet.

Der Sequenzer merkt sich auch alle Pitchbend- beziehungsweise Modulationsinformationen. Im Wiedergabemodus können alle gespeicherten Informationen dann entweder real-time oder auto-corrected, wobei Timing Fehler des Einspielens nachkorrigiert werden, an den angeschlossen Synthesizer gegeben werden. Der Speicher des Sequenzers läßt sich in acht Blocks unterteilen, jeder dieser Blocks enthält dann eine sechsstimmig polyphone Sequenz, die alle unterschiedliche Längen haben können. Die Sequenzen kann man nachträglich per Software ganz, oder in Teilbereichen ändern, transportieren und auf Diskette beziehungsweise Kassette abspeichern. Der Sequenzer ist so konstruiert, daß er auch ohne Monitor betrieben werden kann. LEDs auf der Frontplatte signalisieren den jeweiligen Betriebszustand, was natürlich vor allem für Livemusiker auf der Bühne praktisch ist. An den Sequenzer kann man einen Fußschalter anschließen, zum Starten und Stoppen, wenn keine Hand frei ist; außerdem läßt er sich mit externen Rhythmusgeräten synchronisieren. Es kostet 725 Mark.

Natürlich gibt es noch mehr Software, noch mehr Interfaces. Alles Aufzuzählen würde den Rahmen erheblich sprengen. Für den Keyboarder zumindest, kann ein gut durchdachtes Midi-System mit entsprechender Software ein herkömmliches Recordingsystem mit Mehrspurmaschine und Mischpult in vielen Fällen ersetzen. Billiger kommt man jedoch auch nicht weg. Die Anschaffungskosten eines Computersystems und der Midi-Soft- und Hardware dürften sich in der Größenordnung eines Acht-Spur-Recorders der Low-Cost-Klasse bewegen.

(Richard Aicher/aa)

# Klangsynthese und Synthesizertechnik


> Unser Commodore 64 ist ein hervorragender Musikus. Manches Musikprogramm läßt Ihn sogar teurere, professionelle Musiksynthesizer übertreffen. Will man ihm selbst gezielt Töne entlocken, muß man über einige grundlegende Dinge der Klangsynthese und Synthesizertechnik Bescheid wissen.

Drei verschiedene Kurvenformen und sogenanntes »weißes Rauschen« stellt der Sound-Chip des Commodore 64 für unsere Experimente zur Verfügung. Die drei Kurvenformen nennt man Dreieck, Rechteck und Sägezahn (siehe Bild 1).

Jede der drei Kurven klingt ganz charakteristisch und zwar unabhängig von der Tonhöhe. Keine der drei klingt identisch mit irgendeinem natürlichen Instrument. Leider, sonst wäre nämlich alles viel einfacher. Bei den genannten Schwingungsformen handelt es sich um sehr einfache Basiskurven. Betrachtet man Kurvenformen natürlicher Klangerzeuger, also etwa eines Musikinstruments oder irgend eines anderen Geräusches am Oszillograph, stellt man sehr viel kompliziertere Kurvenverläufe fest (siehe Bild 2).

Außerdem verändern sich die Kurven kontinuierlich während des gesamten Klangablaufes. Wie lassen sich so komplexe Abläufe elektronisch realisieren?

Zu Beginn des 19. Jahrhunderts lebte der französische Mathematiker Jean Baptiste Joseph Fourier. Er entwickelte die mathematischphysikalischen Grundlagen, die uns auch heute noch Klänge verstehen und elektronisch nachahmen lassen. Es handelt sich um das Verfahren der sogenannten harmonischen Analyse von Klängen. Heute nennen wir das zugrundeliegende mathematische Prinzip ihm zu Ehren Fourier-Synthese. Fourier stellte fest, daß sämtliche periodischen Schwingungen in eine sinusförmige Grundschwingung und ebenfalls sinusförmige Oberschwingungen zerlegt werden können. Man nennt diese auch harmonische Oberschwingungen oder einfach Harmonische. Diese unterscheiden sich nur in der Frequenz und der jeweiligen Amplitude. Er bewies auch, daß die Umkehrung dieses Satzes ebenso gilt.

## Unterschiedliche Obertongemische produzieren verschiedene Klänge

Jede periodische Schwingung läßt sich durch Addition ihrer Grundkomponenten, also Sinusschwingungen mit bestimmter Frequenz und Amplitude, aufbauen. Sein Beweis war natürlich rein mathematischer Natur. Prinzipiell handelt es sich hier um Mathematik in Reinkultur. Natürlich bestehen nicht alle Klänge aus periodischen Schwingungsverläufen. Deshalb kann man mit diesem Verfahren auch nicht alle Klänge analysieren beziehungsweise synthetisieren. Rauschen ist zum Beispiel eine absolut nicht periodische Schwingungsform und kann nicht nach diesem Verfahren behandelt werden. Für die Frequenzen der Harmonischen gilt die Bedingung, daß sie in einem geradzahligen Verhältnis zur Frequenz der Grundschwingung stehen. Die Reihen der möglichen Sinuskurven haben also alle denselben Frequenzabstand, nämlich die Frequenz der Grundschwingung. Die Grundschwingung ist die Sinuskurve mit der tiefsten Frequenz. Sie bestimmt meist gleichzeitig die Tonhöhe des Klangs. Die Harmonischen bestimmen den Charakter des Klanges.

Wie ein Ton nun letztlich klingt, bestimmt die Zusammensetzung seines Obertongemisches. Entscheidend ist, welche Harmonischen beteiligt sind und mit welcher Amplitude. Betrachten wir wieder unsere Grundschwingungsformen. Hier handelt es sich um reine periodische Grundschwingungen. Sie lassen sich auch sehr leicht mit Mitteln der Elektronik erzeugen. Deshalb sind sie für uns so wichtig.

Der Sinuston besitzt keine Oberschwingungen, er ist rein. Sein Klang hört sich unnatürlich weich an. Reine Sinustöne existieren in der Natur nicht. Ganz anders der Sägezahn. In einer Sägezahnschwingung sind alle Obertöne vertreten. Der n-te Oberton ist hierbei l/n mal so laut wie der Grundton. Die Amplitude der Obertöne nimmtalso hier mit zunehmender Ordnungszahl ab. Der Sägezahn klingt hell, trompetenhaft. Die Dreieckschwingung weist sehr viel weniger Obertöne auf. Sie klingt dumpf. Man kann den Klang auch als flötenähnlich bezeichnen. Die Rechteckschwingung besteht aus ungeradzahligen Obertönen. Sie klingt hohl.

## Bob Moog konstruierte den ersten Synthesizer

Bob A. Moog hatte als erster die Idee, diese Grundschwingungsformen zur Klangsynthese einzusetzen. Inspiriert von den Klangwünschen seines Freundes Herb Deutsch, eines Experimental-Musikers, hatte er den Sommer 1964 damit verbracht, Elektronik-Module zu konstruieren, die die absonderlichsten Klänge hervorbrachten. Mit diesen Modulen war es erstmals möglich, die drei Größen, mit denen sich jedes Klangereignis beschreiben läßt, nämlich Tonhöhe (Frequenz), Klangfarbe (Kurvenform-Oberwellengehalt) und Lautstärke (Amplitude) relativ genau zu kontrollieren. Die entscheidende Idee war die Einführung der Spannungssteuerung. Er entwickelte Module, die direkt diesen drei Größen zuzuordnen und mittels Spannungssteuerung elektronisch kontrollierbar waren.

So entstand der Moog-Synthesizer, ein Klangmonster von 1 x 2 m Größe. Dieses Gerät revolutionierte die gesamte elektronische Tonerzeugung grundlegend. Auch unser kleiner SID-Chip ist prinzipiell nichts anderes als ein Nachfolger des Riesenkastens von einst. Nur mit dem Unterschied, daß er aus wenigen Kubikzentimetern Raum Leistung zaubert, für die ehedem der Moog-Synthesizer Kubikmeter benötigte und statt analoger Technik und Spannungssteuerung Digitaltechnik und Digitalkontrolle einsetzt.

Eines hat jedoch der Moog von einst dem SID-Chip von heute immer noch voraus. Er klingt wesentlich besser. SID-Klänge sind nicht sehr bombastisch. Es fehlen volle Bässe und höchste Höhen. Deshalb konnte sich auch bisher der Commodore 64 mit dem SID bei Profimusikern als Instrument nicht etablieren.

Im folgenden möchte ich kurz die einzelnen Funktionsgruppen eines Synthesizers, wie es auch unser SID ist, beschreiben.

Töne und Melodien entstehen in Tongeneratoren. Unser SID stellt uns drei unabhängig voneinander funktionierende Tongeneratoren zur Verfügung. Jeder produziert drei verschiedene Kurvenformen, nämlich Dreieck, Sägezahn und Rechteck. Überdies erzeugt jeder noch weißes Rauschen, ein Gemisch sämtlicher Frequenzen, die von einem Zufallsgenerator erzeugt werden.

## Töne entstehen in Oszillatoren

Wir haben gehört, daß sich unsere Basis-Kurvenformen durch ihren unterschiedlichen Gehalt an Obertönen und somit durch ihren Klang prinzipiell unterscheiden. Nach einigem Üben mit dem SID wissen wir bald, welche Kurvenform sich für einen bestimmten Klang anbietet.

Verschiedene Kurvenformen, schön und gut, aber wozu drei Tongeneratoren? Ganz einfach. Musik besteht nicht nur aus Solo-Melodien. Mit einem Tongenerator alleine könnten wir kaum Musik produzieren. Drei Tongeneratoren lassen uns jedoch schon ein ganzes Kammer-musik-Trio realisieren. Das heißt, wollen wir drei verschiedene Töne gleichzeitig erzeugen, also dreistimmig polyphon spielen, muß für jeden Ton ein eigener Tongenerator vorhanden sein.

## Der Rauschgenerator — kein Sturm ist ihm heilig

Mit dem Rausch-Generator (Noise-Generator) ist es möglich, Effekte wie Wind und Brandung zu erzeugen, den Klang einer Pauke oder eines Beckens, den Anblaswind von Orgelpfeifen, Holzblasinstrumenten und schließlich Gewehrschüsse in allen Variationen nachzuahmen.

Ein Ton macht nun aber noch lange keine Musik. Viele Töne unterschiedlicher Tonhöhe sind hierzu nötig. Deshalb muß die Tonhöhe der Oszillatoren steuerbar sein. Wie wir schon wissen, erfand Moog das Prinzip der Spannungssteuerung. Sämtliche Module seines Synthesizers konnten von analogen Steuerspannungen geregelt werden. Man nannte deshalb die Module auch »voltage controlled modules« (spannungsgesteuerte Module).

Computer hantieren nur ungern mit analogen Spannungen. Auch die Tongeneratoren unseres SIDs werden deshalb nicht von Analogspannungen, sondern mittels digitalen Informationen gesteuert. Wir nennen diese Oszillatoren deshalb auch nicht VCOs (voltage controlled oscillators), wie dies Moog machte, sondern besser DCOs (digital controlled oscillators).

Musiker wollen mit ihrem Instrument spielen. Es soll Töne produzieren. Wie teilen wir unseren Tongeneratoren mit, welche Töne sie spielen sollen? Routinierte Klavierspieler möchten ihre Ideen am liebsten über eine Klaviatur einspielen. Leider verfügt der Commodore 64 über keine richtige. So bleibt nichts anderes, als die Alpha-Tastatur in ein Keyboard zu verwandeln. Hierzu ordnet man jeder QWERTYTaste eine Tonfrequenz zu. Drückt man die Taste, erklingt der Ton. Das Spielen auf einer Schreibmaschinentastatur bereitet jedoch wenig Freude, zumindest muß man sich erst daran gewöhnen.

Kürzlich erschienen jedoch zwei Klaviaturen auf dem Markt, die mit richtigen Klaviertasten ausgerüstet, an den Commodore 64 angeschlossen werden können. Ihre Anschaffung lohnt sich sicher für den, der mit dem Commodore ausschließlich Musik machen will und eine Klaviertastatur gewöhnt ist.

Viele beherrschen das Klavierspiel jedoch nicht. Sie können trotzdem Musik mit dem Commodore 64 komponieren. Die Kompositionen werden nun nicht »Live« eingespielt, sondern Ton für Ton über die Alpha-Tastatur eingetippt. Es spielt dabei keine Rolle, in welcher Geschwindigkeit die Eingabe erfolgt. Man kann sich also viel Zeit lassen und Eingabefehler nachträglich ausbessern. Die einzelnen Töne werden hierbei mittels mehreren Eingaben für Tonhöhe, Tondauer und Lautstärke bestimmt. Das Verfahren ist relativ langwierig. Hat man alles eingegeben, spielt der Commodore den Song in der gewünschten Geschwindigkeit ab.

Bei den meisten ordentlichen Musikprogrammen kann der Computer die eingespielten oder eingetippten Songs speichern und auf Befehl wieder ausgeben. Die Länge der Kompositionen kann hierbei meist einige tausend Töne betragen. Ein Moog-Synthesizer von einst konnte sich nur 16 Töne merken und diese zyklisch immer wieder abspielen. Man nannte Geräte, die dies ermöglichten, Sequenzer. Heute benutzt man diesen Begriff meist allgemein für Tonspeichersysteme.

Wir sagten schon, daß sich jeder Klangeindruck durch die drei Größen Tonhöhe, Klangfarbe und Lautstärke beschreiben läßt. Wir wissen nun, daß die Töne in den Oszillatoren entstehen und die Tonhöhe durch digitale Steuerung dieser Oszillatoren entsteht. Außerdem können wir durch Auswahl der Kurvenformen bereits unterschiedliche Klangfarben erhalten. Wie können wir nun die Lautstärke bestimmen?

## Der ADSR steuert den Lautstärkeverlauf der Klänge

Der Klang eines Klaviers weist ein ähnliches Frequenzspektrum wie der einer Geige auf. Trotzdem unterscheiden sich die beiden Klänge voneinander gravierend. Eine wesentliche Ursache hierfür ist der unterschiedliche zeitliche Verlauf der Lautstärken. Schlägt man eine Klaviersaite an, setzt der Ton schlagartig ein und schwillt dann relativ rasch wieder ab. Im Gegensatz dazu schwillt der Geigenklang langsam an und behält, solange der Bogen gestrichen wird, eine konstante Lautstärke bei. Erst wenn der Bogen nicht mehr über die Saite streicht, klingt der Ton langsam ab. Klavier und Geige unterscheiden sich also im zeitlichen Verlauf der Lautstärke in der sogenannten »Hüllkurve«.

Jedes Instrument, jedes Geräusch zeichnet sich vor allem durch einen ganz spezifischen Lautstärkenverlauf aus. Hier spielen sich sehr komplexe Vorgänge ab, und nicht zuletzt bestimmt die Möglichkeit, solche komplexe Hüllkurven nachzubilden, die Qualität eines Synthesizers. Moog reduzierte bei der Entwicklung seines Synthesizers den Verlauf der Hüllkurve auf die Nachbildung der für das menschliche Klangempfinden wichtigsten vier Phasen: Attack, Decay, Sustain und Release (ADSR). Zu Deutsch: Anstieg, Abfall, Aushalten und Freigabe des Lautstärkeverlaufes. Der sogenannte ADSR- oder Hüllkurvengenerator liefert nun eine dem gewünschten Hüllkurvenverlauf entsprechende Steuerinformation. In unserem SID handelt es sich hierbei wieder um Digitalinformationen, die direkt die Lautstärke der drei Tongeneratoren beeinfllussen. In Analogsynthesizern benutzt man auch in diesem Fall Steuerspannungen. Unser SID stellt drei ADSRs zur Verfügung. Jede Stimme kann folglich einen eigenen Hüllkurvenverlauf erhalten. In Bild 3 sehen wir links eine typische ADSR-Kurve. Auf der x-Achse ist die Zeit, auf der y-Achse die Amplitude (Lautstärke) des Klanges abgetragen. Sofort nach dem Anschlag einer Taste würde die Lautstärke des Tons zunächst langsam bis zum Maximum ansteigen (Attack) und dann auf einem bestimmten Sustainpegel einige Zeit verweilen (Sustain). Läßt man die Taste los, verklingt er in der Abklingphase (Release), bis man nichts mehr hört. Natürliche Attack-Werte liegen, je nach Klang, im Bereich von einigen Millisekunden bis zu einigen Sekunden. Kurze Attack-Werte besitzen alle percussiven Instrumente wie Pauke, Schuß, auch Saiten-Instrumente wie Gitarre und Klavier gehören hierzu. Längere Attack-Zeiten finden wir zum Beispiel bei Blasinstrumenten. Es dauert, bis die Atemluft des Trompeters das Instrument zum Klingen bringt. Streichinstrumente weisen noch längere Attack-Werte auf. Sehr lange Attack-Zeiten, im Bereich vieler Sekunden, benötigt man zum Beispiel, um Wind oder Brandungsgeräusche nachzuahmen. Hat der Ton dann den maximalen Attack-Pegel mehr oder weniger schnell erreicht, können wir ihn in der ebenfalls regelbaren Decay-Phase bis auf einen gewissen Pegel abfallen lassen, den Sustain-Pegel.

Wie lange der Ton den Sustain-Pegel beibehält, bestimmt das Gate-Signal. Solange unser Gate gleich 1 ist, bleibt der Ton auf dem durch den eingestellten Sustain-Pegel bestimmten Lautstärkeniveau. Wird das Gate-Signal gleich 0, geht der Ton in die letzte der vier Phasen, die Release-Phase über.

Die Release-Phase bestimmt, in welcher Zeit unser Ton vom Sustain-Pegel auf die Lautstärke Null abfällt. Sobald unser Gate gleich 0 wird, beginnt die Release-Phase. Natürliche Instrumente besitzen nur kurze Release-Phasen. Man denke zum Beispiel an ein Klavier. Läßt man die Tasten nach dem Anschlag wieder los, verklingt der Ton relativ schnell. Die Zeit des Tastendrucks entspricht der Zeit, die wir unser Gate-Signal auf dem Wert 1 halten, also eingeschaltet haben müssen. Manche Klänge durchlaufen nicht alle vier Phasen der Hüllkurve. Denken wir zum Beispiel an die Orgel. Der Orgelton erklingt fast augenblicklich nach dem Anschlagen einer Taste und verlischt ebenso schnell wieder. Der elektronisch erzeugte Klang benötigt im Vergleich zu einem natürlichen Instrument keine Zeit, um sich aufzubauen, und es schwingt auch kein Resonanzkörper nach. Um das zu realisieren, müßten wir Attack, Decay und Release gleich Null setzen, den Sustain-Pegel auf Maximum einstellen. Percussionsinstrumente wiederum verfügen nur über Attack und Decay. Trifft der Schlegel die Pauke, baut sich der Ton fast sofort auf. Genau so schnell klingt er jedoch wieder ab. Man kann ihn nicht durch längeres Drücken auf das Fell in eine Sustain-Phase zwingen. Ein Beispiel für so eine percussive Hüllkurve sehen wir rechts in Bild 3.

## Unser SID-Chip wird digital gesteuert

Durch Auswahl verschiedener Grundschwingungsformen können wir unsere Klänge schon in bestimmte Richtungen lenken. Wir können diese Grundklänge jedoch noch weiter verändern.

Jede Stereo-Anlage verfügt über einen Klangregler. Wie jeder weiß, kann man mit diesem die Musik hell oder dumpf klingen lassen. Elektronisch wird dies mit einem Filter realisiert. Solche Filter kann man mit Kaffee-Filtern vergleichen. Diese halten Kaffekörnchen bestimmter Größe zurück. Ab einer bestimmten Größe können sie nicht mehr durch die Filterporen schlüpfen. Unsere Elektronik-Filter tun auch nichts anderes. Nur daß sie nicht Kaffeepartikel bestimmter Größe aufhalten, sondern harmonische Oberschwingungen bestimmter Frequenz. Wie wir bereits wissen, verändert dies unseren Gesamtklang unter Umständen beträchtlich. Nimmt man zum Beispiel alle Oberschwingungen höherer Frequenz weg, wird der Klang immer dumpfer. Nimmt man alle tieffrequenten Oberschwingungen weg, klingt der Ton heller. Auf diese Weise können wir also unsere Grundwellenformen nochmals entscheidend im Klang verändern.

## Filter bestimmen, ob unser Ton hell oder dumpf klingt

Unser SID stellt zunächst drei verschiedene Grundfiltertypen zur Verfügung. Der Hochpaßfilter läßt alle hochfrequenten Oberschwingung passieren. Die Tiefen schneidet er ab. Leitet man einen Klang hindurch, klingt er am Schluß heller als zuvor. Der Tiefpaßfilter stellt das Gegenteil unseres Hochpasses dar. Er beschneidet die hohen Klanganteile, läßt tiefe ungehindert passieren. Die Klänge klingen dann dumpfer als vorher. Der dritte Filtertyp ist der Bandpaßfilter. Er läßt ein bestimmtes Frequenzband passieren, schneidet alle darüber- und darunterliegenden Frequenzanteile ab. Die Klänge werden dadurch flach.

Bei allen drei Filtertypen kann man die jeweilige Filterfrequenz bei der sie wirken sollen, genau einstellen.

Neben diesen drei Hauptfiltertypen, kann unser SID durch Mischung dieser drei, noch weitere Mischfiltertypen erzeugen.

Neben der Filterfrequenz existiert noch eine weitere wichtige klangbestimmende Größe, die Filterresonanz. Eine Gitarre klingt völlig anders als eine Geige, auch wenn man bei beiden die selben Töne spielt. Dies rührt von der unterschiedlichen mechanischen Bauweise der Resonanzkörper der beiden Instrumente her. Eine Elektrogitarre ohne solchen klingt ohne angeschlossenen Verstärker fast gar nicht. Der Resonanzkörper ist für den Klang verantwortlich. Er dient bei unseren Instrumenten gewissermaßen als Klangverstärker. Die Bauweise entscheidet hierbei, welche Frequenzen besonders verstärkt werden, welche weniger. Dieses Phänomen nennt man Resonanz.

Bei unserem elektronischen Filter kann natürlich kein Gehäuse mitschwingen. Die Resonanz wird elektronisch erzeugt. Welche Frequenzen dabei besonders angehoben werden sollen und welche nicht, können wir mit der sogenannten Filterresonanz einstellen. Auf diese Weise läßt sich das Resonanzverhalten natürlicher Instrumente simulieren.

Unser Sound-Chip besitzt nur einen Filter. Durch diesen müssen alle drei Tonoszillatoren geleitet werden. Sie lassen sich folglich nicht unabhängig voneinander mit diversen Filtereinstellungen versehen. Wir können aber für jeden Oszillator bestimmen, ob er den Filter durchlaufen soll oder nicht. Wir können die Oszillatoren, also auch um den Filter herum, direkt in den Verstärker leiten.

Ein weites Feld an Klangeffekten eröffnen Ringmodulation und Synchronisation von Oszillatoren. Ich möchte hier weniger auf die theoretischen Grundlagen dieser beiden Effekte eingehen. Nur so viel sei gesagt, in beiden Fällen wird ein Oszillatorsignal mit einem zweiten, von einem anderen Oszillator, moduliert.

Bei der Ringmodulation multipliziert man die Frequenzen der beteiligten Oszillatoren miteinander. Es entsteht dann eine neue Frequenz, die viele nicht harmonische Obertöne enthält. Im SID werden natürlich keine Frequenzen sondern digitale Zahlenwerte multipliziert. Auf diese Weise kann man vor allem metallische oder glockenähnliche Klänge synthetisieren.

Synchronisiert ein Oszillator einen anderen, so zwingt er diesen dazu, seine Kurvennulldurchgänge den eigenen anzupassen. Vor allem, wenn beide Oszillatoren unterschiedliche Frequenz aufweisen, ergeben sich hier interessante Klangeffekte.

So, dies war nun die graue Theorie, zumindest die erste Lektion auf dem steinigen Weg, dem SID-Chip Töne, Klänge und Musik zu entlocken. In einer weiteren Lektion werden wir lernen, mit welchen Befehlen wir die Parameter der Oszillatoren, Hüllkurvengeneratoren, des Filters und des Ringmodulators unseres SID-Chips ansprechen können.

(Richard Aicher/aa)

# »Der Sumpf«

> Unser Beitrag über die Raubkopierer-Szene in der 64’er 6/84 hat weite Wellen geschlagen. Nachstehend bringen wir einen in mehrfacher Hinsicht bemerkenswerten Leserbrief zu diesem Thema — und unsere Antwort darauf.

Als Vorwegnahme meiner Meinung zu Ihrem Artikel »Der Sumpf« muß ich Ihnen sagen, daß ich selbst Raubkopierer bin. Ich bin 15 Jahre und mir voll und ganz bewußt, daß mein Tun illegal ist. Jedoch läßt sich von dieser »kleinen« Taschengeldaufbesserung (zirka 100 Mark pro Monat) ganz gut leben. Ich möchte aber Ihre These, »die Raubkopierer sind für die hohen Softwarepreise verantwortlich« widerlegen. Denn was war eher, die Software oder die Raubkopie? Es ist doch logisch, daß man ohne die teure Software, die urheberrechtlich geschützt ist, keine Raubkopie machen kann. Ich stimme Ihnen voll und ganz zu, daß es (auf gut deutsch gesagt) eine Schweinerei ist, daß Kinder genau dieselbe Strafe bekommen wie Profihacker. Ich will Ihnen für die wirklich gute Idee der billigen Kleinanzeigen keine Vorwürfe machen, sie ist nur ein weiterer guter Bestandteil Ihres sonst hervorragenden Heftes, aber meinen Sie nicht, daß Sie damit Raubkopierer etwas animieren? Meinen Brief unterzeichne ich mit

H. Acker

Es ist richtig, wenn Sie meinen, nicht die Raubkopierer allein wären für die-hohen Software-Preise verantwortlich zu machen. Dazu kommt natürlich auch der oft enorme Entwicklungsaufwand, der in so einem Programm steckt. Nicht zuletzt wollen auch der Hersteller, die Distributoren und Händler einen kleinen Gewinn nach Hause tragen.

Es ist traurig aber wahr, daß die kleinen (sprich jungen) Raubkopierer mit demselben Strafmaß zu rechnen haben wie die großen. Die Firmen gehen in dieser Hinsicht aber nach dem Grundsatz: »Wehret den Anfängen« vor. Ein amerikanischer Datenschützer sprach einmal von der »fehlenden Moral« im Bereich der Software. Es ist in der Tat unter den Jugendlichen ein schwereres Vergehen, jemandem die Cola wegzutrinken, als einem relativ anonymen Entwickler das geistige Eigentum in Form eines Spiels oder Anwenderprogramms zu klauen. Sicher, die Materie, das Programm ist etwas reell nicht Greifbares; außer auf der Diskette (und das sollte man ja tunlichst vermeiden).

Die von Ihnen angesprochenen Kleinanzeigen in unserer Zeitschrift sind da nur ein Spiegel der Gesellschaft. Geplant waren sie, um dem Leser eine billige Möglichkeit zu bieten, Kontakte zu knüpfen, Erfahrungen auszutauschen, nicht mehr benötigte Hard- und Software zu verkaufen und vieles andere mehr. Nicht beabsichtigt war natürlich, den Raubkopierern ein preisgünstiges Forum für ihre illegalen Geschäftspraktiken zu sein. Wir sind um Abhilfe bemüht, aber wie läßt sich eine Anzeige über 100 selbstgeschriebene Programme von 100 raubkopierten unterscheiden, wenn dies nicht im Text erscheint. Außerdem gibt es in einigen Bereichen, wie zum Beispiel dem Lehrberuf, sogenannte »Public Domain Software«, die der Öffentlichkeit zugänglich gemacht wird.

Es ist nicht unsere Aufgabe und entspricht auch nicht unserem Selbstverständnis, der Vorreiter für die Industrie zu sein. Doch es ist unser Bestreben, ein in allen Belangen »sauberes« Magazin für den Computer-Fan zu machen. Dazu gehört es auch, rechtzeitig zu warnen, Mißstände aufzuzeigen und Hilfestellung zu leisten. Und diese Art der Taschengeldaufbesserung ist nicht in Ordnung. Die jungen Schüler und Studenten, denen es gelingt, den Software-Schutz fremder Programme zu knacken, eigene Kommentare und Veränderungen im Programm anzubringen, die verstehen doch etwas vom Programmieren. Diese Energien und dieses Know-how ließe sich doch wesentlich sinnvoller für die Entwicklung eigener, guter Programme einsetzen. Es gibt genug Programme auf dem Markt, die es nicht einmal wert sind, kopiert zu werden. Dagegen sollte man mit seinem ganzen Können angehen. Gerade in Deutschland sind wir in der Computertechnologie und der Softwareerstellung noch um Jahre hinter den USA, Großbritannien oder Japan. Es ist an der Zeit, denen zu zeigen, wo der Bartel den Most holt. Gute Software erstellen, zu einem fairen Preis, da liegt Eure Chance.

(aa)

# Fehlersuche in Basicprogrammen - 2. Teil

> Immer wieder erreichen uns Anrufe von Lesern, die (besorgt) anfragen, ob in diesem oder jenem Listing Fehler bekannt sind. Meistens handelt es sich jedoch um Eintipp-Fehler, vom Leser selbst verursacht. Und meistens liegen die tückischen Fehler innerhalb von DATA-Zeilen. Was tun?

Wie schon in der vorletzten Ausgabe des 64'er-Magazins angedeutet wurde, sind Eintipp-Fehler in DATA-Zeilen besonders tückisch. Und das hauptsächlich aus zwei Gründen. Erstens zeigt eine eventuelle Fehlermeldung nie auf den wirklichen Fehler, sondern in der Regel auf die Einlese- (READ-) Schleife dieser Daten. Zweitens, und das ist noch viel unangenehmer, kann es vorkommen, daß es gar keine Fehlermeldung gibt, sondern der Computer einfach aussteigt und »abstürzt«. Hoffentlich haben Sie das mühsam eingegebene Programm vor dem ersten RUN abgespeichert!

Gerade Anfänger haben jetzt Schwierigkeiten. Und deshalb möchte ich mich hauptsächlich an diese wenden.

Als erstes möchte ich Ihnen empfehlen, noch einmal das »Handbuch« des VC 20/C 64 in die Hände zu nehmen. Lesen Sie noch einmal durch, was dort über den READ/DATA-Be-fehl geschrieben steht. Auch ich bin diesem ominösen READ-Befehl anfangs möglichst aus dem Weg gegangen und stehe ihm jetzt noch manchmal mit Mißtrauen gegenüber. Und das liegt an den oben genannten zwei Punkten.

Oft sind nämlich diese DATA-Werte nichts anderes als codierte Maschinensprache. Und dann kann sogar eine einzige falsch abgetippte Ziffer zum absoluten Kollaps führen. Aber wenn es sich um Maschinensprache handelt, haben alle DATA-Werte einige gemeinsame Merkmale: Erstens sind sie nicht negativ, zweitens sind sie niemals größer als 256 und drittens sind es immer ganze Zahlen. Diese Merkmale können wir benutzen um eine kleine Prüfroutine zu entwickeln, die einen, aufgrund eines Eingabefehlers, falschen DATA-Wert sofort sichtbar macht, wenn er gegen diese Merkmale verstoßen sollte.

Dieses folgende kleine Programm sollten Sie vor oder hinter das zu überprüfende Programm schreiben. Nach abgeschlossener Prüfung kann es ruhig wieder gelöscht werden. Hier das Programm:
50000 READ A$; PRINT "ZEILE "PEEK(64)*256 + PEEK(63);A$
50010 POKE198,0: WAIT 198,1:GOTO 50000

Starten Sie das Programm in diesem Fall mit RUN 50000. Sie werden jetzt den ersten DATA-Wert am Bildschirm sehen, davor die Zeilennummer, in der dieser Wert steht. Wenn Sie dann eine Taste drücken , zum Beispiel die große Leertaste, wird der nächste Wert sichtbar, direkt darunter. Bei fortwährendem Drücken der Leertaste, rasen die Zahlen sehr schnell über den Bildschirm. Für den ersten Durchlauf sollten Sie das ruhig machen. Man sieht dann sofort, ob eine Zahl (unzulässiger Weise?) länger als drei Ziffern ist. Falls dies der Fall ist, können Sie sehr schnell im Originallisting nachschauen, ob der Wert in Ordnung ist. Falls der Fehler so jedoch nicht erkannt werden kann, bleibt nichts anderes übrig, als das Programm noch einmal zu starten und diesmal jeden einzelnen Wert mit dem Original zu vergleichen. Machen Sie sich aber keine Sorgen über die Fehlermeldung »OUT OF DATA ERROR» die unweigerlich am Ende auftaucht. Sie zeigt hier lediglich, daß alle DATAs angezeigt wurden.

Apropos Fehlermeldung. »OUT OF DATA ERROR« oder »ILLEGAL QUANTITY ERROR«. Wenn nach dem Starten des Hauptprogramms eine dieser Fehlermeldungen kommt, können Sie fast todsicher davon ausgehen, daß ein DATA-Wert falsch eingetippt wurde. Das »fast« nur deswegen, weil Sie eventuell die FOR-NEXT-Schleife, in der ein READ-Befehl steht, falsch eingegeben haben. Die Bedeutung dieser Fehlermeldungen sind im schon erwähnten Handbuch erklärt.

Ich hoffe, daß Sie mit dieser kleinen Routine in Zukunft schneller diese lästigen Fehler finden. Um Ihnen aber die Fehlersuche noch etwas weiter zu erleichtern, habe ich ein weiteres Programm geschrieben. Wir werden in den kommenden Heften bei Programmen mit vielen DATA-Werten eine spezielle Prüfsummenliste mit abdrucken, die es gestattet, alle DATA-Werte blockweise zu überprüfen. Dazu müßen Sie dann jedesmal das hier abgedruckte Programm (siehe Listing) an das zu testende Programm anhängen (entweder mit MERGE oder durch Abtippen) und laufen lassen. Damit kann ein Tippfehler auf wenige DATAs eingegrenzt werden. Wenn Sie das nebenstehende Programm laufen lassen, sollten Sie am Bildschirm die gleichen Werte erhalten wie die dann abgedruckte Prüfsummenliste. Eine Abweichung kann auf einen Eingabefehler hinweisen (muß aber nicht). Die vier Spalten der Prüfsummenliste haben folgende Bedeutung:

Ganz links steht unter ZEILE die Zeilennummer des letzten DATA-Wertes des jeweiligen Blocks, daneben die Anzahl der bisher gelesenen DATAs, rechts davon die Summe aller bisher gelesenen Werte und ganz rechts eine mögliche Fehlerquelle, das heißt, hier wird ein Wert angezeigt, wenn er größer als 256 ist oder einer gebrochenen Zahl, aber auch, wenn er keine Zahl ist und Buchstaben enthält.

Die als Beispiel abgedruckte Prüfsummenliste sieht so aus, wenn Sie den DATA-Tester an das in diesem Heft veröffentlichte Mailbox-Programm angehängt haben. Es wurden hier jeweils 30 DATAs gelesen und deren Prüfsumme errechnet. Man sieht auch, daß sich zum Beispiel in Zeile 10030 (die erste Zahl in der Prüfsummenliste) ein Leerstring befindet. An dieser Stelle werden Sie im Mailbox-Programm zwei Kommata finden. Das gleiche gilt für die Zeilen 10040,10100,10150,10170 und 10220. Insgesamt werden 282 DATAs gelesen. Die Gesamtsumme beträgt 32970. Die Spalte unter »TEXT« bleibt leer, weil in den DATAs weder Text noch negative Zahlen vorkommen.

Ich hoffe, daß Sie mit diesen Mitteln mögliche Eingabefehler schneller finden und somit nicht vorschnell Frust aufkommt. Aber einen Fehler werden Sie oft vergebens suchen: Das ist der, den unser Fehlerteufel hinzaubert. Aber dem werden wir in der Redaktion schon das Leben schwer machen (umgekehrt allerdings genauso).

(gk)

# Spring Vogel, Spring

> Kennen Sie Jumpman, Miner 2049 oder Mister Robot and his Factory? Dann haben Sie sich sicherlich geärgert, daß Sie nie die letzten Bilder erreicht haben. Oder Sie haben sich über die eintönigen Spielszenen geärgert. Mit dem Listing des Monats wäre das nicht passiert. Spring-Vogel ist eine Kombination aus den drei Spielen. Eines kann jedoch nicht mehr passieren! Wird eines der Bilder langweilig, dann machen Sie sich einfach ein neues.

Tatsächlich kann man Spring-Vogel fast als Spielgenerator bezeichnen. Mit Spring-Vogel gelingt es Ihnen, sich jedes beliebige Spielfeld aufzubauen. Das klingt sehr vielversprechend, und das ist es auch. Spring-Vogel ist ein Vertreter derJump and Run-Kategorie. Damit lassen sich also keine Schieß- oder Abenteuerspiele erzeugen, aber innerhalb der Spring- und Laufgruppe bleibt kein Wunsch offen. Worum handelt es sich bei Spring-Vogel nun eigentlich? Zunächst die Story.

Ein heftiger Sturm hat einen Vogel – unseren Helden – mitsamt seinen Eiern aus dem Nest geweht. Durch den harten Aufprall auf die Erde hat er sich seine Flügel gebrochen. Er kann also nicht mehr richtig fliegen, sondern nur noch auf dem Boden laufen, hüpfen und springen. Die Aufgaben des Vogels (die genaue Klassifizierung bleibt Ihnen überlassen) besteht nun darin, in einem Labyrinth aus Aufzügen, Transportbändern, Seilen, Einbahnstraßen, Trampolinen, Rutschbahnen, Gummiwänden, magischen Flügeln, gemeinen Vogelfallen und mißgestimmten Monstern alle Eier wieder einzusammeln. Gelingt es dem Vogel, die Eier in einer Spielszene aufzunehmen, muß er mit der nächsten Überraschung fertig werden; es waren nicht alle. Das nächste vom Winde verwehte Bild erwartet ihn mit weiteren schwierigen Aufgaben.

Die Anzahl der Torturen für unseren leidgeprüften Helden bestimmen Sie selbst. Doch Vorsicht, unser Vogel verfügt nicht wie eine Katze über sieben, sondern »nur« über sechs Leben. Und diese sechs Leben sind schnell, durch Kontakt mit den Monstern oder Verzehrern einer roten Tollkirsche, ausgehaucht.

Der Sturz über mehr als vier Etagen ist ebenfalls für den flugunfähigen Vogel lebensbedrohend. Es sei denn, er findet die von seinem Tierschützer verstreuten »magischen Flügel«. Ausgestattet mit deren zauberhaften Fähigkeiten kann er in einem ökologischen Flecken beliebig umherfliegen. Durch Betätigen des Feuerknopfes wird er wieder in seinen behinderten Zustand zurückversetzt, erlangte allerdings vorher die Fähigkeit an unzugänglichen Stellen landen zu können. Diese magischen Flügel gestatten es, Bilder so aufzubauen, daß nur der taktisch gezielte Einsatz dieser Flughilfe es ermöglicht, ein Bild vollständig abzuräumen. Dabei kann es vorkommen, daß sich der Vogel in eine völlig aussichtslose Situation manövriert, und in einer Sackgasse landet. Auch hier bietet das Programm einen Ausweg an, die Funktionstasten. Diese können jederzeit (außer während der Flugphase) benutzt werden.

Die genaue Bedeutung können Sie der Beschreibung zum Listing entnehmen. Um zu sehen, welcher Vogel von welchem Spieler der bessere ist, gibt es auch hier eine Punktezählung. Bei den bereits mitgelieferten Bildern ist diese in Zehnerschritten ab dem ersten Bild gestaffelt.
Entscheidungskriterien

Weshalb wurde dieses Programm zum Listing des Monats auserkoren? Das Hauptkriterium war die Realisierung eines Spielegenerators. Mit dem Editiermodus von Spring-Vogel lassen sich nahezu beliebig viele Bilder konstruieren. Wird ein Bild langweilig, so kann man ohne großen Aufwand ein neues mit noch größeren Schwierigkeiten entwickeln (versuchen Sie aber erst einmal, die beiden bereits existierenden Bilder 5 und 6 zu bewältigen). Der Phantasie sind keine Grenzen gesetzt.

## Warum alleine spielen?

Vorstellbar ist ein Wettbewerb unter Freunden, wer das lustigste, das interessanteste, das schwierigste oder das raffinierteste Bild entwirft. Der Programmieraufwand hält sich für ein solch komplexes Programm in relativ bescheidenen Grenzen. Die vorgegebenen Bausteine bieten eine derartige Vielfalt an verschiedenen Bildern, daß jeder nach seinem eigenen Geschmack entwerfen kann. Insgesamt ein Programm, das durch Witz und Programmierkunst überzeugt.

(aa/Matthias Törk)

## Der Gewinner

> Sein Ärger brachte Matthias Törk 2000 Mark ein.

Ich bin am 18.4.1955 geboren und studiere derzeit Germanistik, Philosophie und Informatik. Mein erster Computer war ein VC 20, der dann Anfang 1983 durch einen C 64 ersetzt wurde.

Für die Entwicklung des Programms »Spring-Vogel« ist neben der verlockenden Aussicht auf 2000 Mark vor allem der Ärger über Spiele wie »Jumpman Jnr.« oder »Miner 2049er« verantwortlich, bei denen ich die letzten Bilder nie zu sehen bekam. Nach kleinen Änderungen an diesen Programmen, die die Helden mit Unsterblichkeit versorgten, war zwar das Ende einfach zu erreichen, aber leider wurden die Spiele dadurch auch schnell langweilig. Deshalb wollte ich ein ähnliches Spielprogramm entwickeln, daß diese Nachteile vermeidet.

Zunächst sollte es möglich sein, jedes einzelne Bild extra anzuwählen und vor allem sollten sich einfach neue Bilder erstellen lassen sobald die alten langweilig werden. Durch konsequente Parametrisierung und eine Spielroutine, die in der Art eines Interpreters die Bilder und Tabellen abarbeitet, entwickelte sich aus dieser Idee schließlich ein regelrechter »Generator« für solche »Jump an Run«-Spiele. Das Ergebnis liegt nun nach rund einem Monat Entwicklungszeit in Form von »Spring-Vogel« vor, einem Programm, mit dem Sie sicher viel Spaß haben werden.

(Matthias Törk)

# Die Musik macht der C 64

> Wie musikalisch der C 64 sein kann, ist den meisten bekannt, wie man die Musik macht, aber den wenigsten. Dieses Programm, als Anwendung des Monats, zeigt die Fähigkeiten Ihres Computers.

Elf verschiedene Instrumente sind in diesem Programm schon verwirklicht. Sie können zwischen Piano, Röhrengong, Metallophon, Xylophon, Glocke, Glasorgel, Violine, Flöte, Panflöte, Klarinette und Harfe auswählen. Das Programm läßt sich jedoch noch erweitern. Ihrer Phantasie sind keine Grenzen gesetzt.

Empfehlenswert ist ein Verstärker oder eine Stereoanlage. Das Programmlisting ist weitgehend selbstdokumentierend, daher nur einige Hinweise zur Bedienung:

Oben rechts wird eine Klaviatur dargestellt, die der augenblicklichen Tastenbelegung entspricht. Gespielt wird durch Drücken der jeweiligen Taste.

Die Instrumente werden durch geshiftete Buchstaben gewählt.
<b>Besondere Funktionen:</b>
- Halleffekt:
Alle drei Tongeneratoren werden abwechselnd benutzt, so daß immer zwei Töne nachklingen. Symbol: <<<0>>> ganz unten.
— Oktavenwahl:
Oktaven wählbar von Sub-contraoktave (SCO) bis dreigestrichene Oktave (O'''). Die Subcontraoktave ist nur durch Einzeltonverschiebung zu erreichen. Das Pfundzeichen setzt Instrumente in die Grundoktave zurück und die Einzeltonverschiebung 0. Symbol: unter der Klaviatur.
— Einzeltonverschiebung:
Die Tastaturbelegung kann in Einzeltonschritten über den gesamten Tonbereich verschoben werden. Symbol: Klaviatur
- Akkorde:
Zweiklang, wählbar bis None. Apostroph setzt Akkorde auf 0. Symbol: >?< links neben Halleffekt.
— Lautstärke:
wählbar von 0 bis 15.
Symbol: 0000000000...unten.

Von der Bildschirmaufteilung her kann noch ein Instrument zusätzlich entworfen werden. Dazu muß man die Variable IZ in 150 gleich 11 setzen. Nun kann man ab Zeile 620 das neue Instrument entwerfen.
<b>Format:</b>
Name, Wellenform, Anschlag-Abschwellen, Halten-Ausklingen. Tastverhältnis low, Tastverhältnis high, Hall (3 = ja, 1 = nein), Grundoktave Contraoktave = 0), Bild (10 x 7).

Soll mehr als ein neues Instrument entworfen werden, muß man die Bildschirmgestaltung ändern.

(Christian Gebauer/rg)

## Der Orgelbauer

>> Wohlklngende Münze erhiett Christian Gebauer fiir sein Musikprogramm. Der Autor steBt sich selbst kurz vor.

Ich wurde am 21. Oktober 1965 in Bad Nauheim geboren. Nach der Grundschule besuchte ich das Ernst-Ludwig-Gymnasium, an dem ich gerade die 12. Klasse absolviert habe und mich auf das Abitur vorbereite.

Meine Kombination der Leistungskurse ist Chemie und Mathematik, beides Fächer, die mich sehr interessieren. In diesemJahr belegte ich einen EDV-Kurs, der von der Schule angeboten wurde.

### So fing es an

Zur Computerei bin ich durch einen Bekannten gekommen, der mir im Herbst 1982 für mehrere Wochen einen Computer geliehen hat und mich in Basic einweihte. Meine Kenntnisse dieser Sprache vertiefte ich dann im Selbststudium.

Im darauffolgenden Frühjahr kauften mir meine Eltern einen Commodore 64 mit Floppy 1541, ein halbes Jahr später kam dann noch ein Seikosha-Drucker GP-100VC hinzu.

Das Programm »Orgel« begann ich im Sommer 1983 zu schreiben, um die hervorragenden Toneigenschaften des Gerätes auszunutzen. Diese Version ist das Ergebnis eines halben Jahres Erweiterungs- und Verbesserungsarbeit.

(Christian Gebauer)

# Schiebung

>Dieses kleine Strategiespiel auf dem VC 20 ist die Computerversion eines bekannten »Zeitvertreibers«.

Nach dem Eintippen und Starten des Schiebespiels erscheint ein Feld mit 24 Buchstaben von A bis X und ein Feld mit einem »—«. Es kann nun immer ein Buchstabe eingegeben werden, der neben, über oder unter diesem Feld steht. Anschließend ertönt ein kurzer Piepston und der Buchstabe wandert in das »Leerfeld«, wobei an der Stelle, an der zuvor der Buchstabe war, ein neues Leerfeld entsteht (Buchstabe und »—« wechseln also den Platz). Wird ein Buchstabe eingegeben, der nicht Nachbar des mit »—« bezeichneten Feldes ist, so wird die Eingabe ignoriert.

Dieser Schiebevorgang muß so oft und geschickt wiederholt werden, bis die Buchstaben schließlich in alphabetischer Reihenfolge (spaltenweise von oben nach unten gelesen) sind. Das Leerfeld muß am Ende wieder rechts unten sein.

Wenn dieses geschafft wurde, muß man die Funktionstaste f 1 betätigen. Danach wird geprüft, ob die Aufgabe richtig gelöst wurde. Wenn man schon f 1 drückt, bevor die Reihenfolge korrekt ist, so meldet der Computer den Irrtum und das Spiel kann fortgesetzt werden. Während des Spiels werden rechts unter dem Feld die Anzahl der bisher benötigten Schritte angezeigt.

Das Spiel läuft auf allen Versionen des VC 20 (mit oder ohne Speichererweiterung).

(Gerhard Gaber/ev)

# Bildschirmmasken schnell erstellt

> Bei jedem selbstgeschriebenen Anwendungsprogramm steht man in der Regel stets aufs Neue vor dem Problem, zur Abfrage diverser Parameter eine geeignete Bildschirmmake zu erstellen. Dieser Maskengenerator macht die Arbeit etwas einfacher.

Dieser Generator für den VC 20 liest eine Maske direkt vom Bildschirm und erzeugt automatisch die entsprechenden PRINT-Befehle im Programm. Durch diesen Vorgang löscht der Generator sich selbst, so daß ein SAVEn des Programms unmittelbar nach dem Eintippen unbedingt notwendig ist.

Das Programm benötigt eine Erweiterung von mindestens 8 KByte, da am Schluß der Basicspeicher höher gelegt wird. Ohne Erweiterung würde Speicherplatz fehlen. Auch müßte man eine Verschiebung des Bildschirm- und Basicspeicher beachten. Das Programm wird nach dem Laden einfach mit »RUN« gestartet. Danach erscheint eine kurze Anleitung.

## So wird die Maske aufgebaut

In Zeile 23 wird der Tastaturpuffer abgefragt. Wurde eine Taste gedrückt, wird er auf 0 zurückgesetzt. Nun wird in Zeile 1000 der Bildschirm gelöscht und eine Datei für den Bildschirm eröffnet, da der Bildschirm dann ja ausgelesen wird und daraus die neuen Zeilen der Maske generiert werden. Sie sehen jetzt eine geänderte Farbe und den blinkenden Cursor. Nun erstellen Sie Ihre Maske nach Ihren Wünschen, wobei Sie mit den Cursortasten bliebig hin- und herfahren können. Ist die Bildschirm-Maske in der richtigen Form, drücken Sie RETURN.

Jetzt wird der Bildschirmspeicher ausgelesen. Die neue Zeile wird mit Zeile 2O1O generiert. Das Fragezeichen ist die Kurzform von Print, (CHR$(34) ist der Code für Anführungsstriche. Das Generieren von neuen Programmzeilen geschieht in einer Schleife. Sind alle 23 Bildschirmreihen ausgelesen, springt das Programm nach Zeile 10000. Jetzt wird der Anfang vom Basicspeicher höher gelegt und Zeile 23 gelistet. Nun muß noch ein Leerzeichen aus Zeile 23 entfernt werden. Damit ist die neue Maske fertig und kann abgespeichert werden, oder das nachfolgende Programm kann direkt geschrieben werden. Zeile 50 sorgt dafür, daß das Bild nicht nach oben gescrollt wird. Dadurch wird auch die READY-Meldung unterdrückt. Die fertige Maske wird auch wieder mit RUN gestartet.

(Bernd Borghold/ev)

# Deutscher Zeichensatz für den VC 20

> Wenn man die ersten (Programmier-) Schritte mit seinem neu erworbenen VC 20 gegangen ist und schon das eine oder andere Programm »geboren« hat, vielleicht ein Adressenprogramm oder eine Lagerliste, spätestens dann wird man die Entdeckung machen, daß der VC 20 trotz deutscher Produktionsstätte nur Englisch spricht, für deutsche Umlaute und »ß« also kein Interesse zu haben scheint.

Dies bedauert man noch umso mehr, wenn man eine anschließbare elektronische Schreibmaschine mit deutschem Typensatz besitzt.

Zwar ist auf der Tastatur des VC 20 kein Platz für einen deutschen Zeichensatz vorgesehen, es ist jedoch möglich, bestimmte Tasten dafür auszuwählen, deren CHR$-Code demjenigen des gewünschten deutschen Umlautes auf der Schreibmaschine entspricht.

Auf diese Weise kann man zwar deutsche Texte drucken, aber auf dem Bildschirm sieht ein solcher Text recht merkwürdig aus: Hier steht zum Beispiel das Zeichen für das britische Pfund statt »ö«.

Auch hier ist mit einigem Know-how Abhilfe zu schaffen oder mit meinem Programm »DEUZEI«.

## Der Zeichengenerator

Woher weiß der VC 20 eigentlich, wie die einzelnen Zeichen auszusehen haben, die man auf dem Bildschirm sieht? Hierzu bedient er sich eines Speicherbereichs Hex. 8000 bis 8FFF beziehungsweise 32768 und 36863 dezimal.

In diesem ROM-Bereich sind in genau festgelegter Reihenfolge (vergleiche Bildschirm-Code-Tabelle des Handbuches) die Bitmuster aller verfügbaren Zeichen in jeweils acht hintereinander stehenden Speicherstellen festgelegt.

Wie das funktioniert, veranschaulicht Bild 1: Jedes Zeichen ist auf dem Bildschirm in einer 8 x 8-Matrixwiedergegeben, ein Bildpunkt entspricht einer »1« im Dualcode, sonst steht die »0« (freie Felder). Da ja pro Speicherplatz 8 Bit gespeichert werden, benötigt man 8 Byte pro Zeichen.

Der Computer weiß durch sein Betriebssystem, welche acht Speicherstellen er bei einem Tastendruck abfragen muß, es erscheint soweit recht leicht möglich, ihm ein geändertes Bitmuster in diese Speicherstellen zu »schmuggeln«, zum Beispiel durch POKEs. Dies scheitert allerdings daran, daß der Zeichengenerator im ROM-Bereich liegt und somit nur Lesen, aber nicht Verändern der gespeicherten Daten zuläßt.

Hier hat dankenswerterweise Commodore ein Hintertürchen offengelassen, um doch noch am Datensatz manipulieren zu können. Man kann dem Betriebssystem mitteilen, daß der Zeichensatz an einer anderen Stelle sitzt als normal; dies ist in Speicherstelle 36869 codiert.

Benutzt man nun einen RAM-Bereich für den alternativen Zeichensatz, so kann man nach Lust und Laune Veränderungen der Bitmuster vornehmen.

Da man ja doch wohl gern die Bitmuster der meisten Zeichen übernehmen möchte, wäre es ganz sinnvoll, vor der Kreation einiger neuer Zeichen erst einmal die Bitmuster des Zeichengenerator-Bereichs in den ausgewählten RAM-Bereich zu kopieren (immerhin 4 KByte). Diese Aufgabe übernimmt ein kleines Maschinenprogramm (Listing 2), das im Programm »DEUZEI« integriert ist. Ein Kopieren durch Basic-POKEs ist hingegen recht zeitraubend.

Um Speicherplatz im RAM zu sparen, kopiert »DEUZEI« allerdings nur den Zeichenset 2, der Groß- und Kleinbuchstaben, Ziffern und einige Grafikzeichen enthält (normal und invers), aber nur 2 KByte RAM beansprucht.
»DEUZEI« benutzt den RAM-Speicher wie folgt: Zeichengenerator: Page 16 bis 23; Bildschirmspeicher: Page 24 und 25; Basicprogramme ab Page 26 (Bild 2). Eine Page entspricht einem 256-Byte-Block. Der Bildschirmspeicher befindet sich beim VC 20 ab 8 KByte Erweiterung normalerweise in Page 16 und 17 (4096 bis 4607), muß bei »DEUZEI« allerdings »umziehen«; dies erfährt das Betriebssystem durch entsprechende Codierung der Speicherstellen 648 (siehe Zeile 130) und 36869 (zugleich Pointer für den Zeichengenerator).
Das eigentliche Programm »DEUZEI« beginnt bei der Speicherstelle 6656 (Page 26). Da man es nach dem Generieren des neuen Zeichensatzesja nicht mehr benötigt, wird es beim Einladen eines neuen Programms ab Page 26 gelöscht. Es fehlen dem neuen Programm also nur genau 2 KByte RAM-Speicherplatz, den der neue Zeichensatz beansprucht.

TODO Tabelle

## Eingabe von »DEUZEI«

Wenn man nun das Programm »DEUZEI« in den Computer eingibt und übereifrig mit RUN startet, wird man eine böse Überraschung erleben: Das Programm stürzt sofort ab und ist zudem auch noch gelöscht!

Des Rätsels Lösung: Normalerweise werden Basicprogramme ja ab Page 18 (Speicherstelle 4608 = 18*256) abgelegt. In diesen Bereich transformiert allerdings das Maschinenprogramm den neuen Zeichensatz und »zerstört« frühzeitig das Basicprogramm. Man muß folglich Sorge tragen, daß das Programm ab Page 26 im Speicher steht. Hierzu sollte man folgendermaßen vorgehen:

1.	»DEUZEI« eingeben und auf Band oder Floppy abspeichern (kein RUN!)
2.	Programm mit NEW löschen und folgende Basiczeile eingeben:
1 POKE 44,26:POKE 6656,0:PRINT CHR$(3):RUN
3.	RETURN-Taste drücken, aber nicht RUN!
4.	POKE 44,26:POKE 6656,0 eintippen, dann RETURN-Taste drücken
5.	Eingabe von NEW; RETURN-Taste
6.	Einladen des abgespeicherten »DEUZEI«
7.	POKE 44,18 eintippen und unter neuem Namen abspeichern.

Die kleine Mühe hat sich sicherlich gelohnt, denn das neu abgespeicherte Programm ist nun absolut »wartungsfrei«. Es kann ganz normal eingeladen werden, setzt automatisch die Basicuntergrenze auf Page 26, generiert den neuen Zeichensatz in 2 bis 3 Sekunden und erlaubt das Einladen beliebiger Basicprogramme ohne Zusatz-POKEs.

Erklärung für obige Prozedur: Die erste Basiczeile muß am Anfang von Page 18 liegen, der Interpreter erwartet das so. Startet man das »umgebaute« Programm, so wird in dieser Zeile der neue Basicbeginn mitgeteilt, und zwar mit POKE 44,26.

Dieses Miniprogramm wird mit PRINT CHR$(3) abgebrochen und mit RUN in der gleichen Zeile das eigentliche »DEUZEI« ab Page 26 gestartet. Dies sitzt bereits richtig, da man es (siehe unter 4) gleich in Page 26 geladen hat. Danach wurde der Basicanfang wieder durch POKE 44,18 herabgesetzt und somit das funktionsfähige Programm abgespeichert.

Dieses Vorgehen bedeutet zwar, daß beim Abspeichern fast 2 KByte unbrauchbares Material mit abgespeichert wird, aber der Vorteil der besonderen Bedienungsfreundlichkeit überwiegt doch eindeutig.

## Arbeiten mit »DEUZEI«

Nach dem Einladen des—wie oben beschrieben bearbeiteten — Programms »DEUZEI« erscheinen die neuen Sonderzeichen auf dem Bildschirm normal/invers, und beliebige Programme können geladen werden.

Die neuen Zeichen und ihr CHR$- beziehungsweise POKE-Code:

TODO Tabelle

Dieser Zeichensatz bleibt erhalten, solange der VC 20 eingeschaltet ist, wird allerdings durch Betätigen der RUN STOP/RESTORE-Tasten abgeschaltet; es wird wieder der Pointer auf den normalen Zeichensatz gesetzt. Durch Eingabe von: POKE 36869,236:POKE 648,24:CLR kann man aber wieder den neuen Zeichensatz verfügbar machen. Leider sind sich offensichtlich nicht alle Produzenten von Drucker-Interfaces bezüglich der CHR$-Codes für die deutschen Umlaute einig. So kann es vorkommen, daß bei bestimmten Druckern das »ß« nicht gedruckt wird, wenn es auch noch so deutlich am Bildschirm prangt. Das ist allerdings kein Beinbruch, man muß nur herausfinden, welchen CHR$-Code dieses Zeichen vom Hersteller erhalten hat. Eine Anpassung von »DEUZEI« ist dann mit Hilfe der Tabellen des VC 20-Handbuchs einfach:

1.	In CHR$-Tabelle Zeichen suchen, das der Code-Nummer entspricht.
2.	In POKE-Tabelle den POKE-Wert für dieses Zeichen ablesen.
3.	POKE-Wert*8+4096 ergibt erste Speicherstelle für neues Zeichen; diesen Wert im Listing ersetzen.

Beispiel: Buchstabe »ß« ist als CHR$(94) vorgesehen.

Normales Zeichen (Pfeil nach oben) entspricht POKE 30. 30*8+4096 = 4336. In Zeile 270 des Listings ist dieser Wert zu finden. Ist nun der CHR$-Code beispielsweise für »ß« = 126 (entspricht dem Zeichen 7r), so ergibt sich aus der POKE-Tabelle: 94*8+4096 = 4848 als neuer Wert im Listing.

Um die entsprechenden Speicherplatzdaten für die inversen Zeichen zu finden, muß man nur zu den berechneten Werten noch 1024 addieren (vergleiche DATA-Zeilen 700 bis 760 in Listing 1).

## »DEUZEI«-Ausbau

Wem die deutschen Sonderzeichen nicht ausreichen für seine verschiedenen Vorhaben, der kann natürlich recht einfach in das Programm noch zusätzliche »Phantasiezeichen« einbauen. Das Auffinden der gewünschten Speicherstelle und die Berechnung der 8 Byte-Werte für das Bitmuster der 8x8-Zeichenmatrix sollten ja keine Schwierigkeiten mehr bereiten.

Als Beispiel sei der Ersatz des »Klammeraffen« (CHR$:64; POKE:0) durch eine »Brezel« aufgezeigt, die ab Speicherstelle 0*8+4096 = 4096 codiert wird (Bild 3). Diese beiden Programmzeilen wären hier einzufügen:
361 forbr=0to7:readda%:poke4096+br,da%:next
770 data0,60,66,165,153,153,102,0

In analoger Weise kann man sich auch leicht beliebige andere Zeichen definieren.

(Peter Wülknitz/ev)

# Spring Vogel, spring

> Das Listing des Monats zur Erzeugung von »Jump and Run«-Spielen für Commodore 64.

Bei dem ersten Start des Progrmms dauert es einige Zeit (bei weiteren Starts geht es dann schneller), bis sich das Programm mit der Frage »Edit, Wahl oder Spiel?« meldet.

Mit »W« kann man eines der sechs Bilder zum Spielen auswählen, mit »S« wird ein vollständiges Spiel ab Bild 1 gewählt.

Die Funktionstasten haben folgende Bedeutung:
f1: Dieses Spiel aufgeben, zurück zum Menü
f2: diesen Vogel opfern und mit dem nächsten Vogel neu an der Startposition beginnen
f3: mit dem nächsten Bild weitermachen
f5: Pause (weiter mit SPACE)

Für jedes Ei gibt es jen ach Bild 10, 20... 60 Punkte. Wird ein Bild in einer bestimmten Zeit beendet, so erhält der Spieler einen Bonus, der um so größer ist, je schneller das Bild beendet wurde.

## Der Editor

Der Editor dient dazu, eigene Spiele zu entwickeln. Mit ihm können neue Bilder erstellt werden, die im Programmtext selbst die alten Bilder überschreiben. Deshalb sollte das Programm vor dem Editieren, das neue Spiel nach dem Editieren unter neuem Namen gespeichert werden. Dazu einfach das Programm mit »STOP« abbrechen. Der Editor fragt zunächst, welches Bild geändert werden soll. Dann erscheint dieses Bild mit einem Cursor. Es stehen folgende Funktionen zur Verfügung:

←: die vorgenommenen Änderungen endgültig in den Programmtext übernehmen
f1: Editor verlassen, ohne Änderungen zu übernehmen. Das Bild bleibt erhalten, wie es vor dem Editoraufruf war. In beiden Fällen fragt das Programm, ob das Bild ausprobiert werden soll. Aus dem Spiel gelangt man mit f1 und E jederzeit in den Editor zurück.

Die Cursorsteuerung erfolgtwie gewohnt über die Cursortasten. SHIFT CLR: Bild löschen

Die Startposition des Vogels wird durch »0« festgelegt. In jedes Bild können zwischen 0 und 7 Monster gesetzt werden, die sich horizontal auf einer Breite von acht Spalten hin und her bewegen. Das linkte Ende dieser Bewegungsbahn kann mit den Tasten 1 bis 7 festgelegt werden.

Mit den Tasten A bis T können die 20 verschiedenen Bausteine, die zur Verfügung stehen, gesetzt werden. Der Vogel reagiert immer nur auf das Zeichen unter seinen Füßen. Bei Sprüngen reagiert er (außer bei Wänden) erst in der absteigenden Phase wieder auf Zeichen. Eine Übersicht über die Bau-steinebietetdieTabelle 1. Dazu einigeergänzende Bemerkungen:

Die Bausteine A bis D sind durch verschiedene Bewegungsmöglichkeiten gekennzeichnet. Springen ist möglich:
A: rechts, links
B: rechts, links, runter
C: rechts, links, rauf
D: alle vier Richtungen

Bei E bis H ist eine Bewegung nur in jeweils eine Richtung und kein Sprung möglich.

Bei I bis N wird der Vogel automatisch bewegt. Er selbst kann nur springen.

Der Trampolin 0 bewirkt einen zufälligen Sprung nach rechts oder links.

Bei der Gummiwand S wird der Vogel auf das letzte Zeichen, das weder Wand noch Luft war, zurückgeworfen.

## Hinweise zum Eintippen

Da das Problem in die Interruptroutine eingreift und seinen eigenen Programmtext verändert, sollte es auf jeden Fall vor dem ersten Start abgespeichert werden.

Um das Abtippen des Listings zu erleichtern, wurden im Listing alle Steuerzeichen innerhalb von Printbefehlen durch leicht lesbare Worte entsprechend Tabelle 2 ersetzt. Wenn zum Beispiel im Listing <CD> steht, dann ist an dieser Stellle CURSOR DOWN einzugeben.

Um Tippfehler bei den zahlreichen DATA-Zeilen besser lokalisieren zu können, wurden diese in verschiedene Blöcke mit jeweils eigener Prüfsumme aufgeteilt.

Um das Eintippen der sechs Bilder zu erleichtern, wurden die Zeilen ab 60000 im Kleinschriftmodus gelistet. Hier ist für jeden Großbuchstaben (nicht bei den Ziffern!) die entsprechende Taste zusammen mit SHIFT zu drücken. Hier ist vor allem darauf zu achten, daß jeder PRINT-Befehl genau 39 Zeichen enthält. Fehlende Zeichen können zur Zerstörung des Programms führen, da der Editor diese Zeilen überschreibt.

Daß die jeweils 39 Zeichen genau mit dem Listing übereinstimmen, ist dagegen nicht so wichtig. Durch Abweichungen wird hier allenfalls die Spielbarkeit des vorgegebenen Spiels beeinflußt, ein Mangel, der jederzeit mit dem Editor behoben werden kann. Im Prinzip ist es auch möglich, auf das Abtippen der Bilder 2 bis 6 zu verzichten und an anderer Stelle einfach mit Hilfe des Bildschirmeditors fünfmal das erste Bild zu kopieren. AufjedenFallaber mußdieZahl derZeilen, die Zeilennummer und die Länge der Zeilen mit dem Listing übereinstimmen.

Um das Eintippen der Bilder zu erleichtern, wurden diese in der vorliegenden Programmversion in den Programmtext selbst gelegt. Deshalb ist die Zahl der Bilder auf sechs (diese Zahl wurde gewählt, um die Tipparbeit in erträglichen Grenzen zu halten) festgelegt. Die Anzahl der Bilder kann aber folgendermaßen erhöht werden:

Der Variablen BM in Zeile 50070 ist die gewünschte Anzahl zuzuweisen. Für jedes weitere Bild sind dem Programm entsprechend dem Schema der ersten sechs Bilder 22 PRINT-Zeilen, die jeweils 39 beliebige Zeichen ausgeben, und ein abschließendes RETURN, anzufügen. Die erste Zeilennummer eines Bildes berechnet sich nach der Formel 59900 + Bildnummer*100 + 1, zum Beispiel 60601 für Bild 7.

(Matthias Törk/aa)

# 1520-Hardcopy mit dem VC 20

> Dieses Programm ermöglicht es allen VC 20-Besitzern, Grafik-Hardcopys mit dem Printer/Plotter VC 1520 von Commodore anzufertigen.

Das Programm ist einfach mit »LOAD« und den gerätespezifischen Parametern zu laden. Da es sich um ein Basicprogramm handelt, wird keine Sekundäradresse benötigt.

Mit RUN wird das Basicprogramm gestartet, welches die eigentliche Maschinensprachroutine in Form von DATA-Statements enthält. Das Programm fragt nun nach der Zieladresse, ab welcher die Routine abgelegt werden soll. Ist dabei der angegebene Wert gleich Null, so werden 388 Byte vom Basic-Pointer ($55/56) abgezogen und das Programm dahinter abgelegt. Wird ein anderer Wert eingegeben, so wird das Programm ab dieser Adresse gespeichert und der Pointer bleibt unverändert. Nach dieser Eingabe braucht man sich, da das Basicprogramm über einen Relocator und Prüfsummenabfrage verfügt, nicht mehr um das weitere Ablesen des Maschinenspracheprogramms zu kümmern. Sollte sich ein Prüfsummenfehler ergeben, so wird dieser angezeigt und der DATA-Block mit dem Maschinenprogramm muß auf Tippfehler hin untersucht werden.

Am Ende des Ladevorganges wird die Position der Routine und die Startadresse für den SYS-Befehl angezeigt. Jetzt kann »HARDCOPY 60« mit SYS 0 oder der ausgegebenen Absolutadresse gestartet werden.

Folgende Einschränkungen sind zu beachten:
(a)	Falls ein File mit der logischen File-Nummer 127 geöffnet wurde, so ist dieses vor dem Start von »HARDCOPY 60« wieder zu schließen.
(b)	Der Startbefehl darf nicht im »Direktmodus« stehen.

Das Maschinenprogramm liest beim Aufruf die aktuellen Daten aus den Registern des Video-Interface-Controller (VIC) und berechnet daraus folgende Parameter:

TODO Tabelle

Das Programm liest von links nach rechts die Bildschirm-Codes aus dem Video-RAM und berechnet unter Zuhilfenahme der oben genannten Parameter die Position der Bitmuster im Zeichengenerator. Ist ein Bit gesetzt, so wird seine Position in den MOVE-Befehl des Plotters umgesetzt und dort ein Strich der Länge 1 gezogen.

Ein Video-Punkt entspricht vier Plotter-Punkten woraus sich eine Auflösung von 30 Zeichen pro Plotterzeile ergibt. Dieser 2x2-Punkt hätte einen zweiten Plotvorgang nötig gemacht. Tatsächlich wurde aber die Dauer eines Plot-Vorgangs halbiert indem der Wagenrücklauf des Stiftes mitbenutzt wird. Eine weitere Zeitoptimierung wird dadurch erreicht, indem keine »Leer-Plot«-Befehle ausgegeben werden. Der Stift wird also nur dann bewegt, wenn ein Bit auch gesetzt ist.

Das dauernde »Ticken« des Stiftes läßt sich leider nicht vermeiden, da pro Bit eine neue Positionierung des Stiftes nötig ist (sonst hätte ein Punkt die Größe 3x2).

»Hardcopy 60« kann sowohl für normale Texte, als auch für Grafik-Bildschirme eingesetzt werden.

(Wolfgang W. Wirth/ev)

# Druckfehlerteufekhen

Folgende Fehler sind in den Ausgaben 7 und 8 auf dem Konto von unserem Teufelchen gutgeschrieben worden.

### Komfortables Treiberprogramm für Centronics-Drucker, 7/84, Seite 110

Ein Leserbrief hat ergeben, daß der Drucker NEC 8032 im Bitmustermodus das niederwertige Bit nicht wie der Epson-Drucker unten sondern oben druckt. Damit stehen alle ausgedruckten Bildschirmzeichen bei Verwendung meines Treiberprogramms auf dem Kopf. Bei diesem Drucker müssen deshalb im Programm 2 Byte geändert werden. In Zeile 260 das 2. Datum in 128 und in Zeile 264 das 3. Datum in 70.

(Helmut Eyssele)

### Hardcopy mit dem VC 1520, 7/84, Seite 108

In dem einleitenden Text sind zwei Fehler vorhanden, ein Druck- und ein Denkfehler. Der Druckfehler ist in der POKE-Zeile. Da muß das + durch ein * ersetzt werden. Der Denkfehler ist, daß dies eigentlich überhaupt nicht notwendig ist. Als ich Ihnen das HC 1520-Programm zuschickte, war es ein Teilprogramm in der Pic-Show 1520 und nur für diese Pic-Show war die POKE-Zeile notwendig. Ein Fehler ist auch mir unterlaufen. Die letzte Zeile wird nicht geplottet. Dieser Fehler ist aber leicht zu korrigieren. Einfach die Zahl 7680 in Zeile 330 in die Zahl 8000 verwandeln.

(Jörg Wichmann)

### Zwei Einzeiler, 7/84, Seite 135

Der zweite Einzeiler muß korrekt lauten:
x$ = " ":fori=1to4:xO = x/16:x=x-int(xO)*16:x$ = chr$(48 + x-(x(9)*7)+x$:x=int(xO):next

### Centronics-Schnittstellen, 7/84, Seite 13

In Zeile 110 der Hardcopyroutine für das Görlitz-Interface muß vor dem V unbedingt ein SPACE in den Anführungszeichen eingefügt werden. Die korrekte Zeile lautet:
110 PRINT#1,CHR$(27)”V”.

### Vollautomatisches Blumengießen, 7/84, Seite 82

1.	Der Minuspol vom Netzteil muß mit der Masse (GND) vom User-Port verbunden sein, da die Ansteuerung von T1 sonst nicht klappt.
2.	Der Pfeil im Schaltzeichen von T1 ist umzudrehen.
3.	C1 muß aufgrund seiner Größe ein Elco sein. Im Schaltzeichen muß daher ein + am Pluspol des Gleichrichters eingezeichnet sein.
4.	In einer Zeitschrift für Software-Anwender ist der Hinweis, daß 220 Volt, vor allem im Zusammenhang mit Wasser, auch für Hardware-Bastler tödlich sein können, sicherlich angebracht.

Die Software-Spezialisten danken dem Hardware-Profi und Leser Michael Scharf für diese Hinweise.

### Was ist Comal?, 8/84, Seite 41

Die angebene Adresse der Firma INSTRUTEK in Dänemark ist leider nicht ganz richtig. Genauer, die Adresse stimmt schon, nur kann man dort die Sprache Comal nicht umsonst beziehen. In-struktek bietet nämlich nur die Version 2.0 von Comal für die großen CBMs an, und die kostet um die 600 Mark.

Die von uns besprochene Version 0.14 gibt es als sogenannte Public Domain Software gegen Verpackungs-und Versandkosten bei:
Interpool c/o Prof. Burkard Leuschner
Wiesengrund 6
7487 Gammetingen-Bronnen
Tel: 07574/3728

### Steuerzeichen

Unser Drucker beherrscht immer noch nicht alle Commodore-Steuerzeichen. So ist das Zeichen »_« durch Pfeil links, »^« durch Pfeil nach oben,»/«(revers) durch das reverse Pfundzeichen und »§« durch den Klammeraffen (@) zu ersetzen.

### Pascal, 7/84, Seite 44

Die Version Pascal 64 von Data Becker ist seit einem halben Jahr nicht mehr erhältlich und durch Pascal 64 Version 3.0 vollständig ersetzt worden. Der Umtausch ist für 50 Mark (mit neuem Handbuch) möglich.

# Der Super-Sprite-Editor

> Zirka fünfzig verschiedene Sprite-Editorprogramme erreichten uns in der Redaktion. Das beste Programm haben wir für Sie ausgewählt.

Der Hauptbildschirm besteht aus einem Anzeigefeld (Spalte 0 bis 12) und einem Arbeitsfeld (rechts eingerahmt). Im Anzeigefeld stehen das zu bearbeitende Sprite und Hinweise auf verfügbare Kommandos, im Arbeitsfeld wird das Sprite erstellt. Die Zahlen im Rahmen des Arbeitsfeldes ergeben sich aus dem Format der Sprites im Speicher.

## Das Menü

Das Menü (=Command List) wird mit »Space« ins Anzeigefeld gerufen.
*0 bis 7*
Es werden bis zu sieben Sprites gleichzeitig im Spritefeld dargestellt. Die Tasten 0 bis 7 fungieren als On/Off-Schalter.
*I*
Das jeweils zuletzt angeschaltete Sprite wird nacheinander in Y-, XY- und X-Richtung vergrößert.
*M*
Schaltet für das zuletzt bearbeitete Sprite den Multicolormodus ein.
*C*
Verzweigt in die Routine für die Farbwahl.
*R*
Reproduktion des zuletzt bearbeiteten Sprites ins Arbeitsfeld. Kann mit beliebiger Taste abgebrochen werden.
*F1*
Schaltet in den Arbeitsmodus (siehe unten).
*F3*
Ändert die Hintergrundfarbe.
*F7*
Schiebt das Sprite im Speicher um eine Zeile tiefer. Es kann passieren, daß Punkte aus dem Sprite davor ins Bild verschoben werden.
*F8*
Wie F7, schiebt das Sprite hoch.
*H*
Verzweigt in die Handle-Routine, mit der Sprites auf dem Bildschirm verschoben werden können.
*$*
Zeigt das Diskettendirectory an. Kann mit F 1 abgebrochen werden.
*@*
Ermöglicht Disk-Befehle zu senden, beziehungsweise nur mit RETURN den Fehlerkanal abzufragen.
*S*
Gibt die Dezimalwerte des zuletzt bearbeiteten Sprite im Anzeigefeld aus. Am Kopf der Tabelle steht die Anfangsadresse des Sprites im Speicher (dezimal).
*P*
Ausgabe auf Drucker. Zusätzliche Angabe eines 20 Zeichen langen Namens möglich. Geräteadresse = 4
*F*
Verzweigt ins Floppymenü. Dieser Programmteil erklärt sich weitgehend selbst. Beim ersten Einsprung in die Routine sollte ein Name definiert werden, sonstwird das File (sequentiell) unter dem Namen »Data« geSAVEd. Später kann die Position »Filename« mit RETURN übergangen werden und der alte Name wird verwendet. Unter einem Namen können beliebig viele Sprites abgelegt werden. Geräteadresse = 8
*D*
Alle acht Sprites werden in Datazeilen umgewandelt.
*K*
Das Programm wird gelöscht. Datazeilen bleiben bestehen und können an andere Programme angehängt werden. Geduld, die Sache dauert!

## Der Arbeitsmodus

<b>’*’ beziehungsweise ’@’</b>
Diese Tasten zeichnen Punkte (Linien) in horizontaler beziehungsweise vertikaler Richtung.
<b>’=’ beziehungsweise ’;’</b>
Wie oben, nur werden Punkte gelöscht. Die Belegung dieser Tasten ist an die Cursortasten angelehnt. Gleichzeitig mit SHIFT ist die Bewegungsrichtung umgekehrt.
Außerdem definiert: RETURN, HOME, CLEAR, F1

Aus fast jeder Routine kann mit F1 ausgestiegen werden. Auf Fragen wird mit Y(es) oder RETURN und N(o) oder beliebiger Taste geantwortet. NichtdefinierteTasten bewirken nichts. Fehleingaben sind abgefangen.

Man sollte das Programm nicht mit STOP/RESTORE beenden. Der Bildschirminhalt ist sonst nicht mehr lesbar. Nach QUIT oder STOP kann allerdings problemlos ohne Verlust der Sprites neu gestartet werden.

Für »Tippfaule«: Sämtliche Remzeilen sind optional, da sie nicht angesprungen werden, und dienen nur der Orientierung im Listing. Man kann sie also auch später einfügen, oder ganz weglassen.

Und wenn’s dann endlich drin ist (wunde Finger gehören nunmal dazu): Viel Spaß beim Malen!

## Erweiterungen

1)	Der Bildschirm ist nach 33792 verlegt, um für acht Sprites Platz zu schaffen. Dementsprechend liegen die Sprites auch in Block 3, nämlich ab Adresse 32768.
2)	Die Tastenbelegung der »Work«-Routine ist der Verwendung von Cursortasten angeglichen. Links vertikale, rechts horizontale Bewegungen.
3)	Es stehen drei Routinen für Diskettenverwaltung zur Verfügung:
a)	Anzeige des Directory
b)	Senden von Disk-Commands
c)	Floppy Controller
4)	Die »Floppy«-Routine ist so gestaltet, daß ein relativ bequemes Umsortieren der Sprites auf Diskette von einem File ins andere möglich wird.

Das heißt: Viele Stellen, an denen bei Irrtum noch eine »Umkehr« möglich ist; immer wieder wird gezeigt, was gerade passiert. Bei Eingabe des Filenamens kann jetzt mit DELETE korrigiert werden. Bei fehlender Namensangabe heißt das File »Data« — kein unlöschbares »,« mehr.

Wenn man in letzter Minute noch aussteigt und doch kein einziges Sprite abgespeichert, entsteht nun kein Geisterfile mehr, das zwar einen Eintrag im Directory hat, aber keine Daten enthält und das Programm bei nächster Gelegenheit böswillig zum Absturz bringt.

5)	Diverse Kleinigkeiten.

(A. Kölbach/rg)

# Screen Change

> Ärgern Sie sich beim Erstellen umfangreicher Programme auch manchmal darüber, daß Sie nicht mehr genau wissen, wie ein bestimmter Programmteil aussieht? Dann werden Sie neu listen und der zuletzt bearbeitete Programmteil ist verschwunden. Die entsprechende Stelle muß wieder gesucht werden. Bis dahin hat man die zuerst gesuchte Stelle vielleicht schon wieder vergessen.

Die Routine »Screen Change« erweitert den Basicbefehlssatz dahingehend, daß der aktuelle Bildschirminhalt im RAM zwischengespeichert und bei Bedarf wieder zurückgeholt werden kann. So können bis zu vier Seiten abgelegt werden. Man hat also die Möglichkeit Notizen, oder andere Informationen, wie beispielsweise Listings oder Low-Resolution-Grafik, zu konservieren. Gleichermaßen sind Sie in der Lage, im Programmablauf eine Text- oder Grafikseite darzustellen, während eine weitere unsichtbar aufgebaut wird.

Nachdem der Basic-Lader gestartet wurde, ist das Programm automatisch initialisiert (SYS 49152). Durch gleichzeitiges Drücken der Tasten »CTRL« und »COMMODORE C« und einer f-Taste werden nun Video-RAM und entsprechender Seitenspeicher vertauscht. Normalerweise wird anschließend lediglich »Müll« auf dem Bildschirm zu sehen sein, da die betreffende Seite noch nicht beschrieben war. Drücken Sie nun aber die gleiche Kombination, oder einfach nur die Tasten »CTRL-und f-Taste« dann erscheint sofort der ursprüngliche Inhalt. Haben Sie die erste Kombination eingegeben wurden die Speicher wieder vertauscht, das heißt der Müll wurde zurückgeschrieben. Hingegen bleibt bei der zweiten Kombination der Seitenspeicher mit der gerade eingelesenen Information gefüllt. Dies läßt sich leicht überprüfen, indem der Bildschirm gelöscht wird, um daraufhin die zweite Kombination noch einmal einzugeben. Es zeigt sich sofort, daß der Inhalt unverändert geblieben ist. Dies istsolange der Fall bis die betreffende Seite mit Tastenkombination 1 »CTRL + C« eine andere Bildschirmseite aufnimmt. Das oben gesagte gilt für alle vier Funktionstasten.

Natürlich versagt diese Methode, wenn die gewünschte Funktion vom Basicprogramm her aufgerufen werden soll. Dazu wird der neue Befehl »SEITEx.m« eingeführt. Der Index x gibt dabei die Seitennummer und m den Modus an. Die Seitennummer darf dabei zwischen 0 und 3 liegen.m kann T oder H sein.
T bedeutet: Seiten tauschen; entsprechend Tastenkombination 1
H bedeutet: Seite holen; entsprechend Tastenkombination 2

Damit hat man die Möglichkeit Zwischenergebnisse abzulegen, eine Bedienungsanleitung einzublenden, um dann wieder in die normale Textseite zurückzukehren, Bildschirmmasken einzublenden und vieles mehr. Der interessierte Anwender wird sicher eine Fülle weiterer Einsatzmöglichkeiten entdecken. Doch nun einige Worte zum Programm selbst. Natürlich ist es auch möglich die Seiten über das Befehlswort im Basicdirektmodus aufzurufen. Dies hat jedoch den Nachteil, daß der Befehlstext sowie die READY-Meldung mit übertragen werden. Um dies zu umgehen wird die Tastaturabfrage über eine neue Routine geleitet, die die f-Tasten decodiert.

Der Befehl »SEITE« wird erkannt indem die Interpreterschleife meine Routine durchläuft. Dies kann im einzelnen dem Assemblerlisting entnommen werden.

Interessant ist in diesem Zusammenhang, daß die zusätzlich benötigten 4 KByte Video-RAM den freien Basicspeicherbereich nicht einschränken, da sie im normalerweise nicht nutzbaren Bereich hinter dem Interpreter liegen.

Zusätzlich habe ich eine Routine entwickelt, die über eine Befehlserweiterung das Laden und Speichern der Seiten auf Diskette zuläßt.

Über die normale Anwendung hinaus mögen folgende Anmerkungen von Nutzen sein:

lm CTRL-Modus wird in die rechte obere Bildecke die gewählte Seitennummer eingeblendet. Sollte dies als störend empfunden werden, so kann durch Ändern der letzten Zahl der letzten DATA-Zeile in eine beliebige andere die Einblendung ausgeschaltet werden.

Das Zurückschreiben der »32« führt wieder zur Standardausgabe. Über die Adresse 49313 (POKE 49313,F) läßt sich die Zeichenfarbe F der einzublendenden Seiten ändern. Gekoppelt mit dem Befehl SEITE ließen sich die verschiedenen Seiten in jeweils typischen Farben darstellen. Soll von vornherein eine bestimmte Zeichenfarbe eingestellt werden, so ist die »14« in der DATA-Zeile 79 dahingehend zu ändern.

Durch Anpassung der Zieladressen-Tabelle lassen sich die Seiten in jeden möglichen Speicherbereich legen. Dabei muß lediglich beachtet werden, ob eventuell das Basic-RAM oder ein darin liegendes Programm geschützt werden muß! Auf diese Weise lassen sich natürlich auch weit mehr Seiten anlegen.

Soll nun im Rahmen eines Basicprogramms eine Seite beschrieben werden, so kann dies wie gewohnt über POKEs erfolgen. Zu berücksichtigen sind lediglich die Startadressen der vier Seitenspeicher. Will man normalerweise den Bildschirm über POKE ansprechen, dann geht man von Adresse 1024 aus. Diese ersetzt man nun gegen die unten angegebenen und die gewählte Seite läßt sich unsichtbar beschreiben um bei Bedarf eingeblendet zu werden. Das Farb-RAM muß hier nicht neu beschrieben werden. Im folgenden nun die benötigten Adressen:
Seite 0: 40960 bis 41959
Seite 1 : 41984 bis 42983
Seite 2 : 43008 bis 44007
Seite 3 : 44032 bis 45031

(Harald Soyka/rg)














































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































































