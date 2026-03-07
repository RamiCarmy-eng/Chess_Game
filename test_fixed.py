# -*- coding: utf-8 -*-
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog, font as tkfont
import chess
import chess.engine
import threading
from pathlib import Path
import json
import time
import queue
import tempfile
import os
import winsound

try:
    import tksvg

    HAS_TKSVG = True
except ImportError:
    HAS_TKSVG = False

# ── Paths ─────────────────────────────────────────────────────────────────────
PIECES_FOLDER = Path("pieces")
ENGINE_PATH = Path("stockfish/stockfish-windows-x86-64-avx2.exe")
STATS_FILE = "chess_stats.json"


# ── Opening book (ECO prefix table) ───────────────────────────────────────────

def _load_openings() -> dict:
    """Load openings from opening.json if it exists, otherwise use built-in list."""
    json_path = Path("Clean_openings.json")
    if json_path.exists():
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            print(f"Loaded {len(data)} openings from opening.json")
            return data
        except Exception as e:
            print(f"Could not load opening.json: {e} — using built-in list")

    # Built-in fallback
    return {
        # --- 1. e4 ---
        "e4": "King's Pawn Opening",
        "e4 e5": "Open Game",
        "e4 e5 Nf3": "King's Knight Opening",
        "e4 e5 Nf3 Nc6 Bb5": "Ruy López",
        "e4 e5 Nf3 Nc6 Bb5 a6": "Ruy López – Morphy Defence",
        "e4 e5 Nf3 Nc6 Bb5 Nf6": "Ruy López – Berlin Defence",
        "e4 e5 Nf3 Nc6 Bb5 d6": "Ruy López – Steinitz Defence",
        "e4 e5 Nf3 Nc6 Bb5 Bc5": "Ruy López – Classical Defence",

        "e4 e5 Nf3 Nc6 Bc4": "Italian Game",
        "e4 e5 Nf3 Nc6 Bc4 Bc5": "Giuoco Piano",
        "e4 e5 Nf3 Nc6 Bc4 Bc5 c3": "Giuoco Pianissimo",
        "e4 e5 Nf3 Nc6 Bc4 Nf6": "Two Knights Defence",
        "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5": "Fried Liver Attack",

        "e4 e5 Nf3 Nc6 d4": "Scotch Game",
        "e4 e5 Nf3 Nc6 d4 exd4 Nxd4": "Scotch Game – Classical",

        "e4 e5 Nc3": "Vienna Game",
        "e4 e5 Nc3 Nf6": "Vienna – Falkbeer",

        "e4 e5 f4": "King's Gambit",
        "e4 e5 f4 exf4": "King's Gambit Accepted",
        "e4 e5 f4 d5": "Falkbeer Countergambit",

        "e4 c5": "Sicilian Defence",
        "e4 c5 Nf3 d6": "Sicilian – Classical",
        "e4 c5 Nf3 d6 d4": "Sicilian – Open",
        "e4 c5 d4": "Sicilian – Smith-Morra Gambit",
        "e4 c5 Nc3": "Sicilian – Closed",

        "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6": "Sicilian – Najdorf",
        "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 g6": "Sicilian – Dragon",
        "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 g6": "Sicilian – Accelerated Dragon",
        "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 e6": "Sicilian – Scheveningen",
        "e4 c5 Nf3 e6 d4 cxd4 Nxd4 Nc6": "Sicilian – Taimanov",
        "e4 c5 Nf3 e6 d4 cxd4 Nxd4 a6": "Sicilian – Kan",
        "e4 c5 c3": "Sicilian – Alapin",

        "e4 e6": "French Defence",
        "e4 e6 d4 d5": "French – Main Line",
        "e4 e6 d4 d5 Nc3 Bb4": "French – Winawer",
        "e4 e6 d4 d5 Nd2": "French – Tarrasch",

        "e4 c6": "Caro–Kann Defence",
        "e4 c6 d4 d5 Nc3 dxe4": "Caro–Kann – Classical",
        "e4 c6 d4 d5 Nd2": "Caro–Kann – Tartakower",

        "e4 d5": "Scandinavian Defence",
        "e4 d5 exd5 Qxd5 Nc3": "Scandinavian – Main Line",

        "e4 Nf6": "Alekhine Defence",
        "e4 Nf6 e5 Nd5 d4": "Alekhine – Modern",

        "e4 d6": "Pirc Defence",
        "e4 d6 d4 Nf6 Nc3 g6": "Pirc – Classical",
        "e4 g6": "Modern Defence",

        "e4 b6": "Owen's Defence",

        # --- 1. d4 ---
        "d4": "Queen's Pawn Opening",
        "d4 d5": "Closed Game",
        "d4 d5 c4": "Queen's Gambit",
        "d4 d5 c4 e6": "Queen's Gambit Declined",
        "d4 d5 c4 dxc4": "Queen's Gambit Accepted",
        "d4 d5 c4 c6": "Slav Defence",
        "d4 d5 c4 e6 Nc3 c5": "Tarrasch Defence",

        "d4 d5 Nf3": "London System (transposition)",
        "d4 Nf6": "Indian Defence",
        "d4 Nf6 c4": "Indian Game",
        "d4 Nf6 c4 g6": "King's Indian Defence",
        "d4 Nf6 c4 e6": "Nimzo/Queen's Indian Setup",
        "d4 Nf6 c4 e6 Nc3 Bb4": "Nimzo-Indian Defence",
        "d4 Nf6 c4 e6 g3": "Catalan Opening",

        "d4 f5": "Dutch Defence",
        "d4 Nf6 Bg5": "Trompowsky Attack",

        "d4 c5": "Benoni Defence",
        "d4 Nf6 c4 c5 d5": "Benoni – Modern",
        "d4 Nf6 c4 c5 d5 b5": "Benko Gambit",

        # --- 1. c4 ---
        "c4": "English Opening",
        "c4 e5": "English – Reversed Sicilian",
        "c4 c5": "English – Symmetrical",
        "c4 g6": "English – King's Fianchetto",
        "c4 Nf6 Nc3 e5": "English – Four Knights",
        "c4 g6 Nc3 Bg7 e4": "English – Botvinnik System",

        # --- 1. Nf3 ---
        "Nf3": "Réti Opening",
        "Nf3 d5 g3": "Réti – King's Fianchetto",
        "Nf3 d5 b3": "Zukertort Opening",
        "Nf3 c5": "Réti – Sicilian Invitation",

        # --- 1. f4 ---
        "f4": "Bird's Opening",
        "f4 e5": "From Gambit",
        "f4 g6": "Bird – Leningrad Variation",

        # --- 1. b4 ---
        "b4": "Polish (Sokolsky) Opening",
        "b4 e5": "Polish Gambit",

        # --- 1. g4 ---
        "g4": "Grob Attack",
        "g4 d5": "Grob – Spike Variation",

        # --- Misc ---
        "b3": "Nimzowitsch–Larsen Attack",
        "g3": "King's Fianchetto Opening",
        "Nc3": "Dunst Opening",
        "a3": "Anderssen's Opening",
        "h3": "Clemenz Opening",
        "a4": "Ware Opening",
        "h4": "Desprez Opening",
    }

OPENINGS = _load_openings()


def translate_to_hebrew(text: str) -> str:
    """Translate English spoken text to Hebrew using phrase substitution."""
    result = text
    for eng, heb in sorted(HEBREW_PHRASES.items(), key=lambda x: -len(x[0])):
        result = result.replace(eng, heb)
    return result





def detect_opening(board: chess.Board) -> str:
    """Return the best matching opening name for the current move stack."""
    moves = list(board.move_stack)
    tmp = chess.Board()
    san_list = []
    for m in moves:
        san_list.append(tmp.san(m).replace("x", "").replace("+", "").replace("#", ""))
        tmp.push(m)
    # Walk backwards from longest prefix to shortest
    for length in range(len(san_list), 0, -1):
        key = " ".join(san_list[:length])
        if key in OPENINGS:
            return OPENINGS[key]
    return ""


HEBREW_PHRASES = {
    # Move announcements
    "plays": "מוציא",
    "Computer plays": "המחשב מוציא",
    "Check": "שח",
    "Check!": "שח!",
    "Checkmate": "שח מט",
    "Undo": "בוטל מהלך",
    "Game over": "המשחק הסתיים",

    # Welcome / setup
    "Good luck": "בהצלחה",
    "Welcome": "ברוך הבא",
    "New game": "משחק חדש",
    "Difficulty set to Easy": "רמה קלה",
    "Difficulty set to Medium": "רמה בינונית",
    "Difficulty set to Pro": "רמה מקצועית",
    "Coach is ON. I will help you!": "המאמן פעיל. אני אעזור לך!",
    "Coach is off.": "המאמן כבוי.",

    # Game results
    "You won": "ניצחת",
    "Congratulations": "כל הכבוד",
    "The engine wins this time. Keep practising!": "המחשב ניצח הפעם. תמשיך להתאמן!",
    "It is a draw. Well played!": "תיקו. שיחקת יפה!",

    # Move grades
    "Best move! Well done!": "המהלך הטוב ביותר! כל הכבוד!",
    "Move played.": "מהלך בוצע.",
    "Good move": "מהלך טוב",
    "Excellent move": "מהלך מצוין",
    "Best move": "המהלך הטוב ביותר",
    "Book move": "מהלך מהספר",
    "Blunder": "טעות חמורה",
    "Mistake": "טעות",
    "Inaccuracy": "אי דיוק",
    "Consider": "כדאי לשקול",
    "Better is": "עדיף לשחק",
    "White is winning": "הלבן מנצח",
    "Black is winning": "השחור מנצח",
    "The game is equal": "המצב שקול",
    "developing your remaining knight": "פיתוח הפרש הנותר",

    # Coach tips — piece safety
    "is undefended": "אינו מוגן",
    "the opponent can take it": "היריב יכול לקחת אותו",
    "Moving away left your": "הזזת הכלי חשפה את ה",
    "undefended": "ללא הגנה",

    # Coach tips — tactics
    "You missed CHECKMATE": "פספסת שח מט",
    "was the winning move": "היה המהלך המנצח",
    "יכול היה לתפוס": "יכול היה לתפוס",
    "for free": "בחינם",
    "יכול היה לנוע ל": "יכול היה לנוע ל",
    "ולשים את המלך בשח": "ולשים את המלך בשח",

    # Coach tips — suggestions
    "Better": "עדיף",
    "consider moving your": "שקול להזיז את ה",
    "הוא משבצת חזקה יותר": "הוא משבצת חזקה יותר",
    "Because": "כי",

    # Coach tips — opening
    "Good — developing your pieces early is the right idea!": "טוב — לפתח כלים מוקדם זה הכיוון הנכון!",
    "Good central pawn push": "דחיפת רגלי מרכז טובה",
    "controlling the centre": "שולטת במרכז",
    "Bringing your Queen out early is risky": "הוצאת המלכה מוקדם היא מסוכנת",
    "develop your": "פתח את ה",
    "first": "קודם",

    # Coach tips — king safety
    "Moving your King early loses castling rights": "הזזת המלך מוקדם מאבדת זכות הצרחה",
    "try to castle first to stay safe": "נסה להצריח קודם להישאר מוגן",
    "castling keeps your King safe and connects your Rooks": "הצרחה שומרת על המלך ומחברת צריחים",

    # Coach tips — pawn structure
    "You now have doubled pawns": "יש לך עכשיו רגלים כפולים",
    "they can be hard to defend": "הם קשים להגנה",

    # Coach tips — strategy
    "Try to castle soon": "נסה להצריח בקרוב",
    "keeping your King in the center too long is risky": "להשאיר את המלך במרכז זמן רב מסוכן",
    "Consider developing your remaining": "שקול לפתח את ה",
    "get all your pieces active": "הפוך את כל הכלים לפעילים",
    "your knight is on a strong outpost": "הפרש שלך על עמדה חזקה",
    "hard to challenge": "קשה לאתגר",
    "Your bishop is blocked by your own pawns": "הרץ שלך חסום על ידי הרגלים שלך",
    "consider opening the diagonal": "שקול לפתוח את האלכסון",
    "Try not to move the same piece twice early": "נסה לא להזיז את אותו כלי פעמיים מוקדם",
    "develop all your pieces first": "פתח את כל הכלים קודם",
    "In the endgame, activate your King": "בסיומה, הפעל את המלך",
    "it becomes a strong piece": "הוא הופך לכלי חזק",
    "This is a quiet improving move": "זה מהלך שקט משפר",
    "it slightly improves your position": "הוא משפר מעט את עמדתך",

    # Blunder severity
    "This move is a serious blunder": "מהלך זה הוא בלונדר חמור",
    "it heavily worsens your position": "הוא מחמיר מאוד את עמדתך",
    "This move is a mistake": "מהלך זה הוא טעות",
    "it weakens your position": "הוא מחליש את עמדתך",
    "This move is a small inaccuracy": "מהלך זה הוא אי דיוק קטן",
    "there was a more precise option": "הייתה אפשרות מדויקת יותר",

    # Threat detection
    "After this move, your": "אחרי המהלך הזה, ה",
    "is now under attack": "נמצא תחת מתקפה",

    # Captures
    "Nice capture! You traded well.": "לכידה יפה! סחרת טוב.",

    # Theory
    "Theory suggests": "התיאוריה מציעה",
    "leading to the": "המובילה ל",
    "You are out of the opening book": "יצאת מספר הפתיחות",
    "Coach says": "המאמן אומר",

    # Piece names for move announcements
    "Knight": "פרש",
    "Bishop": "רץ",
    "Rook": "צריח",
    "Queen": "מלכה",
    "King": "מלך",
    "takes": "לוכד",
    "check": "שח",
    "checkmate": "שח מט",
    "pawn": "רגלי",
    "knight": "פרש",
    "bishop": "רץ",
    "rook": "צריח",
    "queen": "מלכה",
    "king": "מלך",
    "piece": "כלי",
    "Good move!": "מהלך טוב!",
    "Bad move!": "מהלך גרוע!",
    "Develop your knight": "פתח את הפרש",
    "Control the center": "שלוט במרכז",
    "Castle now": "עשה רוקדה עכשיו",
    "Welcome Rami! Good luck!": "ברוך הבא רמי! בהצלחה!"
}


# ── Main application ───────────────────────────────────────────────────────────
# ── SpeechManager — Hebrew TTS via edge_tts ───────────────────────────────────

class SpeechManager:
    """Background Hebrew TTS using edge_tts (he-IL-AvriNeural)."""

    def __init__(self, voice="he-IL-AvriNeural"):
        self.voice = voice
        self.msg_queue = queue.Queue()
        self._busy = False
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    @property
    def is_busy(self):
        return self._busy or not self.msg_queue.empty()

    def speak(self, text: str):
        """Queue a text to be spoken in Hebrew."""
        if text and text.strip():
            self.msg_queue.put(str(text).strip())

    def stop(self):
        """Shut down the worker thread."""
        self.msg_queue.put(None)

    def _worker(self):
        """Background thread — processes messages one at a time.
        asyncio is imported LOCALLY here so it never touches the main thread's
        event loop, which chess.engine needs to stay as ProactorEventLoop.
        """
        import asyncio, sys
        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        while True:
            text = self.msg_queue.get()
            if text is None:
                break
            self._busy = True
            try:
                asyncio.run(self._speak_async(text))
            except Exception as e:
                print(f"[edge_tts] error: {e}")
            finally:
                self._busy = False

    async def _speak_async(self, text: str):
        """Generate Hebrew MP3 via edge_tts and play it."""
        import edge_tts
        from playsound import playsound

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            temp_path = f.name

        try:
            tts = edge_tts.Communicate(text, voice=self.voice)
            await tts.save(temp_path)
            playsound(temp_path)
        finally:
            try:
                os.remove(temp_path)
            except Exception:
                pass


