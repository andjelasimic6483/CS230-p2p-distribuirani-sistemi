import socket
import threading
import json
import os
import sys



SERVER_IP   = "127.0.0.1"
SERVER_PORT = 5000
CHUNK_SIZE  = 4096


class Peer:
    def __init__(self, peer_port, folder_sa_fajlovima):
        self.peer_port = peer_port
        self.folder = folder_sa_fajlovima
        self.moja_ip = "127.0.0.1"

        
        os.makedirs(self.folder, exist_ok=True)

       
        self.file_server_thread = threading.Thread(target=self._pokreni_file_server)
        self.file_server_thread.daemon = True
        self.file_server_thread.start()

   
    def _posalji_serveru(self, poruka: dict) -> dict:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_IP, SERVER_PORT))
            s.send(json.dumps(poruka).encode("utf-8"))
            odgovor = s.recv(65536)
            s.close()
            return json.loads(odgovor.decode("utf-8"))
        except ConnectionRefusedError:
            print("[GRESKA] Ne mogu da se povezem sa centralnim serverom!")
            print(f"         Proveri da li server radi na {SERVER_IP}:{SERVER_PORT}")
            return {"status": "greska"}
        except Exception as e:
            print(f"[GRESKA] Problem u komunikaciji sa serverom: {e}")
            return {"status": "greska"}

    def registruj_se(self):
        moji_fajlovi = os.listdir(self.folder)

        if not moji_fajlovi:
            print(f"[INFO] Folder '{self.folder}' je prazan - registrujem se bez fajlova")
        else:
            print(f"[INFO] Registrujem fajlove: {moji_fajlovi}")

        poruka = {
            "komanda": "registracija",
            "port": self.peer_port,
            "fajlovi": moji_fajlovi
        }
        odgovor = self._posalji_serveru(poruka)

        if odgovor.get("status") == "ok":
            print(f"[OK] Registracija uspesna: {odgovor.get('poruka')}")
        else:
            print(f"[GRESKA] Registracija neuspesna: {odgovor}")

    def odjavi_se(self):
        poruka = {"komanda": "odjava", "port": self.peer_port}
        self._posalji_serveru(poruka)
        print("[INFO] Odjavljen sa servera.")

    def pretrazi(self, naziv):
        poruka = {"komanda": "pretraga", "naziv": naziv}
        odgovor = self._posalji_serveru(poruka)

        if odgovor.get("status") == "ok":
            return odgovor.get("rezultati", {})
        else:
            return {}

    def lista_svih(self):
        poruka = {"komanda": "lista"}
        odgovor = self._posalji_serveru(poruka)
        return odgovor.get("index", {})

    

    def _pokreni_file_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("0.0.0.0", self.peer_port))
            s.listen(5)
            print(f"[FILE SERVER] Slusam zahteve za fajlove na portu {self.peer_port}")
            while True:
                conn, addr = s.accept()
                t = threading.Thread(target=self._posalji_fajl, args=(conn, addr))
                t.daemon = True
                t.start()
        except OSError as e:
            print(f"[GRESKA] Ne mogu da pokrenem file server na portu {self.peer_port}: {e}")

    def _posalji_fajl(self, conn, addr):
        try:
            ime_fajla = conn.recv(1024).decode("utf-8").strip()
            putanja = os.path.join(self.folder, ime_fajla)

            if not os.path.exists(putanja):
                conn.send(b"GRESKA: fajl ne postoji")
                print(f"[FILE SERVER] Zahtev za nepostojeci fajl: {ime_fajla}")
                conn.close()
                return

            velicina = os.path.getsize(putanja)
            conn.send(f"OK:{velicina}".encode("utf-8"))

            ack = conn.recv(8)
            if ack != b"SPREMAN":
                conn.close()
                return

            print(f"[FILE SERVER] Saljem '{ime_fajla}' ({velicina} bajtova) peeru {addr}")
            poslato = 0
            with open(putanja, "rb") as f:
                while True:
                    blok = f.read(CHUNK_SIZE)
                    if not blok:
                        break
                    conn.send(blok)
                    poslato += len(blok)

            print(f"[FILE SERVER] Slanje zavrseno: {poslato} bajtova")
        except Exception as e:
            print(f"[FILE SERVER] Greska pri slanju: {e}")
        finally:
            conn.close()

    def preuzmi_fajl(self, ime_fajla, peer_ip, peer_port):
        print(f"[PREUZIMANJE] Povezujem se sa peer-om {peer_ip}:{peer_port}...")
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((peer_ip, int(peer_port)))

            s.send(ime_fajla.encode("utf-8"))

            odgovor = s.recv(64).decode("utf-8")
            if odgovor.startswith("GRESKA"):
                print(f"[GRESKA] {odgovor}")
                s.close()
                return False

            
            velicina = int(odgovor.split(":")[1])
            print(f"[PREUZIMANJE] Velicina fajla: {velicina} bajtova")

            s.send(b"SPREMAN")

            putanja = os.path.join(self.folder, ime_fajla)
            primljeno = 0
            with open(putanja, "wb") as f:
                while primljeno < velicina:
                    blok = s.recv(CHUNK_SIZE)
                    if not blok:
                        break
                    f.write(blok)
                    primljeno += len(blok)

            s.close()

            if primljeno == velicina:
                print(f"[OK] Fajl '{ime_fajla}' uspesno preuzet ({primljeno} bajtova)")
                return True
            else:
                print(f"[GRESKA] Preuzimanje nepotpuno: {primljeno}/{velicina} bajtova")
                return False

        except Exception as e:
            print(f"[GRESKA] Problem pri preuzimanju: {e}")
            return False




