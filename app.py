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
        --highlight-square: #ddb15f;
        --highlight-ink: #2b1d0f;
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
    [data-testid="stHorizontalBlock"] {
        align-items: center;
    }
    div.stButton > button {
        min-height: 4.4rem;
        white-space: pre-line;
        font-size: 2rem;
        border-radius: 0.15rem;
        padding: 0;
        border: 1px solid rgba(59, 34, 15, 0.18);
        box-shadow: none;
        transition: transform 120ms ease, box-shadow 120ms ease, filter 120ms ease;
    }
    div.stButton > button:hover {
        transform: scale(1.015);
        filter: brightness(1.03);
    }
    div.stButton > button[kind="primary"] {
        background: var(--dark-square);
        color: #fff8f1;
    }
    div.stButton > button[kind="secondary"] {
        background: var(--light-square);
        color: #1f1710;
    }
    div.stButton > button[kind="tertiary"] {
        background: linear-gradient(180deg, #f3cf86, var(--highlight-square));
        color: var(--highlight-ink);
        border: 2px solid #a8752f;
        box-shadow: inset 0 0 0 1px rgba(255, 247, 226, 0.55);
    }
    .axis-cell {
        text-align: center;
        color: rgba(255, 250, 243, 0.9);
        font-size: 0.92rem;
        font-weight: 600;
        line-height: 1;
        padding-top: 0.2rem;
    }
    .board-note, .board-heading {
        text-align: center;
        color: rgba(43, 33, 24, 0.78);
    }
    .board-heading {
        margin-bottom: 0.65rem;
        font-size: 1rem;
    }
    .board-note {
        margin-top: 0.85rem;
        font-size: 0.94rem;
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
) -> str:
    piece = game.get_piece(square)
    return piece_symbol(piece) or ("•" if square in legal_targets else " ")


def square_button_type(
    game: ChessGame,
    square: tuple[int, int],
    selected_source: tuple[int, int] | None,
    legal_targets: set[tuple[int, int]],
) -> str:
    in_check_square = game.is_in_check(game.turn) and square == game.find_king(game.turn)
    is_last_move_square = game.last_move is not None and square in {game.last_move.start, game.last_move.end}
    if square == selected_source or square in legal_targets or in_check_square or is_last_move_square:
        return "tertiary"
    return "secondary" if (square[0] + square[1]) % 2 == 0 else "primary"


def square_help(
    game: ChessGame,
    square: tuple[int, int],
    selected_source: tuple[int, int] | None,
    legal_targets: set[tuple[int, int]],
    ready_sources: set[tuple[int, int]],
) -> str:
    piece = game.get_piece(square)
    parts = [square_name(square)]
    if piece is not None:
        color = "White" if piece.startswith("w") else "Black"
        parts.append(f"{color} {PIECE_LABELS[piece_kind(piece) or 'P']}")
    if square == selected_source:
        parts.append("Selected")
    elif square in legal_targets:
        parts.append("Legal move")
    elif selected_source is None and square in ready_sources:
        parts.append("Movable piece")
    return " | ".join(parts)


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

board_col, control_col = st.columns([1.45, 0.95], gap="large")
with board_col:
    st.subheader("Board")
    st.markdown(
        "<div class='board-heading'>Click the piece you want to move, then click its destination on the same board.</div>",
        unsafe_allow_html=True,
    )

    file_header = st.columns([0.42] + [1] * 8 + [0.42], gap="small")
    for index, file_name in enumerate("abcdefgh", start=1):
        file_header[index].markdown(f"<div class='axis-cell'>{file_name}</div>", unsafe_allow_html=True)

    for row_index in range(8):
        rank = 8 - row_index
        row_cols = st.columns([0.42] + [1] * 8 + [0.42], gap="small")
        row_cols[0].markdown(f"<div class='axis-cell'>{rank}</div>", unsafe_allow_html=True)
        for col_index in range(8):
            square = (row_index, col_index)
            if row_cols[col_index + 1].button(
                square_button_label(game, square, legal_targets),
                key=f"square_{row_index}_{col_index}",
                type=square_button_type(game, square, selected_source, legal_targets),
                help=square_help(game, square, selected_source, legal_targets, ready_sources),
                use_container_width=True,
            ):
                handle_square_click(game, square)
                st.rerun()
        row_cols[-1].markdown(f"<div class='axis-cell'>{rank}</div>", unsafe_allow_html=True)

    file_footer = st.columns([0.42] + [1] * 8 + [0.42], gap="small")
    for index, file_name in enumerate("abcdefgh", start=1):
        file_footer[index].markdown(f"<div class='axis-cell'>{file_name}</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='board-note'>Gold squares show the current selection, legal destinations, the last move, and a king in check.</div>",
        unsafe_allow_html=True,
    )

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
    st.caption("Use the board directly. Promotion options appear here only when a pawn reaches the last rank.")

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
