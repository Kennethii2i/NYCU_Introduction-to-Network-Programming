import socket
import threading
import csv
import os
# A
# Server settings
PORT = 10443
players = {}  # Track online players and their statuses (offline, idle, in_game, in_room)
game_rooms = {}  # Track available game rooms
game_list = {}
CSV_FILE = "account_info/players.csv"
GAME_CSV_FILE = "game_info/games.csv"

# Send
def send_request(command, ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s: # Automatically closes socket after block
            s.connect((ip, int(port)))
            s.send(command.encode('utf-8'))
            response = s.recv(1024).decode('utf-8')
            return response
    except (socket.timeout, ConnectionRefusedError) as e:
        return "ERROR"

def request_invite(ip, port, user_name, player_name, room_name, game_type):
    return send_request(f"INVITE:{user_name}:{player_name}:{room_name}:{game_type}", ip, port)

def request_broadcast(ip, port, user_name, action):
    send_request(f"BROADCAST:{user_name}:{action}", ip, port)

def request_room_broadcast(ip, port, user_name, action, room_name):
    send_request(f"ROOM_BROADCAST:{user_name}:{action}:{room_name}", ip, port)

def request_room_chat(ip, port, user_name, room_name, message):
    send_request(f"ROOM_CHAT:{user_name}:{room_name}:{message}", ip, port)

def request_ip_port(ip, port, room_name, game_ip, game_port):
    return send_request(f"GAME_IP_PORT:{room_name}:{game_ip}:{game_port}", ip, port)

def request_download(ip, port, user_name, game_type):
    file_path = os.path.join("game", f"{game_type}.py")
    if not os.path.exists(file_path):
        return f"DOWNLOAD:N:game not found in folder"
    send_request(f"DOWNLOAD:START:{user_name}:{game_type}", ip, port)
    try:
        with open(file_path, "rb") as f:
            data = f.read(512)
            while data:
                send_request(f"DOWNLOAD:CONTINUE:{user_name}:{game_type}:{data.decode('utf-8')}", ip, port)
                data = f.read(512)
    except Exception as e:
        return f"DOWNLOAD:N:{e}"
    finally:
        send_request(f"DOWNLOAD:END:{user_name}:{game_type}", ip, port)

# Receive
def handle_client(client_socket, addr):
    try:
        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            response = handle_request(data)
            client_socket.send(response.encode('utf-8'))
    finally:
        client_socket.close()

# Process client requests
def handle_request(data):
    command, *args = data.split(":")
    if command == "REGISTER":
        return register(*args)
    elif command == "DISPLAY":
        return display()
    elif command == "LOGIN":
        return login(*args)
    elif command == "LOGOUT":
        return logout(*args)
    elif command == "CREATE_ROOM":
        return create_room(*args)
    elif command == "JOIN_ROOM":
        return join_room(*args)
    elif command == "LEAVE_ROOM":
        return leave_room(*args)
    elif command == "INVITE":
        return invite(*args)
    elif command == "ROOM_CHAT":
        return room_chat(*args)
    elif command == "GAME_START":
        return game_start(*args)
    elif command == "GAME_END":
        return game_end(*args)
    elif command == "GAME_IP_PORT":
        return game_ip_port(*args)
    elif command == "GAME_LIST":
        return all_game_list(*args)
    elif command == "UPLOAD":
        data = ":".join(args[3:])
        return upload(args[0], args[1], args[2], data)
    elif command == "DOWNLOAD":
        return download(*args)
    else:
        return "ERROR"

# Define commands (simplified)
def register(user_name, password):
    if user_name in players:
        return f"REGISTER:N:username exists"
    if user_name == "" or password == "":
        return f"REGISTER:N:invalid input"
    players[user_name] = {
        'user_name': user_name,
        'password': password,
        'status': 'offline',
    }
    save_players_to_csv()
    return f"REGISTER:Y:{user_name}"

def login(user_name, password, ip, port):
    if user_name not in players:
        return f"LOGIN:N:unknown"
    elif players[user_name]['password'] != password:
        return f"LOGIN:N:password incorrect"
    elif players[user_name]['status'] != 'offline':
        return f"LOGIN:N:already logged in"
    players[user_name]['status'] = 'idle'
    players[user_name]['ip'] = ip
    players[user_name]['port'] = port
    broadcast(user_name, "LOGIN")
    return f"LOGIN:Y:{user_name}"

def display():
    # currently online players (e.g., playing, idle)
    # All public game rooms (including the creator, game type, and room status)
    online = [
        f"{player} ({players[player]['status']})"
        for player in players if players[player]['status'] in ['idle', 'in_game', 'in_room']
    ]
    online_str = ', '.join(online) if online else "NO ONLINE PLAYERS"
    rooms = [
        {
            'room_name': room, 'host': game_rooms[room]['host'], 'type': game_rooms[room]['type'],
            'status': game_rooms[room]['status'], 'game_type': game_rooms[room]['game_type']
        }
        for room in game_rooms if game_rooms[room]['type'] == "public"
    ]
    room_str = ','.join([f"{room['room_name']} ({room['host']}) - {room['status']} - {room['game_type']}" for room in rooms]) if rooms else "NO PUBLIC ROOMS"
    return f"DISPLAY:{online_str}\n {room_str}"

def logout(user_name):
    if user_name in players:
        players[user_name]['status'] = 'offline'
        broadcast(user_name, "LOGOUT")
        return f"LOGOUT:Y:{user_name}"
    return f"LOGOUT:N:no such user"

def create_room(room_name, host_name, room_type, game_type):
    if host_name not in players:
        return f"CREATE_ROOM:N:no such user"
    if room_name in game_rooms:
        return f"CREATE_ROOM:N:room already exists"
    if room_name == "":
        return f"CREATE_ROOM:N:invalid room name"
    if game_type not in game_list:
        return f"CREATE_ROOM:N:game type not found"
    game_rooms[room_name] = {
        'room_name': room_name,
        'host': host_name,
        'type': room_type,
        'game_type': game_type,
        'status': 'waiting',
        'client': None,
    }
    players[host_name]['status'] = 'in_room'
    if room_type == 'public':
        broadcast(host_name, "CREATE_ROOM")
    return f"CREATE_ROOM:Y:{room_name}:{host_name}:{room_type}:{game_type}"

def join_room(user_name, room_name):
    if room_name not in game_rooms:
        return f"JOIN_ROOM:N:no such room"
    elif game_rooms[room_name]['status'] != 'waiting':
        return f"JOIN_ROOM:N:room is full"
    game_rooms[room_name]['status'] = 'full'
    game_rooms[room_name]['client'] = user_name
    players[user_name]['status'] = 'in_room'
    request_room_broadcast(players[game_rooms[room_name]['host']]['ip'], players[game_rooms[room_name]['host']]['port'], user_name, "JOIN_ROOM", room_name)
    return f"JOIN_ROOM:Y:{user_name}:{room_name}"

def leave_room(user_name, room_name):
    if room_name not in game_rooms:
        return f"LEAVE_ROOM:N:no such room"
    if game_rooms[room_name]['status'] == 'waiting':
        del game_rooms[room_name]
    else:
        if game_rooms[room_name]['host'] == user_name:
            game_rooms[room_name]['status'] = 'waiting'
            game_rooms[room_name]['host'] = game_rooms[room_name]['client']
            game_rooms[room_name]['client'] = ""
        else:
            game_rooms[room_name]['status'] = 'waiting'
            game_rooms[room_name]['client'] = ""
        request_room_broadcast(players[game_rooms[room_name]['host']]['ip'], players[game_rooms[room_name]['host']]['port'], user_name, "LEAVE_ROOM", room_name)
    players[user_name]['status'] = 'idle'
    return f"LEAVE_ROOM:Y:{user_name}:{room_name}"

def invite(user_name, player_name, room_name):
    if room_name not in game_rooms:
        return f"INVITE:N:no such room"
    elif game_rooms[room_name]['status'] != 'waiting':
        return f"INVITE:N:room not available"
    elif player_name not in players:
        return f"INVITE:N:player not found"
    elif players[player_name]['status'] != 'idle':
        return f"INVITE:N:player not available"
    response = request_invite(players[player_name]['ip'], players[player_name]['port'], user_name, player_name, room_name, game_rooms[room_name]['game_type'])
    return response

def room_chat(user_name, room_name, message):
    if room_name not in game_rooms:
        return f"ROOM_CHAT:N:no such room"
    host = game_rooms[room_name]['host']
    client = game_rooms[room_name]['client']
    if user_name == host:
        request_room_chat(players[client]['ip'], players[client]['port'], user_name, room_name, message)
    elif user_name == client:
        request_room_chat(players[host]['ip'], players[host]['port'], user_name, room_name, message)
    return f"ROOM_CHAT:Y:{room_name}:{message}"

def game_start(room_name, user_name): # host starts game
    if room_name not in game_rooms:
        return f"GAME_START:N:{room_name}"
    host = game_rooms[room_name]['host']
    client = game_rooms[room_name]['client']
    game_type = game_rooms[room_name]['game_type'] 
    if host == user_name:
        if game_rooms[room_name]['status'] != 'full':
            return f"GAME_START:N:room not full"
        game_rooms[room_name]['status'] = 'in_game'
        request_room_broadcast(players[client]['ip'], players[client]['port'], user_name, "GAME_START", room_name)
        return f"GAME_START:Y:{game_type}:{room_name}"
    elif client == user_name:
        if game_rooms[room_name]['status'] != 'in_game':
            return f"GAME_START:N:room not in game"
        return f"GAME_START:Y:{game_type}:{room_name}"

def game_end(room_name): # host ends game
    if room_name not in game_rooms:
        return f"GAME_END:N:{room_name}"
    host = game_rooms[room_name]['host']
    client = game_rooms[room_name]['client']
    players[host]['status'] = 'in_room'
    players[client]['status'] = 'in_room'
    game_rooms[room_name]['status'] = 'full'
    return f"GAME_END:Y:{room_name}"

def broadcast(user_name, action):
    for player in players:
        if player != user_name and players[player]['status'] == 'idle':
            request_broadcast(players[player]['ip'], players[player]['port'], user_name, action)

def game_ip_port(room_name, game_ip, game_port):
    if room_name in game_rooms:
        return request_ip_port(players[game_rooms[room_name]['client']]['ip'], players[game_rooms[room_name]['client']]['port'], room_name, game_ip, game_port)
    return f"GAME_IP_PORT:N:{room_name}:{game_ip}:{game_port}"

def all_game_list(user_name=None):
    if not game_list:
        return "GAME_LIST:NO GAMES"
    if user_name:
        game = [
            f"{game_list[game]['game_type']}, {game_list[game]['user_name']}, {game_list[game]['introduction']}"
            for game in game_list if game_list[game]['user_name'] == user_name
        ]
        if not game:
            game_str = "NO GAMES"
        else:
            game_str = ';'.join(game)
    else:
        game = [
            f"{game_list[game]['game_type']}, {game_list[game]['user_name']}, {game_list[game]['introduction']}"
            for game in game_list
        ]
        if not game:
            game_str = "NO GAMES"
        else :
            game_str = ';'.join(game)
    return f"GAME_LIST:{game_str}"

####################################################
# CSV: truncate -s 0 file.csv                      #
####################################################
def save_players_to_csv():
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["user_name", "password"])
        for user, data in players.items():
            writer.writerow([
                data['user_name'], data['password']
            ])

