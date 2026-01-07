from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, List, Dict, Any, Set
from core.board import Board, Player


class GameMode(Enum):
    HUMAN_VS_HUMAN = 1
    HUMAN_VS_BOT = 2


@dataclass
class GameSnapshot:
    board: Board
    current_player: Player
    captures_black: int
    captures_white: int
    last_move: Optional[Tuple[int, int]]
    pass_streak: int  # số lượt pass liên tiếp (0,1,2...)


class GoGame:
    def __init__(self, size: int, mode: GameMode, human_color: Player = Player.BLACK):
        self.size = size
        self.mode = mode
        self.human_color = human_color
        self.bot: Optional[Any] = None

        # Lịch sử ván cờ (undo/redo & ko)
        self.history: List[GameSnapshot] = []
        self.current_index: int = 0

        # Trạng thái hiện tại
        self.board: Board = Board(size)
        self.current_player: Player = Player.BLACK
        self.captures: Dict[Player, int] = {Player.BLACK: 0, Player.WHITE: 0}
        self.last_move: Optional[Tuple[int, int]] = None
        self.is_over: bool = False
        self.pass_streak: int = 0  # 2 lượt pass liên tiếp => kết thúc
        self.komi: float = 6.5     # komi chuẩn cho Trắng (có thể chỉnh nếu muốn)

        self._create_initial_state()

    # === Khởi tạo & snapshot ===

    def _create_initial_state(self):
        board = Board(self.size)
        snapshot = GameSnapshot(
            board=board,
            current_player=Player.BLACK,
            captures_black=0,
            captures_white=0,
            last_move=None,
            pass_streak=0,
        )
        self.history = [snapshot]
        self.current_index = 0
        self._load_snapshot(snapshot)

    def _load_snapshot(self, snap: GameSnapshot):
        self.board = snap.board
        self.current_player = snap.current_player
        self.captures = {
            Player.BLACK: snap.captures_black,
            Player.WHITE: snap.captures_white,
        }
        self.last_move = snap.last_move
        self.pass_streak = snap.pass_streak
        self.is_over = self._compute_is_over()

    def _compute_is_over(self) -> bool:
        # 1 Bàn đầy
        if self.board.is_full():
            return True
        # 2) Hai lượt pass liên tiếp
        if self.pass_streak >= 2:
            return True
        # 3) (Bổ sung) cả 2 bên không còn nước hợp lệ nào
        if (
            not self.get_legal_moves(self.current_player)
            and not self.get_legal_moves(self.current_player.opposite)
        ):
            return True
        return False

    def reset(self):
        self._create_initial_state()

    def set_bot(self, bot: Any):
        self.bot = bot

    # === Truy vấn cơ bản ===

    def is_human_turn(self) -> bool:
        if self.mode == GameMode.HUMAN_VS_HUMAN:
            return True
        return self.current_player == self.human_color

    def get_captures(self, player: Player) -> int:
        return self.captures[player]

    # === Hợp lệ nước đi (bao gồm Ko) ===

    def get_legal_moves(self, player: Player) -> List[Tuple[int, int]]:
        """Tính các nước đi hợp lệ cho `player` tại trạng thái hiện tại (bao gồm Ko)."""
        moves: List[Tuple[int, int]] = []
        size = self.board.size

        # trạng thái "2 nước trước" để check Ko đơn (simple ko):
        # cấm tạo lại hình cờ giống hệt vị trí chỉ một nước trước đó.
        prev_board_grid = None
        if self.current_index >= 1:
            prev_board_grid = self.history[self.current_index - 1].board.grid

        for y in range(size):
            for x in range(size):
                if self.board.get(x, y) != 0:
                    continue

                temp = self.board.copy()
                success, _ = temp.place_stone(player, x, y)
                if not success:
                    continue

                # Ko: cấm để bàn cờ sau khi đặt quân trùng với bàn ở "một nước trước đó"
                if prev_board_grid is not None and temp.grid == prev_board_grid:
                    continue

                moves.append((x, y))

        return moves

    # === Áp dụng nước đi (đặt quân) ===

    def _apply_move(self, player: Player, x: int, y: int) -> bool:
        if self.is_over or player is not self.current_player:
            return False

        # Tạo bản sao bàn cờ và thử đặt quân (check biên, trùng, tự sát, bắt quân)
        temp_board = self.board.copy()
        success, captured = temp_board.place_stone(player, x, y)
        if not success:
            return False

        # Ko: cấm lặp lại hình cờ cách 1 nước
        if self.current_index >= 1:
            prev_board = self.history[self.current_index - 1].board
            if temp_board.grid == prev_board.grid:
                # vi phạm ko, không chấp nhận nước đi
                return False

        # Cập nhật số quân bắt được
        new_captures = dict(self.captures)
        new_captures[player] += len(captured)
        next_player = player.opposite

        snapshot = GameSnapshot(
            board=temp_board,
            current_player=next_player,
            captures_black=new_captures[Player.BLACK],
            captures_white=new_captures[Player.WHITE],
            last_move=(x, y),
            pass_streak=0,  # đặt quân -> reset chuỗi pass
        )

        # Cắt bỏ nhánh redo nếu có, rồi append snapshot mới
        self.history = self.history[: self.current_index + 1]
        self.history.append(snapshot)
        self.current_index += 1
        self._load_snapshot(snapshot)

        return True

    # === Nước đi của người chơi ===

    def play_human_move(self, x: int, y: int) -> bool:
        if not self.is_human_turn() or self.is_over:
            return False

        moved = self._apply_move(self.current_player, x, y)
        if not moved:
            return False

        # Nếu chế độ vs bot -> cho bot đi tiếp
        if self.mode == GameMode.HUMAN_VS_BOT:
            self._play_bot_turn()
        return True

    # === Nước đi của bot ===

    def _play_bot_turn(self):
        if self.mode != GameMode.HUMAN_VS_BOT or self.bot is None or self.is_over:
            return
        if self.is_human_turn():
            # vẫn là lượt người (ví dụ sau undo)
            return

        legal = self.get_legal_moves(self.current_player)
        if not legal:
            # Bot không có nước hợp lệ -> pass
            self.pass_turn()
            return

        move = self.bot.select_move(self.board.copy(), legal)
        if move is None:
            # Bot quyết định pass
            self.pass_turn()
            return

        x, y = move
        self._apply_move(self.current_player, x, y)

    # === Pass & resign ===

    def pass_turn(self) -> bool:
        """Người chơi hiện tại bỏ lượt (pass). Hai lượt pass liên tiếp => kết thúc ván."""
        if self.is_over:
            return False

        # Tăng chuỗi pass
        new_pass_streak = self.pass_streak + 1
        next_player = self.current_player.opposite

        board_copy = self.board.copy()
        snapshot = GameSnapshot(
            board=board_copy,
            current_player=next_player,
            captures_black=self.captures[Player.BLACK],
            captures_white=self.captures[Player.WHITE],
            last_move=None,
            pass_streak=new_pass_streak,
        )

        self.history = self.history[: self.current_index + 1]
        self.history.append(snapshot)
        self.current_index += 1
        self._load_snapshot(snapshot)

        return True

    def resign(self, loser: Optional[Player] = None):
        """
        Đầu hàng (resign). Ở đây ta chỉ đánh dấu ván cờ đã kết thúc.
        Việc hiển thị người thắng/thua có thể xử lý ở UI (dựa vào `loser`).
        """
        if loser is None:
            loser = self.current_player
        # Không cần snapshot mới, chỉ đánh dấu kết thúc.
        self.is_over = True
        # Có thể sau này bổ sung thêm thuộc tính self.winner nếu cần.

    # === Undo / Redo ===

    def can_undo(self) -> bool:
        return self.current_index > 0

    def can_redo(self) -> bool:
        return self.current_index < len(self.history) - 1

    def undo(self):
        if not self.can_undo():
            return
        self.current_index -= 1
        snap = self.history[self.current_index]
        self._load_snapshot(snap)

    def redo(self):
        if not self.can_redo():
            return
        self.current_index += 1
        snap = self.history[self.current_index]
        self._load_snapshot(snap)

    # === Tính điểm ===

    def _territory(self) -> Dict[Player, int]:
        """
        Đếm lãnh thổ trống bao vây bởi một bên.
        - Là vùng trống kề cạnh với cả Đen & Trắng => không ai sở hữu.
        - Không xử lý seki / nhóm chết phức tạp.
        """
        size = self.board.size
        visited: Set[Tuple[int, int]] = set()
        territory: Dict[Player, int] = {Player.BLACK: 0, Player.WHITE: 0}

        for y in range(size):
            for x in range(size):
                if (x, y) in visited:
                    continue
                if self.board.get(x, y) != 0:
                    continue

                # BFS một vùng trống
                region: Set[Tuple[int, int]] = set()
                border_colors: Set[int] = set()
                stack = [(x, y)]
                visited.add((x, y))
                region.add((x, y))

                while stack:
                    cx, cy = stack.pop()
                    for nx, ny in self.board._neighbors(cx, cy):
                        v = self.board.get(nx, ny)
                        if v == 0:
                            if (nx, ny) not in visited:
                                visited.add((nx, ny))
                                region.add((nx, ny))
                                stack.append((nx, ny))
                        else:
                            border_colors.add(v)

                if len(border_colors) == 1:
                    color_val = border_colors.pop()
                    owner = Player.BLACK if color_val == Player.BLACK.value else Player.WHITE
                    territory[owner] += len(region)

        return territory

    def score(self, komi: Optional[float] = None) -> Tuple[float, float]:
        """
        Tính điểm (Black_score, White_score):
        score = lãnh_thổ + quân_đối_phương_bị_bắt (+ komi cho Trắng).

        - `komi`: nếu truyền vào sẽ override self.komi
        """
        k = self.komi if komi is None else komi
        territory = self._territory()
        black_territory = territory[Player.BLACK]
        white_territory = territory[Player.WHITE]

        black_score = black_territory + self.captures[Player.BLACK]
        white_score = white_territory + self.captures[Player.WHITE] + k
        return float(black_score), float(white_score)
