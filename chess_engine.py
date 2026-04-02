from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field, replace

FILES = "abcdefgh"
PROMOTION_OPTIONS = ("Q", "R", "B", "N")
UNICODE_PIECES = {
    "wK": "♔",
    "wQ": "♕",
    "wR": "♖",
    "wB": "♗",
    "wN": "♘",
    "wP": "♙",
    "bK": "♚",
    "bQ": "♛",
    "bR": "♜",
    "bB": "♝",
    "bN": "♞",
    "bP": "♟",
}
PIECE_LABELS = {
    "K": "King",
    "Q": "Queen",
    "R": "Rook",
    "B": "Bishop",
    "N": "Knight",
    "P": "Pawn",
}

Square = tuple[int, int]
Board = list[list[str | None]]


def initial_board() -> Board:
    back_rank = ["R", "N", "B", "Q", "K", "B", "N", "R"]
    return [
        [f"b{piece}" for piece in back_rank],
        ["bP"] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        [None] * 8,
        ["wP"] * 8,
        [f"w{piece}" for piece in back_rank],
    ]


def square_name(square: Square) -> str:
    row, col = square
    return f"{FILES[col]}{8 - row}"


def parse_square(name: str) -> Square:
    cleaned = name.strip().lower()
    if len(cleaned) != 2 or cleaned[0] not in FILES or cleaned[1] not in "12345678":
        raise ValueError(f"Invalid square: {name}")
    return 8 - int(cleaned[1]), FILES.index(cleaned[0])


def in_bounds(row: int, col: int) -> bool:
    return 0 <= row < 8 and 0 <= col < 8


def piece_color(piece: str | None) -> str | None:
    if piece is None:
        return None
    return "white" if piece[0] == "w" else "black"


def piece_kind(piece: str | None) -> str | None:
    if piece is None:
        return None
    return piece[1]


def enemy(color: str) -> str:
    return "black" if color == "white" else "white"


def piece_symbol(piece: str | None) -> str:
    return UNICODE_PIECES.get(piece or "", "")


@dataclass(frozen=True)
class Move:
    start: Square
    end: Square
    piece: str
    captured: str | None = None
    promotion: str | None = None
    is_castling: bool = False
    is_en_passant: bool = False


