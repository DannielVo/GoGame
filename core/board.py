from __future__ import annotations

from enum import Enum
from typing import List, Tuple, Set


class Player(Enum):
    BLACK = 1
    WHITE = 2

    @property
    def opposite(self) -> "Player":
        return Player.WHITE if self is Player.BLACK else Player.BLACK

    @property
    def name_vi(self) -> str:
        return "Đen" if self is Player.BLACK else "Trắng"


class Board:
    def __init__(self, size: int):
        if size < 5:
            raise ValueError("Board size must be at least 5x5.")
        self.size = size
        # 0 = empty, 1 = black, 2 = white
        self.grid: List[List[int]] = [[0] * size for _ in range(size)]

    def copy(self) -> "Board":
        new_board = Board(self.size)
        new_board.grid = [row[:] for row in self.grid]
        return new_board

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.size and 0 <= y < self.size

    def get(self, x: int, y: int) -> int:
        return self.grid[y][x]

    def set(self, x: int, y: int, value: int) -> None:
        self.grid[y][x] = value

    def _neighbors(self, x: int, y: int) -> List[Tuple[int, int]]:
        coords: List[Tuple[int, int]] = []
        if x > 0:
            coords.append((x - 1, y))
        if x < self.size - 1:
            coords.append((x + 1, y))
        if y > 0:
            coords.append((x, y - 1))
        if y < self.size - 1:
            coords.append((x, y + 1))
        return coords

    def _group_and_liberties(
        self, x: int, y: int
    ) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        """Trả về (group, liberties) cho quân tại (x, y)."""
        color = self.get(x, y)
        if color == 0:
            return set(), set()

        visited: Set[Tuple[int, int]] = set()
        group: Set[Tuple[int, int]] = set()
        liberties: Set[Tuple[int, int]] = set()

        stack = [(x, y)]
        visited.add((x, y))

        while stack:
            cx, cy = stack.pop()
            group.add((cx, cy))
            for nx, ny in self._neighbors(cx, cy):
                v = self.get(nx, ny)
                if v == 0:
                    liberties.add((nx, ny))
                elif v == color and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    stack.append((nx, ny))

        return group, liberties

    def place_stone(self, player: Player, x: int, y: int):
        """
        Đặt quân cho `player` tại (x, y) trên bàn cờ hiện tại.

        Trả về (success, captured_positions):
        - success = False nếu:
            + vị trí ngoài biên
            + vị trí đã có quân
            + nước đi tự sát (sau khi xử lý bắt quân vẫn không còn khí)
        - Luật "ko" KHÔNG xử lý ở đây mà xử lý ở tầng GoGame
          (so sánh toàn bộ hình cờ trước/sau nước đi).
        """
        if not self.in_bounds(x, y):
            return False, []
        if self.get(x, y) != 0:
            return False, []

        # Đặt thử quân
        self.set(x, y, player.value)
        captured_total: List[Tuple[int, int]] = []

        # Kiểm tra & bắt các nhóm đối phương kề cạnh nếu hết khí
        for nx, ny in self._neighbors(x, y):
            if self.get(nx, ny) == player.opposite.value:
                group, liberties = self._group_and_liberties(nx, ny)
                if not liberties:
                    # Bắt nhóm
                    for gx, gy in group:
                        self.set(gx, gy, 0)
                    captured_total.extend(group)

        # Kiểm tra tự sát cho nhóm vừa đặt
        group, liberties = self._group_and_liberties(x, y)
        if not liberties:
            # Tự sát mà không bắt được nhóm nào -> bất hợp lệ, revert
            self.set(x, y, 0)
            # Khôi phục lại các quân đã bắt tạm
            for gx, gy in captured_total:
                self.set(gx, gy, player.opposite.value)
            return False, []

        return True, captured_total

    def is_full(self) -> bool:
        return all(v != 0 for row in self.grid for v in row)
