{**************************************************************************}
{                                                                          }
{ PROGRAMM         : lib.pas                                               }
{                                                                          }
{ AUTOR            : wolfgang schroeder                                    }
{                                                                          }
{ ERSTELLT AM      : 20.07.86                                              }
{                                                                          }
{ LETZTE KORREKTUR :                                                       }
{                                                                          }
{ COMPILER         : turbo pascal 3.0                                      }
{                                                                          }
{ HARDWARE         : commodore c128 oder anderer cp/m-rechner              }
{                                                                          }
{ FUNKTION         : erstellt eine uebersicht der in pascal-sourcen        }
{                    enthaltenen functions und procedures                  }
{                                                                          }
{**************************************************************************}

{$u+}

type
   fcb_type = record
                drive : byte;
                fname : array[0..10] of char;
                extend: byte;
              end;
   file_string = string[14];
   dma_type = array[0..127] of char;
   line = string[132];

const
   aufruf = 'Aufruf: lib infile [outfile]';
   blanks = '                                                              ';
   under_line = '-----------------------------------------';

var
   infile, outfile: file_string;
   workfile: array[1..32] of file_string;
   in_var, out_var: text;
   out_info: boolean;
   answer: char;
   fcb   : fcb_type absolute $5c;
   dma   : dma_type;
   work_ind,index,result : integer;
   in_line,out_line: line;
   drive: string[2];

{**************************************************************************}
{                                                                          }
{ FUNCTION : tab (spalte:integer): string[80];                             }
{                                                                          }
{ FUNKTION : simuliert den fehlenden tabulator-befehl                      }
{                                                                          }
{ EINGABE  : spalte: anzahl der spalten, um die cursor gewegt wird         }
{                                                                          }
{ AUSGABE  : tab: blank line mit der laenge spalte                         }
{                                                                          }
{**************************************************************************}

function tab(spalte:integer): line;
const
  bl_line = '                                                          ';

var
  print: string[80];

begin
   if spalte>length(bl_line) then
      tab:= '*'
   else
      tab:= copy(bl_line,1,spalte);
end; {tab}

{**************************************************************************}
{                                                                          }
{ FUNCTION : check_input (var file1,file2:string[14]): boolean             }
{                                                                          }
{ FUNKTION : Holt eventl. vorhandene beim Programmaufruf angegebene        }
{            Parameter und max. 2 Filenamen ab                             }
{                                                                          }
{ EINGABE  : keine, da Parameterversorgung ueber ParamCount und ParamStr   }
{                                                                          }
{ AUSGABE  : false -> falsche Parametereingabe                             }
{            true  -> Parametereingabe ok                                  }
{                     infile: string[14] -> 1. filename                    }
{                     outfile:string[14] -> 2. filename                    }
{                                                                          }
{**************************************************************************}

function CHECK_INPUT (var file1,file2:file_string): boolean;

begin
   check_input:= false;
   file1:= '';
   file2:= '';

   case ParamCount of
   1:    begin
            file1:= ParamStr(1);
            check_input:= true
         end;
   2:    begin
            file1:= ParamStr(1);
            file2:= ParamStr(2);
            check_input:= true;
         end;
    else writeln (aufruf);
    end; {case}

end; {check_input}

{**************************************************************************}
{                                                                          }
{ FUNCTION : open_output (outfile:string[14]): boolean;                    }
{                                                                          }
{ FUNKTION : oeffnet ausgabedatei fuer textausgabe                         }
{                                                                          }
{ EINGABE  : outfile: name der ausgabedatei                                }
{            append : true  -> ausgabe an bestehende datei anfuegen        }
{                     false -> ausgabe auf neue datei                      }
{                                                                          }
{ AUSGABE  : true  -> ausgabedatei geoeffnet                               }
{            false -> ausgabedatei nicht geoeffnet                         }
{                                                                          }
{**************************************************************************}

function OPEN_OUTPUT(outfile:file_string): boolean;

begin
  open_output:= false;
  assign (out_var,outfile);
  {$i-} reset (out_var) {$i+};
  if IOresult = 0 then begin
     close (out_var);
     gotoxy(3,6);
     write ('Ausgabedatei existiert bereits! Ueberschreiben [j/n] ? ');
     readln (answer);
     if answer = 'j' then begin
        erase (out_var);
        rewrite (out_var);
        open_output:= true;
     end;
  end
  else begin
    rewrite (out_var);
    open_output:= true;
  end;
end; {open_output}

{**************************************************************************}
{                                                                          }
{ FUNCTION : fname_to_fcb (fname: string[14]): boolean                     }
{                                                                          }
{ FUNKTION : kopiert den angegebenen filename unter beruecksichtigung      }
{            der fcb-syntax in den standart fcb bei $5c. der filename      }
{            darf auch die jokerzeichen '?' und '*' enthalten.             }
{                                                                          }
{ EINGABE  : fname : in den fcb zu kopierenden filenamen                   }
{                                                                          }
{ AUSGABE  : true  -> filename ok                                          }
{                     fcb enthaelt konvertierten filenamen                 }
{            false -> syntaxfehler im filenamen                            }
{                                                                          }
{**************************************************************************}

