import socket
from threading import Thread

class P2PServer:
    def __init__(self, host='0.0.0.0', port=1234):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.all_files = {}

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"Servidor iniciado em {self.host}:{self.port}")

        while self.running:
            client_socket, addr = self.server_socket.accept()
            client_thread = Thread(target=self.handle_client, args=(client_socket, addr))
            client_thread.start()

    def handle_client(self, client_socket, addr):
        ip_address = addr[0]
        print(f"Conexão estabelecida com {ip_address}")

        try:
            while True:
                data = client_socket.recv(1024).decode().strip()
                if not data:
                    break

                parts = data.split()
                if parts[0] == "JOIN":
                    client_socket.send("CONFIRMJOIN".encode())
                elif parts[0] == "CREATEFILE" and len(parts) == 3:
                    filename = parts[1]
                    size = int(parts[2])
                    if ip_address not in self.all_files:
                        self.all_files[ip_address] = []
                    self.all_files[ip_address].append({"filename": filename, "size": size})
                    client_socket.send(f"CONFIRMCREATEFILE {filename}".encode())
        finally:
            if ip_address in self.all_files:
                del self.all_files[ip_address]
            client_socket.close()

if __name__ == "__main__":
    server = P2PServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.server_socket.close()
        print("Servidor parado")