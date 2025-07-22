import socket
import threading
import sys

# Server address
HOST = socket.gethostbyname(socket.gethostname())
PORT = 5050
SERVER_ADDR = (HOST, PORT)
DATA_BUFF = 2048

def client():
    # Create socket and connect to server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(SERVER_ADDR)
        print(f"Connected to server at {SERVER_ADDR}")
    except ConnectionError as e:
        print(f"ERROR: Failed to connect to server: {e}")
        return

    # Track if client is in a room
    in_room = False
    current_room_id = None

    # Start a thread to listen for server messages
    def receive_messages():
        nonlocal in_room, current_room_id
        while True:
            try:
                msg = sock.recv(DATA_BUFF).decode().strip()
                if not msg:  # Server closed connection
                    print("DISCONNECTED: Server closed the connection")
                    sock.close()
                    break
                print(f"{msg}")
                # Update in_room status based on server responses
                if "Room created successfully" in msg or "Successfully joined room" in msg:
                    in_room = True
                    if "Room ID: " in msg:
                        current_room_id = msg.split("Room ID: ")[1].split("\n")[0]
                elif "has disconnected" in msg or "ERROR: Room does not exist" in msg:
                    in_room = False
                    current_room_id = None
            except ConnectionError:
                print("DISCONNECTED: Connection to server lost")
                sock.close()
                break

    # Start the receive thread
    receive_thread = threading.Thread(target=receive_messages, daemon=True)
    receive_thread.start()

    try:
        while True:
            # Show simplified menu based on whether user is in a room
            if in_room:
                print(f"\nIn room {current_room_id}: (1) Chat, (2) Quit")
                op = input("Enter 1 or 2: ").strip()
            else:
                print("\nOptions: (1) Create room, (2) Join room, (3) Quit")
                op = input("Enter 1, 2, or 3: ").strip()

            if in_room:
                if op == "1":
                    message = input("Message: ").strip()
                    if not message:
                        print("ERROR: Message cannot be empty")
                        continue
                    sock.send(f"CHAT:{message}".encode())
                elif op == "2":
                    sock.send("QUIT".encode())
                    break
                else:
                    print("ERROR: Enter 1 or 2")
            else:
                if op == "1":
                    username = input("Username: ").strip()
                    if not username:
                        print("ERROR: Username cannot be empty")
                        continue
                    sock.send("CREATE".encode())
                    sock.send(username.encode())
                elif op == "2":
                    room_id = input("Room ID: ").strip()
                    username = input("Username: ").strip()
                    if not room_id or not username:
                        print("ERROR: Room ID and username cannot be empty")
                        continue
                    sock.send("JOIN".encode())
                    sock.send(room_id.encode())
                    sock.send(username.encode())
                elif op == "3":
                    sock.send("QUIT".encode())
                    break
                else:
                    print("ERROR: Enter 1, 2, or 3")

    except KeyboardInterrupt:
        print("\nCLOSING: Shutting down")
        sock.send("QUIT".encode())
    except ConnectionError as e:
        print(f"ERROR: Connection error: {e}")
    finally:
        sock.close()
        print("DISCONNECTED: Connection closed")

if __name__ == "__main__":
    client()