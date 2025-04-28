import socket
import threading

PORT = 5000         # Porta padrão de comunicação
BUFFER_SIZE = 1024  # Tamanho máximo da mensagem
ENCODING = 'utf-8'  # Codificação de texto

# Pergunta o IP do amigo para enviar mensagem
peer_ip = input("Digite o IP do peer (ou deixe vazio para só receber mensagens): ").strip()

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

