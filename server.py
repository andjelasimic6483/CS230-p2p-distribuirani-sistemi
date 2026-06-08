

import socket
import threading
import json


index = {}
index_lock = threading.Lock()


def handle_peer(conn, addr):
    
    print(f"[SERVER] Peer povezan: {addr}")
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            try:
                poruka = json.loads(data.decode("utf-8"))
            except json.JSONDecodeError:
                odgovor = {"status": "greska", "poruka": "Neispravan format poruke"}
                conn.send(json.dumps(odgovor).encode("utf-8"))
                continue

            komanda = poruka.get("komanda")

            if komanda == "registracija":
                peer_port = poruka.get("port")
                fajlovi = poruka.get("fajlovi", [])
                peer_ip = addr[0]

                with index_lock:
                    for fajl in fajlovi:
                        if fajl not in index:
                            index[fajl] = []

                        if (peer_ip, peer_port) not in index[fajl]:
                            index[fajl].append((peer_ip, peer_port))

                print(f"[SERVER] Registrovan peer {peer_ip}:{peer_port} sa fajlovima: {fajlovi}")
                odgovor = {"status": "ok", "poruka": f"Registrovano {len(fajlovi)} fajl(ova)"}
                conn.send(json.dumps(odgovor).encode("utf-8"))

            elif komanda == "pretraga":
                naziv = poruka.get("naziv", "")

                with index_lock:
                    rezultati = {}
                    for fajl, peer_lista in index.items():
                        if naziv.lower() in fajl.lower():
                            rezultati[fajl] = peer_lista

                if rezultati:
                    print(f"[SERVER] Pretraga '{naziv}' -> pronadjeno {len(rezultati)} fajl(ova)")
                    odgovor = {"status": "ok", "rezultati": rezultati}
                else:
                    print(f"[SERVER] Pretraga '{naziv}' -> nije pronadjeno")
                    odgovor = {"status": "nije_pronadjeno", "rezultati": {}}

                conn.send(json.dumps(odgovor).encode("utf-8"))

            elif komanda == "lista":
                with index_lock:
                    snapshot = dict(index)

                print(f"[SERVER] Poslata lista svih fajlova peeru {addr}")
                odgovor = {"status": "ok", "index": snapshot}
                conn.send(json.dumps(odgovor).encode("utf-8"))

            elif komanda == "odjava":
                peer_port = poruka.get("port")
                peer_ip = addr[0]

                with index_lock:
                    for fajl in list(index.keys()):
                        if (peer_ip, peer_port) in index[fajl]:
                            index[fajl].remove((peer_ip, peer_port))

                        if not index[fajl]:
                            del index[fajl]

                print(f"[SERVER] Peer {peer_ip}:{peer_port} se odjavio")
                odgovor = {"status": "ok", "poruka": "Odjavljen"}
                conn.send(json.dumps(odgovor).encode("utf-8"))
                break

            else:
                odgovor = {"status": "greska", "poruka": f"Nepoznata komanda: {komanda}"}
                conn.send(json.dumps(odgovor).encode("utf-8"))

    except Exception as e:
        print(f"[SERVER] Greska sa peer-om {addr}: {e}")
    finally:
        conn.close()
        print(f"[SERVER] Konekcija zatvorena: {addr}")


def pokreni_server(host="0.0.0.0", port=5000):
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((host, port))
    server_socket.listen(10)

    print("=" * 50)
    print("  CS230 - P2P Centralni Indeks Server")
    print("=" * 50)
    print(f"  Slusam na {host}:{port}")
    print(f"  Cekam peer-ove...")
    print("=" * 50)

    try:
        while True:
            conn, addr = server_socket.accept()
            nit = threading.Thread(target=handle_peer, args=(conn, addr))
            nit.daemon = True
            nit.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Gasenje servera...")
    finally:
        server_socket.close()


if __name__ == "__main__":
    pokreni_server()
