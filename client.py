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
        self.server_thread = None

    def start(self):
        """Inicia o cliente, conecta-se ao servidor e inicia o servidor de escuta em uma thread."""
        if not os.path.exists(self.public_folder):
            os.makedirs(self.public_folder)
            print(f"Pasta '{self.public_folder}' criada")

        self.register_with_server()

        self.server_thread = Thread(target=self.start_client_server)
        self.server_thread.daemon = True 
        self.server_thread.start()

    def register_with_server(self):
        """Conecta ao servidor central, envia JOIN e a lista de arquivos."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.server_host, self.server_port))
                
                # Envia JOIN com o IP do cliente (simplificado para localhost)
                ip_address = "127.0.0.1"
                sock.sendall(f"JOIN {ip_address}".encode())
                response = sock.recv(1024).decode()
                print(f"Resposta do servidor: {response}")

                if response == "CONFIRMJOIN":
                    self.send_public_files(sock)

        except Exception as e:
            print(f"Erro ao registrar com o servidor: {e}")

    def send_public_files(self, sock):
        """Envia a lista de arquivos públicos para o servidor usando uma conexão existente."""
        for filename in os.listdir(self.public_folder):
            filepath = os.path.join(self.public_folder, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                sock.sendall(f"CREATEFILE {filename} {size}".encode())
                response = sock.recv(1024).decode()
                print(f"Resposta do servidor para {filename}: {response}")

    def send_command_to_server(self, command):
        """Abre uma nova conexão para enviar um único comando e obter a resposta."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.server_host, self.server_port))
                sock.sendall(command.encode())
                response = sock.recv(4096).decode()
                return response
        except Exception as e:
            print(f"Erro ao comunicar com o servidor: {e}")
            return None

    def delete_file(self, filename):
        """Envia comando para deletar um arquivo do servidor."""
        response = self.send_command_to_server(f"DELETEFILE {filename}")
        print(f"Resposta do servidor ao deletar '{filename}':\n{response}")


    def search_file(self, pattern):
        """Envia comando para buscar arquivos no servidor."""
        response = self.send_command_to_server(f"SEARCH {pattern}")
        print(f"Resultados da busca por '{pattern}':\n{response}")

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
                if not self.running:
                    break
                client_thread = Thread(target=self.handle_client_request, args=(client_socket, addr))
                client_thread.start()
            except Exception as e:
                if self.running:
                    print(f"Erro no servidor do cliente: {e}")

    def handle_client_request(self, client_socket, addr):
        """Lida com requisições de outros clientes"""
        try:
            request = client_socket.recv(1024).decode().strip()
            print(f"\n[Requisição recebida de {addr}: {request}]")
            parts = request.split()
            command = parts[0].upper()

            if command == "GET" and len(parts) == 3:
                filename = parts[1]
                offset_range = parts[2]

                filepath = os.path.join(self.public_folder, filename)

                if not os.path.exists(filepath):
                    client_socket.sendall(f"ERRO: Arquivo {filename} não encontrado".encode())
                    return
                
                try:
                    offset_parts = offset_range.split('-')
                    start_offset = int(offset_parts[0])
                    file_size = os.path.getsize(filepath)
                    
                    if start_offset >= file_size or start_offset < 0:
                        client_socket.sendall("ERRO: Offset inválido".encode())
                        return
                    
                    if len(offset_parts) > 1 and offset_parts[1]:
                        end_offset = int(offset_parts[1])
                        
                        if end_offset < start_offset:
                             client_socket.sendall("ERRO: Final do offset não pode ser menor que o começo".encode())
                             return

                        end_offset = min(end_offset, file_size - 1)
                        
                    else:
                        end_offset = file_size - 1
                        
                    bytes_to_read = end_offset - start_offset + 1
                    with open(filepath, 'rb') as f:
                        f.seek(start_offset)
                        remaining_bytes = bytes_to_read
                        
                        while remaining_bytes > 0:
                            chunk_size = min(4096, remaining_bytes)
                            chunk = f.read(chunk_size)
                            if not chunk:
                                break
                            client_socket.sendall(chunk)
                            remaining_bytes -= len(chunk)
                            
                except ValueError:
                    client_socket.sendall("ERRO: Formato de offset inválido. Use START-END".encode())
                    return   
                    
            else: 
                client_socket.sendall(f"ERRO: Comando inválido '{command}'".encode())
                
        except Exception as e:
            print(f"Erro ao lidar com requisição: {e}")
        finally:
            client_socket.close()
            print("> ", end="", flush=True)

    def stop(self):
        """Para o cliente e sua thread de servidor"""
        self.running = False
        if self.server_socket:
            try:
                # Conecta-se a si mesmo para desbloquear o accept() e fechar a thread
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    s.connect(('127.0.0.1', self.client_port))
            except Exception:
                pass
            finally:
                self.server_socket.close()
        
        if self.server_thread:
            self.server_thread.join(timeout=2)

        print("Cliente parado.")

    def leave(self):
        """Informa ao servidor que o cliente está saindo."""
        response = self.send_command_to_server("LEAVE")
        if response and "CONFIRMLEAVE" in response:
            print("Saída confirmada pelo servidor.")
        else:
            print("Não foi possível confirmar a saída com o servidor.")

if __name__ == "__main__":
    client = P2PClient()
    client.start()
    
    print("\nCliente P2P iniciado. Comandos disponíveis:")
    print("\tsearch <pattern>  -\tBusca por arquivos")
    print("\tdelete <filename> -\tRemove um arquivo do compartilhamento")
    print("\texit              -\tSai da rede e encerra o cliente")

    try:
        while True:
            command_input = input("> ").strip()
            if not command_input:
                continue

            parts = command_input.split()
            command = parts[0].lower()

            if command == "search" and len(parts) > 1:
                client.search_file(parts[1])
            elif command == "delete" and len(parts) == 2:
                client.delete_file(parts[1])
            elif command == "exit":
                print("Saindo...")
                client.leave()
                break
            else:
                print("Comando inválido. Tente novamente.")
    
    except KeyboardInterrupt:
        print("\nSaindo por interrupção do teclado...")
    finally:
        client.stop()