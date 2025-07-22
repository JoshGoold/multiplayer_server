import socket
import threading
import sys

# Server address
HOST = socket.gethostbyname(socket.gethostname())
PORT = 5060
SERVER_ADDR = (HOST, PORT)
DATA_BUFF = 2048

def client():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(SERVER_ADDR)
        print(f"Connected to server at {SERVER_ADDR}")
    except ConnectionError as e:
        print(f"ERROR: Failed to connect to server: {e}")
        return


    # Start a thread to listen for server messages
    def listen_for_messages_thread():
        while True:
            msg = sock.recv(DATA_BUFF).decode().strip()
            if not msg:  
                print("[DISCONNECTED]: Server closed the connection")
                break
            print(f"\n{msg}\n")
        sock.close()
                

    # Start the receive thread
    receive_thread = threading.Thread(target=listen_for_messages_thread, daemon=True)
    receive_thread.start()

    phase1 = True
    while phase1:
        answer = int(input("CREATE ROOM: 1\nJOIN ROOM: 2\nQUIT: 3\nEnter here:"))
        if answer == 1:
            username = input("Username: ").strip()
            if not username:
                print("[ERROR]: Username cannot be empty")
                continue
            sock.send(f"CREATE:{username}".encode())
            phase1 = False
        elif answer == 2:
            room_id = input("Room ID: ").strip()
            username = input("Username: ").strip()
            if not room_id or not username:
                print("ERROR: Room ID and username cannot be empty")
                continue
            sock.send(f"JOIN:{room_id}:{username}".encode())
            phase1 = False
        elif answer == 3:
            sock.send("QUIT:".encode())
            break

    while True:
        op = int(input("Enter (1) Chat or (2) to Exit: ").strip())
        if op == 1:
            message = input("Message: ").strip()
            if not message:
                print("[ERROR]: Message cannot be empty")
            sock.send(f"CHAT:{message}".encode())
        elif op == 2:
            sock.send("QUIT:".encode())
            break
        else:
            print("[404]: Enter 1 or 2")

    sock.close()



if __name__ == "__main__":
    client()