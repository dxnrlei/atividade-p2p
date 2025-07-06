# Aplicação de Compartilhamento de Arquivos P2P com Docker

Este projeto é uma aplicação simples de compartilhamento de arquivos P2P (peer-to-peer) containerizada com Docker. Consiste em um servidor central para descoberta de peers e múltiplos clientes que podem compartilhar e baixar arquivos uns dos outros.

## Pré-requisitos

- Docker
- Docker Compose

## Como Executar

0.  **Salve os arquivos para compartilhamento**

    Crie os diretórios /public em client1 e client2 e lá, armazene os arquivos que serão compartilhados.

    ```bash
    mkdir -p ./client1/public
    mkdir -p ./client2/public
    ```

    Esses comandos irão criar os diretórios `public` dentro das pastas `client1` e `client2`. Coloque os arquivos que deseja compartilhar dentro desses diretórios antes de prosseguir.

1.  **Construa e inicie os serviços:**

    Abra um terminal no diretório raiz do projeto e execute:

    ```bash
    docker-compose up --build
    ```

    Este comando irá construir a imagem Docker e iniciar os contêineres do servidor e de dois clientes. A saída de todos os contêineres será exibida neste terminal. Você verá logs indicando que o servidor e os clientes foram iniciados.

    Os arquivos presentes em /public de cada peer serão registrados como disponíveis para compartilhamento no servidor assim que os containeres forem inicializados. Arquivos adicionados posteriormente deverão ser registrados com o comando `createfile` na interface do cliente. 

2.  **Interaja com os clientes:**

    Você precisará abrir terminais separados para executar a interface de linha de comando para cada cliente.

    -   **Para usar a CLI do client1 (em um novo terminal):**
        ```bash
        docker-compose exec client1 python cli.py
        ```

    -   **Para usar a CLI do client2 (em outro novo terminal):**
        ```bash
        docker-compose exec client2 python cli.py
        ```

## Comandos Disponíveis

Dentro da CLI de um cliente, você pode usar os seguintes comandos:

-   `search <pattern>`: Procura por arquivos compartilhados por outros peers.
    -   Exemplo: `search file`
-   `get <filename>`: Baixa um arquivo de um peer. O nome do arquivo deve ser exatamente como foi registrado pelo server. 
    -   Exemplo: `get file2.txt` (ao executar no client1 após uma busca)
-   `createfile <filename>`: Registra um único arquivo do diretório /public no servidor. 
-   `delete <filename>`: Remove um de seus arquivos do compartilhamento (remove o registro do servidor).
    -   Exemplo: `delete file1.txt` (ao executar no client1)
-   `leave`: Informa ao servidor que você está saindo da rede. Seus arquivos não serão mais pesquisáveis.
-   `exit`: Sai da CLI.

### Exemplo de Fluxo de Trabalho

    Presumindo que client1 tem o arquivo `file1.txt` em seu diretório public, e client2 tem `file2.txt`. Lembre-se de adicionar os arquivos antes de iniciar os serviços.

1.  Inicie os serviços com `docker-compose up --build`.
2.  Abra um novo terminal e inicie a CLI para o `client1`: `docker-compose exec client1 python cli.py`.
3.  No prompt do `client1`, procure por arquivos: `search file`. Você deve ver `file1.txt` do `client1` e `file2.txt` do `client2`.
4.  Baixe `file2.txt` do `client2`: `get file2.txt`.
5.  O arquivo será baixado na pasta `public` do `client1` (`./client1/public` na sua máquina host).
6.  Abra outro terminal e inicie a CLI para o `client2`: `docker-compose exec client2 python cli.py`.
7.  No prompt do `client2`, procure e baixe `file1.txt`: `search file` e depois `get file1.txt`.

## Parando a Aplicação

-   Para parar todos os serviços, pressione `Ctrl+C` no terminal onde `docker-compose up` está sendo executado. Isso encerrará os clientes e o servidor de forma graciosa.
-   Para limpar todos os contêineres, redes e volumes criados pelo docker-compose, execute:
    ```bash
    docker-compose down
    ```