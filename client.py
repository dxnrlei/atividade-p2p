import socket
import os

class P2PClient:
    def __init__(self, server_host='localhost', server_port=1234):
        self.server_host = server_host
        self.server_port = server_port
        self.public_folder = "public"

    def start(self):
        if not os.path.exists(self.public_folder):
            os.makedirs(self.public_folder)
            print(f"Pasta '{self.public_folder}' criada")

        self.connect_to_server()

    def connect_to_server(self):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.server_host, self.server_port))
                
                # Envia JOIN
                sock.send("JOIN 127.0.0.1".encode())
                response = sock.recv(1024).decode()
                print(f"Resposta do servidor: {response}")

                # Envia arquivos públicos
                for filename in os.listdir(self.public_folder):
                    filepath = os.path.join(self.public_folder, filename)
                    if os.path.isfile(filepath):
                        size = os.path.getsize(filepath)
                        sock.send(f"CREATEFILE {filename} {size}".encode())
                        response = sock.recv(1024).decode()
                        print(f"Resposta para {filename}: {response}")
        except Exception as e:
            print(f"Erro ao conectar ao servidor: {e}")

if __name__ == "__main__":
    client = P2PClient()
    client.start()