import socket
from threading import Thread
import glob

SERVER_IP = '127.0.0.1'
SERVER_PORT = 88



def recv_full(client, size):
    data = b""
    while len(data) < size:
        packet = client.recv(size - len(data))
        if not packet:
            return None
        data += packet
    return data.decode()


def receive_messages(client):
    while True:
        try:
            length = recv_full(client, 4)
            if not length or not length.isdigit():
                print("Invalid length field received from server. Disconnecting...")
                break

            message = recv_full(client, int(length))
            if not message:
                break
            print(f"Server: {message}")
        except Exception as e:
            print(f"Error while receiving message: {e}")
            break


def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((SERVER_IP, SERVER_PORT))
        print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")

        Thread(target=receive_messages, args=(client,), daemon=True).start()

        while True:
            message = input("Enter your message (type 'exit' to quit): ")
            if message.lower() == 'exit':
                print("Disconnecting from the server...")
                break

            try:
                length = str(len(message)).zfill(4)
                message = length + message
                client.send(message.encode())
            except Exception as e:
                print(f"Failed to send message: {e}")
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        client.close()
        print("Client disconnected.")


if __name__ == "__main__":
    start_client()
