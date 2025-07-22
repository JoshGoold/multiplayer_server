import socket
import threading
import game_logic.main

# server credentials
backlog = 5
data_buff = 2048

QUIT = "QUIT:"
CHAT = "CHAT:"
GUESS = "GUESS:"

HOST = socket.gethostbyname(socket.gethostname())
PORT = 5050
ADDR = (HOST, PORT)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(ADDR)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Global lock for thread-safe access to shared state
lock = threading.Lock()

# Rooms dictionary: key is room_id (string), value is room details
rooms = {}

def server():
    print(f"[SERVER] started at {ADDR}")
    sock.listen()
    while True:
        conn, addr = sock.accept()
        thread = threading.Thread(target=handle_client, args=(conn,addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")
 
def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected")
    connected = True

    while connected:
        msg = conn.recv(data_buff).decode()
        print(f"[{addr}] {msg}")
        if msg == QUIT:
            connected = False

    conn.close()

def create_room():
    pass

def join_room():
    pass

def remove_client():
    pass

# josh's functions
def broadcast_to_room():
    pass



