''' CLI User Interface for Tic-Tac-Toe game.
    Use as the main program, no reusable functions'''

import oxo_logic

menu = ["Start new game",
        "Resume saved game",
        "Display help",
        "Quit"]

def getMenuChoice(aMenu):
    ''' getMenuChoice(aMenu) -> int
        Displays a numbered menu and loops until a valid number is selected '''
    if not aMenu:
        raise ValueError('No menu content')
    while True:
        for index, item in enumerate(aMenu, start=1):
            print(index, "\t", item)
        try:
            choice = int(input("\nChoose a menu option: "))
            if 1 <= choice <= len(aMenu):
                return choice
            else:
                print("Choose a number between 1 and", len(aMenu))
        except ValueError:
            print("Choose the number of a menu option")

def startGame():
    return oxo_logic.Game.new_game()

def resumeGame():
    return oxo_logic.Game.restore_game()

def displayHelp():
    print('''
    Start new game:     Starts a new game of Tic-Tac-Toe.
    Resume saved game:  Restores the last saved game and resumes play.
    Display help:       Shows this page.
    Quit:               Quits the application.
    ''')

def quit():
    print("Goodbye...")
    raise SystemExit

def executeChoice(choice):
    ''' executeChoice(int) -> None
        Execute whichever option the user selected. '''
    dispatch = [startGame, resumeGame, displayHelp, quit]
    game = dispatch[choice - 1]()
    if isinstance(game, oxo_logic.Game):
        playGame(game)

def printGame(game):
    display = '''
      1 | 2 | 3      {} | {} | {}
     ----------     -----------
      4 | 5 | 6      {} | {} | {}
      ---------     -----------
      7 | 8 | 9      {} | {} | {}
      '''
    print(display.format(*game.board))

def playGame(game):
    result = ""
    while not result:
        printGame(game)
        choice = input("Cell[1-9 or q to quit]: ")
        if choice.lower()[0] == 'q':
            save = input("Save game before quitting? [y/n]: ")
            if save.lower()[0] == 'y':
                game.save_game()
            quit()
        else:
            try:
                cell = int(choice) - 1
                if not (0 <= cell <= 8):
                    raise ValueError
            except ValueError:
                print("Choose a number between 1 and 9 or 'q' to quit")
                continue

            try:
                result = game.user_move(cell)
            except ValueError:
                print("Choose an empty cell")
                continue

            if not result:
                result = game.computer_move()

            if not result:
                continue
            elif result == 'D':
                printGame(game)
                print("It's a draw")
            else:
                printGame(game)
                print("Winner is", result, '\n')

def main():
    while True:
        choice = getMenuChoice(menu)
        executeChoice(choice)

if __name__ == "__main__":
    main()
