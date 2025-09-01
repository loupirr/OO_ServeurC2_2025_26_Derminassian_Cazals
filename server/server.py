mport socket
import threading

class C2Server:
    def __init__(self, host='10.102.61.45', port=4444):
        self.host = host
        self.port = port
        self.agents = {}  # {agent_id: socket}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[+] Serveur C2 en écoute sur {self.host}:{self.port}")

        while True:
            client_socket, addr = self.server_socket.accept()
            agent_id = f"{addr[0]}:{addr[1]}"
            self.agents[agent_id] = client_socket
            print(f"[+] Nouvel agent connecté : {agent_id}")

            # Lance un thread pour gérer ce client
            client_thread = threading.Thread(target=self.handle_client, args=(client_socket, agent_id))
            client_thread.daemon = True
            client_thread.start()

    def handle_client(self, client_socket, agent_id):
        try:
            while True:
                data = client_socket.recv(4096).decode(errors="ignore")
                if not data:
                    break
                print(f"[{agent_id}] {data.strip()}")
        except Exception as e:
            print(f"[!] Erreur avec {agent_id}: {e}")
        finally:
            print(f"[-] Agent déconnecté : {agent_id}")
            client_socket.close()
            if agent_id in self.agents:
                del self.agents[agent_id]


if __name__ == "__main__":
    server = C2Server()
    server.start()
