import socket
import os
from threading import Thread

class P2PClient:
    def __init__(self, server_host='localhost', server_port=1234, client_port=1235):
        self.server_host = server_host
        self.server_port = server_port
        self.client_port = client_port
        self.public_folder = "public" 
        self.running = False
        self.server_socket = None

    def start(self):
        """Inicia o cliente e se conecta ao servidor"""
        if not os.path.exists(self.public_folder):
            os.makedirs(self.public_folder)
            print(f"Pasta '{self.public_folder}' criada")

        self.connect_to_server()

        self.start_client_server()

    def connect_to_server(self):
        """Conecta ao servidor central e envia informações"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.server_host, self.server_port))
                
                # Envia JOIN com o IP do cliente (simplificado para localhost)
                ip_address = "127.0.0.1"
                sock.send(f"JOIN {ip_address}".encode())
                response = sock.recv(1024).decode()
                print(f"Resposta do servidor: {response}")

                if response == "CONFIRMJOIN":
                    self.send_public_files(sock)

        except Exception as e:
            print(f"Erro ao conectar ao servidor: {e}")

    def send_public_files(self, sock):
        """Envia a lista de arquivos públicos para o servidor"""
        try:
            for filename in os.listdir(self.public_folder):
                filepath = os.path.join(self.public_folder, filename)
                if os.path.isfile(filepath):
                    size = os.path.getsize(filepath)
                    sock.send(f"CREATEFILE {filename} {size}".encode())
                    response = sock.recv(1024).decode()
                    print(f"Resposta do servidor para {filename}: {response}")
        except Exception as e:
            print(f"Erro ao enviar arquivos públicos: {e}")

    def start_client_server(self):
        """Inicia o servidor do cliente para receber conexões de outros clientes"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.client_port))
        self.server_socket.listen(5)
        self.running = True
        print(f"Cliente ouvindo na porta {self.client_port}")

        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_thread = Thread(target=self.handle_client_request, args=(client_socket, addr))
                client_thread.start()
            except Exception as e:
                if self.running:
                    print(f"Erro ao aceitar conexão: {e}")

    def handle_client_request(self, client_socket, addr):
        """Lida com requisições de outros clientes"""
        try:
            data = client_socket.recv(1024).decode().strip()
            print(f"Recebido de {addr}: {data}")
            # Aqui será implementado o tratamento de GET mais tarde
            client_socket.send("COMANDO NÃO IMPLEMENTADO".encode())
        except Exception as e:
            print(f"Erro ao lidar com requisição: {e}")
        finally:
            client_socket.close()

    def stop(self):
        """Para o cliente"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("Cliente parado")

if __name__ == "__main__":
    client = P2PClient()
    try:
        client.start()
    except KeyboardInterrupt:
        client.stop()