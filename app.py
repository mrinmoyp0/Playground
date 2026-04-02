from __future__ import annotations

import streamlit as st

from chess_engine import ChessGame, Move, PIECE_LABELS, piece_color, piece_kind, piece_symbol, square_name

st.set_page_config(page_title="Offline Chess Duel", page_icon="♟️", layout="wide")

PAGE_CSS = """
<style>
    :root {
        --ink: #2b2118;
        --panel: rgba(255, 249, 239, 0.92);
        --light-square: #f1ddbf;
        --dark-square: #9a6f47;
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(192, 139, 68, 0.18), transparent 32%),
            radial-gradient(circle at bottom right, rgba(104, 134, 92, 0.16), transparent 30%),
            linear-gradient(180deg, #f7f2e8 0%, #efe6d7 100%);
        color: var(--ink);
        font-family: "Palatino Linotype", "Book Antiqua", Georgia, serif;
    }
    .hero, .status-strip {
        border: 1px solid rgba(43, 33, 24, 0.08);
        border-radius: 24px;
        background: linear-gradient(135deg, rgba(255, 250, 243, 0.95), rgba(244, 232, 210, 0.9));
        box-shadow: 0 18px 40px rgba(88, 60, 32, 0.08);
    }
    .hero {
        padding: 1.35rem 1.5rem;
        margin-bottom: 1rem;
    }
    .hero h1 {
        margin: 0;
        font-size: clamp(2rem, 4vw, 3.3rem);
        line-height: 1.05;
        letter-spacing: 0.02em;
    }
    .hero p {
        margin: 0.45rem 0 0;
        max-width: 48rem;
        font-size: 1.03rem;
    }
    .status-strip {
        margin: 0.85rem 0 1rem;
        padding: 0.9rem 1rem;
    }
    div.stButton > button {
        min-height: 4.2rem;
        white-space: pre-line;
        font-size: 1.05rem;
        border-radius: 18px;
    }
    .board-frame {
        background: linear-gradient(145deg, #6e4e32, #4b311f);
        padding: 1rem;
        border-radius: 28px;
        box-shadow: 0 18px 44px rgba(48, 28, 12, 0.18);
        width: fit-content;
        margin: 0 auto;
    }
    table.chess-board {
        border-collapse: collapse;
        overflow: hidden;
        border-radius: 18px;
        background: #5b3c24;
    }
    table.chess-board td, table.chess-board th {
        text-align: center;
        vertical-align: middle;
        width: clamp(2.6rem, 9vw, 4.8rem);
        height: clamp(2.6rem, 9vw, 4.8rem);
        padding: 0;
    }
    table.chess-board th.axis {
        color: rgba(255, 250, 243, 0.85);
        background: rgba(59, 34, 15, 0.85);
        font-size: 0.92rem;
        font-weight: 600;
    }
    table.chess-board td.square {
        font-size: clamp(1.6rem, 5vw, 2.5rem);
        font-weight: 700;
        line-height: 1;
    }
    table.chess-board td.light { background: var(--light-square); }
    table.chess-board td.dark { background: var(--dark-square); }
    table.chess-board td.last-move { box-shadow: inset 0 0 0 999px rgba(244, 194, 124, 0.34); }
    table.chess-board td.selected { box-shadow: inset 0 0 0 5px rgba(227, 180, 76, 0.95); }
    table.chess-board td.ready { box-shadow: inset 0 0 0 4px rgba(183, 199, 231, 0.78); }
    table.chess-board td.target { box-shadow: inset 0 0 0 5px rgba(115, 183, 157, 0.95); }
    table.chess-board td.check { box-shadow: inset 0 0 0 5px rgba(217, 100, 89, 0.95); }
    .piece.white {
        color: #fff8f1;
        text-shadow: 0 1px 0 #5d4632, 0 0 8px rgba(0, 0, 0, 0.12);
    }
    .piece.black {
        color: #21150f;
        text-shadow: 0 1px 0 rgba(255, 255, 255, 0.12);
    }
    .marker {
        color: rgba(23, 56, 46, 0.88);
        font-size: 2rem;
    }
    .board-note {
        text-align: center;
        margin-top: 0.85rem;
        color: rgba(43, 33, 24, 0.78);
        font-size: 0.96rem;
    }
</style>
"""


def init_state() -> None:
    if "game" not in st.session_state:
        st.session_state.game = ChessGame.new_game()
    if "selected_square" not in st.session_state:
        st.session_state.selected_square = None
    if "pending_promotion" not in st.session_state:
        st.session_state.pending_promotion = None
    if "notice" not in st.session_state:
        st.session_state.notice = ("info", "Click one of the current player's pieces, then click a destination square.")


def reset_interaction(message: tuple[str, str] | None = None) -> None:
    st.session_state.selected_square = None
    st.session_state.pending_promotion = None
    if message is not None:
        st.session_state.notice = message


def source_label(game: ChessGame, square: tuple[int, int]) -> str:
    piece = game.get_piece(square)
    return f"{square_name(square)}  {piece_symbol(piece)} {PIECE_LABELS[piece_kind(piece) or 'P']}"


