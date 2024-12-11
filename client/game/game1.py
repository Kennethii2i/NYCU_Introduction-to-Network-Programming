import random

class Server:
    def __init__(self):
        self.deck = self.create_deck()
        random.shuffle(self.deck)
        self.server_hand = []
        self.client_hand = []
        self.discard_pile = []
        self.id = "1 "

    def create_deck(self):
        suits = ['H', 'D', 'S', 'C']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        return [f"{suit}{rank}" for suit in suits for rank in ranks]

    def deal_cards(self):
        self.server_hand = [self.deck.pop() for _ in range(10)]
        self.client_hand = [self.deck.pop() for _ in range(10)]
        self.discard_pile.append(self.deck.pop())
        print("Discard pile starts with:", self.discard_pile[-1])
    
    def print_hand(self, hand=None):
        print("------------")
        print("In suit order:")
        if hand is None:
            self.hand.sort()
            print("Your hand:")
            print(" ".join([f"{i:2}" for i in range(len(self.hand))]))
            print(" ".join(self.hand))
        else:
            hand.sort()
            print("Opponent hand:")
            print(" ".join([f"{i:2}" for i in range(len(hand))]))
            print(" ".join(self.hand))
        print("------------")
        print("In rank order:")
        if hand is None:
            self.hand.sort(key=lambda x: x[1:])
            print("Your hand:")
            print(" ".join([f"{i:2}" for i in range(len(self.hand))]))
            print(" ".join(self.hand))
        else:
            hand.sort(key=lambda x: x[1:])
            print("Opponent hand:")
            print(" ".join([f"{i:2}" for i in range(len(hand))]))
            print(" ".join(self.hand))
    
    def handle_request(self, request):
        id, request = request.split(' ', 1)
        if request == "START": # start game
            self.deal_cards()
            server_hand = ",".join(self.server_hand)
            return f"START {server_hand}", True
        elif request == "DRAW_DISCARD": 
            if not self.deck:
                return "NO_MORE", False
            card = self.discard_pile.pop()
            if id == "1":
                self.server_hand.append(card)
            elif id == "2":
                self.client_hand.append(card)
            else:
                print("Invalid request")
            server_hand = ",".join(self.server_hand)
            client_hand = ",".join(self.client_hand)
            return f"# {card} {client_hand if id == '2' else server_hand}", False
        elif request == "DRAW_DECK":
            if not self.deck:
                return "NO_MORE", False
            card = self.deck.pop()
            if id == "1":
                self.server_hand.append(card)
            elif id == "2":
                self.client_hand.append(card)
            else:
                print("Invalid request")
            server_hand = ",".join(self.server_hand)
            client_hand = ",".join(self.client_hand)
            return f"# {card} {client_hand if id == '2' else server_hand}", False
        elif request.startswith("DISCARD"):
            _, card = request.split()
            if id == "1":
                self.server_hand.remove(card)
            elif id == "2":
                self.client_hand.remove(card)
            else:
                print("Invalid request")
            self.discard_pile.append(card)
            server_hand = ",".join(self.server_hand)
            client_hand = ",".join(self.client_hand)
            return f"! {client_hand if id == '2' else server_hand}", False
        elif request.startswith("STOP"):
            parts = request.split()
            is_stop = parts[1]
            score = parts[2]
            server_hand = ",".join(self.server_hand)
            client_hand = ",".join(self.client_hand)
            if is_stop == "n":
                return f"? {self.discard_pile[-1]} {client_hand if id == '1' else server_hand}", True
            elif is_stop == "y":
                return f"TERMINATE {score} {client_hand if id == '1' else server_hand}", True
            else:
                print("Invalid request")
        elif request.startswith("GAME_END"):
            return request + f" {client_hand if id == '1' else server_hand}", True
    
    def server_turn(self, response):
        switch = False
        if response.startswith("START"):
            parts = response.split()
            self.hand = parts[1].split(",")
            self.print_hand()
            while True:
                request = input("Draw from discard or deck? [1 or 2]: ")
                if request == "1":
                    response, switch = self.handle_request(self.id + "DRAW_DISCARD")
                    break
                elif request == "2":
                    response, switch = self.handle_request(self.id + "DRAW_DECK")
                    break
                else:
                    print("Invalid input. Try again.")
                    continue
        
        if switch:
            return response
        
        if response.startswith("NO_MORE"): # no more cards in the deck
            print("No more cards in the deck.")
            score = self.check_score()
            print(f"Your score: {score}")
            response, switch = self.handle_request(self.id + f"STOP y {score}")
        
        if switch:
            return response
        
        if response.startswith("?"):
            parts = response.split()
            discarded_card = parts[1]
            self.hand = parts[2].split(",")
            self.print_hand()
            print(f"Discarded card: {discarded_card}")
            while True:
                request = input("Draw from discard or deck? [1 or 2]: ")
                if request == "1":
                    response, switch = self.handle_request(self.id + "DRAW_DISCARD")
                    break
                elif request == "2":
                    response, switch = self.handle_request(self.id + "DRAW_DECK")
                    break
                else:
                    print("Invalid input. Try again.")
                    continue
        
        if switch:
            return response
        
        if response.startswith("#"):
            parts = response.split()
            drawn_card = parts[1]
            self.hand = parts[2].split(",")
            self.print_hand()
            print(f"Drawn card: {drawn_card}")
            while True:
                request = input("Discard a card (e.g. H8): ")
                if request in self.hand:
                    response, switch = self.handle_request(self.id + f"DISCARD {request}")
                    break
                print("Invalid input. Try again.")
        
        if switch:
            return response

        if response.startswith("!"):
            self.hand = response.split()[1].split(",")
            self.print_hand()
            while True:
                request = input("Do you want to stop? [y/n]: ")
                if request.lower() == "y":
                    score = self.check_score()
                    if score > 10:
                        print("You cannot stop with a score greater than 10.")
                        response, switch = self.handle_request(self.id + "STOP n 0")
                    else:
                        response, switch = self.handle_request(self.id + f"STOP y {score}")
                    break
                elif request.lower() == "n":
                    response, switch = self.handle_request(self.id + "STOP n 0")
                    break
                else:
                    print("Invalid input. Try again.")
            
        if switch:
            return response
        
        if response.startswith("TERMINATE"):
            print("Opponent stopped the game.")
            parts = response.split()
            opponent_score = parts[1]
            opponent_hand = parts[2].split(",")
            print(f"Opponent score: {opponent_score}")
            self.print_hand(opponent_hand)
            score = self.check_score()
            print(f"Your score: {score}")
            if score > opponent_score:
                print("GAME END: You win!")
                response, switch = self.handle_request(self.id + f"GAME_END {score} {opponent_score}")
            elif score < opponent_score:
                print("GAME END: You lose!")
                response, switch = self.handle_request(self.id + f"GAME_END {score} {opponent_score}")
            else:
                print("GAME END: Tie game.")
                response, switch = self.handle_request(self.id + f"GAME_END {score} {opponent_score}")
        
        if switch:
            return response
        
        if response.startswith("GAME_END"):
            parts = response.split()
            opponent_score = parts[1]
            score = parts[2]
            opponent_hand = parts[3].split(",")
            self.print_hand(opponent_hand)
            if score > opponent_score:
                print("GAME END: You win!")
            elif score < opponent_score:
                print("GAME END: You lose!")
            else:
                print("GAME END: Tie game.")
            return None
        
        if switch:
            return response

    def combination(self, selected_cards):
        print(f"Checking cards: {selected_cards}")
        values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 1}
        ranks = [card[1:] for card in selected_cards]
        suits = [card[0] for card in selected_cards]
        if len(selected_cards) < 3:
            return sum(values[rank] for rank in ranks)
        if len(set(ranks)) == 1:
            return 0
        if len(set(suits)) == 1:
            sorted_ranks = sorted([int(rank) if rank.isdigit() else {'J': 11, 'Q': 12, 'K': 13, 'A': 1}[rank] for rank in ranks])
            if all(sorted_ranks[i] + 1 == sorted_ranks[i + 1] for i in range(len(sorted_ranks) - 1)):
                return 0
        return sum(values[rank] for rank in ranks)
    
    def check_score(self):
        self.print_hand()
        index_string = input("Enter the index of the cards you want to select(e.g. 012 345 678 9): ")
        index_groups = index_string.split()
        total_score = 0
        for group in index_groups:
            selected_cards = [self.hand[int(i)] for i in group]
            total_score += self.combination(selected_cards)
            print(f"Score: {total_score}")
        return total_score

