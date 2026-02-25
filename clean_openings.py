"""
clean_openings.py  (fixed version)
====================================
Reads opening.json (259k entries, ECO codes, stripped notation),
maps ECO → real names, deduplicates, keeps all move lengths up to 12,
and saves clean_openings.json.

The gen_openings.py script stripped x/+/# from moves so:
  cxd4 → cd4,  Nxd4 → Nd4
We keep everything in stripped form. detect_opening in the chess
program must also strip x/+/# before lookup.

Usage:  python clean_openings.py
Input:  opening.json
Output: clean_openings.json
"""

import json
from pathlib import Path

ECO_NAMES = {
    "A00":"Uncommon Opening","A01":"Nimzowitsch-Larsen Attack",
    "A02":"Bird's Opening","A03":"Bird's Opening",
    "A04":"Réti Opening","A05":"Réti Opening",
    "A06":"Réti Opening","A07":"King's Indian Attack",
    "A08":"King's Indian Attack","A09":"Réti Opening",
    "A10":"English Opening","A11":"English – Caro-Kann System",
    "A12":"English – Caro-Kann System","A13":"English Opening",
    "A14":"English Opening","A15":"English Opening",
    "A16":"English Opening","A17":"English Opening",
    "A18":"English – Mikenas-Carls","A19":"English – Mikenas-Carls Sicilian",
    "A20":"English Opening","A21":"English Opening",
    "A22":"English – Two Knights","A23":"English – Two Knights",
    "A24":"English – Two Knights","A25":"English – Closed",
    "A26":"English – Closed","A27":"English – Three Knights",
    "A28":"English – Four Knights","A29":"English – Four Knights",
    "A30":"English – Symmetrical","A31":"English – Symmetrical",
    "A32":"English – Symmetrical","A33":"English – Symmetrical",
    "A34":"English – Symmetrical","A35":"English – Symmetrical",
    "A36":"English – Symmetrical","A37":"English – Symmetrical",
    "A38":"English – Symmetrical","A39":"English – Symmetrical",
    "A40":"Queen's Pawn Opening","A41":"Queen's Pawn – Old Indian",
    "A42":"Modern Defence – Averbakh","A43":"Old Benoni",
    "A44":"Old Benoni","A45":"Trompowsky Attack",
    "A46":"Torre Attack","A47":"Queen's Indian Defence",
    "A48":"King's Indian – London System","A49":"King's Indian Attack",
    "A50":"Budapest Defence","A51":"Budapest Defence",
    "A52":"Budapest Defence","A53":"Old Indian Defence",
    "A54":"Old Indian – Ukrainian","A55":"Old Indian Defence",
    "A56":"Benoni Defence","A57":"Benko Gambit",
    "A58":"Benko Gambit Accepted","A59":"Benko Gambit",
    "A60":"Benoni Defence","A61":"Benoni Defence",
    "A62":"Benoni – Fianchetto","A63":"Benoni – Fianchetto",
    "A64":"Benoni – Fianchetto","A65":"Benoni Defence",
    "A66":"Benoni Defence","A67":"Benoni – Taimanov",
    "A68":"Benoni – Four Pawns","A69":"Benoni – Four Pawns",
    "A70":"Benoni Defence","A71":"Benoni Defence",
    "A72":"Benoni Defence","A73":"Benoni – Classical",
    "A74":"Benoni – Classical","A75":"Benoni – Classical",
    "A76":"Benoni – Classical","A77":"Benoni – Classical",
    "A78":"Benoni – Classical","A79":"Benoni – Classical",
    "A80":"Dutch Defence","A81":"Dutch Defence",
    "A82":"Dutch – Staunton Gambit","A83":"Dutch – Staunton Gambit",
    "A84":"Dutch Defence","A85":"Dutch – Queen's Knight",
    "A86":"Dutch – Leningrad","A87":"Dutch – Leningrad",
    "A88":"Dutch – Leningrad","A89":"Dutch – Leningrad",
    "A90":"Dutch Defence","A91":"Dutch Defence",
    "A92":"Dutch Defence","A93":"Dutch – Stonewall",
    "A94":"Dutch – Stonewall","A95":"Dutch – Stonewall",
    "A96":"Dutch – Classical","A97":"Dutch – Ilyin-Zhenevsky",
    "A98":"Dutch – Ilyin-Zhenevsky","A99":"Dutch – Ilyin-Zhenevsky",
    "B00":"King's Pawn Opening","B01":"Scandinavian Defence",
    "B02":"Alekhine Defence","B03":"Alekhine Defence",
    "B04":"Alekhine Defence – Modern","B05":"Alekhine Defence – Modern",
    "B06":"Modern Defence","B07":"Pirc Defence",
    "B08":"Pirc Defence – Classical","B09":"Pirc – Austrian Attack",
    "B10":"Caro-Kann Defence","B11":"Caro-Kann – Two Knights",
    "B12":"Caro-Kann Defence","B13":"Caro-Kann – Exchange",
    "B14":"Caro-Kann – Panov-Botvinnik","B15":"Caro-Kann Defence",
    "B16":"Caro-Kann – Bronstein-Larsen","B17":"Caro-Kann – Steinitz",
    "B18":"Caro-Kann – Classical","B19":"Caro-Kann – Classical",
    "B20":"Sicilian Defence","B21":"Sicilian – Grand Prix Attack",
    "B22":"Sicilian – Alapin","B23":"Sicilian – Closed",
    "B24":"Sicilian – Closed","B25":"Sicilian – Closed",
    "B26":"Sicilian – Closed","B27":"Sicilian Defence",
    "B28":"Sicilian – O'Kelly","B29":"Sicilian – Nimzovich",
    "B30":"Sicilian Defence","B31":"Sicilian – Rossolimo",
    "B32":"Sicilian Defence","B33":"Sicilian – Sveshnikov",
    "B34":"Sicilian Defence","B35":"Sicilian Defence",
    "B36":"Sicilian – Accelerated Dragon","B37":"Sicilian – Accelerated Dragon",
    "B38":"Sicilian – Accelerated Dragon","B39":"Sicilian – Accelerated Dragon",
    "B40":"Sicilian Defence","B41":"Sicilian – Kan",
    "B42":"Sicilian – Kan","B43":"Sicilian – Kan",
    "B44":"Sicilian – Taimanov","B45":"Sicilian – Taimanov",
    "B46":"Sicilian – Taimanov","B47":"Sicilian – Taimanov",
    "B48":"Sicilian – Taimanov","B49":"Sicilian – Taimanov",
    "B50":"Sicilian Defence","B51":"Sicilian – Moscow",
    "B52":"Sicilian – Moscow","B53":"Sicilian Defence",
    "B54":"Sicilian Defence","B55":"Sicilian Defence",
    "B56":"Sicilian Defence","B57":"Sicilian – Classical",
    "B58":"Sicilian – Classical","B59":"Sicilian – Classical",
    "B60":"Sicilian – Richter-Rauzer","B61":"Sicilian – Richter-Rauzer",
    "B62":"Sicilian – Richter-Rauzer","B63":"Sicilian – Richter-Rauzer",
    "B64":"Sicilian – Richter-Rauzer","B65":"Sicilian – Richter-Rauzer",
    "B66":"Sicilian – Richter-Rauzer","B67":"Sicilian – Richter-Rauzer",
    "B68":"Sicilian – Richter-Rauzer","B69":"Sicilian – Richter-Rauzer",
    "B70":"Sicilian – Dragon","B71":"Sicilian – Dragon",
    "B72":"Sicilian – Dragon","B73":"Sicilian – Dragon",
    "B74":"Sicilian – Dragon","B75":"Sicilian – Dragon",
    "B76":"Sicilian – Dragon","B77":"Sicilian – Dragon",
    "B78":"Sicilian – Dragon","B79":"Sicilian – Dragon",
    "B80":"Sicilian – Scheveningen","B81":"Sicilian – Scheveningen",
    "B82":"Sicilian – Scheveningen","B83":"Sicilian – Scheveningen",
    "B84":"Sicilian – Scheveningen","B85":"Sicilian – Scheveningen",
    "B86":"Sicilian – Sozin Attack","B87":"Sicilian – Sozin Attack",
    "B88":"Sicilian – Sozin Attack","B89":"Sicilian – Sozin Attack",
    "B90":"Sicilian – Najdorf","B91":"Sicilian – Najdorf",
    "B92":"Sicilian – Najdorf","B93":"Sicilian – Najdorf",
    "B94":"Sicilian – Najdorf","B95":"Sicilian – Najdorf",
    "B96":"Sicilian – Najdorf","B97":"Sicilian – Najdorf",
    "B98":"Sicilian – Najdorf","B99":"Sicilian – Najdorf",
    "C00":"French Defence","C01":"French – Exchange",
    "C02":"French – Advance","C03":"French – Tarrasch",
    "C04":"French – Tarrasch – Guimard","C05":"French – Tarrasch",
    "C06":"French – Tarrasch","C07":"French – Tarrasch",
    "C08":"French – Tarrasch","C09":"French – Tarrasch",
    "C10":"French Defence","C11":"French – Classical",
    "C12":"French – MacCutcheon","C13":"French – Classical",
    "C14":"French – Classical","C15":"French – Winawer",
    "C16":"French – Winawer","C17":"French – Winawer",
    "C18":"French – Winawer","C19":"French – Winawer",
    "C20":"King's Pawn Opening","C21":"Centre Game",
    "C22":"Centre Game","C23":"Bishop's Opening",
    "C24":"Bishop's Opening","C25":"Vienna Game",
    "C26":"Vienna Game","C27":"Vienna Game",
    "C28":"Vienna Game","C29":"Vienna Gambit",
    "C30":"King's Gambit","C31":"King's Gambit – Falkbeer",
    "C32":"King's Gambit – Falkbeer","C33":"King's Gambit Accepted",
    "C34":"King's Gambit Accepted","C35":"King's Gambit Accepted",
    "C36":"King's Gambit Accepted","C37":"King's Gambit Accepted",
    "C38":"King's Gambit Accepted","C39":"King's Gambit Accepted",
    "C40":"King's Knight Opening","C41":"Philidor Defence",
    "C42":"Petrov's Defence","C43":"Petrov's Defence – Modern",
    "C44":"King's Pawn Game","C45":"Scotch Game",
    "C46":"Three Knights Game","C47":"Four Knights Game",
    "C48":"Four Knights – Spanish","C49":"Four Knights – Double Spanish",
    "C50":"Italian Game","C51":"Evans Gambit",
    "C52":"Evans Gambit","C53":"Italian Game – Classical",
    "C54":"Italian – Giuoco Pianissimo","C55":"Italian – Two Knights",
    "C56":"Italian – Two Knights","C57":"Italian – Fried Liver Attack",
    "C58":"Italian – Two Knights","C59":"Italian – Two Knights",
    "C60":"Ruy López","C61":"Ruy López – Bird's Defence",
    "C62":"Ruy López – Old Steinitz","C63":"Ruy López – Schliemann",
    "C64":"Ruy López – Classical","C65":"Ruy López – Berlin Defence",
    "C66":"Ruy López – Berlin Defence","C67":"Ruy López – Berlin Defence",
    "C68":"Ruy López – Exchange","C69":"Ruy López – Exchange",
    "C70":"Ruy López","C71":"Ruy López – Modern Steinitz",
    "C72":"Ruy López – Modern Steinitz","C73":"Ruy López – Modern Steinitz",
    "C74":"Ruy López – Modern Steinitz","C75":"Ruy López – Modern Steinitz",
    "C76":"Ruy López – Modern Steinitz","C77":"Ruy López – Morphy Defence",
    "C78":"Ruy López – Morphy Defence","C79":"Ruy López – Morphy Defence",
    "C80":"Ruy López – Open Defence","C81":"Ruy López – Open Defence",
    "C82":"Ruy López – Open Defence","C83":"Ruy López – Open Defence",
    "C84":"Ruy López – Closed","C85":"Ruy López – Closed",
    "C86":"Ruy López – Closed","C87":"Ruy López – Closed",
    "C88":"Ruy López – Closed","C89":"Ruy López – Marshall Attack",
    "C90":"Ruy López – Closed","C91":"Ruy López – Closed",
    "C92":"Ruy López – Closed","C93":"Ruy López – Closed",
    "C94":"Ruy López – Smyslov","C95":"Ruy López – Breyer",
    "C96":"Ruy López – Closed","C97":"Ruy López – Chigorin",
    "C98":"Ruy López – Chigorin","C99":"Ruy López – Chigorin",
    "D00":"Queen's Pawn – London System","D01":"Richter-Veresov Attack",
    "D02":"Queen's Pawn – London System","D03":"Torre Attack",
    "D04":"Queen's Pawn – London System","D05":"Colle System",
    "D06":"Queen's Gambit","D07":"Queen's Gambit – Chigorin",
    "D08":"Albin Countergambit","D09":"Albin Countergambit",
    "D10":"Slav Defence","D11":"Slav Defence",
    "D12":"Slav Defence","D13":"Slav Defence",
    "D14":"Slav – Exchange","D15":"Slav Defence",
    "D16":"Slav Defence","D17":"Slav Defence",
    "D18":"Slav – Dutch","D19":"Slav – Dutch",
    "D20":"Queen's Gambit Accepted","D21":"Queen's Gambit Accepted",
    "D22":"Queen's Gambit Accepted","D23":"Queen's Gambit Accepted",
    "D24":"Queen's Gambit Accepted","D25":"Queen's Gambit Accepted",
    "D26":"Queen's Gambit Accepted","D27":"Queen's Gambit Accepted",
    "D28":"Queen's Gambit Accepted – Classical","D29":"Queen's Gambit Accepted – Classical",
    "D30":"Queen's Gambit Declined","D31":"Queen's Gambit Declined",
    "D32":"QGD – Tarrasch","D33":"QGD – Tarrasch",
    "D34":"QGD – Tarrasch","D35":"Queen's Gambit Declined",
    "D36":"QGD – Exchange","D37":"Queen's Gambit Declined",
    "D38":"QGD – Ragozin","D39":"QGD – Ragozin",
    "D40":"QGD – Semi-Tarrasch","D41":"QGD – Semi-Tarrasch",
    "D42":"QGD – Semi-Tarrasch","D43":"QGD – Semi-Slav",
    "D44":"QGD – Semi-Slav","D45":"QGD – Semi-Slav",
    "D46":"QGD – Semi-Slav","D47":"QGD – Semi-Slav",
    "D48":"QGD – Semi-Slav Meran","D49":"QGD – Semi-Slav Meran",
    "D50":"Queen's Gambit Declined","D51":"Queen's Gambit Declined",
    "D52":"Queen's Gambit Declined","D53":"Queen's Gambit Declined",
    "D54":"Queen's Gambit Declined","D55":"Queen's Gambit Declined",
    "D56":"Queen's Gambit Declined","D57":"QGD – Lasker Defence",
    "D58":"QGD – Tartakower","D59":"QGD – Tartakower",
    "D60":"QGD – Orthodox","D61":"QGD – Orthodox",
    "D62":"QGD – Orthodox","D63":"QGD – Orthodox",
    "D64":"QGD – Orthodox","D65":"QGD – Orthodox",
    "D66":"QGD – Orthodox","D67":"QGD – Orthodox",
    "D68":"QGD – Orthodox","D69":"QGD – Orthodox",
    "D70":"Grünfeld Defence","D71":"Grünfeld Defence",
    "D72":"Grünfeld Defence","D73":"Grünfeld Defence",
    "D74":"Grünfeld Defence","D75":"Grünfeld Defence",
    "D76":"Grünfeld Defence","D77":"Grünfeld Defence",
    "D78":"Grünfeld Defence","D79":"Grünfeld Defence",
    "D80":"Grünfeld Defence","D81":"Grünfeld – Russian",
    "D82":"Grünfeld – Brinckmann","D83":"Grünfeld Defence",
    "D84":"Grünfeld Defence","D85":"Grünfeld Defence",
    "D86":"Grünfeld – Exchange","D87":"Grünfeld – Exchange",
    "D88":"Grünfeld – Exchange","D89":"Grünfeld – Exchange",
    "D90":"Grünfeld Defence","D91":"Grünfeld Defence",
    "D92":"Grünfeld Defence","D93":"Grünfeld Defence",
    "D94":"Grünfeld Defence","D95":"Grünfeld Defence",
    "D96":"Grünfeld – Russian","D97":"Grünfeld – Russian",
    "D98":"Grünfeld – Russian","D99":"Grünfeld – Russian",
    "E00":"Indian Defence","E01":"Catalan Opening",
    "E02":"Catalan Opening","E03":"Catalan Opening",
    "E04":"Catalan – Open","E05":"Catalan – Open",
    "E06":"Catalan – Closed","E07":"Catalan – Closed",
    "E08":"Catalan – Closed","E09":"Catalan – Closed",
    "E10":"Queen's Indian Defence","E11":"Bogo-Indian Defence",
    "E12":"Queen's Indian Defence","E13":"Queen's Indian Defence",
    "E14":"Queen's Indian Defence","E15":"Queen's Indian Defence",
    "E16":"Queen's Indian Defence","E17":"Queen's Indian Defence",
    "E18":"Queen's Indian Defence","E19":"Queen's Indian Defence",
    "E20":"Nimzo-Indian Defence","E21":"Nimzo-Indian Defence",
    "E22":"Nimzo-Indian – Spielmann","E23":"Nimzo-Indian – Spielmann",
    "E24":"Nimzo-Indian – Sämisch","E25":"Nimzo-Indian – Sämisch",
    "E26":"Nimzo-Indian – Sämisch","E27":"Nimzo-Indian – Sämisch",
    "E28":"Nimzo-Indian – Sämisch","E29":"Nimzo-Indian – Sämisch",
    "E30":"Nimzo-Indian – Leningrad","E31":"Nimzo-Indian – Leningrad",
    "E32":"Nimzo-Indian – Classical","E33":"Nimzo-Indian – Classical",
    "E34":"Nimzo-Indian – Classical","E35":"Nimzo-Indian – Classical",
    "E36":"Nimzo-Indian – Classical","E37":"Nimzo-Indian – Classical",
    "E38":"Nimzo-Indian – Classical","E39":"Nimzo-Indian – Classical",
    "E40":"Nimzo-Indian Defence","E41":"Nimzo-Indian Defence",
    "E42":"Nimzo-Indian – Rubinstein","E43":"Nimzo-Indian – Fischer",
    "E44":"Nimzo-Indian – Fischer","E45":"Nimzo-Indian – Fischer",
    "E46":"Nimzo-Indian Defence","E47":"Nimzo-Indian Defence",
    "E48":"Nimzo-Indian Defence","E49":"Nimzo-Indian Defence",
    "E50":"Nimzo-Indian Defence","E51":"Nimzo-Indian Defence",
    "E52":"Nimzo-Indian Defence","E53":"Nimzo-Indian Defence",
    "E54":"Nimzo-Indian Defence","E55":"Nimzo-Indian Defence",
    "E56":"Nimzo-Indian Defence","E57":"Nimzo-Indian Defence",
    "E58":"Nimzo-Indian Defence","E59":"Nimzo-Indian Defence",
    "E60":"King's Indian Defence","E61":"King's Indian Defence",
    "E62":"King's Indian – Fianchetto","E63":"King's Indian – Fianchetto",
    "E64":"King's Indian – Fianchetto","E65":"King's Indian – Fianchetto",
    "E66":"King's Indian – Fianchetto","E67":"King's Indian – Fianchetto",
    "E68":"King's Indian – Fianchetto","E69":"King's Indian – Fianchetto",
    "E70":"King's Indian Defence","E71":"King's Indian – Averbakh",
    "E72":"King's Indian – Averbakh","E73":"King's Indian – Averbakh",
    "E74":"King's Indian – Averbakh","E75":"King's Indian – Averbakh",
    "E76":"King's Indian – Four Pawns","E77":"King's Indian – Four Pawns",
    "E78":"King's Indian – Four Pawns","E79":"King's Indian – Four Pawns",
    "E80":"King's Indian – Sämisch","E81":"King's Indian – Sämisch",
    "E82":"King's Indian – Sämisch","E83":"King's Indian – Sämisch",
    "E84":"King's Indian – Sämisch","E85":"King's Indian – Sämisch",
    "E86":"King's Indian – Sämisch","E87":"King's Indian – Sämisch",
    "E88":"King's Indian – Sämisch","E89":"King's Indian – Sämisch",
    "E90":"King's Indian Defence","E91":"King's Indian – Classical",
    "E92":"King's Indian – Classical","E93":"King's Indian – Petrosian",
    "E94":"King's Indian – Orthodox","E95":"King's Indian – Orthodox",
    "E96":"King's Indian – Orthodox","E97":"King's Indian – Mar del Plata",
    "E98":"King's Indian – Mar del Plata","E99":"King's Indian – Mar del Plata",
}


