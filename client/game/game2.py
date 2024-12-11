import random

class Server:
    def __init__(self):
        self.board = [" " for _ in range(9)]
        self.id = "O"
        self.opponent_id = "X"
    
    def handle_request(self, request):
        if request == "2 START":
            if random.choice([True, False]):
                return "X", True
            return "O", True
        elif request.startswith("MOVE"):
            _, move = request.split()
            if move == "NONE":
                return "POS NONE", True
            return "POS " + move, True
        elif request.startswith("GAME_END"):
            return request, True
    
    def server_turn(self, response):
        switch = False
        
        if response == self.id:
            print("You move first.")
            self.print_board()
            pos = self.move()
            response, switch = self.handle_request(f"MOVE {pos}")
        elif response == self.opponent_id:
            print("Opponent's move first.")
            response, switch = self.handle_request("MOVE NONE")
        
        if switch:
            return response
        
        if response.startswith("POS"):
            print("Your turn.")
            _, move = response.split()
            if move == "NONE":
                print("You move first.")
                self.print_board()
                pos = self.move()
                response, switch = self.handle_request(f"MOVE {pos}")
            else:
                self.board[int(move)] = self.opponent_id
                self.print_board()
                if self.is_full():
                    print("Tie game.")
                    response, switch = self.handle_request("GAME_END TIE")
                else:
                    pos = self.move()
                    if self.is_win():
                        print("You win!")
                        response, switch = self.handle_request(f"GAME_END {pos}")
                    else:
                        response, switch = self.handle_request(f"MOVE {pos}")
        
        if switch:
            return response
        
        if response.startswith("GAME_END"):
            parts = response.split()
            if parts[1] == "TIE":
                self.print_board()
                print("Tie game.")
            else:
                self.board[int(parts[1])] = self.opponent_id
                self.print_board()
                print("You lose!")
            return None
    
    def is_valid_move(self, move):
        if 0 <= move < 9 and self.board[move] == " ":
            return True
        return False
    
    def is_win(self):
        for i in range(3):
            if self.board[i] == self.board[i + 3] == self.board[i + 6] != " ":
                return True
            if self.board[3 * i] == self.board[3 * i + 1] == self.board[3 * i + 2] != " ":
                return True, self.board[3 * i]
        if self.board[0] == self.board[4] == self.board[8] != " ":
            return True
        if self.board[2] == self.board[4] == self.board[6] != " ":
            return True
        return False
    
    def is_full(self):
        return all(cell != " " for cell in self.board)
    
    def print_board(self):
        print("------------")
        for i in range(3):
            print(f"| {self.board[3 * i]} | {self.board[3 * i + 1]} | {self.board[3 * i + 2]} |")
            print("------------")
    
    def move(self):
        while True:
            move = input("Enter your move (0-8): ")
            if self.is_valid_move(int(move)):
                self.board[int(move)] = self.id
                break
            print("Invalid move. Try again.")
        self.print_board()
        return move

class Client:
    def __init__(self):
        self.board = [" " for _ in range(9)]
        self.id = "X"
        self.opponent_id = "O"
    
    def client_turn(self, response):
        if response.startswith("POS"):
            print("Your turn.")
            _, move = response.split()
            if move == "NONE":
                print("You move first.")
                self.print_board()
                move = self.move()
                return f"MOVE {move}"
            else:
                self.board[int(move)] = self.opponent_id
                self.print_board()
                if self.is_full():
                    print("GAME END: Tie game.")
                    return f"GAME_END TIE"
                move = self.move()
                if self.is_win():
                    print("GAME END: You win!")
                    return f"GAME_END {move}"
                return f"MOVE {move}"
        elif response.startswith("GAME_END"):
            parts = response.split()
            if parts[1] == "TIE":
                self.print_board()
                print("Tie game.")
            else:
                self.board[int(parts[1])] = self.opponent_id
                self.print_board()
                print("You lose!")
            return None

    def is_valid_move(self, move):
        if 0 <= move < 9 and self.board[move] == " ":
            return True
        return False
    
    def is_win(self):
        for i in range(3):
            if self.board[i] == self.board[i + 3] == self.board[i + 6] != " ":
                return True
            if self.board[3 * i] == self.board[3 * i + 1] == self.board[3 * i + 2] != " ":
                return True, self.board[3 * i]
        if self.board[0] == self.board[4] == self.board[8] != " ":
            return True
        if self.board[2] == self.board[4] == self.board[6] != " ":
            return True
        return False
    
    def is_full(self):
        return all(cell != " " for cell in self.board)
    
    def print_board(self):
        print("------------")
        for i in range(3):
            print(f"| {self.board[3 * i]} | {self.board[3 * i + 1]} | {self.board[3 * i + 2]} |")
            print("------------")
    
    def move(self):
        while True:
            move = input("Enter your move (0-8): ")
            if self.is_valid_move(int(move)):
                self.board[int(move)] = self.id
                break
            print("Invalid move. Try again.")
        self.print_board()
        return move