def destination_label(move: Move) -> str:
    if move.is_castling:
        side = "Kingside castle" if move.end[1] == 6 else "Queenside castle"
        return f"{square_name(move.end)}  {side}"
    details = ["Capture" if move.captured else "Move"]
    if move.is_en_passant:
        details = ["En passant"]
    if move.promotion is not None:
        details.append("Promote")
    return f"{square_name(move.end)}  {' / '.join(details)}"


def render_board(
    game: ChessGame,
    selected_source: tuple[int, int] | None,
    legal_targets: set[tuple[int, int]],
    ready_sources: set[tuple[int, int]],
) -> str:
    checked_king = game.find_king(game.turn) if game.is_in_check(game.turn) else None
    rows = ["<div class='board-frame'><table class='chess-board'><thead><tr><th class='axis'></th>"]
    rows.extend(f"<th class='axis'>{file_name}</th>" for file_name in "abcdefgh")
    rows.append("</tr></thead><tbody>")
    last_move_squares = {game.last_move.start, game.last_move.end} if game.last_move else set()

    for row_index in range(8):
        rank = 8 - row_index
        rows.append(f"<tr><th class='axis'>{rank}</th>")
        for col_index in range(8):
            square = (row_index, col_index)
            classes = ["square", "light" if (row_index + col_index) % 2 == 0 else "dark"]
            if square in last_move_squares:
                classes.append("last-move")
            if square == selected_source:
                classes.append("selected")
            elif selected_source is None and square in ready_sources:
                classes.append("ready")
            if square in legal_targets:
                classes.append("target")
            if square == checked_king:
                classes.append("check")

            piece = game.get_piece(square)
            if piece is not None:
                color_class = "white" if piece.startswith("w") else "black"
                content = f"<span class='piece {color_class}'>{piece_symbol(piece)}</span>"
            elif square in legal_targets:
                content = "<span class='marker'>•</span>"
            else:
                content = "&nbsp;"
            rows.append(f"<td class='{' '.join(classes)}' title='{square_name(square)}'>{content}</td>")
        rows.append(f"<th class='axis'>{rank}</th></tr>")

    rows.append("</tbody><tfoot><tr><th class='axis'></th>")
    rows.extend(f"<th class='axis'>{file_name}</th>" for file_name in "abcdefgh")
    rows.append("</tr></tfoot></table></div>")
    rows.append("<div class='board-note'>Highlights show legal sources, selected moves, the last move, and a checked king.</div>")
    return "".join(rows)


def format_move_history(move_history: list[str]) -> str:
    if not move_history:
        return "No moves played yet."
    lines: list[str] = []
    for index in range(0, len(move_history), 2):
        white_move = move_history[index]
        black_move = move_history[index + 1] if index + 1 < len(move_history) else ""
        lines.append(f"{index // 2 + 1:>2}. {white_move:<14} {black_move}")
    return "\n".join(lines)


def show_notice(level: str, message: str) -> None:
    if level == "success":
        st.success(message)
    elif level == "warning":
        st.warning(message)
    elif level == "error":
        st.error(message)
    else:
        st.info(message)


def current_legal_moves(game: ChessGame) -> list[Move]:
    selected_square = st.session_state.selected_square
    if selected_square is None:
        return []
    return game.legal_moves_for_square(selected_square)


def complete_move(game: ChessGame, start: tuple[int, int], end: tuple[int, int], promotion: str = "Q") -> None:
    success, message = game.move_piece(start, end, promotion)
    reset_interaction(("success", message) if success else ("error", message))


def handle_square_click(game: ChessGame, square: tuple[int, int]) -> None:
    if game.game_over:
        st.session_state.notice = ("warning", "This game is over. Start a new game or undo the last move.")
        return

    if st.session_state.pending_promotion is not None:
        st.session_state.notice = ("info", "Choose the promotion piece first.")
        return

    selected_square = st.session_state.selected_square
    clicked_piece = game.get_piece(square)
    can_select_clicked_piece = (
        clicked_piece is not None
        and piece_color(clicked_piece) == game.turn
        and bool(game.legal_moves_for_square(square))
    )

    if selected_square is None:
        if can_select_clicked_piece:
            st.session_state.selected_square = square
            st.session_state.notice = ("info", f"Selected {square_name(square)}. Now click a destination square.")
        else:
            st.session_state.notice = ("warning", "Click one of the current player's movable pieces.")
        return

    if square == selected_square:
        st.session_state.selected_square = None
        st.session_state.notice = ("info", "Selection cleared.")
        return

    legal_moves = {move.end: move for move in game.legal_moves_for_square(selected_square)}
    if square in legal_moves:
        move = legal_moves[square]
        if move.promotion is not None:
            st.session_state.pending_promotion = (selected_square, square)
            st.session_state.notice = ("info", "Choose a promotion piece to finish the move.")
        else:
            complete_move(game, selected_square, square)
        return

    if can_select_clicked_piece:
        st.session_state.selected_square = square
        st.session_state.notice = ("info", f"Selected {square_name(square)}. Now click a destination square.")
    else:
        st.session_state.notice = ("warning", "That square is not a legal destination.")