def resolve_name(raw: str) -> str:
    if raw.startswith("ECO "):
        code = raw[4:].strip()
        return ECO_NAMES.get(code, raw)
    return raw


def strip_move(m: str) -> str:
    """Strip x, +, # — match gen_openings.py format."""
    return m.replace("x","").replace("+","").replace("#","")


def clean_openings(input_path: str, output_path: str, max_moves: int = 12):
    print(f"Loading {input_path} ...")
    with open(input_path, encoding="utf-8") as f:
        raw = json.load(f)
    print(f"  Raw entries: {len(raw):,}")

    # Step 1: resolve + filter
    resolved = {}
    for key, name in raw.items():
        parts = key.split()
        n = len(parts)
        if n < 2 or n > max_moves:
            continue
        # Normalise key to stripped format
        norm_key = " ".join(strip_move(m) for m in parts)
        real_name = resolve_name(name)
        # Keep most specific (prefer variation names with –)
        if norm_key not in resolved:
            resolved[norm_key] = real_name
        else:
            existing = resolved[norm_key]
            new_spec = "–" in real_name or " – " in real_name
            old_spec = "–" in existing  or " – " in existing
            if new_spec and not old_spec:
                resolved[norm_key] = real_name
            elif new_spec and old_spec and len(real_name) > len(existing):
                resolved[norm_key] = real_name

    print(f"  After filtering/resolving (2–{max_moves} moves): {len(resolved):,}")

    # Step 2: add shorter prefix fallbacks for family names
    extras = {}
    for key, name in resolved.items():
        parts = key.split()
        family = name.split("–")[0].strip()
        for length in range(2, len(parts)):
            prefix = " ".join(parts[:length])
            if prefix not in resolved and prefix not in extras:
                extras[prefix] = family

    final = {**extras, **resolved}

    # Step 3: sort short-first
    final = dict(sorted(final.items(), key=lambda x: len(x[0].split())))
    print(f"  After adding family prefixes: {len(final):,}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Saved {len(final):,} openings to {output_path}")

    print("\nSample short keys:")
    for k, v in list(final.items())[:5]:
        print(f"  {k!r:40} → {v}")
    print("Sample 12-move keys:")
    long = [(k,v) for k,v in final.items() if len(k.split())==12][:4]
    for k, v in long:
        print(f"  {k!r:70} → {v}")


if __name__ == "__main__":
    clean_openings("opening.json", "Clean_openings.json", max_moves=12)