class ChessUltimate:
    SQ = 85  # square pixel size
    PAD = 20  # board left/top padding inside canvas

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("♟ Chess Master Ultimate")
        self.root.geometry("1120x980")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)

        # ── State ─────────────────────────────────────────────────────────────
        self.stats = self.load_stats()
        self.player_name = "Player 1"

        self.board = chess.Board()
        self.engine = None
        self.skill_level = 5
        self.selected_sq = None
        self.legal_targets = set()
        self.last_move = None
        self.piece_images = {}
        self.eval_score = 0.0
        self.opening_name = ""
        self.move_history = []
        self.captured_w = []
        self.captured_b = []
        self.review_mode = False
        self.review_idx = 0
        self.review_boards = []
        self.engine_busy = False

        # ── Coach ─────────────────────────────────────────────────────────────
        self.coach_on = True
        self.pre_move_eval = 0.0
        self.best_move_before = None
        self.coach_highlight = None

        # ── Clocks ────────────────────────────────────────────────────────────
        self.white_time = 600.0
        self.black_time = 600.0
        self.last_tick = time.time()

        # ── Build UI ──────────────────────────────────────────────────────────
        self.init_engine()

        # ── Speech — Hebrew TTS via edge_tts (MUST be after init_engine) ──────
        self._tts = SpeechManager(voice="he-IL-AvriNeural")
        self.create_ui()
        self.load_piece_images()
        self.update_clock()
        self.root.after(150, self.redraw)
        self.root.after(300, self._ask_name_on_start)

    # ──────────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────────
    def load_stats(self):
        if Path(STATS_FILE).exists():
            with open(STATS_FILE) as f:
                return json.load(f)
        return {"wins": 0, "losses": 0, "draws": 0}

    def save_stats(self):
        with open(STATS_FILE, "w") as f:
            json.dump(self.stats, f)

    def ask_name(self):
        n = simpledialog.askstring("Welcome", "Enter your name:", initialvalue="Player 1")
        return n if n else "Player 1"

    def _ask_name_on_start(self):
        # Bring window to front so the dialog is visible
        self.root.lift()
        self.root.focus_force()
        n = simpledialog.askstring("ברוך הבא! / Welcome",
                                   "Enter your name:\nהכנס את שמך:",
                                   initialvalue="", parent=self.root)
        self.player_name = n.strip() if n and n.strip() else "שחקן"
        if hasattr(self, 'stats_label'):
            self.stats_label.config(text=self._stats_text())
        # Speak welcome only after name is confirmed
        self.root.after(500, lambda: self.speak_async(f"ברוך הבא {self.player_name}! בהצלחה!"))

    # ──────────────────────────────────────────────────────────────────────────
    # Engine
    # ──────────────────────────────────────────────────────────────────────────
    def init_engine(self):
        if ENGINE_PATH.exists():
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(str(ENGINE_PATH))
                self.engine.configure({"Skill Level": self.skill_level})
            except Exception as e:
                print(f"[ENGINE] Failed to load: {e}")

    def set_difficulty(self, level):
        text = {0: "Easy", 10: "Medium", 20: "Pro"}.get(level, "Easy")

        self.skill_level = level

        if self.engine:
            try:
                self.engine.configure({"Skill Level": level})
            except:
                pass

        self.diff_label.config(text=f"Difficulty: {text}")
        self.speak_async({"Easy": "רמה קלה", "Medium": "רמה בינונית", "Pro": "רמה מקצועית"}.get(text, text))

    # ──────────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────────
    def create_ui(self):
        BG = "#1a1a2e"
        GOLD = "#f1c40f"
        FG = "#ecf0f1"
        ACCENT = "#16213e"

        # ── Top bar ───────────────────────────────────────────────────────────
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill=tk.X, padx=20, pady=(8, 2))

        self.stats_label = tk.Label(top,
                                    text=self._stats_text(), fg=GOLD, bg=BG, font=("Consolas", 12, "bold"))
        self.stats_label.pack(side=tk.LEFT)

        # Difficulty display (attached to top bar)
        self.diff_label = tk.Label(
            top,
            text="Difficulty: Easy",
            fg="#ffffff",
            bg=BG,
            font=("Consolas", 11, "bold")
        )
        self.diff_label.pack(side=tk.LEFT, padx=20)

        self.opening_label = tk.Label(top, text="", fg="#95a5a6", bg=BG, font=("Consolas", 10, "italic"))
        self.opening_label.pack(side=tk.LEFT, padx=20)

        # ── Clocks ────────────────────────────────────────────────────────────
        clk = tk.Frame(self.root, bg=BG)
        clk.pack(fill=tk.X, padx=50, pady=2)
        self.w_clock = tk.Label(clk, text="10:00", font=("Consolas", 22, "bold"), fg="#2ecc71", bg=BG)
        self.w_clock.pack(side=tk.LEFT)
        self.b_clock = tk.Label(clk, text="10:00", font=("Consolas", 22, "bold"), fg="#e74c3c", bg=BG)
        self.b_clock.pack(side=tk.RIGHT)

        # ── Main row: eval bar + board + right panel ───────────────────────────
        main_row = tk.Frame(self.root, bg=BG)
        main_row.pack(padx=10, pady=4)

        # Eval bar (10px wide, 680px tall)
        eval_col = tk.Frame(main_row, bg=BG)
        eval_col.pack(side=tk.LEFT, padx=(0, 8), anchor="n")
        self.eval_canvas = tk.Canvas(eval_col, width=22, height=self.SQ * 8,
                                     bg="#2c2c2c", highlightthickness=1,
                                     highlightbackground="#555")
        self.eval_canvas.pack()
        self.eval_label = tk.Label(eval_col, text="0.0", fg=FG, bg=BG, font=("Consolas", 9))
        self.eval_label.pack(pady=2)

        # Board canvas
        board_col = tk.Frame(main_row, bg=BG)
        board_col.pack(side=tk.LEFT)

        # Rank/file labels around the board
        rank_labels_left = tk.Frame(board_col, bg=BG)
        rank_labels_left.grid(row=1, column=0)
        for i, r in enumerate("87654321"):
            tk.Label(rank_labels_left, text=r, fg="#7f8c8d", bg=BG,
                     font=("Consolas", 9), width=2,
                     height=1).pack(pady=(self.SQ // 2 - 6, self.SQ // 2 - 7))

        self.canvas = tk.Canvas(board_col, width=self.SQ * 8, height=self.SQ * 8,
                                bg="#2c3e50", highlightthickness=2,
                                highlightbackground="#4a4a6a")
        self.canvas.grid(row=1, column=1)
        self.canvas.bind("<Button-1>", self.on_click)

        file_frame = tk.Frame(board_col, bg=BG)
        file_frame.grid(row=2, column=1)
        for ch in "abcdefgh":
            tk.Label(file_frame, text=ch, fg="#7f8c8d", bg=BG,
                     font=("Consolas", 9), width=int(self.SQ / 7)).pack(side=tk.LEFT)

        # Captured pieces strips
        cap_frame = tk.Frame(board_col, bg=BG)
        cap_frame.grid(row=0, column=1, sticky="w")
        tk.Label(cap_frame, text="Black lost:", fg="#95a5a6", bg=BG,
                 font=("Consolas", 9)).pack(side=tk.LEFT)
        self.cap_black_label = tk.Label(cap_frame, text="", fg="#ecf0f1", bg=BG,
                                        font=("Arial", 11))
        self.cap_black_label.pack(side=tk.LEFT)

        cap_frame2 = tk.Frame(board_col, bg=BG)
        cap_frame2.grid(row=3, column=1, sticky="w")
        tk.Label(cap_frame2, text="White lost:", fg="#95a5a6", bg=BG,
                 font=("Consolas", 9)).pack(side=tk.LEFT)
        self.cap_white_label = tk.Label(cap_frame2, text="", fg="#ecf0f1", bg=BG,
                                        font=("Arial", 11))
        self.cap_white_label.pack(side=tk.LEFT)

        # ── Right panel ───────────────────────────────────────────────────────
        right = tk.Frame(main_row, bg=ACCENT, relief="flat", bd=0)
        right.pack(side=tk.LEFT, padx=(12, 0), fill=tk.Y)

        tk.Label(right, text="MOVE HISTORY", fg=GOLD, bg=ACCENT,
                 font=("Consolas", 10, "bold")).pack(pady=(8, 2))

        hist_frame = tk.Frame(right, bg=ACCENT)
        hist_frame.pack(fill=tk.BOTH, expand=True, padx=6)

        scrollbar = tk.Scrollbar(hist_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hist_list = tk.Listbox(hist_frame, width=22, height=28,
                                    bg="#0f0f23", fg=FG, selectbackground="#273c75",
                                    font=("Consolas", 10), yscrollcommand=scrollbar.set,
                                    highlightthickness=0, bd=0)
        self.hist_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.hist_list.yview)

        # ── Coach panel ───────────────────────────────────────────────────────
        tk.Frame(right, bg="#0a0a1a", height=2).pack(fill=tk.X, padx=6, pady=(8, 4))

        coach_hdr = tk.Frame(right, bg=ACCENT)
        coach_hdr.pack(fill=tk.X, padx=6)
        tk.Label(coach_hdr, text="🎓 COACH", fg="#27ae60", bg=ACCENT,
                 font=("Consolas", 10, "bold")).pack(side=tk.LEFT)
        self.coach_toggle_btn = tk.Button(
            coach_hdr, text="ON", bg="#27ae60", fg="white",
            font=("Consolas", 8, "bold"), relief="flat", padx=6, pady=1,
            cursor="hand2", command=self.toggle_coach)
        self.coach_toggle_btn.pack(side=tk.RIGHT)

        coach_msg_frame = tk.Frame(right, bg="#0d1117", relief="flat")
        coach_msg_frame.pack(fill=tk.X, padx=6, pady=(2, 6))

        self.coach_text = tk.Text(
            coach_msg_frame, width=22, height=8,
            bg="#0d1117", fg="#a8d8a8",
            font=("Consolas", 9), wrap=tk.WORD,
            relief="flat", padx=6, pady=4,
            state=tk.DISABLED, cursor="arrow")
        self.coach_text.pack(fill=tk.BOTH)

        # Tag styles for coach messages
        self.coach_text.tag_config("good", foreground="#2ecc71")
        self.coach_text.tag_config("warn", foreground="#f39c12")
        self.coach_text.tag_config("blunder", foreground="#e74c3c")
        self.coach_text.tag_config("info", foreground="#95a5a6")
        self.coach_text.tag_config("tip", foreground="#3498db")

        self._coach_msg("Hi! I'll guide you during the game.\nMake your first move! ♟", "info")

        # ── Bottom buttons ────────────────────────────────────────────────────
        btm = tk.Frame(self.root, bg=BG)
        btm.pack(pady=8)

        def btn(parent, text, cmd, color="#34495e"):
            return tk.Button(parent, text=text, command=cmd, bg=color, fg="white",
                             font=("Consolas", 10, "bold"), relief="flat", padx=10, pady=4,
                             cursor="hand2", activebackground="#5d6d7e", activeforeground="white")

        btn(btm, "↩  Undo", self.undo_move, "#e67e22").pack(side=tk.LEFT, padx=6)
        btn(btm, "Easy", lambda: self.set_difficulty(0)).pack(side=tk.LEFT, padx=4)
        btn(btm, "Medium", lambda: self.set_difficulty(10)).pack(side=tk.LEFT, padx=4)
        btn(btm, "Pro", lambda: self.set_difficulty(20)).pack(side=tk.LEFT, padx=4)
        btn(btm, "⟳  New Game", self.new_game, "#27ae60").pack(side=tk.LEFT, padx=6)
        btn(btm, "▶  Review Game", self.start_review, "#8e44ad").pack(side=tk.LEFT, padx=6)

        # Review nav (hidden until review mode)
        self.review_frame = tk.Frame(self.root, bg=BG)
        btn(self.review_frame, "◀◀ Start", lambda: self.review_jump(0), "#2c3e50").pack(side=tk.LEFT, padx=4)
        btn(self.review_frame, "◀ Prev", lambda: self.review_step(-1), "#2c3e50").pack(side=tk.LEFT, padx=4)
        btn(self.review_frame, "▶ Next", lambda: self.review_step(+1), "#2c3e50").pack(side=tk.LEFT, padx=4)
        btn(self.review_frame, "▶▶ End", lambda: self.review_jump(-1), "#2c3e50").pack(side=tk.LEFT, padx=4)
        btn(self.review_frame, "✕ Exit Review", self.exit_review, "#c0392b").pack(side=tk.LEFT, padx=8)

        # Status bar
        self.status_var = tk.StringVar(value="Your turn – White")
        tk.Label(self.root, textvariable=self.status_var, fg="#bdc3c7", bg=BG,
                 font=("Consolas", 10)).pack(pady=(0, 6))

    # ──────────────────────────────────────────────────────────────────────────
    # Piece images
    # ──────────────────────────────────────────────────────────────────────────
    def load_piece_images(self):
        MAP = {'K': 'wk', 'Q': 'wq', 'R': 'wr', 'B': 'wb', 'N': 'wn', 'P': 'wp',
               'k': 'bk', 'q': 'bq', 'r': 'br', 'b': 'bb', 'n': 'bn', 'p': 'bp'}
        if HAS_TKSVG:
            for sym, fname in MAP.items():
                p = PIECES_FOLDER / f"{fname}.svg"
                if p.exists():
                    self.piece_images[sym] = tksvg.SvgImage(
                        file=str(p), scaletoheight=int(self.SQ * 0.84))
        # If no SVG images loaded, we fall back to Unicode rendering in draw_pieces

    # ──────────────────────────────────────────────────────────────────────────
    # Clock
    # ──────────────────────────────────────────────────────────────────────────
    def update_clock(self):
        now = time.time()
        dt = now - self.last_tick
        self.last_tick = now

        if not self.board.is_game_over() and not self.review_mode:
            if self.board.turn == chess.WHITE:
                self.white_time = max(0.0, self.white_time - dt)
            else:
                self.black_time = max(0.0, self.black_time - dt)

        self.w_clock.config(text=self._fmt(self.white_time))
        self.b_clock.config(text=self._fmt(self.black_time))
        self.root.after(200, self.update_clock)

    def _fmt(self, s):
        m, sec = divmod(int(s), 60)
        return f"{m:02d}:{sec:02d}"

    # ──────────────────────────────────────────────────────────────────────────
    # Drawing
    # ──────────────────────────────────────────────────────────────────────────
    def redraw(self):
        self.canvas.delete("all")
        self.draw_squares()
        self.draw_legal_dots()
        self.draw_coach_highlight()
        self.draw_pieces()
        self.draw_eval_bar()
        self.update_captured_display()

    def sq_xy(self, sq):
        """Top-left pixel of a square."""
        c = chess.square_file(sq)
        r = 7 - chess.square_rank(sq)
        return c * self.SQ, r * self.SQ

    def draw_squares(self):
        LIGHT = "#EBECD0"
        DARK = "#779556"
        LAST = "#F7F769"
        SEL = "#66B2FF"
        CHECK = "#FF4444"

        in_check_sq = None
        if self.board.is_check():
            in_check_sq = self.board.king(self.board.turn)

        for sq in chess.SQUARES:
            c = chess.square_file(sq)
            r = 7 - chess.square_rank(sq)
            x0, y0 = c * self.SQ, r * self.SQ
            x1, y1 = x0 + self.SQ, y0 + self.SQ

            color = LIGHT if (c + chess.square_rank(sq)) % 2 else DARK

            if self.last_move and sq in (self.last_move.from_square, self.last_move.to_square):
                color = LAST
            if self.selected_sq == sq:
                color = SEL
            if sq == in_check_sq:
                color = CHECK

            self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

    def draw_legal_dots(self):
        """Draw small dots on legal target squares for the selected piece."""
        for sq in self.legal_targets:
            x0, y0 = self.sq_xy(sq)
            cx, cy = x0 + self.SQ // 2, y0 + self.SQ // 2
            has_piece = self.board.piece_at(sq) is not None
            if has_piece:
                # Ring around the target
                r = self.SQ // 2 - 4
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                        outline="#444444", width=5, fill="")
            else:
                # Small dot
                r = self.SQ // 7
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                        fill="#555555", outline="")

    # Unicode fallback glyphs
    UNICODE_PIECES = {
        'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
        'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
    }

    def draw_pieces(self):
        use_svg = bool(self.piece_images)
        piece_font_size = int(self.SQ * 0.72)

        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if not piece:
                continue
            x0, y0 = self.sq_xy(sq)
            cx = x0 + self.SQ // 2
            cy = y0 + self.SQ // 2

            if use_svg:
                # Drop shadow
                self.canvas.create_oval(cx - 18, cy + 16, cx + 18, cy + 24,
                                        fill="#333333", outline="")
                img = self.piece_images.get(piece.symbol())
                if img:
                    self.canvas.create_image(cx, cy, image=img)
            else:
                # Unicode fallback – draw a coloured circle + glyph
                sym = piece.symbol()
                glyph = self.UNICODE_PIECES.get(sym, sym)
                is_white = piece.color == chess.WHITE

                # Shadow
                self.canvas.create_oval(cx - 28, cy - 28, cx + 28, cy + 30,
                                        fill="#333333", outline="")
                # Piece circle
                fill_color = "#f5f0e8" if is_white else "#2d2d2d"
                border_color = "#999" if is_white else "#111"
                self.canvas.create_oval(cx - 28, cy - 30, cx + 28, cy + 26,
                                        fill=fill_color, outline=border_color, width=2)
                # Glyph
                text_color = "#1a1a1a" if is_white else "#e8e8e8"
                self.canvas.create_text(cx, cy - 2,
                                        text=glyph,
                                        fill=text_color,
                                        font=("Segoe UI Symbol", piece_font_size // 3, "bold"))

    def draw_eval_bar(self):
        """White share at top → 50% = equal, 100% = white winning."""
        self.eval_canvas.delete("all")
        h = self.SQ * 8
        w = 22
        # Clamp eval to ±8 pawns
        clamped = max(-8.0, min(8.0, self.eval_score / 100.0))
        white_frac = (clamped + 8) / 16.0  # 0..1  (1 = white winning)
        black_height = int(h * (1 - white_frac))
        white_height = h - black_height

        self.eval_canvas.create_rectangle(0, 0, w, black_height,
                                          fill="#2c2c2c", outline="")
        self.eval_canvas.create_rectangle(0, black_height, w, h,
                                          fill="#f0f0f0", outline="")
        # Centre line
        self.eval_canvas.create_line(0, h // 2, w, h // 2, fill="#888", width=1)

        score_pawn = self.eval_score / 100.0
        sign = "+" if score_pawn > 0 else ""
        self.eval_label.config(text=f"{sign}{score_pawn:.1f}")

    def update_captured_display(self):
        UNICODE = {'P': '♟', 'N': '♞', 'B': '♝', 'R': '♜', 'Q': '♛',
                   'p': '♙', 'n': '♘', 'b': '♗', 'r': '♖', 'q': '♕'}
        self.cap_black_label.config(
            text=" ".join(UNICODE.get(p, p) for p in self.captured_w))
        self.cap_white_label.config(
            text=" ".join(UNICODE.get(p, p) for p in self.captured_b))

    # ──────────────────────────────────────────────────────────────────────────
    # Coach
    # ──────────────────────────────────────────────────────────────────────────

    # Piece values in centipawns
    PIECE_VALUE = {
        chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
        chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
    }
    PIECE_NAME = {
        chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop",
        chess.ROOK: "rook", chess.QUEEN: "queen", chess.KING: "king"
    }

    def toggle_coach(self):
        self.coach_on = not self.coach_on
        if self.coach_on:
            self.coach_toggle_btn.config(text="ON", bg="#27ae60")
            self._coach_msg("Coach is ON. I'll help you!", "good")
            self.coach_speak("המאמן פעיל. אני אעזור לך!")
        else:
            self.coach_toggle_btn.config(text="OFF", bg="#7f8c8d")
            self._coach_msg("Coach is OFF.", "info")
            self.coach_speak("המאמן כבוי.")
        self.coach_highlight = None
        self.redraw()

    def _coach_msg(self, text: str, tag: str = "info"):
        """Replace the coach panel text."""
        self.coach_text.config(state=tk.NORMAL)
        self.coach_text.delete("1.0", tk.END)
        self.coach_text.insert(tk.END, text, tag)
        self.coach_text.config(state=tk.DISABLED)

    # pre_move_eval and best_move_before are set at end of _engine_and_coach,
    # so they're always ready for the next player move with no thread racing.

    def _explain_move_thorough(self, move: chess.Move, board: chess.Board,
                               drop: float, best: chess.Move) -> list:
        """
        Generate ALL coaching tips for a move, sorted by importance.
        """

        tips = []
        board_after = board.copy()
        board_after.push(move)
        moved_piece = board_after.piece_at(move.to_square)
        piece_moved = board.piece_at(move.from_square)
        move_count = len(board.move_stack)

        PNAME = self.PIECE_NAME

        # INTERNAL list of (priority, message)
        # Lower number = more important
        PRIORITY = []

        def add(priority, text):
            PRIORITY.append((priority, text))

        # ───────────────────────────────────────────────────────────────
        # 1. Hung a piece (undefended after move)
        # ───────────────────────────────────────────────────────────────
        if moved_piece and moved_piece.color == chess.WHITE:
            attackers = board_after.attackers(chess.BLACK, move.to_square)
            defenders = board_after.attackers(chess.WHITE, move.to_square)
            if attackers and not defenders:
                pname = PNAME.get(moved_piece.piece_type, "piece")
                sq_name = chess.square_name(move.to_square)
                add(1, f"⚠ Your {pname} on {sq_name} is undefended — the opponent can take it!")

        # ───────────────────────────────────────────────────────────────
        # 2. Left another piece hanging
        # ───────────────────────────────────────────────────────────────
        if piece_moved:
            for sq in chess.SQUARES:
                p = board.piece_at(sq)
                if p and p.color == chess.WHITE and sq != move.from_square:
                    was_defended = bool(board.attackers(chess.WHITE, sq))
                    now_defended = bool(board_after.attackers(chess.WHITE, sq))
                    now_attacked = bool(board_after.attackers(chess.BLACK, sq))
                    if now_attacked and not now_defended and was_defended:
                        pname = PNAME.get(p.piece_type, "piece")
                        add(2, f"⚠ Moving away left your {pname} on {chess.square_name(sq)} undefended!")
                        break

        # ───────────────────────────────────────────────────────────────
        # 3. Missed free capture
        # ───────────────────────────────────────────────────────────────
        if best is not None and best in board.legal_moves and board.is_capture(best) and not board.is_capture(move):
            captured = board.piece_at(best.to_square)
            if captured:
                cap_pname = PNAME.get(captured.piece_type, "piece")
                best_piece = board.piece_at(best.from_square)
                bp_name = PNAME.get(best_piece.piece_type, "piece") if best_piece else "piece"
                add(3, f"💰 Your {bp_name} on {chess.square_name(best.from_square)} could have captured "
                       f"the opponent's {cap_pname} on {chess.square_name(best.to_square)} for free!")

        # ───────────────────────────────────────────────────────────────
        # 4. Missed check
        # ───────────────────────────────────────────────────────────────
        if best is not None and best in board.legal_moves:
            test2 = board.copy();
            test2.push(best)
            if test2.is_check() and not board_after.is_check():
                best_piece = board.piece_at(best.from_square)
                bp_name = PNAME.get(best_piece.piece_type, "piece") if best_piece else "piece"
                add(4, f"🎯 Your {bp_name} on {chess.square_name(best.from_square)} could have moved to "
                       f"{chess.square_name(best.to_square)} and put the King in check!")

        # ───────────────────────────────────────────────────────────────
        # 5. Missed checkmate
        # ───────────────────────────────────────────────────────────────
        if best is not None and best in board.legal_moves:
            test3 = board.copy();
            test3.push(best)
            if test3.is_checkmate():
                best_piece = board.piece_at(best.from_square)
                bp_name = PNAME.get(best_piece.piece_type, "piece") if best_piece else "piece"
                add(0,
                    f"👑 פספסת שח מט! {bp_name} ל-{chess.square_name(best.to_square)} היה המהלך המנצח!")

        # ───────────────────────────────────────────────────────────────
        # 6. Suggest better move (with explanation)
        # ───────────────────────────────────────────────────────────────
        if best is not None and best in board.legal_moves and best != move and drop >= 10:
            best_piece = board.piece_at(best.from_square)
            my_piece = piece_moved
            reason = self._why_better(best, best_piece, board, board_after)

            if best_piece and my_piece and best_piece.piece_type != my_piece.piece_type:
                bp_name = PNAME.get(best_piece.piece_type, "piece")
                my_name = PNAME.get(my_piece.piece_type, "piece")
                to_sq = chess.square_name(best.to_square)
                from_sq = chess.square_name(best.from_square)
                add(5, f"💡 Instead of the {my_name}, consider moving your {bp_name} "
                       f"from {from_sq} to {to_sq}. {reason}")
            else:
                bp_name = PNAME.get(best_piece.piece_type, "piece")
                to_sq = chess.square_name(best.to_square)
                add(5, f"💡 The {bp_name} was right but {to_sq} is a stronger square. {reason}")

        # ───────────────────────────────────────────────────────────────
        # 7. King safety: moved king early
        # ───────────────────────────────────────────────────────────────
        if piece_moved and piece_moved.piece_type == chess.KING:
            if board.has_castling_rights(chess.WHITE):
                add(6, "🏰 Moving your King early loses castling rights — try to castle first to stay safe!")

        # ───────────────────────────────────────────────────────────────
        # 8. Pawn structure: doubled pawns
        # ───────────────────────────────────────────────────────────────
        if piece_moved and piece_moved.piece_type == chess.PAWN:
            col = chess.square_file(move.to_square)
            pawns_on_col = sum(
                1 for sq in chess.SQUARES
                if board_after.piece_at(sq)
                and board_after.piece_at(sq).piece_type == chess.PAWN
                and board_after.piece_at(sq).color == chess.WHITE
                and chess.square_file(sq) == col
            )
            if pawns_on_col >= 2:
                add(7, "📌 You now have doubled pawns — they can be hard to defend.")

        # ───────────────────────────────────────────────────────────────
        # 9. Opening: early queen
        # ───────────────────────────────────────────────────────────────
        if move_count <= 14 and piece_moved:
            if piece_moved.piece_type == chess.QUEEN and move_count < 6:
                undeveloped = []
                for sq in chess.SQUARES:
                    p = board_after.piece_at(sq)
                    if p and p.color == chess.WHITE and p.piece_type in (chess.KNIGHT, chess.BISHOP):
                        if chess.square_rank(sq) == 0:
                            undeveloped.append(PNAME.get(p.piece_type, "piece"))
                if undeveloped:
                    add(8, f"⚠ Bringing your Queen out early is risky — develop your {undeveloped[0]} first!")

        # ───────────────────────────────────────────────────────────────
        # 10. Positive: good development
        # ───────────────────────────────────────────────────────────────
        if move_count <= 10 and piece_moved:
            if piece_moved.piece_type in (chess.KNIGHT, chess.BISHOP):
                add(20, "👌 Good — developing your pieces early is the right idea!")
            elif piece_moved.piece_type == chess.PAWN:
                from_rank = chess.square_rank(move.from_square)
                if from_rank == 1 and chess.square_rank(move.to_square) == 3 and drop < 20:
                    add(20, "👌 Good central pawn push — controlling the centre!")

        # ───────────────────────────────────────────────────────────────
        # 11. Positive: good capture
        # ───────────────────────────────────────────────────────────────
        if board.is_capture(move) and drop < 10:
            captured = board.piece_at(move.to_square)
            if captured:
                cap_val = self.PIECE_VALUE.get(captured.piece_type, 0)
                mover_val = self.PIECE_VALUE.get(piece_moved.piece_type, 0) if piece_moved else 0
                if cap_val >= mover_val:
                    add(21, "💥 Nice capture! You traded well.")

        # ───────────────────────────────────────────────────────────────
        # 12. Positive: castling
        # ───────────────────────────────────────────────────────────────
        if board.is_castling(move):
            add(22, "🏰 Great — castling keeps your King safe and connects your Rooks!")

        # ───────────────────────────────────────────────────────────────
        # 13–19. EXTRA COACHING LAYERS (all 8 upgrades)
        # ───────────────────────────────────────────────────────────────

        # 13. Blunder severity
        if drop >= 600:
            add(1, "This move is a serious blunder — it heavily worsens your position.")
        elif drop >= 200:
            add(4, "This move is a mistake — it weakens your position.")
        elif drop >= 50:
            add(10, "This move is a small inaccuracy — there was a more precise option.")

        # 14. Threat detection
        for sq in chess.SQUARES:
            p = board_after.piece_at(sq)
            if p and p.color == chess.WHITE:
                if board_after.is_attacked_by(chess.BLACK, sq) and not board.is_attacked_by(chess.BLACK, sq):
                    pname = PNAME.get(p.piece_type, "piece")
                    add(3, f"⚠ After this move, your {pname} on {chess.square_name(sq)} is now under attack.")
                    break

        # 15. Strategic plan suggestions
        white_king_sq = board_after.king(chess.WHITE)
        if white_king_sq is not None and chess.square_rank(white_king_sq) == 0 and move_count > 8:
            add(12, "Try to castle soon — keeping your King in the center too long is risky.")

        # undeveloped minor pieces
        undeveloped = []
        for sq, p in board_after.piece_map().items():
            if p.color == chess.WHITE and p.piece_type in (chess.KNIGHT, chess.BISHOP):
                if chess.square_rank(sq) == 0:
                    undeveloped.append(PNAME.get(p.piece_type, "piece"))
        if undeveloped and move_count <= 20:
            add(13, f"Consider developing your remaining {undeveloped[0]} — get all your pieces active.")

        # 16. Positional concepts
        # Knight outpost
        for sq, p in board_after.piece_map().items():
            if p.color == chess.WHITE and p.piece_type == chess.KNIGHT:
                rank = chess.square_rank(sq)
                if rank in (3, 4):
                    add(14, "Nice — your knight is on a strong outpost, hard to challenge.")
                    break

        # Bad bishop — only if own pawns block its diagonals
        for sq, p in board_after.piece_map().items():
            if p.color == chess.WHITE and p.piece_type == chess.BISHOP:
                bishop_attacks = len(list(board_after.attacks(sq)))
                # A bishop on an open diagonal attacks 7-13 squares; if very few, it's blocked
                if bishop_attacks <= 3:
                    add(15, "Your bishop is blocked by your own pawns — consider opening the diagonal.")
                break

        # 17. Opening principles
        if move_count <= 14:
            # Re-count undeveloped pieces fresh here to avoid scope issues
            undeveloped_now = [
                PNAME.get(p.piece_type, "piece")
                for sq, p in board_after.piece_map().items()
                if p.color == chess.WHITE
                   and p.piece_type in (chess.KNIGHT, chess.BISHOP)
                   and chess.square_rank(sq) == 0
            ]
            if len(undeveloped_now) >= 2 and move_count > 6:
                add(16, "Try not to move the same piece twice early — develop all your pieces first.")

        # 18. Endgame coaching
        pieces = board_after.piece_map()
        num_queens = sum(1 for p in pieces.values() if p.piece_type == chess.QUEEN)
        if num_queens == 0:
            ksq = board_after.king(chess.WHITE)
            if ksq and chess.square_rank(ksq) <= 1:
                add(17, "In the endgame, activate your King — it becomes a strong piece.")

        # 19. Move category label (fallback)
        if piece_moved and not PRIORITY:
            add(30, "This is a quiet improving move — it slightly improves your position.")

        # ───────────────────────────────────────────────────────────────
        # SORT BY PRIORITY and return messages only
        # ───────────────────────────────────────────────────────────────
        PRIORITY.sort(key=lambda x: x[0])
        return [msg for _, msg in PRIORITY]

    def _why_better(self, best: chess.Move, best_piece, board: chess.Board,
                    board_after: chess.Board) -> str:
        """Return a detailed plain-English reason why the best move is better."""
        to_sq = best.to_square
        from_sq = best.from_square
        to_file = chess.square_file(to_sq)
        to_rank = chess.square_rank(to_sq)
        to_name = chess.square_name(to_sq)
        bp_name = self.PIECE_NAME.get(best_piece.piece_type, "piece")
        move_num = len(board.move_stack)

        central = {chess.D4, chess.D5, chess.E4, chess.E5}
        near_centre = {chess.C3, chess.C4, chess.C5, chess.C6,
                       chess.D3, chess.D6, chess.E3, chess.E6,
                       chess.F3, chess.F4, chess.F5, chess.F6}

        board_after_best = board.copy()
        board_after_best.push(best)

        reasons = []

        # ── Checkmate ─────────────────────────────────────────────────────────
        if board_after_best.is_checkmate():
            return f"זה שח מט — המשחק היה נגמר מיד! תמיד חפש את ציד המלך!"

        # ── Check ─────────────────────────────────────────────────────────────
        if board_after_best.is_check():
            reasons.append(
                f"it puts the opponent's King in check, forcing them to deal with the threat instead of developing their own attack")

        # ── Capture ───────────────────────────────────────────────────────────
        captured = board.piece_at(to_sq)
        if captured:
            cap_name = self.PIECE_NAME.get(captured.piece_type, "piece")
            cap_val = self.PIECE_VALUE.get(captured.piece_type, 0)
            mv_val = self.PIECE_VALUE.get(best_piece.piece_type, 0)
            if cap_val > mv_val:
                diff = cap_val - mv_val
                reasons.append(
                    f"it captures the opponent's {cap_name} for free — you gain {diff} points of material advantage")
            elif cap_val == mv_val:
                reasons.append(f"it captures the opponent's {cap_name} in an even exchange — keeping material balanced")
            else:
                reasons.append(f"it captures a piece, removing it from the board")

        # ── Fork (attacks two pieces at once) ────────────────────────────────
        attacked_pieces = []
        for sq in chess.SQUARES:
            p = board_after_best.piece_at(sq)
            if p and p.color == chess.BLACK and p.piece_type != chess.KING:
                if board_after_best.is_attacked_by(chess.WHITE, sq):
                    attacked_pieces.append(self.PIECE_NAME.get(p.piece_type, "piece"))
        if len(attacked_pieces) >= 2:
            reasons.append(
                f"it forks the opponent — attacking their {attacked_pieces[0]} and {attacked_pieces[1]} at the same time, and they can only save one!")

        # ── Attacks a valuable undefended piece ───────────────────────────────
        elif attacked_pieces:
            for sq in chess.SQUARES:
                p = board_after_best.piece_at(sq)
                if p and p.color == chess.BLACK:
                    if board_after_best.is_attacked_by(chess.WHITE, sq):
                        defenders = board_after_best.attackers(chess.BLACK, sq)
                        pname = self.PIECE_NAME.get(p.piece_type, "piece")
                        pval = self.PIECE_VALUE.get(p.piece_type, 0)
                        mv_val = self.PIECE_VALUE.get(best_piece.piece_type, 0)
                        if not defenders:
                            reasons.append(
                                f"it attacks the opponent's undefended {pname} on {chess.square_name(sq)} — they must move it or lose it")
                        elif pval > mv_val:
                            reasons.append(
                                f"it threatens to win the opponent's {pname} on {chess.square_name(sq)} which is worth more than your {bp_name}")
                        break

        # ── Central control ───────────────────────────────────────────────────
        if to_sq in central:
            controlled = len([sq for sq in chess.SQUARES
                              if board_after_best.is_attacked_by(chess.WHITE, sq)])
            reasons.append(
                f"placing your {bp_name} on {to_name} gives it maximum reach — central pieces control the most squares and influence both sides of the board")
        elif to_sq in near_centre and best_piece.piece_type in (chess.KNIGHT, chess.BISHOP):
            reasons.append(
                f"{to_name} is a strong outpost near the centre, giving your {bp_name} excellent influence over the key squares")

        # ── Development (opening principles) ─────────────────────────────────
        if move_num <= 14 and chess.square_rank(from_sq) == 0:
            if best_piece.piece_type == chess.KNIGHT:
                squares_controlled = len(list(board_after_best.attacks(to_sq)))
                reasons.append(
                    f"it develops your Knight which now controls {squares_controlled} squares — in the opening, get your pieces off the back rank as quickly as possible")
            elif best_piece.piece_type == chess.BISHOP:
                diagonal_len = len(list(board_after_best.attacks(to_sq)))
                reasons.append(
                    f"it activates your Bishop with a diagonal controlling {diagonal_len} squares — Bishops become much stronger when they have open diagonals")

        # ── King safety ───────────────────────────────────────────────────────
        if best_piece.piece_type == chess.KING and board.is_castling(best):
            reasons.append(
                "castling tucks your King safely behind your pawns and connects your Rooks — two important goals in one move!")

        # ── Rook on open file ─────────────────────────────────────────────────
        if best_piece.piece_type == chess.ROOK:
            file_pawns = [sq for sq in chess.SQUARES
                          if board_after_best.piece_at(sq) and
                          board_after_best.piece_at(sq).piece_type == chess.PAWN and
                          chess.square_file(sq) == to_file]
            if not file_pawns:
                reasons.append(
                    f"it places your Rook on an open file with no pawns blocking it — Rooks are most powerful on open files where they can attack freely")

        # ── Piece activity comparison ─────────────────────────────────────────
        if not reasons:
            my_squares_before = len(list(board.attacks(from_sq)))
            my_squares_after = len(list(board_after_best.attacks(to_sq)))
            if my_squares_after > my_squares_before:
                diff = my_squares_after - my_squares_before
                reasons.append(
                    f"your {bp_name} controls {diff} more squares from {to_name} than where it was — more active pieces give you more options every turn")
            elif best_piece.piece_type == chess.QUEEN:
                reasons.append(f"the Queen is more centralised and harder to attack from {to_name}")
            else:
                reasons.append(f"your {bp_name} is simply more active and better placed on {to_name}")

        if reasons:
            if len(reasons) == 1:
                return f"Because {reasons[0]}."
            else:
                return f"Because {reasons[0]}, and also {reasons[1]}."

        return "It gives your piece a more active and influential role in the position."

    def draw_coach_highlight(self):
        """Draw green arrow/highlight for the suggested best move."""
        if not self.coach_highlight or not self.coach_on:
            return
        from_sq, to_sq = self.coach_highlight
        fx, fy = self.sq_xy(from_sq)
        tx, ty = self.sq_xy(to_sq)
        fcx, fcy = fx + self.SQ // 2, fy + self.SQ // 2
        tcx, tcy = tx + self.SQ // 2, ty + self.SQ // 2
        # Highlight squares in blue-green
        self.canvas.create_rectangle(fx, fy, fx + self.SQ, fy + self.SQ,
                                     outline="#00c896", width=4, fill="")
        self.canvas.create_rectangle(tx, ty, tx + self.SQ, ty + self.SQ,
                                     outline="#00c896", width=4, fill="")
        # Arrow
        self.canvas.create_line(fcx, fcy, tcx, tcy,
                                fill="#00c896", width=3, arrow=tk.LAST,
                                arrowshape=(14, 18, 6))

    # ──────────────────────────────────────────────────────────────────────────
    # Move history panel
    # ──────────────────────────────────────────────────────────────────────────
    def refresh_history(self):
        self.hist_list.delete(0, tk.END)
        for i in range(0, len(self.move_history), 2):
            w_san = self.move_history[i]
            b_san = self.move_history[i + 1] if i + 1 < len(self.move_history) else ""
            move_num = i // 2 + 1
            self.hist_list.insert(tk.END, f"  {move_num:2d}. {w_san:<8} {b_san}")
        self.hist_list.yview_moveto(1.0)  # scroll to bottom

    # ──────────────────────────────────────────────────────────────────────────
    # Click handler
    # ──────────────────────────────────────────────────────────────────────────
    def on_click(self, event):
        if self.board.turn == chess.BLACK:
            return
        if self.board.is_game_over():
            return
        if self.review_mode:
            return
        if self.engine_busy:
            return

        col = event.x // self.SQ
        row = 7 - (event.y // self.SQ)
        if not (0 <= col <= 7 and 0 <= row <= 7):
            return
        sq = chess.square(col, row)

        if self.selected_sq is None:
            piece = self.board.piece_at(sq)
            if piece and piece.color == chess.WHITE:
                self.selected_sq = sq
                self.legal_targets = {m.to_square for m in self.board.legal_moves
                                      if m.from_square == sq}
                self.redraw()
        else:
            move = chess.Move(self.selected_sq, sq)
            # Auto-promote to queen
            piece = self.board.piece_at(self.selected_sq)
            if (piece and piece.piece_type == chess.PAWN
                    and chess.square_rank(sq) in (0, 7)):
                move.promotion = chess.QUEEN

            if move in self.board.legal_moves:
                self.execute_player_move(move)
            else:
                # Maybe user clicked a different own piece
                p2 = self.board.piece_at(sq)
                if p2 and p2.color == chess.WHITE:
                    self.selected_sq = sq
                    self.legal_targets = {m.to_square for m in self.board.legal_moves
                                          if m.from_square == sq}
                    self.redraw()
                    return

            self.selected_sq = None
            self.legal_targets = set()
            self.redraw()

    # ──────────────────────────────────────────────────────────────────────────
    # Move execution
    # ──────────────────────────────────────────────────────────────────────────
    def _record_capture(self, move: chess.Move):
        captured = self.board.piece_at(move.to_square)
        if self.board.is_en_passant(move):
            # The pawn is on a different square for EP
            ep_sq = chess.square(chess.square_file(move.to_square),
                                 chess.square_rank(move.from_square))
            captured = self.board.piece_at(ep_sq)
        if captured:
            if captured.color == chess.BLACK:
                self.captured_w.append(captured.symbol())
            else:
                self.captured_b.append(captured.symbol())

    def execute_player_move(self, move: chess.Move):
        san = self.board.san(move)
        is_capture = self.board.is_capture(move)
        is_castle = self.board.is_castling(move)
        self._record_capture(move)
        board_before = self.board.copy()  # snapshot for coach

        move_san = self.board.san(move)
        self.board.push(move)

        self._tts.speak(f"{self.player_name} מוציא {translate_to_hebrew(move_san)}")

        if self.board.is_check():
            self._tts.speak("שח!")
        self.last_move = move
        self.coach_highlight = None  # clear previous suggestion
        self.move_history.append(san)
        self.review_boards.append(self.board.fen())
        self.refresh_history()
        self.opening_label.config(text=detect_opening(self.board))
        self.redraw()
        self.speak(san)

        self.status_var.set("Engine thinking…")

        if self.board.is_game_over():
            self.handle_end()
        else:
            self.engine_busy = True
            threading.Thread(
                target=self._engine_and_coach,
                args=(move, board_before),
                daemon=True).start()

    def _engine_and_coach(self, player_move: chess.Move, board_before: chess.Board):
        """
        Single background thread that does ALL engine work sequentially:
        1. Evaluate the position after player's move (for coach feedback)
        2. Get engine's reply move
        3. Evaluate after engine's reply (for eval bar)
        """
        if not self.engine:
            return
        try:
            self._run_engine(player_move, board_before)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.engine_busy = False

    def _run_engine(self, player_move, board_before):
        if not self.engine:
            return

        coach_msg = None
        coach_tag = "good"
        coach_hi = None
        spoken_tip = None

        # ── Step 1: Coach feedback (pure pattern analysis, no engine call) ──────
        if self.coach_on:
            try:
                best = self.best_move_before
                drop = self.pre_move_eval  # if no post_eval, use pre as proxy

                # Try to get post-move eval from engine (optional — don't crash if fails)
                try:
                    info_after = self.engine.analyse(self.board, chess.engine.Limit(depth=10, time=0.3))
                    score_after = info_after["score"].white()
                    post_eval = float(score_after.score(mate_score=3000) or 0)
                    drop = self.pre_move_eval - post_eval
                except Exception as e:
                    drop = 0.0

                player_played_best = (best is not None and player_move == best)

                if player_played_best:
                    grade = "best";
                    coach_tag = "good"
                elif drop >= 250:
                    grade = "blunder";
                    coach_tag = "blunder"
                elif drop >= 100:
                    grade = "mistake";
                    coach_tag = "warn"
                elif drop >= 40:
                    grade = "inaccuracy";
                    coach_tag = "warn"
                elif drop >= 10:
                    grade = "slight";
                    coach_tag = "tip"
                else:
                    grade = "good";
                    coach_tag = "good"

                headers = {
                    "best": "✅ Best move! Well done!",
                    "good": "👍 Good move!",
                    "slight": "💡 Slightly better options exist.",
                    "inaccuracy": "💡 Inaccuracy – a better option was available.",
                    "mistake": "⚠️ Mistake – you gave up advantage.",
                    "blunder": f"❌ Blunder! Lost ~{abs(drop) // 100} pawn(s) of advantage.",
                }
                msg_lines = [headers[grade]]

                tips = self._explain_move_thorough(player_move, board_before, drop, best)
                msg_lines.extend(tips)

                show_best = grade not in ("best", "good")
                if show_best and best is not None:
                    try:
                        best_san = board_before.san(best)
                        msg_lines.append(f"\n🔵 Better: {best_san}")
                        coach_hi = (best.from_square, best.to_square)
                    except Exception:
                        pass

                coach_msg = "\n".join(msg_lines)

                # Build spoken parts
                import unicodedata, re
                _piece_map = {'N': 'Knight', 'B': 'Bishop', 'R': 'Rook', 'Q': 'Queen', 'K': 'King'}

                def _translate_better(text):
                    def _piece(m):
                        return 'Better: ' + _piece_map.get(m.group(1), m.group(1)) + ' ' + m.group(2)

                    return re.sub(r'Better: ([NBRQK])([a-h1-8x])', _piece, text)

                def _clean_for_tts(line):
                    out = []
                    for ch in line:
                        cat = unicodedata.category(ch)
                        if cat == 'Pd':
                            out.append(',')
                        elif cat.startswith('L') or cat.startswith('N') or cat == 'Zs' or ch in ' ,.!?:':
                            out.append(ch)
                        else:
                            out.append(' ')
                    return ' '.join(''.join(out).split()).strip().strip(',').strip()

                spoken_parts = []
                for line in msg_lines:
                    clean = _clean_for_tts(line)
                    clean = _translate_better(clean)
                    clean = translate_to_hebrew(clean)
                    if clean:
                        spoken_parts.append(clean)
                spoken_tip = '. '.join(spoken_parts) if spoken_parts else None

            except Exception:
                pass

        # ── Step 2: Engine plays its move ─────────────────────────────────────
        try:
            result = self.engine.play(self.board, chess.engine.Limit(time=0.6),
                                      options={"Skill Level": self.skill_level})
        except Exception as e:
            self.root.after(0, lambda: setattr(self, 'engine_busy', False))
            return

        # ── Step 3: Eval after engine move (for eval bar) ─────────────────────
        try:
            info2 = self.engine.analyse(self.board, chess.engine.Limit(depth=10))
            s2 = info2["score"].white()
            self.eval_score = float(s2.score(mate_score=3000) or 0)
        except Exception:
            pass

        # ── Step 4: Pre-analyse for NEXT player move ──────────────────────────
        new_pre_eval = 0.0
        new_best_move = None
        try:
            # Peek at board after engine move to get baseline for next turn
            test_board = self.board.copy()
            test_board.push(result.move)
            info3 = self.engine.analyse(test_board, chess.engine.Limit(depth=12))
            s3 = info3["score"].white()
            new_pre_eval = float(s3.score(mate_score=3000) or 0)
            new_best_move = info3.get("pv", [None])[0]
        except Exception:
            pass

        # ── Deliver everything back to UI thread ──────────────────────────────
        def _deliver():
            if coach_msg and self.coach_on:
                self._coach_msg(coach_msg, coach_tag)
                self.coach_highlight = coach_hi
            if spoken_tip and self.coach_on:
                parts = [p.strip() for p in spoken_tip.split('.') if p.strip()]
                for part in parts:
                    self.coach_speak(part)
            self.execute_engine_move(result.move)
            self.pre_move_eval = new_pre_eval
            self.best_move_before = new_best_move

        self.root.after(0, _deliver)

    def engine_move(self):
        try:
            if self.engine and not self.board.is_game_over():
                result = self.engine.play(
                    self.board,
                    chess.engine.Limit(time=0.5)
                )

                move_san = self.board.san(result.move)
                self.board.push(result.move)

                self.root.after(0, self.update_board)

                self._tts.speak(f"המחשב מוציא {translate_to_hebrew(move_san)}")

                if self.board.is_check():
                    self.speak_async("שח!")

        except Exception as e:
            print("Engine crashed:", e)

    def execute_engine_move(self, move: chess.Move):
        self.engine_busy = False
        san = self.board.san(move)
        is_capture = self.board.is_capture(move)
        is_castle = self.board.is_castling(move)
        self._record_capture(move)

        self.board.push(move)
        self.last_move = move
        self.move_history.append(san)
        self.review_boards.append(self.board.fen())
        self.refresh_history()
        self.opening_label.config(text=detect_opening(self.board))
        self.redraw()
        self.speak(san)
        winsound.Beep(600 if is_capture else 1000, 50)

        if self.board.is_game_over():
            result = self.board.result()
            self.status_label.config(text=f"Game Over: {result}")
            self.speak_async("המשחק הסתיים")
        else:
            self.status_var.set("Your turn – White")

    # ──────────────────────────────────────────────────────────────────────────
    # Undo
    # ──────────────────────────────────────────────────────────────────────────
    def undo_move(self):
        if self.review_mode:
            return
        if len(self.board.move_stack) >= 2:
            self.board.pop();
            self.board.pop()
            if len(self.move_history) >= 2:
                self.move_history.pop();
                self.move_history.pop()
            if len(self.review_boards) >= 2:
                self.review_boards.pop();
                self.review_boards.pop()
            self.last_move = None
            self.selected_sq = None
            self.legal_targets = set()
            self.coach_highlight = None
            self.pre_move_eval = 0.0
            self.best_move_before = None
            self.refresh_history()
            self.redraw()
            self._tts.speak("בוטל מהלך")
            self.status_var.set("Your turn – White")
            self._coach_msg("Move undone. Let's try again!", "info")
            self._tts.speak("בוטל מהלך. בוא ננסה שוב!")

    # ──────────────────────────────────────────────────────────────────────────
    # Game over
    # ──────────────────────────────────────────────────────────────────────────
    def handle_end(self):
        res = self.board.result()
        if res == "1-0":
            self.stats["wins"] += 1;
            msg = f"ניצחת, {self.player_name}! כל הכבוד!"
        elif res == "0-1":
            self.stats["losses"] += 1;
            msg = "המחשב ניצח הפעם. תמשיך להתאמן!"
        else:
            self.stats["draws"] += 1;
            msg = "תיקו. שיחקת יפה!"
        self.coach_speak(msg)
        self.save_stats()
        self.stats_label.config(text=self._stats_text())
        self.status_var.set(f"Game over – {res}")
        messagebox.showinfo("Game Over", f"{msg}\n\nResult: {res}")

    def _stats_text(self):
        return (f"🏆 {self.player_name}:  "
                f"{self.stats['wins']}W  {self.stats['losses']}L  {self.stats['draws']}D")

    # ──────────────────────────────────────────────────────────────────────────
    # New game
    # ──────────────────────────────────────────────────────────────────────────
    def new_game(self):
        self.board = chess.Board()
        self.last_move = None
        self.selected_sq = None
        self.legal_targets = set()
        self.eval_score = 0.0
        self.move_history = []
        self.captured_w = []
        self.captured_b = []
        self.review_boards = []
        self.white_time = 600.0
        self.black_time = 600.0
        self.engine_busy = False
        self.coach_highlight = None
        self.pre_move_eval = 0.0
        self.best_move_before = None
        self.exit_review()
        self.refresh_history()
        self.opening_label.config(text="")
        self.status_var.set("Your turn – White")
        self._coach_msg("New game! Good luck! I will coach you as you play.", "info")
        self._tts.speak("משחק חדש! בהצלחה!")
        self.redraw()

    # ──────────────────────────────────────────────────────────────────────────
    # Review mode
    # ──────────────────────────────────────────────────────────────────────────
    def start_review(self):
        if not self.review_boards:
            messagebox.showinfo("Review", "No moves to review yet.")
            return
        self.review_mode = True
        self.review_idx = len(self.review_boards) - 1
        self.review_frame.pack(pady=4)
        self.status_var.set("Review mode – use ◀ ▶ to step through moves")
        self._show_review_pos()

    def exit_review(self):
        self.review_mode = False
        self.review_frame.pack_forget()
        self.board = chess.Board()
        # Replay all moves to restore live board
        tmp = chess.Board()
        for san in self.move_history:
            try:
                tmp.push_san(san)
            except:
                break
        self.board = tmp
        self.redraw()

    def review_step(self, delta: int):
        if not self.review_mode:
            return
        self.review_idx = max(0, min(len(self.review_boards) - 1, self.review_idx + delta))
        self._show_review_pos()

    def review_jump(self, idx: int):
        if idx == -1:
            idx = len(self.review_boards) - 1
        self.review_idx = max(0, min(len(self.review_boards) - 1, idx))
        self._show_review_pos()

    def _show_review_pos(self):
        self.board = chess.Board(self.review_boards[self.review_idx])
        move_num = self.review_idx + 1
        san = self.move_history[self.review_idx] if self.review_idx < len(self.move_history) else "?"
        color = "White" if move_num % 2 == 1 else "Black"
        self.status_var.set(f"Review: move {move_num} – {color} played {san}")
        self.last_move = None
        self.redraw()
        # Highlight reviewed move on board
        if self.review_idx > 0:
            # We need the previous board to know from/to squares
            prev = chess.Board(self.review_boards[self.review_idx - 1])
            moves_played = list(prev.legal_moves)
            # Find which move was made (compare FEN)
            for m in prev.legal_moves:
                prev.push(m)
                if prev.fen() == self.board.fen():
                    self.last_move = m
                    break
                prev.pop()
        self.redraw()

    # ──────────────────────────────────────────────────────────────────────────
    # Speech — Hebrew via edge_tts SpeechManager
    # ──────────────────────────────────────────────────────────────────────────

    def speak_async(self, text: str):
        """Queue text for Hebrew TTS speech."""
        if text and text.strip():
            self._tts.speak(translate_to_hebrew(str(text)))

    def coach_speak(self, text: str):
        """Speak coach feedback — strip emojis then queue for Hebrew TTS."""
        if not self.coach_on:
            return
        for ch in ['✅', '👌', '💡', '⚠️', '❌', '🔵', '👍', '💰', '🎯', '👑', '🏰', '📌', '💥', '⚠', '–', '—']:
            text = text.replace(ch, '')
        text = text.strip()
        if text:
            self._tts.speak(translate_to_hebrew(text))

    def speak(self, text: str):
        """Speak a chess SAN move in Hebrew."""
        readable = (text
                    .replace('N', 'פרש').replace('B', 'רץ')
                    .replace('R', 'צריח').replace('Q', 'מלכה')
                    .replace('K', 'מלך').replace('x', 'לוכד')
                    .replace('+', 'שח').replace('#', 'שח מט'))
        self._tts.speak(readable)

    # ──────────────────────────────────────────────────────────────────────────
    def __del__(self):
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass
        try:
            self._tts.stop()
        except:
            pass


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = ChessUltimate(root)
    root.mainloop()

# -*- coding: utf-8 -*-
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog, font as tkfont
import chess
import chess.engine
import threading
from pathlib import Path
import json
import time
import queue
import tempfile
import os
import winsound

try:
    import tksvg

    HAS_TKSVG = True
except ImportError:
    HAS_TKSVG = False

# ── Paths ─────────────────────────────────────────────────────────────────────
PIECES_FOLDER = Path("pieces")
ENGINE_PATH = Path("stockfish/stockfish-windows-x86-64-avx2.exe")
STATS_FILE = "chess_stats.json"


# ── Opening book (ECO prefix table) ───────────────────────────────────────────

def _load_openings() -> dict:
    """Load openings from opening.json if it exists, otherwise use built-in list."""
    json_path = Path("Clean_openings.json")
    if json_path.exists():
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
            print(f"Loaded {len(data)} openings from opening.json")
            return data
        except Exception as e:
            print(f"Could not load opening.json: {e} — using built-in list")

    # Built-in fallback
    return {
        # --- 1. e4 ---
        "e4": "King's Pawn Opening",
        "e4 e5": "Open Game",
        "e4 e5 Nf3": "King's Knight Opening",
        "e4 e5 Nf3 Nc6 Bb5": "Ruy López",
        "e4 e5 Nf3 Nc6 Bb5 a6": "Ruy López – Morphy Defence",
        "e4 e5 Nf3 Nc6 Bb5 Nf6": "Ruy López – Berlin Defence",
        "e4 e5 Nf3 Nc6 Bb5 d6": "Ruy López – Steinitz Defence",
        "e4 e5 Nf3 Nc6 Bb5 Bc5": "Ruy López – Classical Defence",

        "e4 e5 Nf3 Nc6 Bc4": "Italian Game",
        "e4 e5 Nf3 Nc6 Bc4 Bc5": "Giuoco Piano",
        "e4 e5 Nf3 Nc6 Bc4 Bc5 c3": "Giuoco Pianissimo",
        "e4 e5 Nf3 Nc6 Bc4 Nf6": "Two Knights Defence",
        "e4 e5 Nf3 Nc6 Bc4 Nf6 Ng5": "Fried Liver Attack",

        "e4 e5 Nf3 Nc6 d4": "Scotch Game",
        "e4 e5 Nf3 Nc6 d4 exd4 Nxd4": "Scotch Game – Classical",

        "e4 e5 Nc3": "Vienna Game",
        "e4 e5 Nc3 Nf6": "Vienna – Falkbeer",

        "e4 e5 f4": "King's Gambit",
        "e4 e5 f4 exf4": "King's Gambit Accepted",
        "e4 e5 f4 d5": "Falkbeer Countergambit",

        "e4 c5": "Sicilian Defence",
        "e4 c5 Nf3 d6": "Sicilian – Classical",
        "e4 c5 Nf3 d6 d4": "Sicilian – Open",
        "e4 c5 d4": "Sicilian – Smith-Morra Gambit",
        "e4 c5 Nc3": "Sicilian – Closed",

        "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 a6": "Sicilian – Najdorf",
        "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 g6": "Sicilian – Dragon",
        "e4 c5 Nf3 Nc6 d4 cxd4 Nxd4 g6": "Sicilian – Accelerated Dragon",
        "e4 c5 Nf3 d6 d4 cxd4 Nxd4 Nf6 Nc3 e6": "Sicilian – Scheveningen",
        "e4 c5 Nf3 e6 d4 cxd4 Nxd4 Nc6": "Sicilian – Taimanov",
        "e4 c5 Nf3 e6 d4 cxd4 Nxd4 a6": "Sicilian – Kan",
        "e4 c5 c3": "Sicilian – Alapin",

        "e4 e6": "French Defence",
        "e4 e6 d4 d5": "French – Main Line",
        "e4 e6 d4 d5 Nc3 Bb4": "French – Winawer",
        "e4 e6 d4 d5 Nd2": "French – Tarrasch",

        "e4 c6": "Caro–Kann Defence",
        "e4 c6 d4 d5 Nc3 dxe4": "Caro–Kann – Classical",
        "e4 c6 d4 d5 Nd2": "Caro–Kann – Tartakower",

        "e4 d5": "Scandinavian Defence",
        "e4 d5 exd5 Qxd5 Nc3": "Scandinavian – Main Line",

        "e4 Nf6": "Alekhine Defence",
        "e4 Nf6 e5 Nd5 d4": "Alekhine – Modern",

        "e4 d6": "Pirc Defence",
        "e4 d6 d4 Nf6 Nc3 g6": "Pirc – Classical",
        "e4 g6": "Modern Defence",

        "e4 b6": "Owen's Defence",

        # --- 1. d4 ---
        "d4": "Queen's Pawn Opening",
        "d4 d5": "Closed Game",
        "d4 d5 c4": "Queen's Gambit",
        "d4 d5 c4 e6": "Queen's Gambit Declined",
        "d4 d5 c4 dxc4": "Queen's Gambit Accepted",
        "d4 d5 c4 c6": "Slav Defence",
        "d4 d5 c4 e6 Nc3 c5": "Tarrasch Defence",

        "d4 d5 Nf3": "London System (transposition)",
        "d4 Nf6": "Indian Defence",
        "d4 Nf6 c4": "Indian Game",
        "d4 Nf6 c4 g6": "King's Indian Defence",
        "d4 Nf6 c4 e6": "Nimzo/Queen's Indian Setup",
        "d4 Nf6 c4 e6 Nc3 Bb4": "Nimzo-Indian Defence",
        "d4 Nf6 c4 e6 g3": "Catalan Opening",

        "d4 f5": "Dutch Defence",
        "d4 Nf6 Bg5": "Trompowsky Attack",

        "d4 c5": "Benoni Defence",
        "d4 Nf6 c4 c5 d5": "Benoni – Modern",
        "d4 Nf6 c4 c5 d5 b5": "Benko Gambit",

        # --- 1. c4 ---
        "c4": "English Opening",
        "c4 e5": "English – Reversed Sicilian",
        "c4 c5": "English – Symmetrical",
        "c4 g6": "English – King's Fianchetto",
        "c4 Nf6 Nc3 e5": "English – Four Knights",
        "c4 g6 Nc3 Bg7 e4": "English – Botvinnik System",

        # --- 1. Nf3 ---
        "Nf3": "Réti Opening",
        "Nf3 d5 g3": "Réti – King's Fianchetto",
        "Nf3 d5 b3": "Zukertort Opening",
        "Nf3 c5": "Réti – Sicilian Invitation",

        # --- 1. f4 ---
        "f4": "Bird's Opening",
        "f4 e5": "From Gambit",
        "f4 g6": "Bird – Leningrad Variation",

        # --- 1. b4 ---
        "b4": "Polish (Sokolsky) Opening",
        "b4 e5": "Polish Gambit",

        # --- 1. g4 ---
        "g4": "Grob Attack",
        "g4 d5": "Grob – Spike Variation",

        # --- Misc ---
        "b3": "Nimzowitsch–Larsen Attack",
        "g3": "King's Fianchetto Opening",
        "Nc3": "Dunst Opening",
        "a3": "Anderssen's Opening",
        "h3": "Clemenz Opening",
        "a4": "Ware Opening",
        "h4": "Desprez Opening",
    }


def translate_to_hebrew(text: str) -> str:
    """Translate English spoken text to Hebrew using phrase substitution."""
    result = text
    for eng, heb in sorted(HEBREW_PHRASES.items(), key=lambda x: -len(x[0])):
        result = result.replace(eng, heb)
    return result


OPENINGS = _load_openings()


def detect_opening(board: chess.Board) -> str:
    """Return the best matching opening name for the current move stack."""
    moves = list(board.move_stack)
    tmp = chess.Board()
    san_list = []
    for m in moves:
        san_list.append(tmp.san(m).replace("x", "").replace("+", "").replace("#", ""))
        tmp.push(m)
    # Walk backwards from longest prefix to shortest
    for length in range(len(san_list), 0, -1):
        key = " ".join(san_list[:length])
        if key in OPENINGS:
            return OPENINGS[key]
    return ""


HEBREW_PHRASES = {
    # Move announcements
    "plays": "מוציא",
    "Computer plays": "המחשב מוציא",
    "Check": "שח",
    "Check!": "שח!",
    "Checkmate": "שח מט",
    "Undo": "בוטל מהלך",
    "Game over": "המשחק הסתיים",

    # Welcome / setup
    "Good luck": "בהצלחה",
    "Welcome": "ברוך הבא",
    "New game": "משחק חדש",
    "Difficulty set to Easy": "רמה קלה",
    "Difficulty set to Medium": "רמה בינונית",
    "Difficulty set to Pro": "רמה מקצועית",
    "Coach is ON. I will help you!": "המאמן פעיל. אני אעזור לך!",
    "Coach is off.": "המאמן כבוי.",

    # Game results
    "You won": "ניצחת",
    "Congratulations": "כל הכבוד",
    "The engine wins this time. Keep practising!": "המחשב ניצח הפעם. תמשיך להתאמן!",
    "It is a draw. Well played!": "תיקו. שיחקת יפה!",

    # Move grades
    "Best move! Well done!": "המהלך הטוב ביותר! כל הכבוד!",
    "Good move!": "מהלך טוב!",
    "Inaccuracy": "אי דיוק",
    "Mistake": "טעות",
    "Blunder": "בלונדר חמור",
    "Move played.": "מהלך בוצע.",

    # Coach tips — piece safety
    "is undefended": "אינו מוגן",
    "the opponent can take it": "היריב יכול לקחת אותו",
    "Moving away left your": "הזזת הכלי חשפה את ה",
    "undefended": "ללא הגנה",

    # Coach tips — tactics
    "You missed CHECKMATE": "פספסת שח מט",
    "was the winning move": "היה המהלך המנצח",
    "יכול היה לתפוס": "יכול היה לתפוס",
    "for free": "בחינם",
    "יכול היה לנוע ל": "יכול היה לנוע ל",
    "ולשים את המלך בשח": "ולשים את המלך בשח",

    # Coach tips — suggestions
    "Better": "עדיף",
    "consider moving your": "שקול להזיז את ה",
    "הוא משבצת חזקה יותר": "הוא משבצת חזקה יותר",
    "Because": "כי",

    # Coach tips — opening
    "Good — developing your pieces early is the right idea!": "טוב — לפתח כלים מוקדם זה הכיוון הנכון!",
    "Good central pawn push": "דחיפת רגלי מרכז טובה",
    "controlling the centre": "שולטת במרכז",
    "Bringing your Queen out early is risky": "הוצאת המלכה מוקדם היא מסוכנת",
    "develop your": "פתח את ה",
    "first": "קודם",

    # Coach tips — king safety
    "Moving your King early loses castling rights": "הזזת המלך מוקדם מאבדת זכות הצרחה",
    "try to castle first to stay safe": "נסה להצריח קודם להישאר מוגן",
    "castling keeps your King safe and connects your Rooks": "הצרחה שומרת על המלך ומחברת צריחים",

    # Coach tips — pawn structure
    "You now have doubled pawns": "יש לך עכשיו רגלים כפולים",
    "they can be hard to defend": "הם קשים להגנה",

    # Coach tips — strategy
    "Try to castle soon": "נסה להצריח בקרוב",
    "keeping your King in the center too long is risky": "להשאיר את המלך במרכז זמן רב מסוכן",
    "Consider developing your remaining": "שקול לפתח את ה",
    "get all your pieces active": "הפוך את כל הכלים לפעילים",
    "your knight is on a strong outpost": "הפרש שלך על עמדה חזקה",
    "hard to challenge": "קשה לאתגר",
    "Your bishop is blocked by your own pawns": "הרץ שלך חסום על ידי הרגלים שלך",
    "consider opening the diagonal": "שקול לפתוח את האלכסון",
    "Try not to move the same piece twice early": "נסה לא להזיז את אותו כלי פעמיים מוקדם",
    "develop all your pieces first": "פתח את כל הכלים קודם",
    "In the endgame, activate your King": "בסיומה, הפעל את המלך",
    "it becomes a strong piece": "הוא הופך לכלי חזק",
    "This is a quiet improving move": "זה מהלך שקט משפר",
    "it slightly improves your position": "הוא משפר מעט את עמדתך",

    # Blunder severity
    "This move is a serious blunder": "מהלך זה הוא בלונדר חמור",
    "it heavily worsens your position": "הוא מחמיר מאוד את עמדתך",
    "This move is a mistake": "מהלך זה הוא טעות",
    "it weakens your position": "הוא מחליש את עמדתך",
    "This move is a small inaccuracy": "מהלך זה הוא אי דיוק קטן",
    "there was a more precise option": "הייתה אפשרות מדויקת יותר",

    # Threat detection
    "After this move, your": "אחרי המהלך הזה, ה",
    "is now under attack": "נמצא תחת מתקפה",

    # Captures
    "Nice capture! You traded well.": "לכידה יפה! סחרת טוב.",

    # Theory
    "Theory suggests": "התיאוריה מציעה",
    "leading to the": "המובילה ל",
    "You are out of the opening book": "יצאת מספר הפתיחות",
    "Coach says": "המאמן אומר",

    # Piece names for move announcements
    "Knight": "פרש",
    "Bishop": "רץ",
    "Rook": "צריח",
    "Queen": "מלכה",
    "King": "מלך",
    "takes": "לוכד",
    "check": "שח",
    "checkmate": "שח מט",
    "pawn": "רגלי",
    "knight": "פרש",
    "bishop": "רץ",
    "rook": "צריח",
    "queen": "מלכה",
    "king": "מלך",
    "piece": "כלי",
    "Good move!": "מהלך טוב!",
    "Bad move!": "מהלך גרוע!",
    "Check!": "שח!",
    "Checkmate": "מט!",
    "Develop your knight": "פתח את הפרש",
    "Control the center": "שלוט במרכז",
    "Castle now": "עשה רוקדה עכשיו",
    "Welcome Rami! Good luck!": "ברוך הבא רמי! בהצלחה!"
}


# ── Main application ───────────────────────────────────────────────────────────
# ── SpeechManager — Hebrew TTS via edge_tts ───────────────────────────────────

class SpeechManager:
    """Background Hebrew TTS using edge_tts (he-IL-AvriNeural)."""

    def __init__(self, voice="he-IL-AvriNeural"):
        self.voice = voice
        self.msg_queue = queue.Queue()
        self._busy = False
        self.thread = threading.Thread(target=self._worker, daemon=True)
        self.thread.start()

    @property
    def is_busy(self):
        return self._busy or not self.msg_queue.empty()

    def speak(self, text: str):
        """Queue a text to be spoken in Hebrew."""
        if text and text.strip():
            self.msg_queue.put(str(text).strip())

    def stop(self):
        """Shut down the worker thread."""
        self.msg_queue.put(None)

    def _worker(self):
        """Background thread — processes messages one at a time.
        asyncio is imported LOCALLY here so it never touches the main thread's
        event loop, which chess.engine needs to stay as ProactorEventLoop.
        """
        import asyncio, sys
        if sys.platform.startswith("win"):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        while True:
            text = self.msg_queue.get()
            if text is None:
                break
            self._busy = True
            try:
                asyncio.run(self._speak_async(text))
            except Exception as e:
                print(f"[edge_tts] error: {e}")
            finally:
                self._busy = False

    async def _speak_async(self, text: str):
        """Generate Hebrew MP3 via edge_tts and play it. Retries on 503."""
        import edge_tts
        from playsound import playsound
        import asyncio

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            temp_path = f.name

        for attempt in range(3):
            try:
                tts = edge_tts.Communicate(text, voice=self.voice)
                await tts.save(temp_path)
                playsound(temp_path)
                break  # success
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(1.5)  # wait before retry
                else:
                    print(f"[TTS] Failed after 3 attempts: {e}")
            finally:
                if attempt == 2 or os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except:
                        pass


class ChessUltimate:
    SQ = 85  # square pixel size
    PAD = 20  # board left/top padding inside canvas

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("♟ Chess Master Ultimate")
        self.root.geometry("1120x980")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(False, False)

        # ── State ─────────────────────────────────────────────────────────────
        self.stats = self.load_stats()
        self.player_name = "Player 1"

        self.board = chess.Board()
        self.engine = None
        self.skill_level = 5
        self.selected_sq = None
        self.legal_targets = set()
        self.last_move = None
        self.piece_images = {}
        self.eval_score = 0.0
        self.opening_name = ""
        self.move_history = []
        self.captured_w = []
        self.captured_b = []
        self.review_mode = False
        self.review_idx = 0
        self.review_boards = []
        self.engine_busy = False

        # ── Coach ─────────────────────────────────────────────────────────────
        self.coach_on = True
        self.pre_move_eval = 0.0
        self.best_move_before = None
        self.coach_highlight = None

        # ── Clocks ────────────────────────────────────────────────────────────
        self.white_time = 600.0
        self.black_time = 600.0
        self.last_tick = time.time()

        # ── Build UI ──────────────────────────────────────────────────────────
        self.init_engine()

        # ── Speech — Hebrew TTS via edge_tts (MUST be after init_engine) ──────
        self._tts = SpeechManager(voice="he-IL-AvriNeural")
        self.create_ui()
        self.load_piece_images()
        self.update_clock()
        self.root.after(150, self.redraw)
        self.root.after(300, self._ask_name_on_start)

    # ──────────────────────────────────────────────────────────────────────────
    # Persistence
    # ──────────────────────────────────────────────────────────────────────────
    def load_stats(self):
        if Path(STATS_FILE).exists():
            with open(STATS_FILE) as f:
                return json.load(f)
        return {"wins": 0, "losses": 0, "draws": 0}

    def save_stats(self):
        with open(STATS_FILE, "w") as f:
            json.dump(self.stats, f)

    def ask_name(self):
        n = simpledialog.askstring("Welcome", "Enter your name:", initialvalue="Player 1")
        return n if n else "Player 1"

    def _ask_name_on_start(self):
        # Bring window to front so the dialog is visible
        self.root.lift()
        self.root.focus_force()
        n = simpledialog.askstring("ברוך הבא! / Welcome",
                                   "Enter your name:\nהכנס את שמך:",
                                   initialvalue="", parent=self.root)
        self.player_name = n.strip() if n and n.strip() else "שחקן"
        if hasattr(self, 'stats_label'):
            self.stats_label.config(text=self._stats_text())
        # Speak welcome only after name is confirmed
        self.root.after(500, lambda: self.speak_async(f"ברוך הבא {self.player_name}! בהצלחה!"))

    # ──────────────────────────────────────────────────────────────────────────
    # Engine
    # ──────────────────────────────────────────────────────────────────────────
    def init_engine(self):
        if ENGINE_PATH.exists():
            try:
                self.engine = chess.engine.SimpleEngine.popen_uci(str(ENGINE_PATH))
                self.engine.configure({"Skill Level": self.skill_level})
            except Exception as e:
                print(f"[ENGINE] Failed to load: {e}")

    def set_difficulty(self, level):
        text = {0: "Easy", 10: "Medium", 20: "Pro"}.get(level, "Easy")

        self.skill_level = level

        if self.engine:
            try:
                self.engine.configure({"Skill Level": level})
            except:
                pass

        self.diff_label.config(text=f"Difficulty: {text}")
        self.speak_async({"Easy": "רמה קלה", "Medium": "רמה בינונית", "Pro": "רמה מקצועית"}.get(text, text))

    # ──────────────────────────────────────────────────────────────────────────
    # UI construction
    # ──────────────────────────────────────────────────────────────────────────
    def create_ui(self):
        BG = "#1a1a2e"
        GOLD = "#f1c40f"
        FG = "#ecf0f1"
        ACCENT = "#16213e"

        # ── Top bar ───────────────────────────────────────────────────────────
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill=tk.X, padx=20, pady=(8, 2))

        self.stats_label = tk.Label(top,
                                    text=self._stats_text(), fg=GOLD, bg=BG, font=("Consolas", 12, "bold"))
        self.stats_label.pack(side=tk.LEFT)

        # Difficulty display (attached to top bar)
        self.diff_label = tk.Label(
            top,
            text="Difficulty: Easy",
            fg="#ffffff",
            bg=BG,
            font=("Consolas", 11, "bold")
        )
        self.diff_label.pack(side=tk.LEFT, padx=20)

        self.opening_label = tk.Label(top, text="", fg="#95a5a6", bg=BG, font=("Consolas", 10, "italic"))
        self.opening_label.pack(side=tk.LEFT, padx=20)

        # ── Clocks ────────────────────────────────────────────────────────────
        clk = tk.Frame(self.root, bg=BG)
        clk.pack(fill=tk.X, padx=50, pady=2)
        self.w_clock = tk.Label(clk, text="10:00", font=("Consolas", 22, "bold"), fg="#2ecc71", bg=BG)
        self.w_clock.pack(side=tk.LEFT)
        self.b_clock = tk.Label(clk, text="10:00", font=("Consolas", 22, "bold"), fg="#e74c3c", bg=BG)
        self.b_clock.pack(side=tk.RIGHT)

        # ── Main row: eval bar + board + right panel ───────────────────────────
        main_row = tk.Frame(self.root, bg=BG)
        main_row.pack(padx=10, pady=4)

        # Eval bar (10px wide, 680px tall)
        eval_col = tk.Frame(main_row, bg=BG)
        eval_col.pack(side=tk.LEFT, padx=(0, 8), anchor="n")
        self.eval_canvas = tk.Canvas(eval_col, width=22, height=self.SQ * 8,
                                     bg="#2c2c2c", highlightthickness=1,
                                     highlightbackground="#555")
        self.eval_canvas.pack()
        self.eval_label = tk.Label(eval_col, text="0.0", fg=FG, bg=BG, font=("Consolas", 9))
        self.eval_label.pack(pady=2)

        # Board canvas
        board_col = tk.Frame(main_row, bg=BG)
        board_col.pack(side=tk.LEFT)

        # Rank/file labels around the board
        rank_labels_left = tk.Frame(board_col, bg=BG)
        rank_labels_left.grid(row=1, column=0)
        for i, r in enumerate("87654321"):
            tk.Label(rank_labels_left, text=r, fg="#7f8c8d", bg=BG,
                     font=("Consolas", 9), width=2,
                     height=1).pack(pady=(self.SQ // 2 - 6, self.SQ // 2 - 7))

        self.canvas = tk.Canvas(board_col, width=self.SQ * 8, height=self.SQ * 8,
                                bg="#2c3e50", highlightthickness=2,
                                highlightbackground="#4a4a6a")
        self.canvas.grid(row=1, column=1)
        self.canvas.bind("<Button-1>", self.on_click)

        file_frame = tk.Frame(board_col, bg=BG)
        file_frame.grid(row=2, column=1)
        for ch in "abcdefgh":
            tk.Label(file_frame, text=ch, fg="#7f8c8d", bg=BG,
                     font=("Consolas", 9), width=int(self.SQ / 7)).pack(side=tk.LEFT)

        # Captured pieces strips
        cap_frame = tk.Frame(board_col, bg=BG)
        cap_frame.grid(row=0, column=1, sticky="w")
        tk.Label(cap_frame, text="Black lost:", fg="#95a5a6", bg=BG,
                 font=("Consolas", 9)).pack(side=tk.LEFT)
        self.cap_black_label = tk.Label(cap_frame, text="", fg="#ecf0f1", bg=BG,
                                        font=("Arial", 11))
        self.cap_black_label.pack(side=tk.LEFT)

        cap_frame2 = tk.Frame(board_col, bg=BG)
        cap_frame2.grid(row=3, column=1, sticky="w")
        tk.Label(cap_frame2, text="White lost:", fg="#95a5a6", bg=BG,
                 font=("Consolas", 9)).pack(side=tk.LEFT)
        self.cap_white_label = tk.Label(cap_frame2, text="", fg="#ecf0f1", bg=BG,
                                        font=("Arial", 11))
        self.cap_white_label.pack(side=tk.LEFT)

        # ── Right panel ───────────────────────────────────────────────────────
        right = tk.Frame(main_row, bg=ACCENT, relief="flat", bd=0)
        right.pack(side=tk.LEFT, padx=(12, 0), fill=tk.Y)

        tk.Label(right, text="MOVE HISTORY", fg=GOLD, bg=ACCENT,
                 font=("Consolas", 10, "bold")).pack(pady=(8, 2))

        hist_frame = tk.Frame(right, bg=ACCENT)
        hist_frame.pack(fill=tk.BOTH, expand=True, padx=6)

        scrollbar = tk.Scrollbar(hist_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.hist_list = tk.Listbox(hist_frame, width=22, height=28,
                                    bg="#0f0f23", fg=FG, selectbackground="#273c75",
                                    font=("Consolas", 10), yscrollcommand=scrollbar.set,
                                    highlightthickness=0, bd=0)
        self.hist_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.hist_list.yview)

        # ── Coach panel ───────────────────────────────────────────────────────
        tk.Frame(right, bg="#0a0a1a", height=2).pack(fill=tk.X, padx=6, pady=(8, 4))

        coach_hdr = tk.Frame(right, bg=ACCENT)
        coach_hdr.pack(fill=tk.X, padx=6)
        tk.Label(coach_hdr, text="🎓 COACH", fg="#27ae60", bg=ACCENT,
                 font=("Consolas", 10, "bold")).pack(side=tk.LEFT)
        self.coach_toggle_btn = tk.Button(
            coach_hdr, text="ON", bg="#27ae60", fg="white",
            font=("Consolas", 8, "bold"), relief="flat", padx=6, pady=1,
            cursor="hand2", command=self.toggle_coach)
        self.coach_toggle_btn.pack(side=tk.RIGHT)

        coach_msg_frame = tk.Frame(right, bg="#0d1117", relief="flat")
        coach_msg_frame.pack(fill=tk.X, padx=6, pady=(2, 6))

        self.coach_text = tk.Text(
            coach_msg_frame, width=22, height=8,
            bg="#0d1117", fg="#a8d8a8",
            font=("Consolas", 9), wrap=tk.WORD,
            relief="flat", padx=6, pady=4,
            state=tk.DISABLED, cursor="arrow")
        self.coach_text.pack(fill=tk.BOTH)

        # Tag styles for coach messages
        self.coach_text.tag_config("good", foreground="#2ecc71")
        self.coach_text.tag_config("warn", foreground="#f39c12")
        self.coach_text.tag_config("blunder", foreground="#e74c3c")
        self.coach_text.tag_config("info", foreground="#95a5a6")
        self.coach_text.tag_config("tip", foreground="#3498db")

        self._coach_msg("Hi! I'll guide you during the game.\nMake your first move! ♟", "info")

        # ── Bottom buttons ────────────────────────────────────────────────────
        btm = tk.Frame(self.root, bg=BG)
        btm.pack(pady=8)

        def btn(parent, text, cmd, color="#34495e"):
            return tk.Button(parent, text=text, command=cmd, bg=color, fg="white",
                             font=("Consolas", 10, "bold"), relief="flat", padx=10, pady=4,
                             cursor="hand2", activebackground="#5d6d7e", activeforeground="white")

        btn(btm, "↩  Undo", self.undo_move, "#e67e22").pack(side=tk.LEFT, padx=6)
        btn(btm, "Easy", lambda: self.set_difficulty(0)).pack(side=tk.LEFT, padx=4)
        btn(btm, "Medium", lambda: self.set_difficulty(10)).pack(side=tk.LEFT, padx=4)
        btn(btm, "Pro", lambda: self.set_difficulty(20)).pack(side=tk.LEFT, padx=4)
        btn(btm, "⟳  New Game", self.new_game, "#27ae60").pack(side=tk.LEFT, padx=6)
        btn(btm, "▶  Review Game", self.start_review, "#8e44ad").pack(side=tk.LEFT, padx=6)

        # Review nav (hidden until review mode)
        self.review_frame = tk.Frame(self.root, bg=BG)
        btn(self.review_frame, "◀◀ Start", lambda: self.review_jump(0), "#2c3e50").pack(side=tk.LEFT, padx=4)
        btn(self.review_frame, "◀ Prev", lambda: self.review_step(-1), "#2c3e50").pack(side=tk.LEFT, padx=4)
        btn(self.review_frame, "▶ Next", lambda: self.review_step(+1), "#2c3e50").pack(side=tk.LEFT, padx=4)
        btn(self.review_frame, "▶▶ End", lambda: self.review_jump(-1), "#2c3e50").pack(side=tk.LEFT, padx=4)
        btn(self.review_frame, "✕ Exit Review", self.exit_review, "#c0392b").pack(side=tk.LEFT, padx=8)

        # Status bar
        self.status_var = tk.StringVar(value="Your turn – White")
        tk.Label(self.root, textvariable=self.status_var, fg="#bdc3c7", bg=BG,
                 font=("Consolas", 10)).pack(pady=(0, 6))

    # ──────────────────────────────────────────────────────────────────────────
    # Piece images
    # ──────────────────────────────────────────────────────────────────────────
    def load_piece_images(self):
        MAP = {'K': 'wk', 'Q': 'wq', 'R': 'wr', 'B': 'wb', 'N': 'wn', 'P': 'wp',
               'k': 'bk', 'q': 'bq', 'r': 'br', 'b': 'bb', 'n': 'bn', 'p': 'bp'}
        if HAS_TKSVG:
            for sym, fname in MAP.items():
                p = PIECES_FOLDER / f"{fname}.svg"
                if p.exists():
                    self.piece_images[sym] = tksvg.SvgImage(
                        file=str(p), scaletoheight=int(self.SQ * 0.84))
        # If no SVG images loaded, we fall back to Unicode rendering in draw_pieces

    # ──────────────────────────────────────────────────────────────────────────
    # Clock
    # ──────────────────────────────────────────────────────────────────────────
    def update_clock(self):
        now = time.time()
        dt = now - self.last_tick
        self.last_tick = now

        if not self.board.is_game_over() and not self.review_mode:
            if self.board.turn == chess.WHITE:
                self.white_time = max(0.0, self.white_time - dt)
            else:
                self.black_time = max(0.0, self.black_time - dt)

        self.w_clock.config(text=self._fmt(self.white_time))
        self.b_clock.config(text=self._fmt(self.black_time))
        self.root.after(200, self.update_clock)

    def _fmt(self, s):
        m, sec = divmod(int(s), 60)
        return f"{m:02d}:{sec:02d}"

    # ──────────────────────────────────────────────────────────────────────────
    # Drawing
    # ──────────────────────────────────────────────────────────────────────────
    def redraw(self):
        self.canvas.delete("all")
        self.draw_squares()
        self.draw_legal_dots()
        self.draw_coach_highlight()
        self.draw_pieces()
        self.draw_eval_bar()
        self.update_captured_display()

    def sq_xy(self, sq):
        """Top-left pixel of a square."""
        c = chess.square_file(sq)
        r = 7 - chess.square_rank(sq)
        return c * self.SQ, r * self.SQ

    def draw_squares(self):
        LIGHT = "#EBECD0"
        DARK = "#779556"
        LAST = "#F7F769"
        SEL = "#66B2FF"
        CHECK = "#FF4444"

        in_check_sq = None
        if self.board.is_check():
            in_check_sq = self.board.king(self.board.turn)

        for sq in chess.SQUARES:
            c = chess.square_file(sq)
            r = 7 - chess.square_rank(sq)
            x0, y0 = c * self.SQ, r * self.SQ
            x1, y1 = x0 + self.SQ, y0 + self.SQ

            color = LIGHT if (c + chess.square_rank(sq)) % 2 else DARK

            if self.last_move and sq in (self.last_move.from_square, self.last_move.to_square):
                color = LAST
            if self.selected_sq == sq:
                color = SEL
            if sq == in_check_sq:
                color = CHECK

            self.canvas.create_rectangle(x0, y0, x1, y1, fill=color, outline="")

    def draw_legal_dots(self):
        """Draw small dots on legal target squares for the selected piece."""
        for sq in self.legal_targets:
            x0, y0 = self.sq_xy(sq)
            cx, cy = x0 + self.SQ // 2, y0 + self.SQ // 2
            has_piece = self.board.piece_at(sq) is not None
            if has_piece:
                # Ring around the target
                r = self.SQ // 2 - 4
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                        outline="#444444", width=5, fill="")
            else:
                # Small dot
                r = self.SQ // 7
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                        fill="#555555", outline="")

    # Unicode fallback glyphs
    UNICODE_PIECES = {
        'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
        'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
    }

    def draw_pieces(self):
        use_svg = bool(self.piece_images)
        piece_font_size = int(self.SQ * 0.72)

        for sq in chess.SQUARES:
            piece = self.board.piece_at(sq)
            if not piece:
                continue
            x0, y0 = self.sq_xy(sq)
            cx = x0 + self.SQ // 2
            cy = y0 + self.SQ // 2

            if use_svg:
                # Drop shadow
                self.canvas.create_oval(cx - 18, cy + 16, cx + 18, cy + 24,
                                        fill="#333333", outline="")
                img = self.piece_images.get(piece.symbol())
                if img:
                    self.canvas.create_image(cx, cy, image=img)
            else:
                # Unicode fallback – draw a coloured circle + glyph
                sym = piece.symbol()
                glyph = self.UNICODE_PIECES.get(sym, sym)
                is_white = piece.color == chess.WHITE

                # Shadow
                self.canvas.create_oval(cx - 28, cy - 28, cx + 28, cy + 30,
                                        fill="#333333", outline="")
                # Piece circle
                fill_color = "#f5f0e8" if is_white else "#2d2d2d"
                border_color = "#999" if is_white else "#111"
                self.canvas.create_oval(cx - 28, cy - 30, cx + 28, cy + 26,
                                        fill=fill_color, outline=border_color, width=2)
                # Glyph
                text_color = "#1a1a1a" if is_white else "#e8e8e8"
                self.canvas.create_text(cx, cy - 2,
                                        text=glyph,
                                        fill=text_color,
                                        font=("Segoe UI Symbol", piece_font_size // 3, "bold"))

    def draw_eval_bar(self):
        """White share at top → 50% = equal, 100% = white winning."""
        self.eval_canvas.delete("all")
        h = self.SQ * 8
        w = 22
        # Clamp eval to ±8 pawns
        clamped = max(-8.0, min(8.0, self.eval_score / 100.0))
        white_frac = (clamped + 8) / 16.0  # 0..1  (1 = white winning)
        black_height = int(h * (1 - white_frac))
        white_height = h - black_height

        self.eval_canvas.create_rectangle(0, 0, w, black_height,
                                          fill="#2c2c2c", outline="")
        self.eval_canvas.create_rectangle(0, black_height, w, h,
                                          fill="#f0f0f0", outline="")
        # Centre line
        self.eval_canvas.create_line(0, h // 2, w, h // 2, fill="#888", width=1)

        score_pawn = self.eval_score / 100.0
        sign = "+" if score_pawn > 0 else ""
        self.eval_label.config(text=f"{sign}{score_pawn:.1f}")

    def update_captured_display(self):
        UNICODE = {'P': '♟', 'N': '♞', 'B': '♝', 'R': '♜', 'Q': '♛',
                   'p': '♙', 'n': '♘', 'b': '♗', 'r': '♖', 'q': '♕'}
        self.cap_black_label.config(
            text=" ".join(UNICODE.get(p, p) for p in self.captured_w))
        self.cap_white_label.config(
            text=" ".join(UNICODE.get(p, p) for p in self.captured_b))

    # ──────────────────────────────────────────────────────────────────────────
    # Coach
    # ──────────────────────────────────────────────────────────────────────────

    # Piece values in centipawns
    PIECE_VALUE = {
        chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
        chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
    }
    PIECE_NAME = {
        chess.PAWN: "pawn", chess.KNIGHT: "knight", chess.BISHOP: "bishop",
        chess.ROOK: "rook", chess.QUEEN: "queen", chess.KING: "king"
    }

    def toggle_coach(self):
        self.coach_on = not self.coach_on
        if self.coach_on:
            self.coach_toggle_btn.config(text="ON", bg="#27ae60")
            self._coach_msg("Coach is ON. I'll help you!", "good")
            self.coach_speak("המאמן פעיל. אני אעזור לך!")
        else:
            self.coach_toggle_btn.config(text="OFF", bg="#7f8c8d")
            self._coach_msg("Coach is OFF.", "info")
            self.coach_speak("המאמן כבוי.")
        self.coach_highlight = None
        self.redraw()

    def _coach_msg(self, text: str, tag: str = "info"):
        """Replace the coach panel text."""
        self.coach_text.config(state=tk.NORMAL)
        self.coach_text.delete("1.0", tk.END)
        self.coach_text.insert(tk.END, text, tag)
        self.coach_text.config(state=tk.DISABLED)

    # pre_move_eval and best_move_before are set at end of _engine_and_coach,
    # so they're always ready for the next player move with no thread racing.

    def _explain_move_thorough(self, move: chess.Move, board: chess.Board,
                               drop: float, best: chess.Move) -> list:
        """
        Generate ALL coaching tips for a move, sorted by importance.
        """

        tips = []
        board_after = board.copy()
        board_after.push(move)
        moved_piece = board_after.piece_at(move.to_square)
        piece_moved = board.piece_at(move.from_square)
        move_count = len(board.move_stack)

        PNAME = self.PIECE_NAME

        # INTERNAL list of (priority, message)
        # Lower number = more important
        PRIORITY = []

        def add(priority, text):
            PRIORITY.append((priority, text))

        # ───────────────────────────────────────────────────────────────
        # 1. Hung a piece (undefended after move)
        # ───────────────────────────────────────────────────────────────
        if moved_piece and moved_piece.color == chess.WHITE:
            attackers = board_after.attackers(chess.BLACK, move.to_square)
            defenders = board_after.attackers(chess.WHITE, move.to_square)
            if attackers and not defenders:
                pname = PNAME.get(moved_piece.piece_type, "piece")
                sq_name = chess.square_name(move.to_square)
                add(1, f"⚠ Your {pname} on {sq_name} is undefended — the opponent can take it!")

        # ───────────────────────────────────────────────────────────────
        # 2. Left another piece hanging
        # ───────────────────────────────────────────────────────────────
        if piece_moved:
            for sq in chess.SQUARES:
                p = board.piece_at(sq)
                if p and p.color == chess.WHITE and sq != move.from_square:
                    was_defended = bool(board.attackers(chess.WHITE, sq))
                    now_defended = bool(board_after.attackers(chess.WHITE, sq))
                    now_attacked = bool(board_after.attackers(chess.BLACK, sq))
                    if now_attacked and not now_defended and was_defended:
                        pname = PNAME.get(p.piece_type, "piece")
                        add(2, f"⚠ Moving away left your {pname} on {chess.square_name(sq)} undefended!")
                        break

        # ───────────────────────────────────────────────────────────────
        # 3. Missed free capture
        # ───────────────────────────────────────────────────────────────
        if best is not None and best in board.legal_moves and board.is_capture(best) and not board.is_capture(move):
            captured = board.piece_at(best.to_square)
            if captured:
                cap_pname = PNAME.get(captured.piece_type, "piece")
                best_piece = board.piece_at(best.from_square)
                bp_name = PNAME.get(best_piece.piece_type, "piece") if best_piece else "piece"
                add(3, f"💰 Your {bp_name} on {chess.square_name(best.from_square)} could have captured "
                       f"the opponent's {cap_pname} on {chess.square_name(best.to_square)} for free!")

        # ───────────────────────────────────────────────────────────────
        # 4. Missed check
        # ───────────────────────────────────────────────────────────────
        if best is not None and best in board.legal_moves:
            test2 = board.copy();
            test2.push(best)
            if test2.is_check() and not board_after.is_check():
                best_piece = board.piece_at(best.from_square)
                bp_name = PNAME.get(best_piece.piece_type, "piece") if best_piece else "piece"
                add(4, f"🎯 Your {bp_name} on {chess.square_name(best.from_square)} could have moved to "
                       f"{chess.square_name(best.to_square)} and put the King in check!")

        # ───────────────────────────────────────────────────────────────
        # 5. Missed checkmate
        # ───────────────────────────────────────────────────────────────
        if best is not None and best in board.legal_moves:
            test3 = board.copy();
            test3.push(best)
            if test3.is_checkmate():
                best_piece = board.piece_at(best.from_square)
                bp_name = PNAME.get(best_piece.piece_type, "piece") if best_piece else "piece"
                add(0,
                    f"👑 פספסת שח מט! {bp_name} ל-{chess.square_name(best.to_square)} היה המהלך המנצח!")

        # ───────────────────────────────────────────────────────────────
        # 6. Suggest better move (with explanation)
        # ───────────────────────────────────────────────────────────────
        if best is not None and best in board.legal_moves and best != move and drop >= 10:
            best_piece = board.piece_at(best.from_square)
            my_piece = piece_moved
            reason = self._why_better(best, best_piece, board, board_after)

            if best_piece and my_piece and best_piece.piece_type != my_piece.piece_type:
                bp_name = PNAME.get(best_piece.piece_type, "piece")
                my_name = PNAME.get(my_piece.piece_type, "piece")
                to_sq = chess.square_name(best.to_square)
                from_sq = chess.square_name(best.from_square)
                add(5, f"💡 Instead of the {my_name}, consider moving your {bp_name} "
                       f"from {from_sq} to {to_sq}. {reason}")
            else:
                bp_name = PNAME.get(best_piece.piece_type, "piece")
                to_sq = chess.square_name(best.to_square)
                add(5, f"💡 The {bp_name} was right but {to_sq} is a stronger square. {reason}")

        # ───────────────────────────────────────────────────────────────
        # 7. King safety: moved king early
        # ───────────────────────────────────────────────────────────────
        if piece_moved and piece_moved.piece_type == chess.KING:
            if board.has_castling_rights(chess.WHITE):
                add(6, "🏰 Moving your King early loses castling rights — try to castle first to stay safe!")

        # ───────────────────────────────────────────────────────────────
        # 8. Pawn structure: doubled pawns
        # ───────────────────────────────────────────────────────────────
        if piece_moved and piece_moved.piece_type == chess.PAWN:
            col = chess.square_file(move.to_square)
            pawns_on_col = sum(
                1 for sq in chess.SQUARES
                if board_after.piece_at(sq)
                and board_after.piece_at(sq).piece_type == chess.PAWN
                and board_after.piece_at(sq).color == chess.WHITE
                and chess.square_file(sq) == col
            )
            if pawns_on_col >= 2:
                add(7, "📌 You now have doubled pawns — they can be hard to defend.")

        # ───────────────────────────────────────────────────────────────
        # 9. Opening: early queen
        # ───────────────────────────────────────────────────────────────
        if move_count <= 14 and piece_moved:
            if piece_moved.piece_type == chess.QUEEN and move_count < 6:
                undeveloped = []
                for sq in chess.SQUARES:
                    p = board_after.piece_at(sq)
                    if p and p.color == chess.WHITE and p.piece_type in (chess.KNIGHT, chess.BISHOP):
                        if chess.square_rank(sq) == 0:
                            undeveloped.append(PNAME.get(p.piece_type, "piece"))
                if undeveloped:
                    add(8, f"⚠ Bringing your Queen out early is risky — develop your {undeveloped[0]} first!")

        # ───────────────────────────────────────────────────────────────
        # 10. Positive: good development
        # ───────────────────────────────────────────────────────────────
        if move_count <= 10 and piece_moved:
            if piece_moved.piece_type in (chess.KNIGHT, chess.BISHOP):
                add(20, "👌 Good — developing your pieces early is the right idea!")
            elif piece_moved.piece_type == chess.PAWN:
                from_rank = chess.square_rank(move.from_square)
                if from_rank == 1 and chess.square_rank(move.to_square) == 3 and drop < 20:
                    add(20, "👌 Good central pawn push — controlling the centre!")

        # ───────────────────────────────────────────────────────────────
        # 11. Positive: good capture
        # ───────────────────────────────────────────────────────────────
        if board.is_capture(move) and drop < 10:
            captured = board.piece_at(move.to_square)
            if captured:
                cap_val = self.PIECE_VALUE.get(captured.piece_type, 0)
                mover_val = self.PIECE_VALUE.get(piece_moved.piece_type, 0) if piece_moved else 0
                if cap_val >= mover_val:
                    add(21, "💥 Nice capture! You traded well.")

        # ───────────────────────────────────────────────────────────────
        # 12. Positive: castling
        # ───────────────────────────────────────────────────────────────
        if board.is_castling(move):
            add(22, "🏰 Great — castling keeps your King safe and connects your Rooks!")

        # ───────────────────────────────────────────────────────────────
        # 13–19. EXTRA COACHING LAYERS (all 8 upgrades)
        # ───────────────────────────────────────────────────────────────

        # 13. Blunder severity
        if drop >= 600:
            add(1, "This move is a serious blunder — it heavily worsens your position.")
        elif drop >= 200:
            add(4, "This move is a mistake — it weakens your position.")
        elif drop >= 50:
            add(10, "This move is a small inaccuracy — there was a more precise option.")

        # 14. Threat detection
        for sq in chess.SQUARES:
            p = board_after.piece_at(sq)
            if p and p.color == chess.WHITE:
                if board_after.is_attacked_by(chess.BLACK, sq) and not board.is_attacked_by(chess.BLACK, sq):
                    pname = PNAME.get(p.piece_type, "piece")
                    add(3, f"⚠ After this move, your {pname} on {chess.square_name(sq)} is now under attack.")
                    break

        # 15. Strategic plan suggestions
        white_king_sq = board_after.king(chess.WHITE)
        if white_king_sq is not None and chess.square_rank(white_king_sq) == 0 and move_count > 8:
            add(12, "Try to castle soon — keeping your King in the center too long is risky.")

        # undeveloped minor pieces
        undeveloped = []
        for sq, p in board_after.piece_map().items():
            if p.color == chess.WHITE and p.piece_type in (chess.KNIGHT, chess.BISHOP):
                if chess.square_rank(sq) == 0:
                    undeveloped.append(PNAME.get(p.piece_type, "piece"))
        if undeveloped and move_count <= 20:
            add(13, f"Consider developing your remaining {undeveloped[0]} — get all your pieces active.")

        # 16. Positional concepts
        # Knight outpost
        for sq, p in board_after.piece_map().items():
            if p.color == chess.WHITE and p.piece_type == chess.KNIGHT:
                rank = chess.square_rank(sq)
                if rank in (3, 4):
                    add(14, "Nice — your knight is on a strong outpost, hard to challenge.")
                    break

        # Bad bishop — only if own pawns block its diagonals
        for sq, p in board_after.piece_map().items():
            if p.color == chess.WHITE and p.piece_type == chess.BISHOP:
                bishop_attacks = len(list(board_after.attacks(sq)))
                # A bishop on an open diagonal attacks 7-13 squares; if very few, it's blocked
                if bishop_attacks <= 3:
                    add(15, "Your bishop is blocked by your own pawns — consider opening the diagonal.")
                break

        # 17. Opening principles
        if move_count <= 14:
            # Re-count undeveloped pieces fresh here to avoid scope issues
            undeveloped_now = [
                PNAME.get(p.piece_type, "piece")
                for sq, p in board_after.piece_map().items()
                if p.color == chess.WHITE
                   and p.piece_type in (chess.KNIGHT, chess.BISHOP)
                   and chess.square_rank(sq) == 0
            ]
            if len(undeveloped_now) >= 2 and move_count > 6:
                add(16, "Try not to move the same piece twice early — develop all your pieces first.")

        # 18. Endgame coaching
        pieces = board_after.piece_map()
        num_queens = sum(1 for p in pieces.values() if p.piece_type == chess.QUEEN)
        if num_queens == 0:
            ksq = board_after.king(chess.WHITE)
            if ksq and chess.square_rank(ksq) <= 1:
                add(17, "In the endgame, activate your King — it becomes a strong piece.")

        # 19. Move category label (fallback)
        if piece_moved and not PRIORITY:
            add(30, "This is a quiet improving move — it slightly improves your position.")

        # ───────────────────────────────────────────────────────────────
        # SORT BY PRIORITY and return messages only
        # ───────────────────────────────────────────────────────────────
        PRIORITY.sort(key=lambda x: x[0])
        return [msg for _, msg in PRIORITY]

    def _why_better(self, best: chess.Move, best_piece, board: chess.Board,
                    board_after: chess.Board) -> str:
        """Return a detailed plain-English reason why the best move is better."""
        to_sq = best.to_square
        from_sq = best.from_square
        to_file = chess.square_file(to_sq)
        to_rank = chess.square_rank(to_sq)
        to_name = chess.square_name(to_sq)
        bp_name = self.PIECE_NAME.get(best_piece.piece_type, "piece")
        move_num = len(board.move_stack)

        central = {chess.D4, chess.D5, chess.E4, chess.E5}
        near_centre = {chess.C3, chess.C4, chess.C5, chess.C6,
                       chess.D3, chess.D6, chess.E3, chess.E6,
                       chess.F3, chess.F4, chess.F5, chess.F6}

        board_after_best = board.copy()
        board_after_best.push(best)

        reasons = []

        # ── Checkmate ─────────────────────────────────────────────────────────
        if board_after_best.is_checkmate():
            return f"זה שח מט — המשחק היה נגמר מיד! תמיד חפש את ציד המלך!"

        # ── Check ─────────────────────────────────────────────────────────────
        if board_after_best.is_check():
            reasons.append(
                f"it puts the opponent's King in check, forcing them to deal with the threat instead of developing their own attack")

        # ── Capture ───────────────────────────────────────────────────────────
        captured = board.piece_at(to_sq)
        if captured:
            cap_name = self.PIECE_NAME.get(captured.piece_type, "piece")
            cap_val = self.PIECE_VALUE.get(captured.piece_type, 0)
            mv_val = self.PIECE_VALUE.get(best_piece.piece_type, 0)
            if cap_val > mv_val:
                diff = cap_val - mv_val
                reasons.append(
                    f"it captures the opponent's {cap_name} for free — you gain {diff} points of material advantage")
            elif cap_val == mv_val:
                reasons.append(f"it captures the opponent's {cap_name} in an even exchange — keeping material balanced")
            else:
                reasons.append(f"it captures a piece, removing it from the board")

        # ── Fork (attacks two pieces at once) ────────────────────────────────
        attacked_pieces = []
        for sq in chess.SQUARES:
            p = board_after_best.piece_at(sq)
            if p and p.color == chess.BLACK and p.piece_type != chess.KING:
                if board_after_best.is_attacked_by(chess.WHITE, sq):
                    attacked_pieces.append(self.PIECE_NAME.get(p.piece_type, "piece"))
        if len(attacked_pieces) >= 2:
            reasons.append(
                f"it forks the opponent — attacking their {attacked_pieces[0]} and {attacked_pieces[1]} at the same time, and they can only save one!")

        # ── Attacks a valuable undefended piece ───────────────────────────────
        elif attacked_pieces:
            for sq in chess.SQUARES:
                p = board_after_best.piece_at(sq)
                if p and p.color == chess.BLACK:
                    if board_after_best.is_attacked_by(chess.WHITE, sq):
                        defenders = board_after_best.attackers(chess.BLACK, sq)
                        pname = self.PIECE_NAME.get(p.piece_type, "piece")
                        pval = self.PIECE_VALUE.get(p.piece_type, 0)
                        mv_val = self.PIECE_VALUE.get(best_piece.piece_type, 0)
                        if not defenders:
                            reasons.append(
                                f"it attacks the opponent's undefended {pname} on {chess.square_name(sq)} — they must move it or lose it")
                        elif pval > mv_val:
                            reasons.append(
                                f"it threatens to win the opponent's {pname} on {chess.square_name(sq)} which is worth more than your {bp_name}")
                        break

        # ── Central control ───────────────────────────────────────────────────
        if to_sq in central:
            controlled = len([sq for sq in chess.SQUARES
                              if board_after_best.is_attacked_by(chess.WHITE, sq)])
            reasons.append(
                f"placing your {bp_name} on {to_name} gives it maximum reach — central pieces control the most squares and influence both sides of the board")
        elif to_sq in near_centre and best_piece.piece_type in (chess.KNIGHT, chess.BISHOP):
            reasons.append(
                f"{to_name} is a strong outpost near the centre, giving your {bp_name} excellent influence over the key squares")

        # ── Development (opening principles) ─────────────────────────────────
        if move_num <= 14 and chess.square_rank(from_sq) == 0:
            if best_piece.piece_type == chess.KNIGHT:
                squares_controlled = len(list(board_after_best.attacks(to_sq)))
                reasons.append(
                    f"it develops your Knight which now controls {squares_controlled} squares — in the opening, get your pieces off the back rank as quickly as possible")
            elif best_piece.piece_type == chess.BISHOP:
                diagonal_len = len(list(board_after_best.attacks(to_sq)))
                reasons.append(
                    f"it activates your Bishop with a diagonal controlling {diagonal_len} squares — Bishops become much stronger when they have open diagonals")

        # ── King safety ───────────────────────────────────────────────────────
        if best_piece.piece_type == chess.KING and board.is_castling(best):
            reasons.append(
                "castling tucks your King safely behind your pawns and connects your Rooks — two important goals in one move!")

        # ── Rook on open file ─────────────────────────────────────────────────
        if best_piece.piece_type == chess.ROOK:
            file_pawns = [sq for sq in chess.SQUARES
                          if board_after_best.piece_at(sq) and
                          board_after_best.piece_at(sq).piece_type == chess.PAWN and
                          chess.square_file(sq) == to_file]
            if not file_pawns:
                reasons.append(
                    f"it places your Rook on an open file with no pawns blocking it — Rooks are most powerful on open files where they can attack freely")

        # ── Piece activity comparison ─────────────────────────────────────────
        if not reasons:
            my_squares_before = len(list(board.attacks(from_sq)))
            my_squares_after = len(list(board_after_best.attacks(to_sq)))
            if my_squares_after > my_squares_before:
                diff = my_squares_after - my_squares_before
                reasons.append(
                    f"your {bp_name} controls {diff} more squares from {to_name} than where it was — more active pieces give you more options every turn")
            elif best_piece.piece_type == chess.QUEEN:
                reasons.append(f"the Queen is more centralised and harder to attack from {to_name}")
            else:
                reasons.append(f"your {bp_name} is simply more active and better placed on {to_name}")

        if reasons:
            if len(reasons) == 1:
                return f"Because {reasons[0]}."
            else:
                return f"Because {reasons[0]}, and also {reasons[1]}."

        return "It gives your piece a more active and influential role in the position."

    def draw_coach_highlight(self):
        """Draw green arrow/highlight for the suggested best move."""
        if not self.coach_highlight or not self.coach_on:
            return
        from_sq, to_sq = self.coach_highlight
        fx, fy = self.sq_xy(from_sq)
        tx, ty = self.sq_xy(to_sq)
        fcx, fcy = fx + self.SQ // 2, fy + self.SQ // 2
        tcx, tcy = tx + self.SQ // 2, ty + self.SQ // 2
        # Highlight squares in blue-green
        self.canvas.create_rectangle(fx, fy, fx + self.SQ, fy + self.SQ,
                                     outline="#00c896", width=4, fill="")
        self.canvas.create_rectangle(tx, ty, tx + self.SQ, ty + self.SQ,
                                     outline="#00c896", width=4, fill="")
        # Arrow
        self.canvas.create_line(fcx, fcy, tcx, tcy,
                                fill="#00c896", width=3, arrow=tk.LAST,
                                arrowshape=(14, 18, 6))

    # ──────────────────────────────────────────────────────────────────────────
    # Move history panel
    # ──────────────────────────────────────────────────────────────────────────
    def refresh_history(self):
        self.hist_list.delete(0, tk.END)
        for i in range(0, len(self.move_history), 2):
            w_san = self.move_history[i]
            b_san = self.move_history[i + 1] if i + 1 < len(self.move_history) else ""
            move_num = i // 2 + 1
            self.hist_list.insert(tk.END, f"  {move_num:2d}. {w_san:<8} {b_san}")
        self.hist_list.yview_moveto(1.0)  # scroll to bottom

    # ──────────────────────────────────────────────────────────────────────────
    # Click handler
    # ──────────────────────────────────────────────────────────────────────────
    def on_click(self, event):
        if self.board.turn == chess.BLACK:
            return
        if self.board.is_game_over():
            return
        if self.review_mode:
            return
        if self.engine_busy:
            return

        col = event.x // self.SQ
        row = 7 - (event.y // self.SQ)
        if not (0 <= col <= 7 and 0 <= row <= 7):
            return
        sq = chess.square(col, row)

        if self.selected_sq is None:
            piece = self.board.piece_at(sq)
            if piece and piece.color == chess.WHITE:
                self.selected_sq = sq
                self.legal_targets = {m.to_square for m in self.board.legal_moves
                                      if m.from_square == sq}
                self.redraw()
        else:
            move = chess.Move(self.selected_sq, sq)
            # Auto-promote to queen
            piece = self.board.piece_at(self.selected_sq)
            if (piece and piece.piece_type == chess.PAWN
                    and chess.square_rank(sq) in (0, 7)):
                move.promotion = chess.QUEEN

            if move in self.board.legal_moves:
                self.execute_player_move(move)
            else:
                # Maybe user clicked a different own piece
                p2 = self.board.piece_at(sq)
                if p2 and p2.color == chess.WHITE:
                    self.selected_sq = sq
                    self.legal_targets = {m.to_square for m in self.board.legal_moves
                                          if m.from_square == sq}
                    self.redraw()
                    return

            self.selected_sq = None
            self.legal_targets = set()
            self.redraw()

    # ──────────────────────────────────────────────────────────────────────────
    # Move execution
    # ──────────────────────────────────────────────────────────────────────────
    def _record_capture(self, move: chess.Move):
        captured = self.board.piece_at(move.to_square)
        if self.board.is_en_passant(move):
            # The pawn is on a different square for EP
            ep_sq = chess.square(chess.square_file(move.to_square),
                                 chess.square_rank(move.from_square))
            captured = self.board.piece_at(ep_sq)
        if captured:
            if captured.color == chess.BLACK:
                self.captured_w.append(captured.symbol())
            else:
                self.captured_b.append(captured.symbol())

    def execute_player_move(self, move: chess.Move):
        san = self.board.san(move)
        is_capture = self.board.is_capture(move)
        is_castle = self.board.is_castling(move)
        self._record_capture(move)
        board_before = self.board.copy()  # snapshot for coach

        move_san = self.board.san(move)
        self.board.push(move)

        self._tts.speak(f"{self.player_name} מוציא {translate_to_hebrew(move_san)}")

        if self.board.is_check():
            self._tts.speak("שח!")
        self.last_move = move
        self.coach_highlight = None  # clear previous suggestion
        self.move_history.append(san)
        self.review_boards.append(self.board.fen())
        self.refresh_history()
        self.opening_label.config(text=detect_opening(self.board))
        self.redraw()
        self.speak(san)

        self.status_var.set("Engine thinking…")

        if self.board.is_game_over():
            self.handle_end()
        else:
            self.engine_busy = True
            threading.Thread(
                target=self._engine_and_coach,
                args=(move, board_before),
                daemon=True).start()

    def _engine_and_coach(self, player_move: chess.Move, board_before: chess.Board):
        """
        Single background thread that does ALL engine work sequentially:
        1. Evaluate the position after player's move (for coach feedback)
        2. Get engine's reply move
        3. Evaluate after engine's reply (for eval bar)
        """
        if not self.engine:
            return
        try:
            self._run_engine(player_move, board_before)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.engine_busy = False

    def _run_engine(self, player_move, board_before):
        if not self.engine:
            return

        coach_msg = None
        coach_tag = "good"
        coach_hi = None
        spoken_tip = None

        # ── Step 1: Coach feedback (pure pattern analysis, no engine call) ──────
        if self.coach_on:
            try:
                best = self.best_move_before
                drop = self.pre_move_eval  # if no post_eval, use pre as proxy

                # Try to get post-move eval from engine (optional — don't crash if fails)
                try:
                    info_after = self.engine.analyse(self.board, chess.engine.Limit(depth=10, time=0.3))
                    score_after = info_after["score"].white()
                    post_eval = float(score_after.score(mate_score=3000) or 0)
                    drop = self.pre_move_eval - post_eval
                except Exception as e:
                    drop = 0.0

                player_played_best = (best is not None and player_move == best)

                if player_played_best:
                    grade = "best";
                    coach_tag = "good"
                elif drop >= 250:
                    grade = "blunder";
                    coach_tag = "blunder"
                elif drop >= 100:
                    grade = "mistake";
                    coach_tag = "warn"
                elif drop >= 40:
                    grade = "inaccuracy";
                    coach_tag = "warn"
                elif drop >= 10:
                    grade = "slight";
                    coach_tag = "tip"
                else:
                    grade = "good";
                    coach_tag = "good"

                headers = {
                    "best": "✅ Best move! Well done!",
                    "good": "👍 Good move!",
                    "slight": "💡 Slightly better options exist.",
                    "inaccuracy": "💡 Inaccuracy – a better option was available.",
                    "mistake": "⚠️ Mistake – you gave up advantage.",
                    "blunder": f"❌ Blunder! Lost ~{abs(drop) // 100} pawn(s) of advantage.",
                }
                msg_lines = [headers[grade]]

                tips = self._explain_move_thorough(player_move, board_before, drop, best)
                msg_lines.extend(tips)

                show_best = grade not in ("best", "good")
                if show_best and best is not None:
                    try:
                        best_san = board_before.san(best)
                        msg_lines.append(f"\n🔵 Better: {best_san}")
                        coach_hi = (best.from_square, best.to_square)
                    except Exception:
                        pass

                coach_msg = "\n".join(msg_lines)

                # Build spoken parts
                import unicodedata, re
                _piece_map = {'N': 'Knight', 'B': 'Bishop', 'R': 'Rook', 'Q': 'Queen', 'K': 'King'}

                def _translate_better(text):
                    def _piece(m):
                        return 'Better: ' + _piece_map.get(m.group(1), m.group(1)) + ' ' + m.group(2)

                    return re.sub(r'Better: ([NBRQK])([a-h1-8x])', _piece, text)

                def _clean_for_tts(line):
                    out = []
                    for ch in line:
                        cat = unicodedata.category(ch)
                        if cat == 'Pd':
                            out.append(',')
                        elif cat.startswith('L') or cat.startswith('N') or cat == 'Zs' or ch in ' ,.!?:':
                            out.append(ch)
                        else:
                            out.append(' ')
                    return ' '.join(''.join(out).split()).strip().strip(',').strip()

                spoken_parts = []
                for line in msg_lines:
                    clean = _clean_for_tts(line)
                    clean = _translate_better(clean)
                    clean = translate_to_hebrew(clean)
                    if clean:
                        spoken_parts.append(clean)
                spoken_tip = '. '.join(spoken_parts) if spoken_parts else None

            except Exception:
                pass

        # ── Step 2: Engine plays its move ─────────────────────────────────────
        try:
            result = self.engine.play(self.board, chess.engine.Limit(time=0.6),
                                      options={"Skill Level": self.skill_level})
        except Exception as e:
            self.root.after(0, lambda: setattr(self, 'engine_busy', False))
            return

        # ── Step 3: Eval after engine move (for eval bar) ─────────────────────
        try:
            info2 = self.engine.analyse(self.board, chess.engine.Limit(depth=10))
            s2 = info2["score"].white()
            self.eval_score = float(s2.score(mate_score=3000) or 0)
        except Exception:
            pass

        # ── Step 4: Pre-analyse for NEXT player move ──────────────────────────
        new_pre_eval = 0.0
        new_best_move = None
        try:
            # Peek at board after engine move to get baseline for next turn
            test_board = self.board.copy()
            test_board.push(result.move)
            info3 = self.engine.analyse(test_board, chess.engine.Limit(depth=12))
            s3 = info3["score"].white()
            new_pre_eval = float(s3.score(mate_score=3000) or 0)
            new_best_move = info3.get("pv", [None])[0]
        except Exception:
            pass

        # ── Deliver everything back to UI thread ──────────────────────────────
        def _deliver():
            if coach_msg and self.coach_on:
                self._coach_msg(coach_msg, coach_tag)
                self.coach_highlight = coach_hi
            if spoken_tip and self.coach_on:
                parts = [p.strip() for p in spoken_tip.split('.') if p.strip()]
                for part in parts:
                    self.coach_speak(part)
            self.execute_engine_move(result.move)
            self.pre_move_eval = new_pre_eval
            self.best_move_before = new_best_move

        self.root.after(0, _deliver)

    def engine_move(self):
        try:
            if self.engine and not self.board.is_game_over():
                result = self.engine.play(
                    self.board,
                    chess.engine.Limit(time=0.5)
                )

                move_san = self.board.san(result.move)
                self.board.push(result.move)

                self.root.after(0, self.update_board)

                self._tts.speak(f"המחשב מוציא {translate_to_hebrew(move_san)}")

                if self.board.is_check():
                    self.speak_async("שח!")

        except Exception as e:
            print("Engine crashed:", e)

    def execute_engine_move(self, move: chess.Move):
        self.engine_busy = False
        san = self.board.san(move)
        is_capture = self.board.is_capture(move)
        is_castle = self.board.is_castling(move)
        self._record_capture(move)

        self.board.push(move)
        self.last_move = move
        self.move_history.append(san)
        self.review_boards.append(self.board.fen())
        self.refresh_history()
        self.opening_label.config(text=detect_opening(self.board))
        self.redraw()
        self.speak(san)
        winsound.Beep(600 if is_capture else 1000, 50)

        if self.board.is_game_over():
            result = self.board.result()
            self.status_label.config(text=f"Game Over: {result}")
            self.speak_async("המשחק הסתיים")
        else:
            self.status_var.set("Your turn – White")

    # ──────────────────────────────────────────────────────────────────────────
    # Undo
    # ──────────────────────────────────────────────────────────────────────────
    def undo_move(self):
        if self.review_mode:
            return
        if len(self.board.move_stack) >= 2:
            self.board.pop();
            self.board.pop()
            if len(self.move_history) >= 2:
                self.move_history.pop();
                self.move_history.pop()
            if len(self.review_boards) >= 2:
                self.review_boards.pop();
                self.review_boards.pop()
            self.last_move = None
            self.selected_sq = None
            self.legal_targets = set()
            self.coach_highlight = None
            self.pre_move_eval = 0.0
            self.best_move_before = None
            self.refresh_history()
            self.redraw()
            self._tts.speak("בוטל מהלך")
            self.status_var.set("Your turn – White")
            self._coach_msg("Move undone. Let's try again!", "info")
            self._tts.speak("בוטל מהלך. בוא ננסה שוב!")

    # ──────────────────────────────────────────────────────────────────────────
    # Game over
    # ──────────────────────────────────────────────────────────────────────────
    def handle_end(self):
        res = self.board.result()
        if res == "1-0":
            self.stats["wins"] += 1;
            msg = f"ניצחת, {self.player_name}! כל הכבוד!"
        elif res == "0-1":
            self.stats["losses"] += 1;
            msg = "המחשב ניצח הפעם. תמשיך להתאמן!"
        else:
            self.stats["draws"] += 1;
            msg = "תיקו. שיחקת יפה!"
        self.coach_speak(msg)
        self.save_stats()
        self.stats_label.config(text=self._stats_text())
        self.status_var.set(f"Game over – {res}")
        messagebox.showinfo("Game Over", f"{msg}\n\nResult: {res}")

    def _stats_text(self):
        return (f"🏆 {self.player_name}:  "
                f"{self.stats['wins']}W  {self.stats['losses']}L  {self.stats['draws']}D")

    # ──────────────────────────────────────────────────────────────────────────
    # New game
    # ──────────────────────────────────────────────────────────────────────────
    def new_game(self):
        self.board = chess.Board()
        self.last_move = None
        self.selected_sq = None
        self.legal_targets = set()
        self.eval_score = 0.0
        self.move_history = []
        self.captured_w = []
        self.captured_b = []
        self.review_boards = []
        self.white_time = 600.0
        self.black_time = 600.0
        self.engine_busy = False
        self.coach_highlight = None
        self.pre_move_eval = 0.0
        self.best_move_before = None
        self.exit_review()
        self.refresh_history()
        self.opening_label.config(text="")
        self.status_var.set("Your turn – White")
        self._coach_msg("New game! Good luck! I will coach you as you play.", "info")
        self._tts.speak("משחק חדש! בהצלחה!")
        self.redraw()

    # ──────────────────────────────────────────────────────────────────────────
    # Review mode
    # ──────────────────────────────────────────────────────────────────────────
    def start_review(self):
        if not self.review_boards:
            messagebox.showinfo("Review", "No moves to review yet.")
            return
        self.review_mode = True
        self.review_idx = len(self.review_boards) - 1
        self.review_frame.pack(pady=4)
        self.status_var.set("Review mode – use ◀ ▶ to step through moves")
        self._show_review_pos()

    def exit_review(self):
        self.review_mode = False
        self.review_frame.pack_forget()
        self.board = chess.Board()
        # Replay all moves to restore live board
        tmp = chess.Board()
        for san in self.move_history:
            try:
                tmp.push_san(san)
            except:
                break
        self.board = tmp
        self.redraw()

    def review_step(self, delta: int):
        if not self.review_mode:
            return
        self.review_idx = max(0, min(len(self.review_boards) - 1, self.review_idx + delta))
        self._show_review_pos()

    def review_jump(self, idx: int):
        if idx == -1:
            idx = len(self.review_boards) - 1
        self.review_idx = max(0, min(len(self.review_boards) - 1, idx))
        self._show_review_pos()

    def _show_review_pos(self):
        self.board = chess.Board(self.review_boards[self.review_idx])
        move_num = self.review_idx + 1
        san = self.move_history[self.review_idx] if self.review_idx < len(self.move_history) else "?"
        color = "White" if move_num % 2 == 1 else "Black"
        self.status_var.set(f"Review: move {move_num} – {color} played {san}")
        self.last_move = None
        self.redraw()
        # Highlight reviewed move on board
        if self.review_idx > 0:
            # We need the previous board to know from/to squares
            prev = chess.Board(self.review_boards[self.review_idx - 1])
            moves_played = list(prev.legal_moves)
            # Find which move was made (compare FEN)
            for m in prev.legal_moves:
                prev.push(m)
                if prev.fen() == self.board.fen():
                    self.last_move = m
                    break
                prev.pop()
        self.redraw()

    # ──────────────────────────────────────────────────────────────────────────
    # Speech — Hebrew via edge_tts SpeechManager
    # ──────────────────────────────────────────────────────────────────────────

    def speak_async(self, text: str):
        """Queue text for Hebrew TTS speech."""
        if text and text.strip():
            self._tts.speak(translate_to_hebrew(str(text)))

    def coach_speak(self, text: str):
        """Speak coach feedback — strip emojis then queue for Hebrew TTS."""
        if not self.coach_on:
            return
        for ch in ['✅', '👌', '💡', '⚠️', '❌', '🔵', '👍', '💰', '🎯', '👑', '🏰', '📌', '💥', '⚠', '–', '—']:
            text = text.replace(ch, '')
        text = text.strip()
        if text:
            self._tts.speak(translate_to_hebrew(text))

    def speak(self, text: str):
        """Speak a chess SAN move in Hebrew."""
        readable = (text
                    .replace('N', 'פרש').replace('B', 'רץ')
                    .replace('R', 'צריח').replace('Q', 'מלכה')
                    .replace('K', 'מלך').replace('x', 'לוכד')
                    .replace('+', 'שח').replace('#', 'שח מט'))
        self._tts.speak(readable)

    # ──────────────────────────────────────────────────────────────────────────
    def __del__(self):
        if self.engine:
            try:
                self.engine.quit()
            except:
                pass
        try:
            self._tts.stop()
        except:
            pass


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    app = ChessUltimate(root)
    root.mainloop()


















































































































































































































































