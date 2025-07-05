import socket
import json
from threading import Thread

class P2PServer:
    def __init__(self, host='0.0.0.0', port=1234):
        self.host = host
        self.port = port
        self.all_files = {}
        self.server_socket = None
        self.running = False

    def start(self):
        """Inicia o servidor para aceitar conexões"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.running = True
        print(f"Servidor iniciado em {self.host}:{self.port}")

        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                client_thread = Thread(target=self.handle_client, args=(client_socket, addr))
                client_thread.start()
            except Exception as e:
                if self.running:
                    print(f"Erro ao aceitar conexão: {e}")

    def stop(self):
        """Para o servidor"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("Servidor parado")

    def handle_client(self, client_socket, addr):
        """Lida com as mensagens de um cliente"""
        ip_address = addr[0]
        print(f"Conexão estabelecida com {ip_address}")

        try:
            while True:
                data = client_socket.recv(1024).decode().strip()
                if not data:
                    break

                print(f"Recebido de {ip_address}: {data}")
                response = self.process_command(ip_address, data)
                if response:
                    client_socket.send(response.encode())
                    print(f"Enviado para {ip_address}: {response}")

        except Exception as e:
            print(f"Erro ao lidar com cliente {ip_address}: {e}")
        finally:
            self.user_leave(ip_address)
            client_socket.close()
            print(f"Conexão encerrada com {ip_address}")

    def process_command(self, ip_address, command):
        """Processa os comandos recebidos do cliente"""
        parts = command.split()
        if not parts:
            return None

        cmd = parts[0].upper()

        if cmd == "JOIN" and len(parts) == 2:
            return "CONFIRMJOIN"

        elif cmd == "CREATEFILE" and len(parts) == 3:
            filename = parts[1]
            try:
                size = int(parts[2])
                self.add_file(ip_address, {"filename": filename, "size": size})
                return f"CONFIRMCREATEFILE {filename}"
            except ValueError:
                return None

        elif cmd == "DELETEFILE" and len(parts) == 2:
            filename = parts[1]
            if ip_address in self.all_files:
                client_files = self.all_files[ip_address]
                updated_files = [f for f in client_files if f.get('filename') != filename]

                if len(updated_files) < len(client_files):
                    self.all_files[ip_address] = updated_files
                    print(f"Arquivo {filename} removido para o usuário {ip_address}")
                    return f"CONFIRMDELETEFILE {filename}"
                else:
                    return f"ERRORDELETEFILE {filename} não encontrado"

            else:
                return f"ERRORDELETEFILE ip não encontrado {ip_address}"

        elif cmd == "SEARCH" and len(parts) == 2:
            pattern = parts[1]
            try:
                matching_files = self.search(pattern)
                response_string = ""
                if matching_files:
                    for f in matching_files:
                        response_string += f"FILENAME {f['filename']} {f['ip_address']} {f['size']}\n"
                    
                    return response_string.strip()
                else:
                    return "NOFILESFOUND"
            except ValueError:
                return None

        elif cmd == "LEAVE":
            self.user_leave(ip_address)
            return "CONFIRMLEAVE"
        
        return None

    def add_file(self, ip_address, file):
        """Adiciona um arquivo à lista do cliente"""
        if ip_address not in self.all_files:
            self.all_files[ip_address] = []
        self.all_files[ip_address].append(file)

    def search(self, pattern):
        matching_files = []
        for ip_address in self.all_files.keys():
            for file in self.all_files[ip_address]:
                if pattern in file['filename']:
                    matching_files.append(
                        {
                            "ip_address": ip_address,
                            "filename": file["filename"],
                            "size": file["size"],
                        }
                    )
        return matching_files

    def user_leave(self, ip_address):
        """Remove um cliente e seus arquivos da lista"""
        if ip_address in self.all_files:
            del self.all_files[ip_address]
            print(f"Usuário {ip_address} removido com seus arquivos")

if __name__ == "__main__":
    server = P2PServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()