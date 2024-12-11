import socket
import time
import importlib.util
import os

class GameClient:
    def __init__(self, host, port, game_module):
        try:
            time.sleep(1)
            self.host = host
            self.port = int(port)
            self.game = self.load_game_module(game_module)
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
        except Exception as e:
            print(f"Error1: {e}")
            self.client_socket = None
    
    def load_game_module(self, game_module):
        try:
            module_path = os.path.join("download", f"{game_module}.py")
            if not os.path.exists(module_path):
                raise FileNotFoundError(f"Module {game_module} not found in 'game' folder.")
            spec = importlib.util.spec_from_file_location(game_module, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not hasattr(module, "Client"):
                raise AttributeError(f"{game_module} does not have a Client class.")
            return module.Client()
        except Exception as e:
            print(f"Game Load Error: {e}")
            raise
    
    def start_client(self):
        if not self.client_socket:
            print("Client socket is not connected.")
            returns
        try:
            self.client_socket.send("2 START".encode('utf-8'))
            print("Game started.")
            while True:
                response = self.client_socket.recv(1024).decode('utf-8')
                request = self.game.client_turn(response)
                if request is None: # receive "GAME_END" from server
                    break
                self.client_socket.send(request.encode('utf-8'))
                if request.startswith("GAME_END"): 
                    break
        except Exception as e:
            print(f"Error2: {e}")
        self.client_socket.close()
