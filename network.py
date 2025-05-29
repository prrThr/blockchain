import json
import os
import socket
import threading
import traceback
from typing import Callable, Dict, List
from block import Block, create_block_from_dict, hash_block


def list_peers(fpath: str):
    if not os.path.exists(fpath):
        print("[!] No peers file founded!")
        return []
    with open(fpath) as f:
        return [line.strip() for line in f if line.strip()]


def broadcast_block(block: Block, peers_fpath: str, port: int):
    print("Broadcasting block...")
    for peer in list_peers(peers_fpath):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((peer, port))
            s.send(json.dumps({"type": "block", "data": block.as_dict()}).encode())
            s.close()
        except Exception:
            pass


def broadcast_transaction(tx: Dict, peers_fpath: str, port: int):
    for peer in list_peers(peers_fpath):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((peer, port))
            s.send(json.dumps({"type": "tx", "data": tx}).encode())
            s.close()
        except Exception as e:
            print(f"[BROADCAST_TX] Exception during comunication with {peer}. Exception: {e}")


def is_valid_chain(chain: List[Block], difficulty: int) -> bool:
    for i in range(1, len(chain)):
        current_block = chain[i]
        prev_block = chain[i-1]
        
        if current_block.prev_hash != prev_block.hash:
            return False
            
        if not current_block.hash.startswith("0" * difficulty):
            return False
            
        if current_block.hash != hash_block(current_block):
            return False
            
    return True


def resolve_fork(local_chain: List[Block], received_chain: List[Block], difficulty: int) -> List[Block]:
    """
    Implement Longest Chain Rule for fork resolution
    Returns the chain that should be adopted
    """
    print(f"[FORK DETECTED] Local chain length: {len(local_chain)}, Received chain length: {len(received_chain)}")
    
    # Regra 1: Maior chain valida ganha
    if len(received_chain) > len(local_chain):
        if is_valid_chain(received_chain, difficulty):
            print("[FORK RESOLVED] Adopting longer chain from peer")
            return received_chain
        else:
            print("[FORK RESOLVED] Received chain invalid, keeping local chain")
            return local_chain
    
    # Regra 2: Se forem do mesmo tamanho, mantém a chain local (first-seen rule)
    elif len(received_chain) == len(local_chain):
        local_last_hash = local_chain[-1].hash
        received_last_hash = received_chain[-1].hash

        if received_last_hash < local_last_hash:
            print("[FORK RESOLVED] Same length, adopting chain with lower hash")
            return received_chain
        else:
            print("[FORK RESOLVED] Same length, keeping local chain")
            return local_chain
        
    # Regra 3: Chain local é maior
    else:
        print("[FORK RESOLVED] Local chain is longer, keeping local chain")
        return local_chain


