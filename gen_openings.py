import json
import chess.pgn
from pathlib import Path

# Minimal ECO dictionary (expand later)
ECO_NAMES = {
    "A40": "Queen's Pawn Opening",
    "A45": "Trompowsky Attack",
    "A49": "King's Indian Attack",
}

def extract_openings_from_folder(folder, json_path, max_moves=12):
    openings = {}

    folder = Path(folder)

    # Loop through ALL PGN files in the folder
    for pgn_file in folder.glob("*.pgn"):
        print(f"Processing {pgn_file.name}...")

        with pgn_file.open("r", encoding="utf-8", errors="ignore") as f:
            while True:
                game = chess.pgn.read_game(f)
                if game is None:
                    break

                # Opening name
                opening_name = game.headers.get("Opening")
                eco = game.headers.get("ECO")

                if not opening_name:
                    opening_name = ECO_NAMES.get(eco, f"ECO {eco}")

                # Extract first N moves
                board = game.board()
                moves = []
                for i, move in enumerate(game.mainline_moves()):
                    if i >= max_moves:
                        break
                    san = board.san(move)
                    san = san.replace("x", "").replace("+", "").replace("#", "")
                    moves.append(san)
                    board.push(move)

                move_key = " ".join(moves)

                if move_key and move_key not in openings:
                    openings[move_key] = opening_name

    # Save JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(openings, f, indent=4, ensure_ascii=False)

    print(f"\nSaved {len(openings)} openings to {json_path}")


# Run it on your openings folder
extract_openings_from_folder("openings", "opening.json", max_moves=12)


