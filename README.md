# ♟ Chess Coach — Personal Notes

A Python chess game with a built-in AI coach that speaks move announcements and coaching tips out loud, powered by Stockfish and pyttsx3.

---

## 📁 File Structure

```
Chess_Game/
│
├── claude_test.py          # Main program — run this
├── clean_openings.py       # Cleans opening.json → clean_openings.json
├── gen_openings.py         # Generates opening.json from PGN files
│
├── opening.json            # Raw openings from KingBase PGN (~259k entries, ECO codes)
├── clean_openings.json     # Cleaned openings ready for the program (~820k entries)
│
├── chess_stats.json        # Win/loss/draw stats (auto-created on first run)
│
├── stockfish/
│   └── stockfish-windows-x86-64-avx2.exe
│
├── pieces/                 # SVG piece images (optional — falls back to text)
│
└── openings/               # KingBase PGN files used by gen_openings.py
    ├── KingBaseLite2019-01.pgn
    ├── KingBaseLite2019-B20-B49.pgn
    └── ... (17 files total)
```

---

## ⚙️ Installation

### Requirements
```
pip install python-chess pyttsx3
```

- **Python 3.10+**
- **Stockfish** — download from https://stockfishchess.org and place the `.exe` in `stockfish/`
- **tksvg** (optional) — for SVG piece images: `pip install tksvg`

### First Run
```bash
python claude_test.py
```

On first run it will ask for your name, then start the game.

---

## 🚀 How to Run

```bash
cd C:\Users\carmi\pythonprograms\Chess_Game
python claude_test.py
```

If `clean_openings.json` is present in the same folder, it loads automatically.
The terminal shows: `Loaded 820500 openings from clean_openings.json`

---

## 🎓 Coach Features

The coach panel appears on the right side of the board. Toggle it with the **Coach ON/OFF** button.

### What the coach says after every move:

| Grade | When | Example |
|-------|------|---------|
| ✅ Best move | You played exactly what Stockfish suggested | "Best move! Well done!" |
| 👍 Good move | Small or no loss in position | "Good move!" |
| 💡 Inaccuracy | 50–200 centipawn loss | "Slightly better options exist" |
| ⚠️ Mistake | 200–600 centipawn loss | "You gave up advantage" |
| ❌ Blunder | 600+ centipawn loss | "Blunder! Lost ~2 pawns of advantage" |

### Coaching tips (spoken in priority order):

1. 👑 **Missed checkmate** — highest priority, always spoken first
2. ⚠ **Hung a piece** — you moved a piece to an undefended square
3. ⚠ **Left a piece hanging** — your move exposed another piece
4. 💰 **Missed free capture** — you could have taken a piece for free
5. 🎯 **Missed check** — a better move would have given check
6. 💡 **Better piece suggested** — "Instead of the Pawn, consider your Knight from g1 to f3 — it develops toward the centre"
7. 🏰 **King safety** — moved King before castling
8. 📌 **Doubled pawns** — pawn structure warning
9. ⚠ **Early Queen** — risky in the opening
10. 👌 **Good development** — positive feedback in opening
11. 💥 **Good capture** — positive feedback for good trades
12. 🏰 **Castling** — positive feedback

### Voice system

- Move announcements: `"Yakov plays Knight f3"` / `"Computer plays Bishop c4"`
- Coach tips: spoken after each move in priority order
- All speech goes through a single queue — no overlapping or clashing
- Rate: 170 words/minute (moves) / 155 words/minute (coach queue)

---

## 🔧 Difficulty

| Button | Skill Level | Description |
|--------|-------------|-------------|
| Easy | 0 | Makes deliberate mistakes |
| Medium | 10 | Club player strength |
| Pro | 20 | Full Stockfish strength |

Difficulty is passed to the engine on every move so switching mid-game works immediately.

---

## 📖 Opening Database

### Regenerating openings from PGN files:
```bash
python gen_openings.py
# → saves opening.json (~259k raw entries with ECO codes)
```

### Cleaning the database:
```bash
python clean_openings.py
# → reads opening.json
# → maps ECO codes (e.g. "ECO B92") to real names ("Sicilian – Najdorf")
# → deduplicates, adds family prefixes
# → saves clean_openings.json (~820k entries)
```

### Important: notation format
`gen_openings.py` strips `x`, `+`, `#` from moves:
- `cxd4` → `cd4`
- `Nxd4` → `Nd4`

`detect_opening()` in `claude_test.py` strips the same characters before lookup so both sides match.

---

## 🐛 Known Issues / Notes

- **Voice only works on Windows** — pyttsx3 uses SAPI5
- **Only one pyttsx3 instance allowed** — all speech goes through `_speech_q` queue. Don't add `pyttsx3.init()` anywhere else
- **Coach speak** uses `self._speech_q.put(text)` — NOT `speak_async()` which uses `self.voice` and clashes
- **`drop` is in centipawns** — 100 = 1 pawn. Thresholds: blunder ≥600, mistake ≥200, inaccuracy ≥50
- Engine runs in background thread — never call `engine.analyse()` from two threads at once

---

## 📝 Key Functions

| Function | What it does |
|----------|-------------|
| `_engine_and_coach()` | Background thread: analyses move, gets engine reply, builds coach message |
| `_explain_move_thorough()` | Generates all coaching tips sorted by priority |
| `_why_better()` | Explains WHY a suggested move is better (fork, centre, development...) |
| `detect_opening()` | Looks up current position in `clean_openings.json` |
| `coach_speak()` | Strips emoji, puts text in `_speech_q` |
| `_start_speech_worker()` | Single background thread with its own pyttsx3 engine |
| `execute_player_move()` | Handles player move, triggers coach thread |
| `execute_engine_move()` | Handles computer move, announces it |

---

*Last updated: February 2026*
