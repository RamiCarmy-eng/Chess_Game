import tkinter as tk
from tkinter import messagebox, simpledialog
import chess
import chess.engine
import threading
from pathlib import Path
import tksvg
import pyttsx3
import winsound
import json
import time

# הגדרות נתיבים
PIECES_FOLDER = Path("pieces")
ENGINE_PATH = Path("stockfish/stockfish-windows-x86-64-avx2.exe")
STATS_FILE = "chess_stats.json"


class ChessUltimate:
    def __init__(self, root):
        self.root = root
        self.root.title("♟️ Chess Master Ultimate")
        self.root.geometry("900x950")
        self.root.configure(bg="#1e1e1e")

        # נתונים
        self.stats = self.load_stats()
        self.player_name = self.ask_name()
        self.board = chess.Board()
        self.engine = None
        self.skill_level = 5
        self.square_size = 85
        self.selected_square = None
        self.last_move = None
        self.piece_images = {}

        # שעונים
        self.white_time = 600
        self.black_time = 600
        self.last_tick = time.time()

        # אתחול
        self.speech = pyttsx3.init()
        self.init_engine()
        self.create_ui()
        self.load_piece_images()
        self.update_clock()
        self.root.after(200, self.update_board)

    def load_stats(self):
        if Path(STATS_FILE).exists():
            with open(STATS_FILE, "r") as f: return json.load(f)
        return {"wins": 0, "losses": 0, "draws": 0}

    def save_stats(self):
        with open(STATS_FILE, "w") as f: json.dump(self.stats, f)

    def ask_name(self):
        name = simpledialog.askstring("Welcome", "Please enter your name:", initialvalue="Player 1")
        return name if name else "Player 1"

    def init_engine(self):
        if ENGINE_PATH.exists():
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(str(ENGINE_PATH))
                self.set_difficulty(5)
            except:
                print("Engine failed")

    def set_difficulty(self, level):
        self.skill_level = level
        if self.engine: self.engine.configure({"Skill Level": level})
        self.diff_label.config(text=f"Level: {level}")

    def create_ui(self):
        top_frame = tk.Frame(self.root, bg="#1e1e1e")
        top_frame.pack(fill=tk.X, padx=20, pady=5)

        self.stats_label = tk.Label(top_frame,
                                    text=f"🏆 {self.player_name}: {self.stats['wins']}W | {self.stats['losses']}L",
                                    fg="#f1c40f", bg="#1e1e1e", font=("Arial", 12, "bold"))
        self.stats_label.pack(side=tk.LEFT)

        self.diff_label = tk.Label(top_frame, text="Level: 5", fg="#ecf0f1", bg="#1e1e1e", font=("Arial", 12))
        self.diff_label.pack(side=tk.RIGHT)

        clock_frame = tk.Frame(self.root, bg="#1e1e1e")
        clock_frame.pack(fill=tk.X, padx=50)

        self.w_clock_label = tk.Label(clock_frame, text="10:00", font=("Consolas", 24, "bold"), fg="#2ecc71",
                                      bg="#1e1e1e")
        self.w_clock_label.pack(side=tk.LEFT)

        self.b_clock_label = tk.Label(clock_frame, text="10:00", font=("Consolas", 24, "bold"), fg="#e74c3c",
                                      bg="#1e1e1e")
        self.b_clock_label.pack(side=tk.RIGHT)

        self.canvas = tk.Canvas(self.root, width=self.square_size * 8, height=self.square_size * 8, bg="#2c3e50",
                                highlightthickness=0)
        self.canvas.pack(pady=10)
        self.canvas.bind("<Button-1>", self.on_click)

        bottom_frame = tk.Frame(self.root, bg="#1e1e1e")
        bottom_frame.pack(pady=10)

        tk.Button(bottom_frame, text="↩ Undo Move", command=self.undo_move, bg="#e67e22", fg="white",
                  font=("Arial", 10, "bold")).pack(side=tk.LEFT, padx=10)

        for i, lab in [(0, "Easy"), (10, "Medium"), (20, "Pro")]:
            tk.Button(bottom_frame, text=lab, command=lambda l=i: self.set_difficulty(l), bg="#34495e",
                      fg="white").pack(side=tk.LEFT, padx=5)

    def load_piece_images(self):
        symbols = {'K': 'wk', 'Q': 'wq', 'R': 'wr', 'B': 'wb', 'N': 'wn', 'P': 'wp', 'k': 'bk', 'q': 'bq', 'r': 'br',
                   'b': 'bb', 'n': 'bn', 'p': 'bp'}
        for sym, fname in symbols.items():
            path = PIECES_FOLDER / f"{fname}.svg"
            if path.exists():
                self.piece_images[sym] = tksvg.SvgImage(file=str(path), scaletoheight=int(self.square_size * 0.85))

    def update_clock(self):
        now = time.time()
        dt = now - self.last_tick
        self.last_tick = now

        if not self.board.is_game_over():
            if self.board.turn == chess.WHITE:
                self.white_time = max(0, self.white_time - dt)
            else:
                self.black_time = max(0, self.black_time - dt)

        self.w_clock_label.config(text=self.format_time(self.white_time))
        self.b_clock_label.config(text=self.format_time(self.black_time))
        self.root.after(100, self.update_clock)

    def format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m:02d}:{s:02d}"

    def speak(self, text):
        readable = text.replace('N', 'Knight').replace('B', 'Bishop').replace('R', 'Rook').replace('Q',
                                                                                                   'Queen').replace('K',
                                                                                                                    'King').replace(
            'x', 'takes')

        def _run_speech():
            self.speech.say(readable)
            self.speech.runAndWait()

        threading.Thread(target=_run_speech, daemon=True).start()

    def update_board(self):
        self.canvas.delete("all")
        self.draw_board()
        self.draw_pieces()

    def draw_board(self):
        colors = ["#EBECD0", "#779556"]
        for r in range(8):
            for c in range(8):
                sq = chess.square(c, 7 - r)
                color = colors[(r + c) % 2]
                if self.last_move and sq in [self.last_move.from_square, self.last_move.to_square]:
                    color = "#F7F769"
                if self.selected_square == sq:
                    color = "#66B2FF"
                self.canvas.create_rectangle(c * self.square_size, r * self.square_size, (c + 1) * self.square_size,
                                             (r + 1) * self.square_size, fill=color, outline="#D5D5D5")

    def draw_pieces(self):
        for square in chess.SQUARES:
            piece = self.board.piece_at(square)
            if piece:
                col, row = chess.square_file(square), 7 - chess.square_rank(square)
                x, y = col * self.square_size + self.square_size // 2, row * self.square_size + self.square_size // 2
                self.canvas.create_oval(x - 20, y + 15, x + 20, y + 25, fill="#000000", stipple="gray25", outline="")
                img = self.piece_images.get(piece.symbol())
                if img: self.canvas.create_image(x, y, image=img)

    def on_click(self, event):
        if self.board.turn == chess.BLACK: return
        col, row = event.x // self.square_size, 7 - (event.y // self.square_size)
        if not (0 <= col <= 7 and 0 <= row <= 7): return
        sq = chess.square(col, row)

        if self.selected_square is None:
            p = self.board.piece_at(sq)
            if p and p.color == chess.WHITE:
                self.selected_square = sq
                self.update_board()
        else:
            move = chess.Move(self.selected_square, sq)
            if self.board.piece_at(self.selected_square).piece_type == chess.PAWN and row in [0,
                                                                                              7]: move.promotion = chess.QUEEN

            if move in self.board.legal_moves:
                self.execute_player_move(move)

            self.selected_square = None
            self.update_board()

    def execute_player_move(self, move):
        san = self.board.san(move)
        is_capture = self.board.is_capture(move)
        self.board.push(move)
        self.last_move = move
        self.update_board()
        self.speak(san)
        winsound.Beep(1000, 50)

        if not self.board.is_game_over():
            threading.Thread(target=self.engine_thinking, daemon=True).start()
        else:
            self.handle_end()

    def engine_thinking(self):
        # המחשב "חושב" חצי שנייה ואז מבצע מהלך
        time.sleep(0.5)
        if self.engine:
            res = self.engine.play(self.board, chess.engine.Limit(time=0.5))
            self.root.after(0, lambda: self.execute_engine_move(res.move))

    def execute_engine_move(self, move):
        san = self.board.san(move)
        self.board.push(move)
        self.last_move = move
        self.update_board()
        self.speak(san)
        winsound.Beep(800, 50)
        if self.board.is_game_over(): self.handle_end()

    def undo_move(self):
        # מחזיר 2 מהלכים אחורה (שלך ושל המחשב)
        if len(self.board.move_stack) >= 2:
            self.board.pop()
            self.board.pop()
            self.last_move = None
            self.update_board()
            self.speak("Undo")

    def handle_end(self):
        res = self.board.result()
        if res == "1-0":
            self.stats["wins"] += 1
        elif res == "0-1":
            self.stats["losses"] += 1
        self.save_stats()
        messagebox.showinfo("Game Over", f"Result: {res}")

    def __del__(self):
        if self.engine: self.engine.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = ChessUltimate(root)
    root.mainloop()