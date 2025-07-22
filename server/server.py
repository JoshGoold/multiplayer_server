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
            msg = conn.recv(DATA_BUFF).decode()
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
            elif msg_type == QUIT:
                connected = False

        except ConnectionError:
            connected = False
            break

    # Cleanup: Remove client from any rooms they were in
    with lock:
        for room_id in list(rooms.keys()):
            if any(client == conn for client in rooms[room_id].values()):
                del rooms[room_id][next(username for username, client in rooms[room_id].items() if client == conn)]
                if not rooms[room_id]:  # Remove empty rooms
                    del rooms[room_id]
                else:
                    broadcast_to_room(room_id, f"User at {addr} has disconnected")
    
    conn.close()
    print(f"[DISCONNECTED] {addr}")

def create_room(client, username, addr):
    with lock:
        room_id = gen_room_id()
        while room_id in rooms:
            room_id = gen_room_id()
        
        rooms[room_id] = {username: client}
    
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
    
    client.send(f"Successfully joined room {room_id}\n".encode())
    broadcast_to_room(room_id, f"{username} has joined room {room_id}")
    print(f"[ROOM JOINED] {username} joined room {room_id} at {addr}")

def broadcast_to_room(room_id, message):
    with lock:
        if room_id in rooms:
            for username, client in rooms[room_id].items():
                try:
                    client.send(f"{message}\n".encode())
                except ConnectionError:
                    print(f"[ERROR] Failed to send message to {username} in room {room_id}")

if __name__ == "__main__":
    server()       




