♟ Chess Master Ultimate
A Python desktop chess application with a built-in AI coach, opening theory guide, voice feedback, and game review — powered by Stockfish.

📋 Requirements

Python 3.10+
Windows (voice uses Windows SAPI5 via pywin32)

Install dependencies
bashpip install python-chess pywin32
Optional — for SVG piece images:
bashpip install tksvg

⭐ How to Run
1. Clone the repository
bashgit clone https://github.com/RamiCarmy-eng/Chess_Game.git
cd Chess_Game
2. Install dependencies
bashpip install python-chess pywin32
3. Download Stockfish ⚠️

Stockfish is not included in this repository (the binary is too large for GitHub).
You must download it manually — the game will run without it but you will have no opponent to play against.

Step-by-step:

Go to https://stockfishchess.org/download/
Under Windows, click Download Stockfish 17 for Windows
Choose the AVX2 version (works on most modern PCs made after 2013)
Extract the downloaded .zip file
Inside the extracted folder you will find a file named stockfish-windows-x86-64-avx2.exe
Create a folder called stockfish inside your Chess_Game folder
Move the .exe file into that folder

Your folder should look like this:
Chess_Game/
└── stockfish/
    └── stockfish-windows-x86-64-avx2.exe   ← must be exactly this name and location

Not sure if your PC supports AVX2?
If the game crashes on startup, download the non-AVX2 version instead and update line 18 in test.py:
pythonENGINE_PATH = Path("stockfish/stockfish-windows-x86-64.exe")

4. Run the game
bashpython test.py

📁 File Structure
Chess_Game/
│
├── test.py                          # Main application
├── chess_stats.json                 # Auto-created — saves your W/L/D record
├── Clean_openings.json              # Optional — opening book (ECO database)
│
├── pieces/                          # Optional — SVG piece images
│   ├── wk.svg  wq.svg  wr.svg  wb.svg  wn.svg  wp.svg
│   └── bk.svg  bq.svg  br.svg  bb.svg  bn.svg  bp.svg
│
└── stockfish/                       # NOT included — download manually (see above)
    └── stockfish-windows-x86-64-avx2.exe
Opening book (Clean_openings.json)
A JSON file mapping move sequences to opening names:
json{
  "e4 e5 Nf3 Nc6 Bb5": "Ruy López",
  "e4 c5": "Sicilian Defence"
}
If the file is missing, a built-in fallback list of ~100 openings is used automatically.
Piece images
Place SVG files named wk.svg, bq.svg, etc. in the pieces/ folder. If missing, the board falls back to Unicode chess symbols.

🎮 How to Play
You play as White. Click a piece to select it — legal moves appear as dots on the board. Click a destination to move. The engine (Black) responds automatically.
Pawn promotion is automatic to Queen.

🖥 Interface Overview
AreaDescriptionTop barYour name, W/L/D record, difficulty level, current opening nameClocks10-minute countdown for both sidesEval barVertical bar on the left — white section grows when you're winningBoard8×8 board with rank/file labelsCaptured piecesStrips above and below the board showing lost materialMove historyScrollable panel on the right listing all moves by numberCoach panelBelow move history — feedback and tips after each moveStatus barCurrent game state at the bottom

🔘 Buttons
ButtonAction↩ UndoTake back your last move. If pressed while the coach is still speaking (engine hasn't replied yet), only your move is undone. If the engine has already played, both moves are undone.Easy / Medium / ProSet engine strength (Stockfish Skill Level 0 / 10 / 20)⟳ New GameReset the board and start fresh📖 TheoryShow opening theory for the current position (see below)▶ Review GameEnter game review mode to step through your moves

🎓 Coach
The coach analyses your move and gives feedback in the coach panel, spoken aloud via Windows TTS.
Move grades:

✅ Best move
👍 Good move
💡 Inaccuracy
⚠️ Mistake
❌ Blunder

What the coach checks:

Hung or undefended pieces
Missed captures, checks, or checkmates
Pawn structure issues (doubled pawns)
King safety and castling rights
Early queen development
Piece development and central control
Piece activity and outposts
Endgame king activation

The coach can be toggled ON/OFF using the button in the coach panel header.

📖 Opening Theory (on demand)
Press 📖 Theory during your turn to get opening guidance. The coach will:

Tell you which opening you are currently in
Show up to 3 coloured arrows on the board — each a different theory continuation
Display in the coach panel for each arrow:

A 2–3 move line (your move → Black's response → your follow-up)
The opening name that line leads to
A plain-English explanation of why that move is played


Speak the first suggestion aloud

Arrow colours: 🟠 Orange = first choice, 🟢 Green = second, 🟣 Purple = third
Arrows disappear automatically when you make your next move.
If you are outside the opening book, the coach explains the general principles to rely on instead.

🔍 Game Review
Press ▶ Review Game after a game (or mid-game) to step through every move.
ButtonAction◀◀ StartJump to starting position◀ PrevStep back one move▶ NextStep forward one move▶▶ EndJump to final position✕ Exit ReviewReturn to the live game

🏆 Stats
Wins, losses, and draws are saved to chess_stats.json and shown in the top bar. Stats persist across sessions.

⚠️ Known Limitations

Windows only (TTS uses Windows SAPI via win32com; sound uses winsound)
You always play as White
Pawn promotion always promotes to Queen
Requires the AVX2 Stockfish build — update ENGINE_PATH in test.py if using a different build
Share
          var _sift = (window._sift = window._sift || []);
          _sift.push(["_setAccount", "99dfa2e716"]);
          _sift.push(["_setTrackerUrl", "s-cdn.anthropic.com"]);
          _sift.push(["_setUserId", "88d8e7a9-aa1e-4f2b-8666-b34c3a949edb"]);
          _sift.push(["_setSessionId", "5b3d7a4e-9a33-47f7-9502-44f5c1ab0843"]);
          _sift.push(["_trackPageview"]);
      