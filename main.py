import socket
import threading

PORT = 5000         # Porta padrão de comunicação
BUFFER_SIZE = 1024  # Tamanho máximo da mensagem
ENCODING = 'utf-8'  # Codificação de texto

peers = { 
    "Arthur": "10.147.20.9",
    "Duda": "10.147.20.190",
    "Gabriel": "123.456.789",
    "Pedrini": "321.654.987"
}

print("------------------------------------------------------")
for idx, nome in enumerate(peers.keys(), start=1):
    print(f"{idx}. {nome}")
print(f"{len(peers) + 1}. Só receber mensagens (sem selecionar um peer)")
opcao = input("Digite o número do peer desejado: ").strip()
print("------------------------------------------------------")

if opcao.isdigit():
    opcao = int(opcao)
    if 1 <= opcao <= len(peers):
        nome_escolhido = list(peers.keys())[opcao - 1]
        peer_ip = peers[nome_escolhido]
        print(f"Iniciando conversa com {nome_escolhido} ({peer_ip})...")
    elif opcao == len(peers) + 1:
        peer_ip = ""
        print("Iniciando conversa sem peer, apenas recebendo mensagens.")
    else:
        print("Opção inválida.")
else:
    print("Opção inválida.")

def receber_mensagens():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', PORT))
    server_socket.listen(5)
    print(f"[Servidor] Aguardando mensagens na porta {PORT}...")

    while True:
        conn, addr = server_socket.accept()
        data = conn.recv(BUFFER_SIZE)
        print(f"\n[Mensagem recebida de {addr[0]}]: {data.decode(ENCODING)}")
        conn.close()

def enviar_mensagens():
    while True:
        msg = input("\nDigite a mensagem para enviar (ou 'sair' para terminar): ")
        if msg.lower() == 'sair':
            print("Encerrando envio de mensagens.")
            break
        if not peer_ip:
            print("Nenhum peer IP configurado para envio.")
            continue
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((peer_ip, PORT))
            client_socket.send(msg.encode(ENCODING))
            client_socket.close()
            print("[Mensagem enviada com sucesso!]")
        except Exception as e:
            print(f"[Erro ao enviar mensagem]: {e}")

if __name__ == "__main__":
    thread_receber = threading.Thread(target=receber_mensagens, daemon=True)
    thread_receber.start()

    # Se quiser também enviar, inicia o envio
    if peer_ip:
        enviar_mensagens()
    else:
        # Se o usuário não configurou um IP, apenas mantém a thread de recebimento viva
        try:
            while True:
                pass
        except KeyboardInterrupt:
            print("\nEncerrado.")

