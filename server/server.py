import socket
import sys
import threading

# server credentials
host = '0.0.0.0'
backlog = 5
data_buff = 2048

# Global lock for thread-safe access to shared state
lock = threading.Lock()

# Rooms dictionary: key is room_id (string), value is room details
rooms = {}

def server(port):
    # create socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # bind socket and listen for incoming connections
    serverAddr = (host, port)
    print("Server started on %s: %s" %serverAddr)
    sock.bind(serverAddr)
    sock.listen(backlog)
    
    # dictionary for rooms
    
    while True:
        #accept connection
        client, address = sock.accept()
        clientAddr = client, address
        print(f"connected : {address}")
 
def handle_client():
    pass

def create_room():
    pass

def join_room():
    pass

def remove_client():
    pass

# josh's functions
def broadcast_to_room():
    pass

def start_game():
    pass
        
        
