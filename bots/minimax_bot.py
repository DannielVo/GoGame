from __future__ import annotations
import math
import random
from typing import List, Tuple
from core.board import Board, Player

class HeuristicMinimaxBot:
    def __init__(self, color: Player, board_size: int = 9, depth: int | None = None):
        self.color = color

        # Depth
        if depth is not None:
            self.depth = depth
        else:
            self.depth = 2       

    # === API chính ===

    def select_move(self, board: Board, legal_moves: List[Tuple[int, int]]) -> Tuple[int, int] | None:
        if not legal_moves:
            return None

        max_player = self.color
        best_score = -math.inf
        best_moves: List[Tuple[int, int]] = []

        for (x, y) in legal_moves:
            # Tạo một bản sao để mô phỏng
            child_board = board.copy()
            success, _ = child_board.place_stone(max_player, x, y)
            if not success:
                continue

            score = self._minimax(
                child_board,
                self.depth - 1,
                maximizing=False,
                max_player=max_player,
                alpha=-math.inf,
                beta=math.inf,
            )

            if score > best_score + 1e-6:
                best_score = score
                best_moves = [(x, y)]
            elif abs(score - best_score) <= 1e-6:
                best_moves.append((x, y))

        if not best_moves:
            return None

        return random.choice(best_moves)

    # === Minimax + Alpha-Beta ===

    def _minimax(
        self,
        board: Board,
        depth: int,
        maximizing: bool,
        max_player: Player,
        alpha: float,
        beta: float,
    ) -> float:

        current_player = max_player if maximizing else max_player.opposite
        legal_moves = self._generate_legal_moves(board, current_player)

        # Dừng nếu đạt độ sâu hoặc ko còn nước đi hợp lệ
        if depth == 0 or not legal_moves:
            return self._evaluate(board, max_player)

        if maximizing:  # lượt bot
            value = -math.inf
            for (x, y) in legal_moves:
                child = board.copy()
                success, _ = child.place_stone(current_player, x, y)
                if not success:
                    continue

                value = max(
                    value,
                    self._minimax(
                        child,
                        depth - 1,
                        False,
                        max_player,
                        alpha,
                        beta,
                    ),
                )

                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value

        else:  # lượt đối thủ
            value = math.inf
            for (x, y) in legal_moves:
                child = board.copy()
                success, _ = child.place_stone(current_player, x, y)
                if not success:
                    continue

                value = min(
                    value,
                    self._minimax(
                        child,
                        depth - 1,
                        True,
                        max_player,
                        alpha,
                        beta,
                    ),
                )

                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value

    # === Sinh nước hợp lệ ===

    def _generate_legal_moves(self, board: Board, player: Player) -> List[Tuple[int, int]]:
        moves = []
        size = board.size  # 9

        for y in range(size):
            for x in range(size):
                if board.get(x, y) != 0:
                    continue

                # tránh copy nhiều => chỉ kiểm tra đơn giản
                legal = False
                for nx, ny in board._neighbors(x, y):
                    if board.get(nx, ny) == player.value:
                        legal = True
                        break

                # nếu không cạnh quân mình => vẫn có thể hợp lệ nhưng ưu tiên bỏ qua
                if not legal:
                    continue

                moves.append((x, y))

        # nếu quá ít move thì lấy thêm full board (dự phòng)
        if len(moves) < 15:
            moves = [(x, y) for y in range(size) for x in range(size) if board.get(x, y) == 0]

        # Sắp xếp ưu tiên trung tâm để bot thông minh hơn
        def center_priority(move):
            x, y = move
            return -(4 - abs(4 - x) - abs(4 - y))  

        moves.sort(key=center_priority)

        # CHỈ LẤY TỐI ĐA 20 NƯỚC
        return moves[:20]


    # === Heuristic Evaluation ===

    def _evaluate(self, board: Board, max_player: Player) -> float:
        opp = max_player.opposite
        size = board.size  # 9

        stone_diff = 0
        liberty_diff = 0
        territory_diff = 0

        for y in range(size):
            for x in range(size):
                v = board.get(x, y)

                if v == 0:
                    neighbor_colors = set()
                    for nx, ny in board._neighbors(x, y):
                        nv = board.get(nx, ny)
                        if nv != 0:
                            neighbor_colors.add(nv)

                    if len(neighbor_colors) == 1:
                        color_val = next(iter(neighbor_colors))
                        if color_val == max_player.value:
                            territory_diff += 1
                        else:
                            territory_diff -= 1

                else:
                    # stone diff
                    if v == max_player.value:
                        stone_diff += 1
                    else:
                        stone_diff -= 1

                    # local liberties
                    libs = 0
                    for nx, ny in board._neighbors(x, y):
                        if board.get(nx, ny) == 0:
                            libs += 1

                    if v == max_player.value:
                        liberty_diff += libs
                    else:
                        liberty_diff -= libs

        # Trọng số tuned cho 9×9:
        return (
            1.2 * stone_diff        # quân rất quan trọng
            + 0.7 * territory_diff  # territory mạnh hơn
            + 0.1 * liberty_diff    # local safety nhẹ
        )
