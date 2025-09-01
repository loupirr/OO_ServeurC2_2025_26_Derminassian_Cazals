import socket
import threading
class C2Server:
    def __init__(self, host='…', port=4444):
        self.host = host
        self.port = port
        self.agents = {} # {agent_id: socket}
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

if __name__ == "__main__":
    server = C2Server()
    server.start()
