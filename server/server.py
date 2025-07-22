import socket
import threading
import random
import string

# Server credentials
BACKLOG = 5
DATA_BUFF = 2048

# Message types
QUIT = "QUIT"
CHAT = "CHAT"
GUESS = "GUESS"
CREATE = "CREATE"
JOIN = "JOIN"

# Server setup
HOST = socket.gethostbyname(socket.gethostname())
PORT = 5050
ADDR = (HOST, PORT)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(ADDR)

# Global lock for thread-safe access to shared state
lock = threading.Lock()

# Rooms dictionary: key is room_id (string), value is dictionary of {username: client_socket}
rooms = {}
# Connections dictionary: maps client_socket to room_id
connections = {}

def server():
    print(f"[SERVER] started at {ADDR}")
    sock.listen(BACKLOG)
    while True:
        conn, addr = sock.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")
    connected = True

    while connected:
        try:
            msg = conn.recv(DATA_BUFF).decode().strip()
            if not msg:  # Handle client disconnection
                connected = False
                break

            print(f"[{addr}] {msg}")  # Debug: Log received message
            
            parts = msg.split(":", 2)  # Allow for room_id:username in JOIN
            msg_type = parts[0].upper() if parts else ""
            
            if msg_type == CREATE:
                if len(parts) < 2 or not parts[1]:
                    conn.send("ERROR: Username cannot be empty".encode())
                    continue
                username = parts[1].strip()
                create_room(conn, username, addr)
            elif msg_type == JOIN:
                if len(parts) < 3 or not parts[1] or not parts[2]:
                    conn.send("ERROR: Room ID and username cannot be empty".encode())
                    continue
                room_id = parts[1].strip()
                if room_id not in rooms:
                    conn.send("ERROR: Room does not exist".encode())
                    continue
                username = parts[2].strip()
                join_room(room_id, username, conn, addr)
            elif msg_type == CHAT:
                with lock:
                    if conn not in connections:
                        conn.send("ERROR: You must join a room to chat".encode())
                        continue
                    room_id = connections.get(conn)
                    if not room_id or room_id not in rooms:
                        conn.send("ERROR: Invalid room state".encode())
                        continue
                    message = parts[1] if len(parts) > 1 else ""
                    if not message:
                        conn.send("ERROR: Message cannot be empty".encode())
                        continue
                    # Find username for this client
                    username = None
                    for u, c in rooms.get(room_id, {}).items():
                        if c == conn:
                            username = u
                            break
                    if not username:
                        conn.send("ERROR: User not found in room".encode())
                        connected = False
                        continue
                    print(f"DEBUG: Processing CHAT from {username} in room {room_id}: {message}")
                    send_message(message, username, room_id)
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

    # Cleanup
    with lock:
        if conn in connections:
            room_id = connections.get(conn)
            if room_id in rooms:
                username = None
                for u, c in rooms[room_id].items():
                    if c == conn:
                        username = u
                        break
                if username:
                    del rooms[room_id][username]
                    if not rooms[room_id]:
                        del rooms[room_id]
                    else:
                        broadcast_to_room(room_id, f"{username} has disconnected")
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
    
    client.send(f"Room created successfully. Room ID: {room_id}".encode())
    broadcast_to_room(room_id, f"{username} has created the room (Room ID: {room_id})")
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
            for username, client in rooms[room_id].items():
                try:
                    client.send(f"[ROOM {room_id}] {message}\n".encode())
                except ConnectionError:
                    print(f"[ERROR] Failed to send message to {username} in room {room_id}")

def send_message(message, p_username, room_id):
    with lock:
        if room_id in rooms:
            print(f"DEBUG: Broadcasting message to room {room_id}: {p_username}: {message}")
            for username, client in rooms[room_id].items():
                try:
                    if username != p_username:
                        client.send(f"[ROOM {room_id}] {p_username}: {message}".encode())
                    else:
                        client.send(f"[ROOM {room_id}] You: {message}".encode())
                except ConnectionError as e:
                    print(f"[ERROR] Failed to send message to {username} in room {room_id}: {e}")

if __name__ == "__main__":
    server()