from __future__ import annotations

import streamlit as st

from chess_board_component import render_chess_board
from chess_engine import ChessGame, Move, parse_square, piece_color, piece_symbol, square_name

st.set_page_config(page_title="Offline Chess Duel", page_icon="♟️", layout="wide")

PAGE_CSS = """
<style>
    :root {
        --ink: #2b2118;
        --panel: rgba(255, 249, 239, 0.92);
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
        min-height: 2.9rem;
        border-radius: 16px;
        font-weight: 600;
    }
    .board-copy {
        text-align: center;
        color: rgba(43, 33, 24, 0.8);
        margin: 0.2rem 0 0.75rem;
        font-size: 0.98rem;
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
    if "last_board_event_id" not in st.session_state:
        st.session_state.last_board_event_id = None
    if "notice" not in st.session_state:
        st.session_state.notice = ("info", "Click a piece on the board, then click where you want it to move.")


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
        st.session_state.notice = ("info", "Choose the promotion piece from the board overlay first.")
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
            st.session_state.notice = ("info", "Choose a promotion piece from the board overlay.")
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


def serialize_piece(piece: str | None) -> dict[str, str] | None:
    if piece is None:
        return None
    return {
        "code": piece,
        "symbol": piece_symbol(piece),
        "color": "white" if piece.startswith("w") else "black",
        "kind": piece[1],
    }


def serialize_board_state(
    game: ChessGame,
    selected_source: tuple[int, int] | None,
    legal_targets: set[tuple[int, int]],
    ready_sources: set[tuple[int, int]],
) -> dict[str, object]:
    checked_king = game.find_king(game.turn) if game.is_in_check(game.turn) else None
    last_move = []
    if game.last_move is not None:
        last_move = [square_name(game.last_move.start), square_name(game.last_move.end)]

    return {
        "board": [[serialize_piece(piece) for piece in row] for row in game.board],
        "turn": game.turn,
        "selected_square": square_name(selected_source) if selected_source is not None else None,
        "legal_targets": [square_name(square) for square in sorted(legal_targets)],
        "movable_sources": [square_name(square) for square in sorted(ready_sources)],
        "last_move": last_move,
        "checked_king": square_name(checked_king) if checked_king is not None else None,
        "promotion": {
            "active": st.session_state.pending_promotion is not None,
            "color": game.turn,
        },
    }


init_state()
game: ChessGame = st.session_state.game
st.markdown(PAGE_CSS, unsafe_allow_html=True)
st.markdown(
    """
    <div class="hero">
        <h1>Offline Chess Duel</h1>
        <p>Local two-player chess in Streamlit, built for one device and no internet. The board now uses a custom HTML, CSS, and JavaScript component so the visible chessboard itself is the interactive surface.</p>
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

board_col, control_col = st.columns([1.55, 0.9], gap="large")
with board_col:
    st.subheader("Board")
    st.markdown(
        "<div class='board-copy'>Click directly on the board. Empty legal targets glow on the board itself, and promotion choices appear over the board.</div>",
        unsafe_allow_html=True,
    )
    board_event = render_chess_board(
        serialize_board_state(game, selected_source, legal_targets, ready_sources),
        key="main_chess_board",
    )

if board_event is not None:
    event_id = board_event.get("event_id")
    if event_id is not None and event_id != st.session_state.last_board_event_id:
        st.session_state.last_board_event_id = event_id
        if board_event.get("kind") == "square" and board_event.get("square"):
            handle_square_click(game, parse_square(board_event["square"]))
        elif board_event.get("kind") == "promotion" and board_event.get("piece"):
            complete_promotion(game, str(board_event["piece"]))
        st.rerun()

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
    st.caption("The board handles square selection and promotion directly. These controls are just for match management.")

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
