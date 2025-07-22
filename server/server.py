import socket
import threading
import random
import string
# import game_logic.main  # Uncomment and integrate if needed

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
            if not msg:  # Handle empty message (client disconnected)
                connected = False
                break
                
            print(f"[{addr}] {msg}")
            
            msg_type = msg.split(":")[0].upper()
            
            if msg_type == CREATE:
                conn.send("Please enter username: ".encode())
                username = conn.recv(DATA_BUFF).decode().strip()
                if username:
                    create_room(conn, username, addr)
            elif msg_type == JOIN:
                conn.send("Please enter room_id: ".encode())
                room_id = conn.recv(DATA_BUFF).decode().strip()
                conn.send("Please enter username: ".encode())
                username = conn.recv(DATA_BUFF).decode().strip()
                if room_id and username:
                    join_room(room_id, username, conn, addr)
            elif msg_type == CHAT:
                if conn not in connections:
                    conn.send("ERROR: You must join a room to chat\n".encode())
                    continue
                message = msg.split(":", 1)[1] if ":" in msg else msg
                room_id = connections[conn]
                # Find username for this client
                username = next(u for u, c in rooms[room_id].items() if c == conn)
                send_message(message, username, room_id)
            elif msg_type == QUIT:
                connected = False

        except ConnectionError:
            connected = False
            break

    # Cleanup: Remove client from rooms and connections
    with lock:
        if conn in connections:
            room_id = connections[conn]
            if room_id in rooms:
                username = next(u for u, c in rooms[room_id].items() if c == conn)
                del rooms[room_id][username]
                if not rooms[room_id]:  # Remove empty rooms
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
    
    client.send(f"Room created successfully. Room ID: {room_id}\n".encode())
    broadcast_to_room(room_id, f"{username} has created the room (Room ID: {room_id})")
    print(f"[ROOM CREATED] Room {room_id} by {username} at {addr}")

def gen_room_id():
    return ''.join(random.choice(string.ascii_uppercase) for _ in range(4))

def join_room(room_id, username, client, addr):
    with lock:
        if room_id not in rooms:
            client.send("ERROR: Room does not exist\n".encode())
            return
        if username in rooms[room_id]:
            client.send("ERROR: Username already taken in this room\n".encode())
            return
        rooms[room_id][username] = client
        connections[client] = room_id
    
    client.send(f"Successfully joined room {room_id}\n".encode())
    broadcast_to_room(room_id, f"{username} has joined room {room_id}")
    print(f"[ROOM JOINED] {username} joined room {room_id} at {addr}")

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
            for username, client in rooms[room_id].items():
                try:
                    if username != p_username:
                        client.send(f"[ROOM {room_id}] {p_username}: {message}\n".encode())
                    else:
                        client.send(f"[ROOM {room_id}] You: {message}\n".encode())
                except ConnectionError:
                    print(f"[ERROR] Failed to send message to {username} in room {room_id}")

if __name__ == "__main__":
    server()