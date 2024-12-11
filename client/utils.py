import socket
import re
import os
import config

def get_global_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

def welcome():
    print("\n=== Welcome ===")

def invalid_choice():
    print("Invalid choice. Please try again.")

def handle_response(response):
    command, status, *args = response.split(":")
    if status == "Y":
        return True
    elif status == "N":
        print(f"Error: {args[0]}")
        return False

def lobby_menu():
    print("\n" + "=" * 30)
    print("Lobby Menu")
    print("Please choose an action:")
    print("1. Create Room")
    print("2. Join Room")
    print("3. Logout")
    print("4. Refresh")
    print("5. Invite Management")
    print("6. All Game List")
    print("7. Game Development")
    while True:
        choice = input("Select an option: ")
        if choice in ["1", "2", "3", "4", "5", "6", "7"]:
            break
        invalid_choice()
    return choice

def main_menu():
    print("\n" + "=" * 30)
    print("Main Menu")
    print("Please choose an action:")
    print("1. Register")
    print("2. Login")
    while True:
        choice = input("Select an option: ")
        if choice in ["1", "2", None]:
            break
        invalid_choice()
    return choice

def invite_menu():
    print("\n=== Invite Management ===")
    print("Please choose an action:")
    print("1. Refresh")
    print("2. Accept Invite")
    print("3. Back to Lobby")
    while True:
        choice = input("Select an option: ")
        if choice in ["1", "2", "3"]:
            break
    return choice

def accept_invite_input():
    player_name = input("Enter room name: ")
    return player_name

def developer_menu():
    print("\n=== Developer Menu ===")
    print("Please choose an action:")
    print("1. List your games")
    print("2. Publish the game")
    print("3. Back to Lobby")
    while True:
        choice = input("Select an option: ")
        if choice in ["1", "2", "3"]:
            break
        invalid_choice()
    return choice

def register_input():
    print("\n=== Register New User ===")
    user_name = input("Enter username: ")
    password = input("Enter password: ")
    return user_name, password

def login_input():
    print("\n=== Login ===")
    user_name = input("Enter username: ")
    password = input("Enter password: ")
    return user_name, password

def display(response):
    command, data = response.split(":")
    online_players, rooms = data.split('\n')[:2]
    print("\n=== Online Players ===")
    print("{:<15} {:<10}".format("Player", "Status"))
    print("-" * 25)
    if "NO ONLINE PLAYERS" in online_players:
        print(online_players)
    else:
        players = online_players.split(", ")
        for player in players:
            name, status = player.split("(")
            status = status.strip(")")
            print("{:<15} {:<10}".format(name, status))
    
    print("\n=== Public Game Rooms ===")
    print("{:<20} {:<15} {:<10} {:<10}".format("Room Name", "Host", "Status", "Game Type"))
    print("-" * 60)
    if "NO PUBLIC ROOMS" in rooms:
        print(rooms)
    else:
        rooms_list = rooms.split(",")
        for room in rooms_list:
            # Extract room details using regex
            room_details = re.search(r"(.*) \((.*)\) - (.*) - (.*)", room)
            if room_details:
                room_name = room_details.group(1)
                host = room_details.group(2)
                status = room_details.group(3)
                game_type = room_details.group(4)
                print("{:<20} {:<15} {:<10} {:<10}".format(room_name, host, status, game_type))

def create_room_input():
    print("\n=== Create Room ===")
    room_name = input("Enter room name: ")
    while True:
        room_type = input("Enter room type public or private [1 or 2]: ")
        if room_type == "1":
            room_type = "public"
            break
        elif room_type == "2":
            room_type = "private"
            break
        invalid_choice()
    game_type = input("Enter game type: ")
    return room_name, room_type, game_type

def invite_input():
    print("\n=== Invite Player ===")
    player_name = input("Enter player name: ")
    return player_name

def join_room_input():
    print("\n=== Join Room ===")
    room_name = input("Enter room name: ")
    return room_name

def get_game_info(response):
    command, symbol, game_type, room_name = response.split(":")
    return game_type, room_name

def invite_recv(player_name, room_name, game_type):
    print("\n=== Invite Received ===")
    print(f"You have received an invite from {player_name} to join room {room_name} for a {game_type} game.")

def broadcast(user_name, action):
    print("\n=== Broadcast ===")
    print(f"User: {user_name}")
    print(f"Action: {action}")
    print("=================")

def room_chat_recv(player_name, message):
    print("\n=== Room Chat ===")
    print(f"User: {player_name}")
    print(f"Message: {message}")
    print("=================")

def room_broadcast(player_name, action, room_name):
    if config.ROOM["name"] == room_name:
        print("\n=== Room Broadcast ===")
        print(f"User: {player_name}")
        print(f"Action: {action}")
        if action == "GAME_START":
            print("Host has started the game.")
            print("Please press 1 to enter the game.")
        print("======================")

def room_menu():
    print("\n=== Room ===")
    print("Please choose an action:")
    print("1. Start Game")
    print("2. Leave Room")
    print("3. Invite Player")
    print("4. Room Chat")
    while True:
        choice = input("Select an option: ")
        if choice in ["1", "2", "3", "4"]:
            break
        invalid_choice()
    return choice

def get_room_info(response):
    command, symbol, game_type, room_name = response.split(":")
    return game_type

def invite_list():
    print("\n=== Invite List ===")
    print("{:<15} {:<15} {:<10}".format("Room Name", "Player Name", "Game Type"))
    print("-" * 45)
    if not config.INVITE_LIST:
        print("NO INVITES")
    else:
        for player, details in config.INVITE_LIST.items():
            print("{:<15} {:<15} {:<10}".format(
                details["room_name"], 
                details["player_name"], 
                details["game_type"]
            ))

def game_publish():
    game_type = input("Please enter the game name to publish (e.g.abc.py->abc is game name): ")
    file_path = os.path.join("game", game_type + ".py")
    if not os.path.isfile(file_path):
        print("Game not found.")
        return None, None
    introduction = input("Please enter the introduction of the game: ")
    if introduction == "":
        print("Introduction cannot be empty.")
        return None, None
    return game_type, introduction

def all_game_list(response):
    command, data = response.split(":")
    print("\n=== Game List ===")
    print("{:<15} {:<20} {:<40}".format("Game Type", "User Name", "Introduction"))
    print("-" * 50)
    if "NO GAMES" in data:
        print(data)
    else:
        games = data.split(";")
        for game in games:
            game_type, user_name, introduction = game.split(",")
            print("{:<15} {:<20} {:<40}".format(game_type, user_name, introduction))

def room_chat_input():
    message = input("Enter message: ")
    return message