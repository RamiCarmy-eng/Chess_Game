import urllib.request
import os
from pathlib import Path


def fix_pieces_once_and_for_all():
    path = Path("pieces")
    path.mkdir(exist_ok=True)

    # שימוש במקור יציב של ויקיפדיה עם User-Agent
    base = "https://upload.wikimedia.org/wikipedia/commons/thumb/"
    pieces = {
        'wk': '4/42/Chess_klt45.svg/128px-Chess_klt45.svg.png',
        'bk': 'f/f0/Chess_kdt45.svg/128px-Chess_kdt45.svg.png',
        'wq': '1/15/Chess_qlt45.svg/128px-Chess_qlt45.svg.png',
        'bq': '4/47/Chess_qdt45.svg/128px-Chess_qdt45.svg.png',
        'wr': '7/72/Chess_rlt45.svg/128px-Chess_rlt45.svg.png',
        'br': 'f/ff/Chess_rdt45.svg/128px-Chess_rdt45.svg.png',
        'wb': 'b/b1/Chess_blt45.svg/128px-Chess_blt45.svg.png',
        'bb': '9/98/Chess_bdt45.svg/128px-Chess_bdt45.svg.png',
        'wn': '7/70/Chess_nlt45.svg/128px-Chess_nlt45.svg.png',
        'bn': 'e/ef/Chess_ndt45.svg/128px-Chess_ndt45.svg.png',
        'wp': '4/45/Chess_plt45.svg/128px-Chess_plt45.svg.png',
        'bp': 'c/c7/Chess_pdt45.svg/128px-Chess_pdt45.svg.png'
    }

    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0')]
    urllib.request.install_opener(opener)

    print("מוריד כלים חדשים ותקינים...")
    for name, url in pieces.items():
        try:
            urllib.request.urlretrieve(base + url, path / f"{name}.png")
            print(f"הורד: {name}.png")
        except:
            print(f"נכשל: {name}")


if __name__ == "__main__":
    fix_pieces_once_and_for_all()