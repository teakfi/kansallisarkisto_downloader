Lataa kokonaisia Kansallisarkiston digitaaliarkiston (digi.narc.fi) arkistoyksikköjä pdf-muodossa.

Ohjelma lataa koneelle kunkin digitoidun jakson kuvan (yleensä sivu tai aukeama) ja yhdistää ne pdf-tiedostoksi tai yksittäisen pdf-tiedoston maksimikoon ylittyessä useammaksi tiedostoksi.

Yhdistämisen jälkeen kuvat poistetaan kovalevyltä.

Käyttö: narchaku.py [-h] [-m MAXSIZE] [-f] URL

-h kertoo kuinka ohjelmaa käytetään

-m MAXSIZE määrittelee pdf-tiedoston maksimikoon, 0 = ääretön ja on oletus

-f tiedostolista useamman yksikön lataamiseen yksittäisen URLin sijasta

URL  arkistoyksikön numero tai kokonainen url muotoa http://digi.narc.fi/digi/slistaus.ka?ay=numero
tiedostolista on tekstitiedosto, jossa kullekkin riville laitetaan joko arkistointiyksikön numero tai url taikka generaattori, joka tuottaa numerolistan. Generaattori voi olla muotoa [aloitus,lopetus,askel], joka generoi listan numeroita joka alkaa aloituksesta ja päättyy lopetukseen (ei mukana) käyttäen annettua askelkokoa. Toinen muoto on aloitus-lopetus, tämä generoi listan aloituksesta lopetukseen (mukana) askelkoolla 1.