def handle_client(
    conn: socket.socket,
    addr: str,
    blockchain: List[Block],
    difficulty: int,
    transactions: List[Dict],
    blockchain_fpath: str,
    on_valid_block_callback: Callable,
):
    try:
        data = conn.recv(4096).decode()
        msg = json.loads(data)

        if msg["type"] == "block":
            received_block = create_block_from_dict(msg["data"])
            expected_hash = hash_block(received_block)

            if (received_block.hash != expected_hash or
                not received_block.hash.startswith("0" * difficulty)):
                print(f"[!] Invalid block received from {addr}")
                conn.close()
                return

            # --- CASOS POSSÍVEIS ---

            local_length = len(blockchain)

            if received_block.index == local_length:
                # Bloco esperado: próximo da cadeia
                if received_block.prev_hash == blockchain[-1].hash:

                    if received_block.index < len(blockchain):
                        # Já existe bloco nesse índice
                        if blockchain[received_block.index].hash != received_block.hash:
                            print(f"[FORK] Conflict on block index {received_block.index} — requesting full chain")
                            request_full_chain(addr, blockchain, difficulty, blockchain_fpath, on_valid_block_callback)
                        else:
                            print(f"[i] Duplicate block received (same hash), ignoring.")
                        conn.close()
                        return

                    blockchain.append(received_block)
                    on_valid_block_callback(blockchain_fpath, blockchain)
                    print(f"[✓] New valid block added from {addr}")
                else:
                    print(f"[FORK] Received block with same index but different prev_hash from {addr}")
                    request_full_chain(addr, blockchain, difficulty, blockchain_fpath, on_valid_block_callback)
            elif received_block.index < local_length:
                if blockchain[received_block.index].hash != received_block.hash:
                    print(f"[FORK] Conflict on block index {received_block.index} from {addr}")
                    request_full_chain(addr, blockchain, difficulty, blockchain_fpath, on_valid_block_callback)
                else:
                    print(f"[i] Received known block from {addr} — ignoring.")
            elif received_block.index > local_length:
                print(f"[!] Received future block (index {received_block.index}) from {addr} — ignoring.")

        elif msg["type"] == "tx":
            tx = msg["data"]
            if tx not in transactions:
                transactions.append(tx)
                print(f"[+] Transaction received from {addr}")

        elif msg["type"] == "chain_request":
            send_full_chain(conn, blockchain)

        elif msg["type"] == "full_chain":
            received_chain_data = msg["data"]
            received_chain = [create_block_from_dict(block_data) for block_data in received_chain_data]

            new_chain = resolve_fork(blockchain, received_chain, difficulty)
            if new_chain != blockchain:
                blockchain.clear()
                blockchain.extend(new_chain)
                on_valid_block_callback(blockchain_fpath, blockchain)
                print("[CHAIN REPLACED] Blockchain updated after fork resolution")

    except Exception as e:
        print(f"Exception when handling client. Exception: {e}. {traceback.format_exc()}")

    conn.close()


def send_full_chain(conn: socket.socket, blockchain: List[Block]):
    """Send the full blockchain to a peer"""
    try:
        chain_data = [block.as_dict() for block in blockchain]
        response = json.dumps({"type": "full_chain", "data": chain_data})
        conn.send(response.encode())
    except Exception as e:
        print(f"Error sending full chain: {e}")


def request_full_chain(
    peer_addr: str,
    blockchain: List[Block],
    difficulty: int,
    blockchain_fpath: str,
    on_valid_block_callback: Callable
):
    """Request full chain from a peer for fork resolution"""
    try:
        if isinstance(peer_addr, tuple):
            peer_ip = peer_addr[0]
        else:
            peer_ip = peer_addr
            
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((peer_ip, 5002))  # Assuming standard port
        
        request = json.dumps({"type": "chain_request"})
        s.send(request.encode())
        
        data = s.recv(8192).decode()
        response = json.loads(data)
        
        if response["type"] == "full_chain":
            received_chain_data = response["data"]
            received_chain = [create_block_from_dict(block_data) for block_data in received_chain_data]
            
            new_chain = resolve_fork(blockchain, received_chain, difficulty)
            if new_chain != blockchain:
                blockchain.clear()
                blockchain.extend(new_chain)
                on_valid_block_callback(blockchain_fpath, blockchain)
                print("[CHAIN REPLACED] Blockchain updated after requesting full chain")
        
        s.close()
    except Exception as e:
        print(f"Error requesting full chain from {peer_ip}: {e}")


def start_server(
    host: str,
    port: int,
    blockchain: List[Block],
    difficulty: int,
    transactions: List[Dict],
    blockchain_fpath: str,
    on_valid_block_callback: Callable,
):
    def server_thread():
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((host, port))
        server.listen()
        print(f"[SERVER] Listening on {host}:{port}")
        while True:
            conn, addr = server.accept()
            threading.Thread(
                target=handle_client,
                args=(
                    conn,
                    addr,
                    blockchain,
                    difficulty,
                    transactions,
                    blockchain_fpath,
                    on_valid_block_callback,
                ),
            ).start()

    threading.Thread(target=server_thread, daemon=True).start()
