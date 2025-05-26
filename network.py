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
    print("Broadcasting transaction...")
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
    
    # Rule 1: Longest valid chain wins
    if len(received_chain) > len(local_chain):
        if is_valid_chain(received_chain, difficulty):
            print("[FORK RESOLVED] Adopting longer chain from peer")
            return received_chain
        else:
            print("[FORK RESOLVED] Received chain invalid, keeping local chain")
            return local_chain
    
    # Rule 2: If same length, keep local chain (first-seen rule)
    elif len(received_chain) == len(local_chain):
        print("[FORK RESOLVED] Same length chains, keeping local chain")
        return local_chain
    
    # Rule 3: Local chain is longer
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
            
            # First, validate the received block
            if (received_block.hash != expected_hash or 
                not received_block.hash.startswith("0" * difficulty)):
                print(f"[!] Invalid block received from {addr}")
                conn.close()
                return
            
            # Check if this block extends our current chain
            if received_block.prev_hash == blockchain[-1].hash:
                # This block extends our chain normally
                if received_block.index == len(blockchain):
                    blockchain.append(received_block)
                    on_valid_block_callback(blockchain_fpath, blockchain)
                    print(f"[✓] New valid block added from {addr}")
                else:
                    print(f"[!] Block index mismatch from {addr}")
            
            # Check if we have a fork situation
            elif received_block.index < len(blockchain):
                # We might have a fork - request the full chain from peer
                print(f"[FORK] Potential fork detected with {addr}")
                request_full_chain(addr, blockchain, difficulty, blockchain_fpath, on_valid_block_callback)
            
            else:
                print(f"[!] Block doesn't fit in current chain from {addr}")
        
        elif msg["type"] == "tx":
            tx = msg["data"]
            if tx not in transactions:
                transactions.append(tx)
                print(f"[+] Transaction received from {addr}")
        
        elif msg["type"] == "chain_request":
            # Send our full chain to the requesting peer
            send_full_chain(conn, blockchain)
        
        elif msg["type"] == "full_chain":
            # Received a full chain for fork resolution
            received_chain_data = msg["data"]
            received_chain = [create_block_from_dict(block_data) for block_data in received_chain_data]
            
            # Resolve the fork
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
        # Extract IP from addr tuple if needed
        if isinstance(peer_addr, tuple):
            peer_ip = peer_addr[0]
        else:
            peer_ip = peer_addr
            
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((peer_ip, 5002))  # Assuming standard port
        
        # Request the full chain
        request = json.dumps({"type": "chain_request"})
        s.send(request.encode())
        
        # Receive the response
        data = s.recv(8192).decode()  # Larger buffer for full chain
        response = json.loads(data)
        
        if response["type"] == "full_chain":
            received_chain_data = response["data"]
            received_chain = [create_block_from_dict(block_data) for block_data in received_chain_data]
            
            # Resolve the fork
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
