================================================================
CS230 - Distribuirani sistemi
Projektni zadatak - Tema 1
Distribuirani sistem za deljenje datoteka
P2P arhitektura sa centralizovanim indeksiranjem
================================================================

OPIS SISTEMA
------------
Sistem se sastoji od dva programa:
  - server.py  : Centralni indeks server
  - peer.py    : Peer (korisnik mreze)

Svaki peer moze da deli fajlove i preuzima fajlove od drugih
peer-ova. Centralni server SAMO cuva indeks (ko ima koji fajl).
Prenos fajlova ide DIREKTNO izmedju peer-ova.


POKRETANJE
----------
Potrebno je otvoriti 3 Command Prompt prozora.

Korak 1 - Pokreni centralni server (Terminal 1):
    python server.py

Korak 2 - Pokreni prvog peer-a (Terminal 2):
    python peer.py 6001 peer1_fajlovi

Korak 3 - Pokreni drugog peer-a (Terminal 3):
    python peer.py 6002 peer2_fajlovi

Napomena: U folder peer1_fajlovi staviti fajlove koje peer1 deli.
          Folder peer2_fajlovi moze biti prazan na pocetku.


KOMANDE (unutar peer programa)
------------------------------
  1 - Pretrazi fajlove u mrezi
  2 - Prikazi sve fajlove u mrezi
  3 - Preuzmi fajl od drugog peer-a
  4 - Ponovo registruj svoje fajlove
  5 - Izlaz


STRUKTURA PROJEKTA
------------------
p2p_projekat/
├── server.py          <- Centralni indeks server
├── peer.py            <- Peer program
├── README.txt         <- Ovo uputstvo
├── peer1_fajlovi/     <- Folder peer-a 1
└── peer2_fajlovi/     <- Folder peer-a 2


TEHNICKE INFORMACIJE
--------------------
  Jezik         : Python 3
  Protokol      : TCP (socket)
  Format poruka : JSON
  Server port   : 5000
  Peer portovi  : 6001, 6002 (mogu se menjati)
  Visenitnost   : Da (threading)

================================================================