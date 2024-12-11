import socket
import threading
import time
import utils
import config
import os
from game_server import GameServer
from game_client import GameClient

#######################################################
# Send                                                #
#######################################################
def handle_client():
    utils.welcome()
    while True:
        if config.ROOM["name"]:
            choice = utils.room_menu()
            if choice == "1":
                request_start_game()
            elif choice == "2":
                request_leave_room()
            elif choice == "3":
                request_invite()
            elif choice == "4":
                request_room_chat()
        elif config.USER_NAME:
            request_display()
            choice = utils.lobby_menu()
            if choice == "1":
                request_create_room()
            elif choice == "2":
                request_join_room()
            elif choice == "3":
                request_logout()
            elif choice == "4":
                continue
            elif choice == "5":
                handle_invite()
            elif choice == "6":
                request_game_list()
            elif choice == "7":
                handle_developer()
        else:
            choice = utils.main_menu()
            if choice == "1":
                request_register()
            elif choice == "2":
                request_login()

def send_request(command):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # Automatically closes socket after block
            s.connect((config.SERVER_HOST, config.SERVER_PORT))
            s.send(command.encode('utf-8'))
            return s.recv(1024).decode('utf-8')
    except (socket.timeout, ConnectionRefusedError) as e:
        print(f"Connection error: {e}")
        return None

### INVITE ###
def handle_invite():
    while True:
        utils.invite_list()
        choice = utils.invite_menu()
        if choice == "1":
            continue
        elif choice == "2":
            room_name = utils.accept_invite_input()
            request_join_room(room_name)
            return
        elif choice == "3":
            return

def request_register():
    user_name, password = utils.register_input()
    response = send_request(f"REGISTER:{user_name}:{password}")
    utils.handle_response(response)

def request_display():
    response = send_request("DISPLAY")
    utils.display(response)

def request_login():
    user_name, password = utils.login_input()
    response = send_request(f"LOGIN:{user_name}:{password}:{config.GLOBAL_IP}:{config.PORT}")
    if utils.handle_response(response):
        config.USER_NAME = user_name

def request_logout():
    response = send_request(f"LOGOUT:{config.USER_NAME}")
    if utils.handle_response(response):
        config.USER_NAME = ""

def request_create_room():
    room_name, room_type, game_type = utils.create_room_input()
    response = send_request(f"CREATE_ROOM:{room_name}:{config.USER_NAME}:{room_type}:{game_type}")
    if not utils.handle_response(response):
        return
    config.ROOM["name"] = room_name
    config.ROOM["role"] = "host"
    config.ROOM["game_ip"] = config.GLOBAL_IP
    config.ROOM["game_port"] = config.GAME_PORT
    flag = request_download(config.USER_NAME, config.ROOM['name'])
    if not flag:
        return

def request_join_room(room_name=None):
    if room_name == None:
        room_name = utils.join_room_input()
    response = send_request(f"JOIN_ROOM:{config.USER_NAME}:{room_name}")
    if not utils.handle_response(response):
        return
    if room_name in config.INVITE_LIST:
        del config.INVITE_LIST[room_name]
    config.ROOM["name"] = room_name
    config.ROOM["role"] = "client"
    config.ROOM["game_ip"] = ""
    config.ROOM["game_port"] = ""
    flag = request_download(config.USER_NAME, room_name)
    if not flag:
        return

def request_leave_room():
    response = send_request(f"LEAVE_ROOM:{config.USER_NAME}:{config.ROOM['name']}")
    if utils.handle_response(response):
        config.ROOM["name"] = ""
        config.ROOM["role"] = ""
        config.ROOM["game_ip"] = ""
        config.ROOM["game_port"] = ""

def request_invite():
    request_display()
    player_name = utils.invite_input()
    response = send_request(f"INVITE:{config.USER_NAME}:{player_name}:{config.ROOM['name']}")
    utils.handle_response(response)

def request_room_chat():
    message = utils.room_chat_input()
    response = send_request(f"ROOM_CHAT:{config.USER_NAME}:{config.ROOM['name']}:{message}")
    utils.handle_response(response)

def request_start_game():
    response = send_request(f"GAME_START:{config.ROOM['name']}:{config.USER_NAME}")
    if not utils.handle_response(response):
        return
    game_type, _ = utils.get_game_info(response)
    if config.ROOM["role"] == "host":
        send_request(f"GAME_IP_PORT:{config.ROOM['name']}:{config.GLOBAL_IP}:{config.GAME_PORT}")
        start_game_server(game_type)
        end_game_server()
    elif config.ROOM["role"] == "client":
        game_type, _ = utils.get_game_info(response)
        if not config.ROOM['game_ip']:
            return
        join_game_server(config.ROOM['game_ip'], config.ROOM['game_port'], game_type)

def request_game_list(user_name=None):
    if user_name == None:
        response = send_request("GAME_LIST")
    else:
        response = send_request(f"GAME_LIST:{user_name}")
    utils.all_game_list(response)