def load_players_from_csv():
    if not os.path.exists(CSV_FILE):
        print("[DEBUG] No CSV file found.")
        return
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            players[row['user_name']] = {
                'user_name': row['user_name'],
                'password': row['password'],
                'status': 'offline',
                'ip': None,
                'port': None,
            }

def save_games_to_csv():
    with open(GAME_CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["game_type", "user_name", "introduction"])
        for room, data in game_list.items():
            writer.writerow([
                data['game_type'], data['user_name'], data['introduction']
            ])

def load_games_from_csv():
    if not os.path.exists(GAME_CSV_FILE):
        print("[DEBUG] No CSV file found.")
        return
    with open(GAME_CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            game_list[row['game_type']] = {
                'game_type': row['game_type'],
                'user_name': row['user_name'],
                'introduction': row['introduction']
            }

####################################################
# FILE TRANSFER                                    #
####################################################
def upload(status, user_name, game_type, data=""):
    file_name = f"{game_type}.py"
    file_path = os.path.join("game", file_name)
    if status == "START":
        if game_type in game_list and game_list[game_type]['user_name'] != user_name:
            return f"UPLOAD:N:you are not the owner of {game_type}"
        game_list[game_type] = {
            'game_type': game_type,
            'user_name': user_name,
            'introduction': data,
        }
        if os.path.exists(file_path):
            os.remove(file_path)
        with open(file_path, "wb") as f:
            f.write("".encode('utf-8'))
        return f"UPLOAD:Y:{user_name}:{game_type}"
    elif status == "CONTINUE":
        with open(file_path, "ab") as f:
            f.write(data.encode('utf-8'))
        return f"UPLOAD:Y:{game_type}:CONTINUE"
    elif status == "END":
        save_games_to_csv()
        return f"UPLOAD:Y:{game_type}:END"
    return f"UPLOAD:N:INVALID_STATUS"

def download(user_name, room_name):
    if room_name not in game_rooms:
        return f"DOWNLOAD:N:room not found"
    game_type = game_rooms[room_name]['game_type']
    request_download(players[user_name]['ip'], players[user_name]['port'], user_name, game_type)
    return f"DOWNLOAD:Y:{user_name}:{room_name}"

# Main server loop
def start_server():
    load_players_from_csv()
    load_games_from_csv()
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(("", PORT))
        server_socket.listen()
        print("Server started. Ready to accept connections...")
        while True:
            client_socket, addr = server_socket.accept()
            threading.Thread(target=handle_client, args=(client_socket, addr)).start()
    except Exception as e:
        print(f"Failed to start server: {e}")

if __name__ == "__main__":
    start_server()