class Client:
    def __init__(self):
        self.hand = []
        self.id = "2 "
    
    def client_turn(self, response):
        if response is None:
            return self.id + "START"
        
        if response.startswith("?"): # example: "? DISCARDED_CARD (YOUR_HAND)"
            parts = response.split(" ")
            discarded_card = parts[1]
            self.hand = parts[2].split(",")
            self.print_hand()
            print(f"Discarded card: {discarded_card}")
            while True:
                request = input("Draw from discard or deck? [1 or 2]: ")
                if request == "1":
                    return self.id + "DRAW_DISCARD"
                    break
                elif request == "2":
                    return self.id + "DRAW_DECK"
                    break
                else:
                    print("Invalid input. Try again.")
        
        elif response.startswith("NO_MORE"):
            print("No more cards in deck.")
            score = self.check_score()
            print(f"Your score: {score}")
            return self.id + f"STOP n {score}"
            
        elif response.startswith("#"): # example: "# (DRAWN_CARD) (YOUR_HAND)"
            parts = response.split(" ")
            drawn_card = parts[1]
            self.hand = parts[2].split(",")
            self.print_hand()
            print(f"Drawn card: {drawn_card}")
            while True:
                request = input("Discard a card (e.g. H8): ")
                if request in self.hand:
                    return self.id + f"DISCARD {request}"
                print("Invalid input. Try again.")
        
        elif response.startswith("!"): # example: "! (YOUR HAND)"
            self.hand = response.split(" ")[1].split(",")
            self.print_hand()
            while True:
                request = input("Do you want to stop? [y/n]: ")
                if request.lower() == "y":
                    score = self.check_score()
                    if score > 10:
                        print("You cannot stop with a score greater than 10.")
                        return self.id + "STOP n 0"
                    return self.id + f"STOP y {score}"
                elif request.lower() == "n":
                    return self.id + "STOP n 0"
                else:
                    print("Invalid input. Try again.")
        
        elif response.startswith("TERMINATE"): # example: "TERMINATE (OPPONENT_SCORE) (OPPONENT_HAND)"
            print("Opponent stopped the game.") 
            parts = response.split(" ")
            opponent_score = parts[1]
            opponent_hand = parts[2].split(",")
            print(f"Opponent score: {opponent_score}")
            self.print_hand(opponent_hand)
            score = self.check_score()
            print(f"Your score: {score}")
            if score > opponent_score:
                print("GAME END: You win!")
                return self.id + f"GAME_END {score} {opponent_score}"
            elif score < opponent_score:
                print("GAME END: You lose!")
                return self.id + f"GAME_END {score} {opponent_score}"
            else:
                print("GAME END: Tie game.")
                return self.id + f"GAME_END {score} {opponent_score}"
            
        elif response.startswith("GAME_END"): # example: "GAME_END (OPPONENT_SCORE) (OPPONENT_HAND)"
            parts = response.split(" ")
            opponent_score = parts[1]
            score = parts[2]
            opponent_hand = parts[3].split(",")
            self.print_hand(opponent_hand)
            if score > opponent_score:
                print("GAME END: You win!")
            elif score < opponent_score:
                print("GAME END: You lose!")
            else:
                print("GAME END: Tie game.")
            return None

    def print_hand(self, hand=None):
        print("------------")
        print("In suit order:")
        if hand is None:
            self.hand.sort()
            print("Your hand:")
            print(" ".join([f"{i:2}" for i in range(len(self.hand))]))
            print(" ".join(self.hand))
        else:
            hand.sort()
            print("Opponent hand:")
            print(" ".join([f"{i:2}" for i in range(len(hand))]))
            print(" ".join(self.hand))
        print("------------")
        print("In rank order:")
        if hand is None:
            self.hand.sort(key=lambda x: x[1:])
            print("Your hand:")
            print(" ".join([f"{i:2}" for i in range(len(self.hand))]))
            print(" ".join(self.hand))
        else:
            hand.sort(key=lambda x: x[1:])
            print("Opponent hand:")
            print(" ".join([f"{i:2}" for i in range(len(hand))]))
            print(" ".join(self.hand))
    
    def combination(self, selected_cards):
        print(f"Checking cards: {selected_cards}")
        values = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 10, 'Q': 10, 'K': 10, 'A': 1}
        ranks = [card[1:] for card in selected_cards]
        suits = [card[0] for card in selected_cards]
        
        if len(selected_cards) < 3:
            return sum(values[rank] for rank in ranks)
        
        if len(set(ranks)) == 1:
            return 0
        
        if len(set(suits)) == 1:
            sorted_ranks = sorted([int(rank) if rank.isdigit() else {'J': 11, 'Q': 12, 'K': 13, 'A': 1}[rank] for rank in ranks])
            if all(sorted_ranks[i] + 1 == sorted_ranks[i + 1] for i in range(len(sorted_ranks) - 1)):
                return 0
        
        return sum(values[rank] for rank in ranks)
    
    def check_score(self):
        self.print_hand()
        index_string = input("Enter the index of the cards you want to select(e.g. 012 345 678 9): ")
        index_groups = index_string.split()
        total_score = 0
        for group in index_groups:
            selected_cards = [self.hand[int(i)] for i in group]
            total_score += self.combination(selected_cards)
            print(f"Score: {total_score}")
        return total_score