def request_upload(game_type, introduction):
    file_path = os.path.join("game", f"{game_type}.py")
    response = send_request(f"UPLOAD:START:{config.USER_NAME}:{game_type}:{introduction}")
    if not utils.handle_response(response):
        return
    try:
        with open(file_path, "rb") as f:
            data = f.read(512)
            while data:
                send_request(f"UPLOAD:CONTINUE:{config.USER_NAME}:{game_type}:{data.decode('utf-8')}")
                data = f.read(512)
    except FileNotFoundError:
        print(f"Error: {file_name} not found in the folder.")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        send_request(f"UPLOAD:END:{config.USER_NAME}:{game_type}")
        print("Uploaded game file successfully.")

def request_download(user_name, room_name):
    print("Downloading game file...")
    response = send_request(f"DOWNLOAD:{user_name}:{room_name}")
    if not utils.handle_response(response):
        return False
    print("Downloaded game file successfully.")
    return True

#######################################################
# Receive                                             #
#######################################################
def handle_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", config.PORT))
    server_socket.listen()
    try:
        while True:
            try:
                conn, addr = server_socket.accept()
                message = conn.recv(1024).decode('utf-8')
                response = handle_request(message)
                conn.send(response.encode('utf-8'))
            except socket.error as e:
                print(f"Socket error: {e}")
                conn.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server_socket.close()

def handle_request(data):
    command, *args = data.split(":")
    if command == "INVITE":
        return invite(*args)
    elif command == "BROADCAST":
        return broadcast(*args)
    elif command == "ROOM_BROADCAST":
        return room_broadcast(*args)
    elif command == "GAME_IP_PORT":
        return game_ip_port(*args)
    elif command == "ROOM_CHAT":
        return room_chat(*args)
    elif command == "DOWNLOAD":
        data = ":".join(args[3:])
        return download(args[0], args[1], args[2], data)
    else:
        return "ERROR"

def invite(player_name, user_name, room_name, game_type):
    utils.invite_recv(player_name, room_name, game_type)
    config.INVITE_LIST[player_name] = {
        "player_name": player_name,
        "room_name": room_name,
        "game_type": game_type
    }
    return f"INVITE:Y:{player_name}:{user_name}:{room_name}:{game_type}"

def broadcast(user_name, action):
    utils.broadcast(user_name, action)
    return f"BROADCAST:{user_name}:{action}"

def room_broadcast(player_name, action, room_name):
    utils.room_broadcast(player_name, action, room_name)
    if action == "LEAVE_ROOM" and config.ROOM["role"] == "client":
        print("You are now the host of the room.")
        config.ROOM["role"] = "host"
        config.ROOM["game_ip"] = config.GLOBAL_IP
        config.ROOM["game_port"] = config.GAME_PORT
    return f"ROOM_BROADCAST:{player_name}:{action}:{room_name}"

def game_ip_port(room_name, game_ip, game_port):
    if config.ROOM["name"] == room_name:
        config.ROOM["game_ip"] = game_ip
        config.ROOM["game_port"] = game_port
        return f"GAME_IP_PORT:Y:{room_name}:{game_ip}:{game_port}"
    return f"GAME_IP_PORT:N:{room_name}:{game_ip}:{game_port}"

def room_chat(user_name, room_name, message):
    if config.ROOM["name"] == room_name:
        utils.room_chat_recv(user_name, message)
    return f"ROOM_CHAT:{user_name}:{room_name}:{message}"

def download(status, user_name, game_type, data=""):
    file_name = f"{game_type}.py"
    file_path = os.path.join("download", file_name)
    if status == "START":
        if os.path.exists(file_path):
            os.remove(file_path)
        with open(file_path, "wb") as f:
            f.write("".encode('utf-8'))
        return f"DOWNLOAD:Y:{user_name}:{game_type}"
    elif status == "CONTINUE":
        with open(file_path, "ab") as f:
            f.write(data.encode('utf-8'))
        return f"DOWNLOAD:Y:{user_name}:{game_type}"
    elif status == "END":
        return f"DOWNLOAD:Y:{user_name}:{game_type}"
    return f"DOWNLOAD:N:INVALID_STATUS"

#######################################################
# Other                                               #
#######################################################

def start_game_server(game_type):
    print("Starting game server...")
    game_server = GameServer(config.GAME_PORT, game_type)
    game_server.start_server()

def join_game_server(game_ip, game_port, game_type):
    print("Joining game server...")
    game_client = GameClient(game_ip, game_port, game_type)
    game_client.start_client()

def end_game_server():
    print("Ending game server...")
    response = send_request(f"GAME_END:{config.ROOM['name']}")
    utils.handle_response(response)

#######################################################
# Developer                                           #
#######################################################
def handle_developer():
    while True:
        choice = utils.developer_menu()
        if choice == "1":
            request_game_list(config.USER_NAME)
        elif choice == "2":
            game_type, introduction = utils.game_publish()
            if not game_type or not introduction:
                continue
            request_upload(game_type, introduction)
        elif choice == "3":
            return

#######################################################
# Main                                                #
#######################################################

def start_client():
    config.GLOBAL_IP = utils.get_global_ip()
    threading.Thread(target=handle_server).start()
    threading.Thread(target=handle_client).start()

if __name__ == "__main__":
    start_client()