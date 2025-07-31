import socket
import threading
import random
import string

# add if someone leave inform memebers and if the last person leaves end room

# Server credentials
DATA_BUFF = 2048

# Message types
QUIT = "QUIT"
CHAT = "CHAT"
GUESS = "GUESS"
CREATE = "CREATE"
JOIN = "JOIN"

# Server setup
HOST = socket.gethostbyname(socket.gethostname())
PORT = 5060
ADDR = (HOST, PORT)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(ADDR)

# Global lock for thread-safe access to shared state
lock = threading.Lock()

# Rooms dictionary: key is room_id (string), value is dictionary of {username: client_socket}
rooms = {}
# Connections dictionary: maps client_socket to room_id
connections = {}

def server():
    print(f"[SERVER] started at {ADDR}")
    sock.listen()
    while True:
        conn, addr = sock.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")
    connected = True
    this_username = ""

    while connected:
        try:
            msg = conn.recv(DATA_BUFF).decode().strip()
            if not msg:  # Handle client disconnection
                connected = False
                break

            print(f"[{addr}] {msg}")  # Debug: Log received message
            
            parts = msg.split(":", 2)  
            msg_type = parts[0]
            
            if msg_type == CREATE:           
                username = parts[1].strip()
                this_username = username
                create_room(conn, username, addr)

            elif msg_type == JOIN:
                room_id = parts[1].strip()
                if room_id not in rooms:
                    conn.send("ERROR: Room does not exist".encode())
                    continue
                username = parts[2].strip()
                this_username = username
                join_room(room_id, username, conn, addr)

            elif msg_type == CHAT:

                    room_id = connections.get(conn)
                    message = parts[1]
                    if not message:
                        conn.send("ERROR: Message cannot be empty".encode())
                        continue
                    if this_username: 
                        print(f"DEBUG: Processing CHAT from {this_username} in room {room_id}: {message}")
                        send_message(message, this_username, room_id)
            elif msg_type == QUIT:
                connected = False
            else:
                conn.send("ERROR: Invalid command".encode())

        except ConnectionError as e:
            print(f"[ERROR] Connection error with {addr}: {e}")
            connected = False
        except Exception as e:
            print(f"[ERROR] Unexpected error with {addr}: {e}")
            connected = False
        # finally:
        #     client.close()

    # Cleanup
    with lock:
        if conn in connections:
            room_id = connections.get(conn)
            del rooms[room_id][this_username]
            if not rooms[room_id]:
                 del rooms[room_id]
                 print(f"[ROOM CLOSED] Room {room_id} closed as last member left.")
            else:
                broadcast_to_room(room_id, f"{this_username} has disconnected")
            del connections[conn]
    
    conn.close()
    print(f"[DISCONNECTED] {addr}")

def create_room(client, username, addr):
    with lock:
        room_id = gen_room_id()
        while room_id in rooms:
            room_id = gen_room_id()
        rooms[room_id] = {username: client}
        connections[client] = room_id
    
    client.send(room_id.encode())
    broadcast_to_room(room_id, f"\nROOM CREATED\nJoin Code: {room_id}\n")
    print(f"[ROOM CREATED] Room {room_id} by {username} at {addr}")

def join_room(room_id, username, client, addr):
    with lock:
        if room_id not in rooms:
            client.send("ERROR: Room does not exist".encode())
            return
        if username in rooms[room_id]:
            client.send("ERROR: Username already taken in this room".encode())
            return
        rooms[room_id][username] = client
        connections[client] = room_id
    
    client.send(f"Successfully joined room {room_id}".encode())
    broadcast_to_room(room_id, f"{username} has joined room {room_id}")
    print(f"[ROOM JOINED] {username} joined room {room_id} at {addr}")

def gen_room_id():
    return ''.join(random.choice(string.ascii_uppercase) for _ in range(4))

def broadcast_to_room(room_id, message):
    with lock:
        if room_id in rooms:
            to_remove =[]
            for username, client in rooms[room_id].items():
                try:
                    client.send(f"{message}\n".encode())
                except ConnectionError:
                    print(f"[ERROR] Failed to send message to {username} in room {room_id}")
                    to_remove.append(username)
            
            for username in to_remove:
                del rooms[room_id][username]

def send_message(message, p_username, room_id):
    with lock:
        if room_id in rooms:
            print(f"DEBUG: Broadcasting message to room {room_id}: {p_username}: {message}")
            for username, client in rooms[room_id].items():
                try:
                    if username != p_username:
                        client.send(f"{p_username}: {message}".encode())
                    else:
                        client.send(f"You: {message}".encode())
                except ConnectionError as e:
                    print(f"[ERROR] Failed to send message to {username} in room {room_id}: {e}")

if __name__ == "__main__":
    server()