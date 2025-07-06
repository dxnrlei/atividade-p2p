from client import P2PClient

def main():
    cli_client = P2PClient()

    print("\nCliente P2P CLI. Comandos disponíveis:")
    print("search <pattern>\t- Busca por arquivos")
    print("get <arquivo> [offset_start-offset_end]\t- Baixa um arquivo de um peer.\n\tEx: get doc.txt 0-1023")
    print("createfile <filename> -\tRegistra um arquivo para compartilhamento")
    print("delete <filename>\t- Remove um arquivo do compartilhamento")
    print("leave\t- Sai da rede (o container continua rodando)")
    print("exit\t- Sai da CLI")

    try:
        while True:
            command = input("\nDigite um comando: ").strip()
            parts = command.split()

            if command.startswith("search") and len(parts) == 2:
                pattern = parts[1]
                search_result = cli_client.search_file(pattern)
                
                if search_result and search_result == "NOFILESFOUND":


                    print("Nenhum arquivo encontrado.")

            elif command.startswith("get") and len(parts) >= 2:
                searched_file = parts[1]
                offset_range = parts[2] if len(parts) == 3 else "0-"
                peer_ip = None
                search_result = cli_client.search_file(searched_file)
                known_files = []
                if not search_result or search_result == "NOFILESFOUND":
                    print(f"Erro: Arquivo '{searched_file}' não encontrado.")
                else:
                    for line in search_result.splitlines():
                        if line.startswith("FILE"):
                            parts = line.split()
                            if len(parts) >= 4:
                                filename = parts[1].strip()
                                ip_address = parts[2].strip()
                                known_files.append([filename, ip_address])                  
                    
                
                for file_info in known_files:
                    if file_info[0] == searched_file:
                        peer_ip = file_info[1]
                        break
                
                if not peer_ip:
                    print(f"Erro: Arquivo '{searched_file}' não encontrado em nenhum peer.")
                    continue
                
                print(f"Baixando arquivo: {filename} de {peer_ip} com offset: {offset_range}")
                cli_client.download_file(peer_ip, filename, offset_range)

            elif command.startswith("createfile") and len(parts) == 2:
                filename = parts[1]
                cli_client.send_single_file(filename)

            elif command.startswith("delete") and len(parts) == 2:
                cli_client.delete_file(parts[1])
                # O arquivo físico não é deletado, apenas o registro no servidor.
                # Para deletar o arquivo físico, seria necessário um comando adicional.

            elif command.startswith("leave") and len(parts) == 1:
                print("Informando ao servidor que este cliente está saindo...")
                cli_client.leave()

            elif command.startswith("exit") and len(parts) == 1:
                print("Saindo da CLI...")
                break
            else:
                print("Comando não reconhecido. Tente novamente.")
    except KeyboardInterrupt:
        print("\nEncerrando cliente CLI.")
    except EOFError:
        print("\nSaindo da CLI...")

if __name__ == "__main__":
    main()