@dataclass
class ChessGame:
    board: Board = field(default_factory=initial_board)
    turn: str = "white"
    castling_rights: dict[str, dict[str, bool]] = field(
        default_factory=lambda: {
            "white": {"king_side": True, "queen_side": True},
            "black": {"king_side": True, "queen_side": True},
        }
    )
    en_passant_target: Square | None = None
    move_history: list[str] = field(default_factory=list)
    captured_pieces: dict[str, list[str]] = field(
        default_factory=lambda: {"white": [], "black": []}
    )
    history_stack: list[dict[str, object]] = field(default_factory=list)
    last_move: Move | None = None
    status: str = "White to move."
    game_over: bool = False
    winner: str | None = None

    @classmethod
    def new_game(cls) -> "ChessGame":
        return cls()

    def reset(self) -> None:
        fresh_game = self.new_game()
        self.__dict__.update(deepcopy(fresh_game.__dict__))

    def snapshot(self) -> dict[str, object]:
        return {
            "board": deepcopy(self.board),
            "turn": self.turn,
            "castling_rights": deepcopy(self.castling_rights),
            "en_passant_target": self.en_passant_target,
            "move_history": list(self.move_history),
            "captured_pieces": deepcopy(self.captured_pieces),
            "last_move": self.last_move,
            "status": self.status,
            "game_over": self.game_over,
            "winner": self.winner,
        }

    def restore(self, snapshot: dict[str, object]) -> None:
        self.board = deepcopy(snapshot["board"])  # type: ignore[assignment]
        self.turn = snapshot["turn"]  # type: ignore[assignment]
        self.castling_rights = deepcopy(snapshot["castling_rights"])  # type: ignore[assignment]
        self.en_passant_target = snapshot["en_passant_target"]  # type: ignore[assignment]
        self.move_history = list(snapshot["move_history"])  # type: ignore[assignment]
        self.captured_pieces = deepcopy(snapshot["captured_pieces"])  # type: ignore[assignment]
        self.last_move = snapshot["last_move"]  # type: ignore[assignment]
        self.status = snapshot["status"]  # type: ignore[assignment]
        self.game_over = snapshot["game_over"]  # type: ignore[assignment]
        self.winner = snapshot["winner"]  # type: ignore[assignment]

    def undo(self) -> tuple[bool, str]:
        if not self.history_stack:
            return False, "There isn't a move to undo yet."
        snapshot = self.history_stack.pop()
        self.restore(snapshot)
        return True, "Reverted the last move."

    def get_piece(self, square: Square) -> str | None:
        row, col = square
        return self.board[row][col]

    def set_piece(self, square: Square, piece: str | None) -> None:
        row, col = square
        self.board[row][col] = piece

    def find_king(self, color: str) -> Square:
        target = "wK" if color == "white" else "bK"
        for row in range(8):
            for col in range(8):
                if self.board[row][col] == target:
                    return row, col
        raise ValueError(f"Missing {color} king on board.")

    def square_under_attack(self, square: Square, by_color: str) -> bool:
        row, col = square
        attacker_prefix = "w" if by_color == "white" else "b"

        pawn_row = row + 1 if by_color == "white" else row - 1
        for pawn_col in (col - 1, col + 1):
            if in_bounds(pawn_row, pawn_col) and self.board[pawn_row][pawn_col] == f"{attacker_prefix}P":
                return True

        for row_offset, col_offset in (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ):
            new_row, new_col = row + row_offset, col + col_offset
            if in_bounds(new_row, new_col) and self.board[new_row][new_col] == f"{attacker_prefix}N":
                return True

        for row_offset, col_offset in (
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (0, -1),
            (0, 1),
            (1, -1),
            (1, 0),
            (1, 1),
        ):
            new_row, new_col = row + row_offset, col + col_offset
            if in_bounds(new_row, new_col) and self.board[new_row][new_col] == f"{attacker_prefix}K":
                return True

        for row_step, col_step in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            new_row, new_col = row + row_step, col + col_step
            while in_bounds(new_row, new_col):
                piece = self.board[new_row][new_col]
                if piece is not None:
                    if piece == f"{attacker_prefix}R" or piece == f"{attacker_prefix}Q":
                        return True
                    break
                new_row += row_step
                new_col += col_step

        for row_step, col_step in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            new_row, new_col = row + row_step, col + col_step
            while in_bounds(new_row, new_col):
                piece = self.board[new_row][new_col]
                if piece is not None:
                    if piece == f"{attacker_prefix}B" or piece == f"{attacker_prefix}Q":
                        return True
                    break
                new_row += row_step
                new_col += col_step

        return False

    def is_in_check(self, color: str) -> bool:
        return self.square_under_attack(self.find_king(color), enemy(color))

    def available_source_squares(self, color: str | None = None) -> list[Square]:
        active_color = color or self.turn
        sources: list[Square] = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece_color(piece) != active_color:
                    continue
                if self.legal_moves_for_square((row, col), active_color):
                    sources.append((row, col))
        return sources

    def all_legal_moves(self, color: str | None = None) -> list[Move]:
        active_color = color or self.turn
        legal_moves: list[Move] = []
        for source in self.available_source_squares(active_color):
            legal_moves.extend(self.legal_moves_for_square(source, active_color))
        return legal_moves

    def legal_moves_for_square(self, square: Square | None, color: str | None = None) -> list[Move]:
        if square is None:
            return []

        row, col = square
        piece = self.board[row][col]
        if piece is None:
            return []

        active_color = color or self.turn
        if piece_color(piece) != active_color:
            return []

        legal_moves: list[Move] = []
        for candidate in self._pseudo_legal_moves(square):
            sandbox = deepcopy(self)
            sandbox.history_stack = []
            sandbox._apply_move(candidate, record_history=False, update_status=False)
            if not sandbox.is_in_check(active_color):
                legal_moves.append(candidate)
        return legal_moves

    def move_piece(self, start: Square, end: Square, promotion: str = "Q") -> tuple[bool, str]:
        if self.game_over:
            return False, "This game is already over. Start a new one to keep playing."

        selected_piece = self.get_piece(start)
        if selected_piece is None:
            return False, "Choose a square that has one of the current player's pieces."
        if piece_color(selected_piece) != self.turn:
            return False, f"It is {self.turn}'s turn."

        promotion_choice = promotion.upper()
        if promotion_choice not in PROMOTION_OPTIONS:
            return False, "Promotion must be one of Q, R, B, or N."

        legal_moves = self.legal_moves_for_square(start, self.turn)
        for move in legal_moves:
            if move.end != end:
                continue
            chosen_move = replace(move, promotion=promotion_choice) if move.promotion else move
            self._apply_move(chosen_move, record_history=True, update_status=True)
            return True, self.status if self.game_over else f"Played {self.move_history[-1]}."

        return False, "That move isn't legal in the current position."

    def _pseudo_legal_moves(self, square: Square) -> list[Move]:
        row, col = square
        piece = self.board[row][col]
        if piece is None:
            return []

        kind = piece_kind(piece)
        if kind == "P":
            return self._pawn_moves(square, piece)
        if kind == "N":
            return self._knight_moves(square, piece)
        if kind == "B":
            return self._sliding_moves(square, piece, ((-1, -1), (-1, 1), (1, -1), (1, 1)))
        if kind == "R":
            return self._sliding_moves(square, piece, ((-1, 0), (1, 0), (0, -1), (0, 1)))
        if kind == "Q":
            return self._sliding_moves(
                square,
                piece,
                ((-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)),
            )
        if kind == "K":
            return self._king_moves(square, piece)
        return []

    def _pawn_moves(self, square: Square, piece: str) -> list[Move]:
        row, col = square
        color = piece_color(piece)
        assert color is not None
        direction = -1 if color == "white" else 1
        start_row = 6 if color == "white" else 1
        promotion_row = 0 if color == "white" else 7
        enemy_prefix = "b" if color == "white" else "w"
        moves: list[Move] = []

        one_step = row + direction
        if in_bounds(one_step, col) and self.board[one_step][col] is None:
            moves.append(
                Move(square, (one_step, col), piece, promotion="Q" if one_step == promotion_row else None)
            )
            two_step = row + (2 * direction)
            if row == start_row and self.board[two_step][col] is None:
                moves.append(Move(square, (two_step, col), piece))

        for col_offset in (-1, 1):
            target_row, target_col = row + direction, col + col_offset
            if not in_bounds(target_row, target_col):
                continue

            target_piece = self.board[target_row][target_col]
            promotion = "Q" if target_row == promotion_row else None
            if target_piece is not None and target_piece[0] == enemy_prefix:
                moves.append(Move(square, (target_row, target_col), piece, target_piece, promotion))
                continue

            adjacent_piece = self.board[row][target_col] if in_bounds(row, target_col) else None
            if self.en_passant_target == (target_row, target_col) and adjacent_piece == f"{enemy_prefix}P":
                moves.append(
                    Move(
                        square,
                        (target_row, target_col),
                        piece,
                        captured=f"{enemy_prefix}P",
                        is_en_passant=True,
                    )
                )

        return moves

    def _knight_moves(self, square: Square, piece: str) -> list[Move]:
        row, col = square
        color = piece_color(piece)
        moves: list[Move] = []
        for row_offset, col_offset in (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ):
            new_row, new_col = row + row_offset, col + col_offset
            if not in_bounds(new_row, new_col):
                continue
            target = self.board[new_row][new_col]
            if target is None or piece_color(target) != color:
                moves.append(Move(square, (new_row, new_col), piece, captured=target))
        return moves

    def _sliding_moves(
        self, square: Square, piece: str, directions: tuple[tuple[int, int], ...]
    ) -> list[Move]:
        row, col = square
        color = piece_color(piece)
        moves: list[Move] = []
        for row_step, col_step in directions:
            new_row, new_col = row + row_step, col + col_step
            while in_bounds(new_row, new_col):
                target = self.board[new_row][new_col]
                if target is None:
                    moves.append(Move(square, (new_row, new_col), piece))
                else:
                    if piece_color(target) != color:
                        moves.append(Move(square, (new_row, new_col), piece, captured=target))
                    break
                new_row += row_step
                new_col += col_step
        return moves

    def _king_moves(self, square: Square, piece: str) -> list[Move]:
        row, col = square
        color = piece_color(piece)
        assert color is not None
        moves: list[Move] = []

        for row_offset in (-1, 0, 1):
            for col_offset in (-1, 0, 1):
                if row_offset == 0 and col_offset == 0:
                    continue
                new_row, new_col = row + row_offset, col + col_offset
                if not in_bounds(new_row, new_col):
                    continue
                target = self.board[new_row][new_col]
                if target is None or piece_color(target) != color:
                    moves.append(Move(square, (new_row, new_col), piece, captured=target))

        if self.is_in_check(color):
            return moves

        home_row = 7 if color == "white" else 0
        rook_code = "wR" if color == "white" else "bR"
        if square == (home_row, 4) and self.castling_rights[color]["king_side"]:
            if (
                self.board[home_row][5] is None
                and self.board[home_row][6] is None
                and self.board[home_row][7] == rook_code
                and not self.square_under_attack((home_row, 5), enemy(color))
                and not self.square_under_attack((home_row, 6), enemy(color))
            ):
                moves.append(Move(square, (home_row, 6), piece, is_castling=True))

        if square == (home_row, 4) and self.castling_rights[color]["queen_side"]:
            if (
                self.board[home_row][1] is None
                and self.board[home_row][2] is None
                and self.board[home_row][3] is None
                and self.board[home_row][0] == rook_code
                and not self.square_under_attack((home_row, 3), enemy(color))
                and not self.square_under_attack((home_row, 2), enemy(color))
            ):
                moves.append(Move(square, (home_row, 2), piece, is_castling=True))

        return moves

    def _apply_move(self, move: Move, record_history: bool, update_status: bool) -> None:
        moving_piece = self.get_piece(move.start)
        if moving_piece is None:
            raise ValueError("No piece found on the source square.")

        moving_color = piece_color(moving_piece)
        assert moving_color is not None

        if record_history:
            self.history_stack.append(self.snapshot())

        captured_piece = self.get_piece(move.end)
        self.set_piece(move.start, None)

        if move.is_en_passant:
            capture_row = move.end[0] + 1 if moving_color == "white" else move.end[0] - 1
            captured_piece = self.board[capture_row][move.end[1]]
            self.board[capture_row][move.end[1]] = None

        if move.is_castling:
            if move.end[1] == 6:
                rook_start, rook_end = (move.start[0], 7), (move.start[0], 5)
            else:
                rook_start, rook_end = (move.start[0], 0), (move.start[0], 3)
            rook_piece = self.get_piece(rook_start)
            self.set_piece(rook_start, None)
            self.set_piece(rook_end, rook_piece)

        placed_piece = moving_piece
        if move.promotion is not None:
            placed_piece = f"{moving_piece[0]}{move.promotion.upper()}"
        self.set_piece(move.end, placed_piece)

        if captured_piece is not None:
            self.captured_pieces[moving_color].append(captured_piece)

        self._update_castling_rights(move, moving_piece, captured_piece)

        self.en_passant_target = None
        if piece_kind(moving_piece) == "P" and abs(move.end[0] - move.start[0]) == 2:
            self.en_passant_target = ((move.start[0] + move.end[0]) // 2, move.start[1])

        self.last_move = move
        self.turn = enemy(moving_color)

        if record_history:
            self.move_history.append(self._format_move(move, moving_piece, captured_piece))

        if update_status:
            self._refresh_status()

    def _update_castling_rights(self, move: Move, moving_piece: str, captured_piece: str | None) -> None:
        moving_color = piece_color(moving_piece)
        assert moving_color is not None
        moving_kind = piece_kind(moving_piece)
        if moving_kind == "K":
            self.castling_rights[moving_color]["king_side"] = False
            self.castling_rights[moving_color]["queen_side"] = False

        home_row = 7 if moving_color == "white" else 0
        if moving_kind == "R":
            if move.start == (home_row, 0):
                self.castling_rights[moving_color]["queen_side"] = False
            elif move.start == (home_row, 7):
                self.castling_rights[moving_color]["king_side"] = False

        if captured_piece is None or piece_kind(captured_piece) != "R":
            return

        captured_color = piece_color(captured_piece)
        assert captured_color is not None
        captured_home_row = 7 if captured_color == "white" else 0
        if move.end == (captured_home_row, 0):
            self.castling_rights[captured_color]["queen_side"] = False
        elif move.end == (captured_home_row, 7):
            self.castling_rights[captured_color]["king_side"] = False

    def _refresh_status(self) -> None:
        legal_replies = self.all_legal_moves(self.turn)
        if legal_replies:
            self.game_over = False
            self.winner = None
            self.status = f"{self.turn.capitalize()} is in check." if self.is_in_check(self.turn) else f"{self.turn.capitalize()} to move."
            return

        self.game_over = True
        if self.is_in_check(self.turn):
            self.winner = enemy(self.turn)
            self.status = f"Checkmate! {self.winner.capitalize()} wins."
        else:
            self.winner = None
            self.status = "Stalemate! The game is a draw."

    def _format_move(self, move: Move, moving_piece: str, captured_piece: str | None) -> str:
        if move.is_castling:
            return "O-O" if move.end[1] == 6 else "O-O-O"

        prefix = "" if piece_kind(moving_piece) == "P" else piece_kind(moving_piece)
        separator = "x" if captured_piece is not None else "-"
        notation = f"{prefix}{square_name(move.start)}{separator}{square_name(move.end)}"
        if move.promotion is not None:
            notation += f"={move.promotion}"
        if move.is_en_passant:
            notation += " e.p."
        return notation
