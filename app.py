from __future__ import annotations

import streamlit as st

from chess_engine import ChessGame, Move, PIECE_LABELS, piece_kind, piece_symbol, square_name

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
    if "source_choice" not in st.session_state:
        st.session_state.source_choice = ""
    if "destination_choice" not in st.session_state:
        st.session_state.destination_choice = ""
    if "promotion_choice" not in st.session_state:
        st.session_state.promotion_choice = "Q"
    if "notice" not in st.session_state:
        st.session_state.notice = ("info", "Choose a piece and destination to start the match.")


def reset_controls(message: tuple[str, str] | None = None) -> None:
    st.session_state.source_choice = ""
    st.session_state.destination_choice = ""
    st.session_state.promotion_choice = "Q"
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
source_lookup = {source_label(game, square): square for square in available_sources}
source_options = [""] + list(source_lookup)
if st.session_state.source_choice not in source_options:
    st.session_state.source_choice = ""

selected_source_label = st.selectbox(
    "Piece to move",
    source_options,
    key="source_choice",
    format_func=lambda option: option or "Choose a legal piece",
)
selected_source = source_lookup.get(selected_source_label)
legal_moves = game.legal_moves_for_square(selected_source) if selected_source is not None else []
legal_targets = {move.end for move in legal_moves}

destination_lookup = {destination_label(move): move for move in legal_moves}
destination_options = [""] + list(destination_lookup)
if st.session_state.destination_choice not in destination_options:
    st.session_state.destination_choice = ""

selected_destination_label = st.selectbox(
    "Destination",
    destination_options,
    key="destination_choice",
    format_func=lambda option: option or "Choose a target square",
    disabled=not destination_lookup,
)
selected_move = destination_lookup.get(selected_destination_label)
if selected_move is not None and selected_move.promotion is not None:
    st.selectbox(
        "Promotion piece",
        ["Q", "R", "B", "N"],
        key="promotion_choice",
        format_func=lambda code: PIECE_LABELS[code],
    )

control_col, board_col = st.columns([0.92, 1.28], gap="large")
with control_col:
    st.subheader("Match Controls")
    st.markdown(f"**Turn:** `{game.turn.capitalize()}`")
    st.markdown(f"**White captured:** {' '.join(piece_symbol(piece) for piece in game.captured_pieces['white']) or 'None'}")
    st.markdown(f"**Black captured:** {' '.join(piece_symbol(piece) for piece in game.captured_pieces['black']) or 'None'}")

    if st.button("Play move", type="primary", disabled=selected_move is None, use_container_width=True):
        if selected_move is not None:
            success, message = game.move_piece(
                selected_move.start,
                selected_move.end,
                st.session_state.promotion_choice,
            )
        reset_controls(("success", message) if success else ("error", message))
        st.rerun()

    if st.button("Undo last move", disabled=not game.history_stack, use_container_width=True):
        success, message = game.undo()
        reset_controls(("info", message) if success else ("warning", message))
        st.rerun()

    if st.button("Start new game", use_container_width=True):
        st.session_state.game = ChessGame.new_game()
        reset_controls(("info", "Fresh board ready. White to move."))
        st.rerun()

    st.subheader("Move List")
    st.code(format_move_history(game.move_history), language=None)

with board_col:
    st.subheader("Board")
    st.markdown(
        render_board(
            game,
            selected_source,
            legal_targets,
            set() if selected_source is not None else set(available_sources),
        ),
        unsafe_allow_html=True,
    )
