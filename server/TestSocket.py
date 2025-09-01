import socket

class Server:
    def __init__(self, host='127.0.0.1', port=4444):
        """
        Serveur TCP pédagogique sans multithreading.
        Traite une connexion à la fois (boucle: accept -> échanger -> fermer).
        """
        self.host = host
        self.port = port

        # Socket TCP (IPv4)
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        """Démarre le serveur et gère les clients séquentiellement."""
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[+] Serveur TCP en écoute sur {self.host}:{self.port}")

        while True:
            # Bloque jusqu'à une nouvelle connexion
            client_socket, addr = self.server_socket.accept()
            agent_id = f"{addr[0]}:{addr[1]}"
            print(f"[+] Connecté : {agent_id}")

            try:
                # Message d'accueil
                client_socket.sendall(b"HELLO (TCP)\n")

                # Boucle d'échanges avec CE client uniquement
                while True:
                    data = client_socket.recv(1024)  # bloquant
                    if not data:
                        # 0 octet => fermeture côté client
                        print(f"[-] Fermeture par client : {agent_id}")
                        break

                    message = data.decode("utf-8", errors="replace").strip()
                    print(f"[{agent_id}] -> {message}")

                    # Réponse simple (ACK/echo)
                    response = f"ACK: {message}\n"
                    client_socket.sendall(response.encode("utf-8"))

            except ConnectionResetError:
                print(f"[!] Connexion réinitialisée par {agent_id}")
            except Exception as e:
                print(f"[!] Erreur avec {agent_id} : {e}")
            finally:
                # Toujours fermer la socket du client avant de passer au suivant
                try:
                    client_socket.close()
                except OSError:
                    pass
                print(f"[-] Déconnecté : {agent_id}")

if __name__ == "__main__":
    server = Server()  # 127.0.0.1:4444
    server.start()
