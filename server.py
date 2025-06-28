import socket
from threading import Thread

class P2PServer:
    def __init__(self, host='0.0.0.0', port=1234):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"Servidor iniciado em {self.host}:{self.port}")

        while self.running:
            client_socket, addr = self.server_socket.accept()
            print(f"Conexão estabelecida com {addr[0]}")
            client_socket.send("Conexão estabelecida!".encode())
            client_socket.close()

if __name__ == "__main__":
    server = P2PServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.server_socket.close()
        print("Servidor parado")