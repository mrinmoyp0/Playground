from __future__ import annotations

from pathlib import Path
from typing import Any

import streamlit.components.v1 as components


_COMPONENT_PATH = Path(__file__).parent / "components" / "chess_board"
_CHESS_BOARD = components.declare_component("offline_chess_board", path=str(_COMPONENT_PATH))

def render_chess_board(
    state: dict[str, Any],
    key: str = "offline_chess_board",
    height: int = 700,
) -> dict[str, Any] | None:
    return _CHESS_BOARD(
        board_state=state,
        height=height,
        key=key,
        default=None,
    )