function FNAME_TO_FCB (fname: file_string): boolean;

var
   ind_start,index1, index2: integer;

begin
   fname_to_fcb:= true;
   index2:= 0;

   if fname[2]=':'  then begin
      fcb.drive:= ord(fname[1])-64;
      ind_start:= 3;
      end
   else begin
      fcb.drive:= 0;
      ind_start:= 1;
   end;

   for index1:= ind_start to length(fname) do begin
      case fname[index1] of
      'A'..'Z',
      '0'..'9': begin
                fcb.fname[index2]:= fname[index1];
                index2:= succ(index2);
                end;
      '.':      begin
                if index2<8 then
                   for index2:= index2 to 8 do
                      fcb.fname[index2]:= ' ';
                end;
      '?':      begin
                fcb.fname[index2]:= '?';
                index2:= succ(index2);
                end;
      '*':      begin
                if index2<8 then
                   for index2:= index2 to 8 do
                      fcb.fname[index2]:= '?'
                else
                   for index2:= index2 to 10 do
                      fcb.fname[index2]:= '?';
                end;
      else      begin
                writeln ('falscher dateinamen fuer inputfile');
                fname_to_fcb:= false;
                end;
      end; {case}
      fcb.extend:= 0;
   end;

end; {fcb_to_fname}

{**************************************************************************}
{                                                                          }
{ PROCEDURE: dma_to_fname (var filename:string[14];                        }
{                          dma: array[0..127] of char;                     }
{                          dma_pos: integer);                              }
{                                                                          }
{ FUNKTION : setzt einen directory eintrag im 'dma' in einen fuer          }
{            dateizugriffe gueltigen filename um                           }
{                                                                          }
{ EINGABE  : dma    : von einer bdos-funktion ausgefuellter dma-bereich    }
{            dma_pos: startposition im dma fuer den fileeintrag            }
{                                                                          }
{ AUSGABE  : filename: konvertiert fileeintrag fuer dateizugriffe          }
{                                                                          }
{**************************************************************************}

procedure DMA_TO_FNAME (var filename: file_string;
                        dma: dma_type;
                        dma_pos: integer);

var
  start: integer;

begin
   filename:= copy (dma,dma_pos+2,8); {dateiname holen}
   start:= pos (' ',filename);        {blanks entfernen}
   if start>0 then
      delete (filename,start,5);
   filename:= concat (filename,'.',copy (dma,dma_pos+10,3) ); {ext. dazu}
end; {dma_to_fname}


{**************************************************************************}
{                                                                          }
{ FUNCTION : search_header (var in_file: text;                             }
{                           var in_line: string[132]): boolean;            }
{                                                                          }
{ FUNKTION : durchsucht die angegebene textdatei nach functions- und       }
{            procedure-headern                                             }
{                                                                          }
{ EINGABE  : in_file: dateibeschreibung der eingabedatei                   }
{                                                                          }
{ AUSGABE  : true  -> header gefunden                                      }
{                     in_line: zeile mit headerbeginn                      }
{            false -> keinen header gefunden                               }
{                                                                          }
{**************************************************************************}

function SEARCH_HEADER (var in_file: text;
                        var in_line:line): boolean;

begin
  search_header:= false;
  while not eof(in_file) do begin
     readln (in_file,in_line);
     if ((pos('{ FUNCTION :',in_line)=1) or
         (pos('{ PROCEDURE:',in_line)=1)) then begin
         search_header:= true;
         exit;
     end;
  end; {while}

end; {search_header}

{**************************************************************************}
{                                                                          }
{ PROCEDURE: extract_info (var in_file,out_file:text; out_info:boolean;    }
{                          in_line:string[132]; workfile:string[14]);      }
{                                                                          }
{ FUNKTION : extrahiert ausgabeinformation ueber die uebergebene function  }
{            oder procedure                                                }
{                                                                          }
{ EINGABE  : in_file : dateibeschreibung der eingabedatei                  }
{            out_file: dateibeschreibung der ausgabedatei                  }
{            out_info: ausgabe auf datei(true) oder bildschirm(false);     }
{            in_line : zeile mit function- bzw. procedurenamen             }
{            workfile: name der eingabedatei                               }
{                                                                          }
{ AUSGABE  : extrahierte information                                       }
{                                                                          }
{**************************************************************************}

procedure EXTRACT_INFO (var in_file,out_file:text; out_info:boolean;
                        var in_line: line;workfile:file_string);

type
   func_type = array[0..9] of string[80];
var
   out_line: string[80];
   func_proc: char;
   fp_name: string[20];
   func_desc: func_type;
   index: integer;
   loop, blank_pos:integer;


{**************************************************************************}
{                                                                          }
{ FUNCTION : split (var in_line: func_type; max_line:integer;              }
{                   var index: integer; max_length: integer): line         }
{                                                                          }
{ FUNKTION : reformatiert eine textzeile auf eine andere laenge            }
{                                                                          }
{ EINGABE  : in_line = array[] of string[]                                 }
{                      original text (wird veraendert!)                    }
{            max_line = anzahl der zu reformatierende zeilen in in_line    }
{            max_length = zeilenlaenge des neuen textes                    }
{                                                                          }
{ AUSGABE  : split = string[]   reformatierte zeile                        }
{            index = zeilennummer der zuletzt reformatierten zeile         }
{                                                                          }
{**************************************************************************}

