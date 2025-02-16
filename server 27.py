import socket
from threading import Thread
import glob
import os
import shutil
import subprocess
import pyautogui


MAX_CONNECTIONS = 20
PORT = 5555
SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER.bind(('127.0.0.1', PORT))
clients = []

def dir_command(path):
    dir_path = path[4:]
    try:
        files_list = glob.glob(os.path.join(dir_path, "*.*"))
        if not files_list:
            response = "Directory is empty or not found."
        else:
            response = "\n".join(files_list)
    except Exception as e:
        response = f"Error accessing directory: {e}"
    return response

def delete_file_command(message):
    try:
        file_path = message[7:]
        if os.path.exists(file_path):
            os.remove(file_path)
            return f"File {file_path} has been deleted."
        else:
            return f"File {file_path} does not exist."
    except Exception as e:
        return f"Error deleting file: {e}"

def copy_file_command(message):
    try:
        parts = message[5:].split()
        if len(parts) != 2:
            return "Invalid COPY command format. Please use: COPY <source> <destination>"

        source_path, destination_path = parts
        if os.path.exists(source_path):
            shutil.copy(source_path, destination_path)
            return f"File copied from {source_path} to {destination_path}."
        else:
            return f"Source file {source_path} does not exist."
    except Exception as e:
        return f"Error copying file: {e}"

def execute_program_command(message):
    try:
        program_path = message[8:].strip()

        if not os.path.exists(program_path):
            return f"Executable {program_path} does not exist."

        result = subprocess.call(program_path, shell=True)

        if result == 0:
            return f"Successfully executed {program_path}."
        else:
            return f"Failed to execute {program_path} with error code {result}."
    except Exception as e:
        return f"Error executing program: {e}"

def take_screenshot():
    try:
        screenshot_path = os.path.join(os.getcwd(), "screen.jpg")
        image = pyautogui.screenshot()
        image.save(screenshot_path)
        return f"Screenshot taken successfully and saved to {screenshot_path}"
    except Exception as e:
        return f"Error taking screenshot: {e}"

def send_screenshot(client):
    try:
        screenshot_path = os.path.join(os.getcwd(), "screen.jpg")

        if not os.path.exists(screenshot_path):
            return "Screenshot not found."

        file_size = os.path.getsize(screenshot_path)

        size_str = str(file_size).zfill(7)
        length_str = str(len(size_str)).zfill(4)
        client.send(length_str.encode())
        client.send(size_str.encode())

        with open(screenshot_path, 'rb') as file:
            while (chunk := file.read(1024)):
                client.send(chunk)

        return "Screenshot sent successfully."
    except Exception as e:
        return f"Error sending screenshot: {e}"


def recv_full(client, size):
    data = b""
    while len(data) < size:
        packet = client.recv(size - len(data))
        if not packet:
            return None
        data += packet
    return data.decode()


def handle_client(client, addr):
    print(f"{addr} connected.")
    clients.append(client)
    try:
        while True:
            length = recv_full(client, 4)
            if not length or not length.isdigit():
                print(f"Invalid length field from {addr}. Clearing socket...")
                client.recv(1024)
                response_message = "0004Wrong Protocol"
                client.send(response_message.encode())
                continue

            message = recv_full(client, int(length))
            if not message:
                break

            print(f"Received message from {addr}: {message}")

            if message.lower().startswith("dir"):
                response = dir_command(message)
            elif message.lower().startswith("delete"):
                response = delete_file_command(message)
            elif message.lower().startswith("copy"):
                response = copy_file_command(message)
            elif message.lower().startswith("execute"):
                response = execute_program_command(message)
            elif message.lower().startswith("screenshot_take"):
                response = take_screenshot()
            elif message.lower().startswith("photo_send"):
                response = send_screenshot(client)
            else:
                response = "Wrong Protocol"

            response_message = f"Server response: {response}"
            length = str(len(response_message)).zfill(4)
            response_message = length + response_message
            client.send(response_message.encode())
    except Exception as e:
        print(f"Error with client {addr}: {e}")
    finally:
        print(f"{addr} disconnected.")
        clients.remove(client)
        client.close()


def wait_for_connection():
    while True:
        try:
            print("Waiting for connections...")
            client, addr = SERVER.accept()
            Thread(target=handle_client, args=(client, addr)).start()
        except Exception as e:
            print(e)
            break
    print("SERVER SHUTDOWN")


if __name__ == "__main__":
    SERVER.listen(MAX_CONNECTIONS)
    print(f"Server is listening on port {PORT}...")
    ACCEPT_THREAD = Thread(target=wait_for_connection)
    ACCEPT_THREAD.start()
    ACCEPT_THREAD.join()
    SERVER.close()
