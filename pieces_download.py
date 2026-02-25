import requests
from pathlib import Path
import time

# Folder
pieces_dir = Path("pieces")
pieces_dir.mkdir(exist_ok=True)

# URLs
piece_urls = {
    "wk.svg": "https://upload.wikimedia.org/wikipedia/commons/4/42/Chess_klt45.svg",
    "wq.svg": "https://upload.wikimedia.org/wikipedia/commons/1/15/Chess_qlt45.svg",
    "wr.svg": "https://upload.wikimedia.org/wikipedia/commons/7/72/Chess_rlt45.svg",
    "wb.svg": "https://upload.wikimedia.org/wikipedia/commons/b/b1/Chess_blt45.svg",
    "wn.svg": "https://upload.wikimedia.org/wikipedia/commons/7/70/Chess_nlt45.svg",
    "wp.svg": "https://upload.wikimedia.org/wikipedia/commons/4/45/Chess_plt45.svg",

    "bk.svg": "https://upload.wikimedia.org/wikipedia/commons/f/f0/Chess_kdt45.svg",
    "bq.svg": "https://upload.wikimedia.org/wikipedia/commons/4/47/Chess_qdt45.svg",
    "br.svg": "https://upload.wikimedia.org/wikipedia/commons/f/ff/Chess_rdt45.svg",
    "bb.svg": "https://upload.wikimedia.org/wikipedia/commons/9/98/Chess_bdt45.svg",
    "bn.svg": "https://upload.wikimedia.org/wikipedia/commons/e/ef/Chess_ndt45.svg",
    "bp.svg": "https://upload.wikimedia.org/wikipedia/commons/c/c7/Chess_pdt45.svg",
}

headers = {
    "User-Agent": "ChessApp/1.0 (educational project)"
}

def download_piece(session, name, url):
    file_path = pieces_dir / name

    if file_path.exists():
        print(f"Skipping {name} (already exists)")
        return True

    try:
        print(f"Downloading {name}...")
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        file_path.write_bytes(response.content)
        print(f"Saved {name}")
        time.sleep(1)  # polite delay
        return True

    except requests.exceptions.RequestException as e:
        print(f"Failed {name}: {e}")
        return False


def main():
    print("Downloading chess pieces...\n")

    success_count = 0

    with requests.Session() as session:
        for filename, url in piece_urls.items():
            if download_piece(session, filename, url):
                success_count += 1

    print(f"\nFinished! {success_count}/12 pieces downloaded.")
    print(f"Folder: {pieces_dir.resolve()}")


if __name__ == "__main__":
    main()