function split(var in_line: func_type; max_line:integer;
               var index:integer; max_length:integer): line;

var temp1,temp2: string[80];
    bl_pos:integer;

begin

temp2:='';

repeat
   bl_pos:= pos(' ',in_line[index]);
   if bl_pos=0 then
      temp1:= in_line[index]+' '
   else
      temp1:= copy(in_line[index],1,bl_pos);
   if length(temp1+temp2)>max_length then begin
      split:=temp2;
      exit
   end
   else begin
      temp2:= temp2+temp1;
      delete (in_line[index],1,bl_pos);
      if bl_pos=0 then
         index:= succ(index);
   end;
until (index>max_line);
split:= temp2;
end;  {split}

begin  { of extract_info}
   if pos('{ FUNCTION :',in_line)=1 then
      func_proc:= 'F'
   else
      func_proc:= 'P';

   index:= pos('(',in_line);
   if ((index=0) or (index>34)) then
      fp_name:= copy(in_line,14,20)
   else
      fp_name:= copy(in_line,14,index-14);

   repeat
      readln (in_file,in_line);
   until (pos('{ FUNKTION :',in_line)=1);

   delete (in_line,1,12);   {kommentarzeichen entfernen}
   index:= -1;

   repeat
      delete (in_line,1,1);
      while in_line[1]=' ' do   {blanks am zeilenbeginn entfernen}
         delete (in_line,1,1);

      if in_line<>'}' then begin
         delete (in_line,length(in_line),1);
         while in_line[length(in_line)]=' ' do
            delete (in_line,length(in_line),1);

         index:= succ(index);
         func_desc[index]:= in_line;

         readln (in_file,in_line);
      end;
   until ((in_line='}') or (index=9));

   loop:= 0;

   repeat
      out_line:=' '+func_proc+' !'+fp_name;
      out_line:= copy(out_line+blanks,1,23);
      out_line:= out_line+'!'+split(func_desc,index,loop,40);
      out_line:= copy(out_line+blanks,1,65);
      out_line:= out_line+'!'+workfile;
      if out_info then
         writeln (out_var,out_line)
      else
         writeln (out_line);
      fp_name:= '';
      func_proc:= ' ';
      workfile:= '';
   until (loop>index);

end; {extract_info}

{*********************}
{** hauptprogramm   **}
{*********************}

begin
   clrscr;
   if CHECK_INPUT(infile,outfile) then begin
      if length(outfile) <> 0 then begin
         gotoxy (3,3);
         Write ('Ausgabedatei: ',outfile);
         if not(OPEN_OUTPUT(outfile)) then
            exit
         else
            out_info:= true;
            gotoxy (3,9);
            write ('Datei: ',outfile,' wird geschrieben');
      end
      else
         out_info:= false;
      if infile[2] = ':' then
         drive:= copy (infile,1,2)
      else
         drive:= '';
      if FNAME_TO_FCB(infile) then begin
         work_ind:= 1;
         bdos (26,addr(dma));    {set dma address}
         result:= bdos (17,addr(fcb));  {search for first}
         while ((result<>255) and (work_ind<33)) do begin
            index:= result shl 5;  {startadresse des directory entry}
            DMA_TO_FNAME(workfile[work_ind],dma,index);
            workfile[work_ind]:= drive+workfile[work_ind]; {laufwerk dazu}
            work_ind:= succ(work_ind);
            result:= bdos (18,addr(fcb)); {search for next}
        end; {while}
        if result<>255 then begin
           writeln ('es koennen nicht mehr als 32 files bearbeitet werden!');
           exit;
        end;
        work_ind:= work_ind-1;
        if work_ind=0 then begin
           writeln ('kein inputfile gefunden!');
           exit;
        end;
        if out_info then begin
           writeln (out_var,'TYP! NAME',tab(14),'! FUNCTION',tab(32),'! MODUL');
           writeln (out_var,'---+',copy(under_line,1,19),'+',
                 copy(under_line,1,41),'+------');
        end
        else begin
           writeln ('TYP! NAME',tab(14),'! FUNCTION',tab(32),'! MODUL');
           writeln ('---+',copy(under_line,1,19),'+',
                 copy(under_line,1,41),'+------');
        end;
        for index:= 1 to work_ind do begin
           assign (in_var,workfile[index]);
           reset (in_var);
           while SEARCH_HEADER (in_var,in_line) do begin
              EXTRACT_INFO(in_var,out_var,out_info,in_line,workfile[index]);
              if out_info then
                 writeln (out_var,tab(3),'!',tab(19),'!',tab(41),'!')
              else
                 writeln (tab(3),'!',tab(19),'!',tab(41),'!');
           end;
           close (in_var);
         end;
      end;
      if out_info then
         close (out_var);
   end;
end.
