def _explain_move_thorough(self, move: chess.Move, board: chess.Board,
                           drop: float, best: chess.Move) -> list:
    """
    Generate ALL coaching tips for a move, sorted by importance.
    """

    tips = []
    board_after = board.copy()
    board_after.push(move)
    moved_piece  = board_after.piece_at(move.to_square)
    piece_moved  = board.piece_at(move.from_square)
    move_count   = len(board.move_stack)

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
                was_defended  = bool(board.attackers(chess.WHITE, sq))
                now_defended  = bool(board_after.attackers(chess.WHITE, sq))
                now_attacked  = bool(board_after.attackers(chess.BLACK, sq))
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
            cap_pname  = PNAME.get(captured.piece_type, "piece")
            best_piece = board.piece_at(best.from_square)
            bp_name    = PNAME.get(best_piece.piece_type, "piece") if best_piece else "piece"
            add(3, f"💰 Your {bp_name} on {chess.square_name(best.from_square)} could have captured "
                   f"the opponent's {cap_pname} on {chess.square_name(best.to_square)} for free!")

    # ───────────────────────────────────────────────────────────────
    # 4. Missed check
    # ───────────────────────────────────────────────────────────────
    if best is not None and best in board.legal_moves:
        test2 = board.copy(); test2.push(best)
        if test2.is_check() and not board_after.is_check():
            best_piece = board.piece_at(best.from_square)
            bp_name    = PNAME.get(best_piece.piece_type, "piece") if best_piece else "piece"
            add(4, f"🎯 Your {bp_name} on {chess.square_name(best.from_square)} could have moved to "
                   f"{chess.square_name(best.to_square)} and put the King in check!")

    # ───────────────────────────────────────────────────────────────
    # 5. Missed checkmate
    # ───────────────────────────────────────────────────────────────
    if best is not None and best in board.legal_moves:
        test3 = board.copy(); test3.push(best)
        if test3.is_checkmate():
            best_piece = board.piece_at(best.from_square)
            bp_name    = PNAME.get(best_piece.piece_type, "piece") if best_piece else "piece"
            add(0, f"👑 You missed CHECKMATE! {bp_name} to {chess.square_name(best.to_square)} was the winning move!")

    # ───────────────────────────────────────────────────────────────
    # 6. Suggest better move (with explanation)
    # ───────────────────────────────────────────────────────────────
    if best is not None and best in board.legal_moves and best != move and drop >= 10:
        best_piece = board.piece_at(best.from_square)
        my_piece   = piece_moved
        reason = self._why_better(best, best_piece, board, board_after)

        if best_piece and my_piece and best_piece.piece_type != my_piece.piece_type:
            bp_name  = PNAME.get(best_piece.piece_type, "piece")
            my_name  = PNAME.get(my_piece.piece_type, "piece")
            to_sq    = chess.square_name(best.to_square)
            from_sq  = chess.square_name(best.from_square)
            add(5, f"💡 Instead of the {my_name}, consider moving your {bp_name} "
                   f"from {from_sq} to {to_sq}. {reason}")
        else:
            bp_name = PNAME.get(best_piece.piece_type, "piece")
            to_sq   = chess.square_name(best.to_square)
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
            cap_val   = self.PIECE_VALUE.get(captured.piece_type, 0)
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
