from __future__ import annotations

from html import escape

import streamlit as st

from chess_board_component import render_chess_board
from chess_engine import ChessGame, Move, parse_square, piece_color, piece_symbol, square_name

st.set_page_config(page_title="Offline Chess Duel", page_icon="♟️", layout="wide")

PAGE_CSS = """
<style>
    :root {
        --ink: #2b2118;
        --panel: rgba(255, 249, 239, 0.92);
        --panel-strong: rgba(255, 252, 245, 0.96);
        --line: rgba(78, 54, 31, 0.12);
        --accent: #8b5a2b;
        --accent-soft: rgba(139, 90, 43, 0.12);
        --good: #406a48;
        --warn: #8e6a25;
        --bad: #8a3f35;
        --info: #4f6476;
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(192, 139, 68, 0.18), transparent 32%),
            radial-gradient(circle at bottom right, rgba(104, 134, 92, 0.16), transparent 30%),
            linear-gradient(180deg, #f7f2e8 0%, #efe6d7 100%);
        color: var(--ink);
        font-family: "Palatino Linotype", "Book Antiqua", Georgia, serif;
    }
    header[data-testid="stHeader"] {
        display: none;
    }
    div[data-testid="stToolbar"] {
        display: none;
    }
    div[data-testid="stDecoration"] {
        display: none;
    }
    div[data-testid="stStatusWidget"] {
        display: none;
    }
    #MainMenu,
    footer {
        display: none;
    }
    .block-container {
        padding-top: 0.35rem;
        padding-bottom: 0.35rem;
        max-width: 1600px;
    }
    [data-testid="stHorizontalBlock"] {
        align-items: start;
    }
    .side-card {
        border: 1px solid rgba(43, 33, 24, 0.08);
        border-radius: 20px;
        background: linear-gradient(135deg, rgba(255, 250, 243, 0.95), rgba(244, 232, 210, 0.9));
        box-shadow: 0 18px 40px rgba(88, 60, 32, 0.08);
        padding: 0.95rem 1rem;
        margin-bottom: 0.7rem;
    }
    .title-card {
        padding: 1rem 1rem 0.9rem;
    }
    .title-kicker {
        text-transform: uppercase;
        letter-spacing: 0.14em;
        font-size: 0.73rem;
        color: rgba(70, 50, 30, 0.72);
        margin-bottom: 0.25rem;
    }
    .title-card h1 {
        margin: 0;
        font-size: clamp(1.7rem, 2.4vw, 2.45rem);
        line-height: 1;
        letter-spacing: 0.01em;
    }
    .title-card p {
        margin: 0.35rem 0 0;
        color: rgba(43, 33, 24, 0.74);
        font-size: 0.94rem;
        line-height: 1.35;
    }
    .card-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: rgba(70, 50, 30, 0.72);
        margin-bottom: 0.28rem;
    }
    .status-text {
        font-size: 1.05rem;
        font-weight: 700;
        line-height: 1.25;
        color: #432d1c;
        margin-bottom: 0.55rem;
    }
    .meta-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 0.5rem;
    }
    .meta-item {
        border: 1px solid var(--line);
        background: var(--panel-strong);
        border-radius: 14px;
        padding: 0.55rem 0.7rem;
    }
    .meta-item span {
        display: block;
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: rgba(70, 50, 30, 0.64);
        margin-bottom: 0.15rem;
    }
    .meta-item strong {
        display: block;
        font-size: 0.98rem;
    }
    .capture-line {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.8rem;
        padding: 0.45rem 0;
        border-bottom: 1px solid var(--line);
    }
    .capture-line:last-child {
        border-bottom: none;
        padding-bottom: 0;
    }
    .capture-line span {
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: rgba(70, 50, 30, 0.68);
    }
    .capture-line strong {
        font-size: 1rem;
        text-align: right;
        font-weight: 700;
    }
    .notice-card {
        border-radius: 18px;
        padding: 0.8rem 0.95rem;
        border: 1px solid var(--line);
        background: var(--panel-strong);
        box-shadow: 0 14px 30px rgba(88, 60, 32, 0.06);
        margin-bottom: 0.7rem;
    }
    .notice-card.info { border-left: 5px solid var(--info); }
    .notice-card.success { border-left: 5px solid var(--good); }
    .notice-card.warning { border-left: 5px solid var(--warn); }
    .notice-card.error { border-left: 5px solid var(--bad); }
    .notice-card strong {
        display: block;
        margin-bottom: 0.2rem;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: rgba(70, 50, 30, 0.75);
    }
    .notice-card p {
        margin: 0;
        font-size: 0.95rem;
        line-height: 1.35;
    }
    div.stButton > button {
        min-height: 2.7rem;
        border-radius: 14px;
        font-weight: 600;
        background: linear-gradient(180deg, #fff8ec, #ead8b7);
        color: #3c2817;
        border: 1px solid rgba(92, 62, 34, 0.22);
        box-shadow:
            0 10px 18px rgba(92, 62, 34, 0.10),
            inset 0 1px 0 rgba(255, 255, 255, 0.65);
        transition:
            transform 120ms ease,
            box-shadow 120ms ease,
            filter 120ms ease;
    }
    div.stButton > button:hover {
        background: linear-gradient(180deg, #fffaf1, #efdcb9);
        color: #2f1f12;
        border-color: rgba(139, 90, 43, 0.38);
        box-shadow:
            0 12px 22px rgba(92, 62, 34, 0.14),
            inset 0 1px 0 rgba(255, 255, 255, 0.72);
        transform: translateY(-1px);
    }
    div.stButton > button:disabled {
        background: linear-gradient(180deg, #eee4d2, #dfd0b8);
        color: rgba(60, 40, 23, 0.58);
        border-color: rgba(92, 62, 34, 0.14);
        box-shadow: none;
        opacity: 1;
        cursor: not-allowed;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(180deg, #b78043, #8d5a2f);
        color: #fff7ee;
        border-color: rgba(88, 48, 20, 0.38);
        box-shadow:
            0 12px 22px rgba(96, 57, 27, 0.20),
            inset 0 1px 0 rgba(255, 236, 208, 0.30);
    }
    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(180deg, #c48a49, #996133);
        color: #fffaf4;
    }
    .board-wrap {
        padding-top: 0.15rem;
    }
    .move-box {
        margin: 0;
        padding: 0.8rem 0.9rem;
        border-radius: 16px;
        background: #211812;
        color: #f4eadc;
        font-family: Consolas, "Courier New", monospace;
        font-size: 0.88rem;
        line-height: 1.45;
        max-height: 210px;
        overflow-y: auto;
        white-space: pre-wrap;
        border: 1px solid rgba(255, 255, 255, 0.06);
    }
    .mini-note {
        color: rgba(43, 33, 24, 0.7);
        font-size: 0.84rem;
        line-height: 1.35;
        margin: 0.2rem 0 0.7rem;
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


def notice_markup(level: str, message: str) -> str:
    titles = {
        "success": "Move Accepted",
        "warning": "Heads Up",
        "error": "Illegal Move",
        "info": "Now Playing",
    }
    title = titles.get(level, "Notice")
    return f"""
    <div class="notice-card {escape(level)}">
        <strong>{escape(title)}</strong>
        <p>{escape(message)}</p>
    </div>
    """


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

available_sources = game.available_source_squares()
selected_source = st.session_state.selected_square
legal_moves = current_legal_moves(game)
legal_targets = {move.end for move in legal_moves}
ready_sources = set() if selected_source is not None else set(available_sources)
notice_level, notice_message = st.session_state.notice

board_col, control_col = st.columns([1.82, 0.86], gap="large")
with board_col:
    board_event = render_chess_board(
        serialize_board_state(game, selected_source, legal_targets, ready_sources),
        key="main_chess_board",
        height=655,
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
    st.markdown(
        """
        <div class="side-card title-card">
            <div class="title-kicker">Offline Two-Player Chess</div>
            <h1>Offline Chess Duel</h1>
            <p>Play directly on the board. All match details stay in this right-hand panel.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="side-card">
            <div class="card-label">Status</div>
            <div class="status-text">{escape(game.status)}</div>
            <div class="meta-grid">
                <div class="meta-item">
                    <span>Turn</span>
                    <strong>{escape(game.turn.capitalize())}</strong>
                </div>
                <div class="meta-item">
                    <span>Selected</span>
                    <strong>{escape(square_name(selected_source) if selected_source is not None else 'None')}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(notice_markup(notice_level, notice_message), unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="side-card">
            <div class="card-label">Captured Pieces</div>
            <div class="capture-line">
                <span>White</span>
                <strong>{escape(' '.join(piece_symbol(piece) for piece in game.captured_pieces['white']) or 'None')}</strong>
            </div>
            <div class="capture-line">
                <span>Black</span>
                <strong>{escape(' '.join(piece_symbol(piece) for piece in game.captured_pieces['black']) or 'None')}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div class='mini-note'>Use these controls for selection resets, undo, and starting a new match. The board itself handles moves and promotion.</div>", unsafe_allow_html=True)

    action_left, action_right = st.columns(2, gap="small")
    if action_left.button("Clear Selection", disabled=selected_source is None, use_container_width=True):
        reset_interaction(("info", "Selection cleared."))
        st.rerun()

    if action_right.button("Undo Move", disabled=not game.history_stack, use_container_width=True):
        success, message = game.undo()
        reset_interaction(("info", message) if success else ("warning", message))
        st.rerun()

    if st.button("Start new game", use_container_width=True):
        st.session_state.game = ChessGame.new_game()
        reset_interaction(("info", "Fresh board ready. White to move."))
        st.rerun()

    st.markdown(
        f"""
        <div class="side-card">
            <div class="card-label">Move List</div>
            <pre class="move-box">{escape(format_move_history(game.move_history))}</pre>
        </div>
        """,
        unsafe_allow_html=True,
    )
