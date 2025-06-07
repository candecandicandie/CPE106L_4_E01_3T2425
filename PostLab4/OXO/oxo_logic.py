# oxo_logic.py
import random
import oxo_data

class Game:
    WIN_COMBINATIONS = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6)
    ]

    def __init__(self):
        self.board = [" "] * 9

    @classmethod
    def new_game(cls):
        return cls()

    def save_game(self):
        oxo_data.saveGame(self.board)

    @classmethod
    def restore_game(cls):
        try:
            board = oxo_data.restoreGame()
            if len(board) == 9:
                game = cls()
                game.board = board
                return game
            else:
                return cls.new_game()
        except IOError:
            return cls.new_game()

    def _generate_move(self):
        options = [i for i, v in enumerate(self.board) if v == " "]
        return random.choice(options) if options else -1

    def _is_winning_move(self):
        for a, b, c in self.WIN_COMBINATIONS:
            line = self.board[a] + self.board[b] + self.board[c]
            if line == 'XXX' or line == 'OOO':
                return True
        return False

    def user_move(self, cell):
        if self.board[cell] != " ":
            raise ValueError("Invalid cell")
        self.board[cell] = "X"
        return 'X' if self._is_winning_move() else ""

    def computer_move(self):
        cell = self._generate_move()
        if cell == -1:
            return 'D'
        self.board[cell] = "O"
        return 'O' if self._is_winning_move() else ""