def main():
    if len(sys.argv) < 3:
        print("Upotreba: python peer.py <moj_port> <moj_folder>")
        print("Primer:   python peer.py 6001 fajlovi_peer1")
        sys.exit(1)

    moj_port = int(sys.argv[1])
    moj_folder = sys.argv[2]

    peer = Peer(moj_port, moj_folder)
    peer.registruj_se()

    print("\n" + "=" * 50)
    print("  CS230 - P2P Peer")
    print(f"  Port: {moj_port}  |  Folder: {moj_folder}")
    print("=" * 50)

    while True:
        print("\nKomande:")
        print("  1 - Pretrazi fajlove")
        print("  2 - Prikazi sve fajlove u mrezi")
        print("  3 - Preuzmi fajl")
        print("  4 - Ponovo registruj svoje fajlove")
        print("  5 - Izlaz")
        print("-" * 30)

        izbor = input("Unesi komandu: ").strip()

        if izbor == "1":
            naziv = input("Unesi naziv fajla za pretragu: ").strip()
            rezultati = peer.pretrazi(naziv)
            if rezultati:
                print(f"\nPronadjeni fajlovi ({len(rezultati)}):")
                for fajl, peer_lista in rezultati.items():
                    print(f"  {fajl}")
                    for p in peer_lista:
                        print(f"    -> dostupan kod peer-a {p[0]}:{p[1]}")
            else:
                print("Nije pronadjen nijedan fajl.")

        elif izbor == "2":
            indeks = peer.lista_svih()
            if indeks:
                print(f"\nSvi fajlovi u mrezi ({len(indeks)}):")
                for fajl, peer_lista in indeks.items():
                    lokacije = ", ".join([f"{p[0]}:{p[1]}" for p in peer_lista])
                    print(f"  {fajl:30s} <- {lokacije}")
            else:
                print("Mreza je prazna.")

        elif izbor == "3":
            naziv = input("Unesi tacan naziv fajla: ").strip()
            rezultati = peer.pretrazi(naziv)

            
            if naziv not in rezultati:
                print(f"Fajl '{naziv}' nije pronadjen u mrezi.")
                continue

            peer_lista = rezultati[naziv]
            
            izvor = None
            for p in peer_lista:
                if int(p[1]) != moj_port:
                    izvor = p
                    break

            if not izvor:
                print("Fajl je dostupan samo kod tebe.")
                continue

            print(f"Preuzimam od peer-a {izvor[0]}:{izvor[1]}...")
            uspeh = peer.preuzmi_fajl(naziv, izvor[0], izvor[1])

            
            if uspeh:
                peer.registruj_se()
                print(f"Fajl dodat u tvoj folder i prijavljen serveru.")

        elif izbor == "4":
            peer.registruj_se()

        elif izbor == "5":
            peer.odjavi_se()
            print("Dovidjenja!")
            break

        else:
            print("Nepoznata komanda.")


if __name__ == "__main__":
    main()