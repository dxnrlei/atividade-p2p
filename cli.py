from client import P2PClient

def main():
    cli_client = P2PClient()

    print("\nCliente P2P CLI. Comandos disponíveis:")
    print("\tsearch <pattern>  -\tBusca por arquivos")
    print("\tget <arquivo> [offset_start-offset_end] -\tBaixa um arquivo de um peer. Ex: get doc.txt 0-1023")
    print("\tcreatefile <filename> -\tCria um arquivo para compartilhamento")
    print("\tdelete <filename> -\tRemove um arquivo do compartilhamento")
    print("\tleave             -\tSai da rede (o container continua rodando)")
    print("\texit              -\tSai da CLI")

    try:
        while True:
            command = input("\nDigite um comando: ").strip()
            parts = command.split()

            if command.startswith("search") and len(parts) == 2:
                pattern = parts[1]
                print(f"Buscando arquivos com o padrão: {pattern}")
                search_result = cli_client.search_file(pattern)
                
                if search_result and search_result != "NOFILESFOUND":
                    print("Arquivos encontrados:")
                    for line in search_result.splitlines():
                        if line.startswith("FILE"):
                            print(f"\t{line}")

                else:
                    print("Nenhum arquivo encontrado.")

            elif command.startswith("get") and len(parts) >= 2:
                filename = parts[1]
                offset_range = parts[2] if len(parts) == 3 else "0-"
                peer_ip = None
                search_result = cli_client.search_file(filename)
                
                if not search_result or search_result == "NOFILESFOUND":
                    print(f"Erro: Arquivo '{filename}' não encontrado.")
                else:
                    file_parts = search_result.split()
                    peer_ip = file_parts[2] if len(file_parts) >= 3 else None
                    
                if file_parts[1] != filename:
                    print(f"Erro: Arquivo '{filename}' não encontrado no peer {peer_ip}. Você quis dizer '{file_parts[1]}'?")
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
