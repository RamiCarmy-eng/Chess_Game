import chess
import random


def print_board(board):
    """מדפיס את הלוח בצורה קריאה"""
    print("\n")
    print(board)
    print("\n")


def get_player_move(board):
    """מבקש מהשחקן מהלך ובודק שהוא חוקי"""
    while True:
        try:
            move_str = input("הכנס את המהלך שלך (למשל e2e4): ")
            move = chess.Move.from_uci(move_str)
            if move in board.legal_moves:
                return move
            else:
                print("מהלך לא חוקי, נסה שוב.")
        except ValueError:
            print("פורמט לא תקין. השתמש בסימון כמו e2e4.")


def play_game():
    board = chess.Board()
    print("ברוכים הבאים לאימון השחמט! אתה משחק בלבן.")

    while not board.is_game_over():
        print_board(board)

        # תור השחקן (לבן)
        move = get_player_move(board)
        board.push(move)

        if board.is_game_over():
            break

        # תור המחשב (שחור) - כרגע בוחר מהלך אקראי חוקי
        print("המחשב חושב...")
        computer_move = random.choice(list(board.legal_moves))
        board.push(computer_move)
        print(f"המחשב שיחק: {computer_move}")

    print_board(board)
    print("המשחק נגמר!")
    print(f"תוצאה: {board.result()}")


if __name__ == "__main__":
    play_game()