def complete_promotion(game: ChessGame, promotion: str) -> None:
    pending_promotion = st.session_state.pending_promotion
    if pending_promotion is None:
        return
    start, end = pending_promotion
    complete_move(game, start, end, promotion)


def square_button_label(
    game: ChessGame,
    square: tuple[int, int],
    legal_targets: set[tuple[int, int]],
    ready_sources: set[tuple[int, int]],
) -> str:
    piece = game.get_piece(square)
    symbol = piece_symbol(piece) or ("•" if square in legal_targets else "·")
    footer = square_name(square)

    if game.is_in_check(game.turn) and square == game.find_king(game.turn):
        footer += " !"
    elif square == st.session_state.selected_square:
        footer += " *"
    elif square in legal_targets:
        footer += " ->"
    elif st.session_state.selected_square is None and square in ready_sources:
        footer += " +"
    elif game.last_move is not None and square in {game.last_move.start, game.last_move.end}:
        footer += " •"

    return f"{symbol}\n{footer}"


init_state()
game: ChessGame = st.session_state.game
st.markdown(PAGE_CSS, unsafe_allow_html=True)
st.markdown(
    """
    <div class="hero">
        <h1>Offline Chess Duel</h1>
        <p>Local two-player chess in Streamlit, built for one device and no internet. The app handles legal moves, castling, en passant, promotion, check, checkmate, stalemate, undo, and move history.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown(f"<div class='status-strip'><strong>Status</strong><br>{game.status}</div>", unsafe_allow_html=True)

notice_level, notice_message = st.session_state.notice
show_notice(notice_level, notice_message)

available_sources = game.available_source_squares()
selected_source = st.session_state.selected_square
legal_moves = current_legal_moves(game)
legal_targets = {move.end for move in legal_moves}
ready_sources = set() if selected_source is not None else set(available_sources)

control_col, board_col = st.columns([0.92, 1.28], gap="large")
with control_col:
    st.subheader("Match Controls")
    st.markdown(f"**Turn:** `{game.turn.capitalize()}`")
    st.markdown(
        f"**Selected square:** `{square_name(selected_source)}`"
        if selected_source is not None
        else "**Selected square:** `None`"
    )
    st.markdown(f"**White captured:** {' '.join(piece_symbol(piece) for piece in game.captured_pieces['white']) or 'None'}")
    st.markdown(f"**Black captured:** {' '.join(piece_symbol(piece) for piece in game.captured_pieces['black']) or 'None'}")
    st.caption("Legend: `+` movable piece, `*` selected, `->` legal target, `!` checked king, `•` last move.")

    if st.session_state.pending_promotion is not None:
        st.markdown("**Promotion**")
        promo_cols = st.columns(4, gap="small")
        for column, code in zip(promo_cols, ["Q", "R", "B", "N"]):
            if column.button(PIECE_LABELS[code], key=f"promote_{code}", use_container_width=True):
                complete_promotion(game, code)
                st.rerun()

    if st.button("Clear selection", disabled=selected_source is None, use_container_width=True):
        reset_interaction(("info", "Selection cleared."))
        st.rerun()

    if st.button("Undo last move", disabled=not game.history_stack, use_container_width=True):
        success, message = game.undo()
        reset_interaction(("info", message) if success else ("warning", message))
        st.rerun()

    if st.button("Start new game", use_container_width=True):
        st.session_state.game = ChessGame.new_game()
        reset_interaction(("info", "Fresh board ready. White to move."))
        st.rerun()

    st.subheader("Move List")
    st.code(format_move_history(game.move_history), language=None)

with board_col:
    st.subheader("Board")
    st.caption("Click a piece, then click the square you want to move it to.")
    st.markdown(
        render_board(
            game,
            selected_source,
            legal_targets,
            ready_sources,
        ),
        unsafe_allow_html=True,
    )

    file_header = st.columns([0.5] + [1] * 8 + [0.5], gap="small")
    for index, file_name in enumerate("abcdefgh", start=1):
        file_header[index].markdown(f"**{file_name}**")

    for row_index in range(8):
        rank = 8 - row_index
        row_cols = st.columns([0.5] + [1] * 8 + [0.5], gap="small")
        row_cols[0].markdown(f"**{rank}**")
        for col_index in range(8):
            square = (row_index, col_index)
            button_type = "primary" if (
                square == selected_source or square in legal_targets or square in ready_sources
            ) else "secondary"
            if row_cols[col_index + 1].button(
                square_button_label(game, square, legal_targets, ready_sources),
                key=f"square_{row_index}_{col_index}",
                type=button_type,
                use_container_width=True,
            ):
                handle_square_click(game, square)
                st.rerun()
        row_cols[-1].markdown(f"**{rank}**")

    file_footer = st.columns([0.5] + [1] * 8 + [0.5], gap="small")
    for index, file_name in enumerate("abcdefgh", start=1):
        file_footer[index].markdown(f"**{file_name}**")
