import socket
import threading

class C2Server:
    def __init__(self, host='127.0.0.1', port=4444):
        """
        Initialise le serveur C2 (pédagogique).
        - host : adresse IP d’écoute (par défaut localhost)
        - port : port TCP sur lequel le serveur écoute
        """
        self.host = host
        self.port = port
        self.agents = {}  # {agent_id: socket}

        # Création du socket TCP serveur
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Permet de réutiliser le port rapidement après un crash/redémarrage
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Lock pour protéger l’accès concurrent à self.agents
        self.lock = threading.Lock()

    def start(self):
        """Démarre le serveur et accepte les connexions entrantes."""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"[+] Serveur C2 en écoute sur {self.host}:{self.port}")

            while True:
                client_socket, addr = self.server_socket.accept()
                agent_id = f"{addr[0]}:{addr[1]}"

                # Enregistrer l’agent dans le dictionnaire
                with self.lock:
                    self.agents[agent_id] = client_socket

                print(f"[+] Agent connecté : {agent_id}")

                # Créer un thread pour gérer la communication avec cet agent
                thread = threading.Thread(
                    target=self.handle_agent,
                    args=(agent_id, client_socket),
                    daemon=True
                )
                thread.start()

        except Exception as e:
            print(f"[!] Erreur : {e}")
            self.server_socket.close()
            print("[!] Serveur fermé.")

    def handle_agent(self, agent_id, client_socket):
        """
        Gère la communication avec un agent :
        - reçoit ses messages
        - envoie des réponses simples
        """
        try:
            while True:
                data = client_socket.recv(1024)
                if not data:
                    break  # déconnexion propre du client

                message = data.decode("utf-8", errors="replace")
                print(f"[{agent_id}] → {message}")

                # Réponse envoyée au client (simulant une commande)
                response = f"Commande reçue : {message}"
                client_socket.sendall(response.encode("utf-8"))

        except ConnectionResetError:
            print(f"[!] Connexion perdue avec {agent_id}")

        finally:
            # Nettoyage : retirer l’agent et fermer la socket
            with self.lock:
                if agent_id in self.agents:
                    del self.agents[agent_id]
            client_socket.close()
            print(f"[-] Agent déconnecté : {agent_id}")


if __name__ == "__main__":
    # Demande de l'IP à l'utilisateur
    host = input("Entrez l'adresse IP d'écoute (par défaut 127.0.0.1) : ")

    # Si aucune IP n'est entrée, on ferme la socket et arrête le programme
    if not host:
        print("[!] Aucune adresse IP fournie. Fermeture du serveur.")
        exit()

    server = C2Server(host=host)
    server.start()
