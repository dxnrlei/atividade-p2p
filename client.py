import socket
import os
from threading import Thread

class P2PClient:
    def __init__(self, server_host='localhost', server_port=1234, client_port=1235):
        self.server_host = os.getenv("SERVER_HOST", server_host)
        self.my_address = os.getenv("MY_ADDRESS", "127.0.0.1")
        self.server_port = server_port
        self.client_port = client_port
        self.public_folder = "public" 
        self.running = False
        self.server_socket = None

    def start(self):
        """Inicia o cliente, conecta-se ao servidor."""
        if not os.path.exists(self.public_folder):
            os.makedirs(self.public_folder)
            print(f"Pasta '{self.public_folder}' criada")

        self.register_with_server()

    def register_with_server(self):
        """Conecta ao servidor central, envia JOIN e a lista de arquivos."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((self.server_host, self.server_port))
                
                # Envia JOIN com o IP/endereço do cliente
                sock.sendall(f"JOIN {self.my_address}".encode())
                response = sock.recv(1024).decode()
                print(f"Resposta do servidor: {response}")

                if response == "CONFIRMJOIN":
                    self.send_public_files()

        except Exception as e:
            print(f"Erro ao registrar com o servidor: {e}")

    def send_public_files(self):
        """Envia a lista de arquivos públicos para o servidor usando uma conexão existente."""
        for filename in os.listdir(self.public_folder):
            self.send_single_file(filename)
    
    def send_single_file(self, filename):
        filepath = os.path.join(self.public_folder, filename)
        if os.path.isfile(filepath):
            size = os.path.getsize(filepath)
            resp = self.send_command_to_server(f"CREATEFILE {filename} {size}")
            print(resp)
        else: 
            print(f"Arquivo '{filename}' não encontrado na pasta /public.")
                
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
        return response

    def download_file(self, peer_ip, filename, offset_range="0-"):
        """Baixa um arquivo de outro peer."""
        try:
            print(f"Tentando baixar '{filename}' de {peer_ip}...")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((peer_ip, 1235))
                
                command = f"GET {filename} {offset_range}"
                sock.sendall(command.encode())
                
                save_path = os.path.join(self.public_folder, filename)
                
                with open(save_path, 'wb') as f:
                    first_chunk = True
                    while True:
                        chunk = sock.recv(4096)
                        if not chunk:
                            print("Download completo ou conexão fechada pelo peer.")
                            break 
                        
                        if first_chunk:
                            try:
                                decoded_chunk = chunk.decode()
                                # Caso o primeiro chunk seja uma mensagem de erro do peer
                                if decoded_chunk.startswith("ERRO:"):
                                    print(f"Erro recebido do peer: {decoded_chunk}")
                                    f.close()
                                    os.remove(save_path)
                                    return
                            except UnicodeDecodeError:
                                pass
                            first_chunk = False
                            
                        f.write(chunk)
                
                print(f"Arquivo '{filename}' baixado com sucesso e salvo em '{save_path}'")

        except ConnectionRefusedError:
            print(f"Erro: A conexão com {peer_ip} foi recusada. Verifique se o peer está online.")
        except Exception as e:
            print(f"Ocorreu um erro durante o download: {e}")

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
                    client_socket.sendall("ERRO: Formato de offset inválido ou arquivo com 0 bytes.".encode())
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
                self.server_socket.close()

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
    
    try:
        client.start_client_server()
    except KeyboardInterrupt:
        print("\nSaindo por interrupção do teclado...")
    finally:
        client.leave()
        client.stop()