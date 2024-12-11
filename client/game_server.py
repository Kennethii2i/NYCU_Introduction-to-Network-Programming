import socket
import random
import importlib.util
import os

class GameServer:
    def __init__(self, port, game_module):
        self.port = int(port)
        self.game = self.load_game_module(game_module)
        self.server_socket = None
        
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.bind(("", self.port))
        except OSError as e:
            print(f"Error creating server socket: {e}")
    
    def load_game_module(self, game_module):
        try:
            module_path = os.path.join("download", f"{game_module}.py")
            if not os.path.exists(module_path):
                raise FileNotFoundError(f"Module {game_module} not found in 'game' folder.")
            spec = importlib.util.spec_from_file_location(game_module, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not hasattr(module, "Server"):
                raise AttributeError(f"{game_module} does not have Server class")
            return module.Server()
        except Exception as e:
            print(f"Game Load Error: {e}")
            raise
    
    def handle_request(self, request):
        return self.game.handle_request(request)

    def start_server(self):
        try:
            self.server_socket.listen()
            client_socket, client_address = self.server_socket.accept()
        except Exception as e:
            print(f"Error accepting connection: {e}")
            return
        
        while True:
            try:
                request = client_socket.recv(1024).decode('utf-8')
                response, switch = self.handle_request(request)
                if switch:
                    response = self.game.server_turn(response)
                if response is None:
                    break
                client_socket.send(response.encode('utf-8'))
                if response.startswith("GAME_END"):
                    break
            except Exception as e:
                print(f"Error in game loop: {e}")
                break
        self.server_socket.close()
