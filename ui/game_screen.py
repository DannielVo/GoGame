from __future__ import annotations
from bots.minimax_bot import HeuristicMinimaxBot
import os
import pygame
from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    BG_COLOR,
    WOOD_COLOR,
    BOARD_BORDER_COLOR,
    PANEL_BG,       # vẫn import nếu dùng nơi khác
    PANEL_BORDER,   # vẫn import nếu dùng nơi khác
    TEXT_COLOR,
    TEXT_MUTED,
    BLACK_STONE,
    WHITE_STONE,
    STONE_OUTLINE,
    LAST_MOVE_HIGHLIGHT,
)
from core.board import Player
from core.game import GoGame, GameMode
from ui.widgets import Button
# from bots.random_bot import RandomBot

LETTERS = "ABCDEFGHJKLMNOPQRST"  # standard Go coordinates (skip I)

BOARD_IMG_SIZE = 1000
BOARD_MARGIN = 90
BOARD_MARGIN_FRAC = BOARD_MARGIN / BOARD_IMG_SIZE      
BOARD_INNER_FRAC = 1.0 - 2 * BOARD_MARGIN_FRAC         


class GameScreen:
    def __init__(
        self,
        app: "GoApp",
        board_size: int,
        mode: GameMode,
        board_style: str = "wood",  # "wood" | "stone"
        human_color: Player = Player.BLACK,
    ):
        self.app = app
        # truyền human_color xuống GoGame
        self.game = GoGame(board_size, mode, human_color=human_color)

        if mode == GameMode.HUMAN_VS_BOT:
            # bot luôn chơi màu ngược lại với người
            bot_color = Player.WHITE if human_color == Player.BLACK else Player.BLACK
            bot = HeuristicMinimaxBot(
                color=bot_color,
                board_size=board_size,
                # depth=3  # nếu muốn override lại
            )
            self.game.set_bot(bot)

            if not self.game.is_human_turn():
                self.game._play_bot_turn()


        # khu vực vẽ bàn & panel bên phải
        self.board_rect = pygame.Rect(60, 40, 720, 720)
        self.side_rect = pygame.Rect(840, 40, WINDOW_WIDTH - 840 - 40, 720)

        # style & surface bàn
        self.board_style = board_style
        self.board_surface: pygame.Surface | None = None
        self.use_image_board: bool = False
        self._load_board_image(board_size, board_style)

        # hover coord trên panel (A1, D4, ...)
        self.hover_coord: tuple[int, int] | None = None

        # âm thanh cho nước đi & chiến thắng
        self.move_sound: pygame.mixer.Sound | None = None
        self.victory_sound: pygame.mixer.Sound | None = None
        self._load_sounds()

        # fonts in đậm riêng cho panel
        self.font_panel_body = pygame.font.SysFont("segoeui", 22, bold=True)
        self.font_panel_big = pygame.font.SysFont("segoeui", 32, bold=True)

        # để detect lúc game vừa chuyển sang is_over
        self._prev_is_over: bool = self.game.is_over

        # kết quả cuối ván (điểm + winner)
        self.final_scores: tuple[float, float] | None = None  # (black, white)
        self.winner_text: str | None = None                   # vd: "Black wins by 2.5"
        self.winner_card_rect: pygame.Rect | None = None      # vùng card overlay để detect click

        self._build_ui()

    # ============ LOAD BOARD IMAGE ============

    def _load_board_image(self, board_size: int, style: str):
        """
        Load PNG dạng:
            assets/board_{style}_{size}x{size}.png
        Nếu load được -> dùng image làm nền; nếu không -> fallback vẽ gỗ như cũ.
        """
        base_dir = os.path.dirname(os.path.dirname(__file__))
        assets_dir = os.path.join(base_dir, "assets")
        filename = f"board_{style}_{board_size}x{board_size}.png"
        path = os.path.join(assets_dir, filename)

        try:
            raw = pygame.image.load(path).convert_alpha()
            self.board_surface = pygame.transform.smoothscale(
                raw,
                (self.board_rect.width, self.board_rect.height),
            )
            self.use_image_board = True
            print(f"[GameScreen] Loaded board skin: {filename}")
        except Exception as e:
            print(f"[GameScreen] Không thể load {filename}, dùng board default. Lỗi: {e}")
            self.board_surface = None
            self.use_image_board = False

    # ============ LOAD SOUNDS ============

    def _load_sounds(self):
        """Load click2.mp3 (đặt quân) và victory.mp3 (thắng cuộc)."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        assets_dir = os.path.join(base_dir, "assets")
        click2_path = os.path.join(assets_dir, "click2.mp3")
        victory_path = os.path.join(assets_dir, "victory.mp3")

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            if os.path.exists(click2_path):
                self.move_sound = pygame.mixer.Sound(click2_path)
                self.move_sound.set_volume(0.8)
            else:
                print("[GameScreen] Không tìm thấy click2.mp3")

            if os.path.exists(victory_path):
                self.victory_sound = pygame.mixer.Sound(victory_path)
                self.victory_sound.set_volume(0.9)
            else:
                print("[GameScreen] Không tìm thấy victory.mp3")
        except Exception as e:
            print("[GameScreen] Không thể load hiệu ứng âm thanh:", e)
            self.move_sound = None
            self.victory_sound = None

    # ============ UI ============

    def _build_ui(self):
        btn_h = 50
        spacing_y = 16
        spacing_x = 20
        margin_bottom = 40

        total_inner_w = self.side_rect.width - 80
        x_left = self.side_rect.left + 40

        # Back ở hàng dưới, sát bottom
        back_y = self.side_rect.bottom - margin_bottom - btn_h
        btn_w = (total_inner_w - spacing_x) // 2

        # 2 hàng nút phía trên Back:
        # row2: Pass / Resign
        # row1: Undo / Redo
        row2_y = back_y - spacing_y - btn_h
        row1_y = row2_y - spacing_y - btn_h

        base_btn = (235, 239, 255)
        hover_btn = (210, 220, 255)
        text_btn = (20, 22, 30)

        # Undo / Redo (hàng trên)
        self.undo_button = Button(
            rect=(x_left, row1_y, btn_w, btn_h),
            text="Undo",
            font=self.app.font_body,
            callback=self._on_undo,
            base_color=base_btn,
            hover_color=hover_btn,
            text_color=text_btn,
        )
        self.redo_button = Button(
            rect=(x_left + btn_w + spacing_x, row1_y, btn_w, btn_h),
            text="Redo",
            font=self.app.font_body,
            callback=self._on_redo,
            base_color=base_btn,
            hover_color=hover_btn,
            text_color=text_btn,
        )

        # Pass / Resign (hàng giữa)
        self.pass_button = Button(
            rect=(x_left, row2_y, btn_w, btn_h),
            text="Pass",
            font=self.app.font_body,
            callback=self._on_pass,
            base_color=(230, 244, 255),
            hover_color=(205, 232, 255),
            text_color=text_btn,
        )
        self.resign_button = Button(
            rect=(x_left + btn_w + spacing_x, row2_y, btn_w, btn_h),
            text="Resign",
            font=self.app.font_body,
            callback=self._on_resign,
            base_color=(255, 225, 225),
            hover_color=(255, 205, 205),
            text_color=(120, 20, 20),
        )

        # Back (hàng dưới, full width)
        self.back_button = Button(
            rect=(x_left, back_y, total_inner_w, btn_h),
            text="Back",
            font=self.app.font_body,
            callback=self._on_back,
            base_color=(250, 230, 210),
            hover_color=(255, 210, 160),
            text_color=text_btn,
        )

        # Nút RETURN khi game kết thúc (ẩn cho đến khi game over)
        btn_w = 160
        btn_h = 44
        btn_x = (WINDOW_WIDTH - btn_w) // 2
        btn_y = (WINDOW_HEIGHT // 2) + 90   # dưới khung card

        self.winner_back_button = Button(
            rect=(btn_x, btn_y, btn_w, btn_h),
            text="Back to Menu",
            font=self.font_panel_body,
            callback=self._on_back,
            base_color=(250, 230, 210),
            hover_color=(245, 245, 255),
            text_color=text_btn,
        )


    # === Event & update ===

    def handle_event(self, event: pygame.event.Event):
        # Nếu game đã kết thúc và có kết quả -> chỉ xử lý click lên card overlay
        if self.game.is_over and self.final_scores is not None:
            if self.winner_back_button:
                self.winner_back_button.handle_event(event)
            return


        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.board_rect.collidepoint(event.pos):
                self._handle_board_click(event.pos)

        # phím tắt: P = Pass, R = Resign
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self._on_pass()
            elif event.key == pygame.K_r:
                self._on_resign()

        # Buttons
        self.undo_button.handle_event(event)
        self.redo_button.handle_event(event)
        self.pass_button.handle_event(event)
        self.resign_button.handle_event(event)
        self.back_button.handle_event(event)

    def update(self, dt: float):
        # cập nhật ô đang hover (toạ độ) để hiển thị bên panel
        mx, my = pygame.mouse.get_pos()
        if self.board_rect.collidepoint((mx, my)):
            self.hover_coord = self._pixel_to_coord((mx, my))
        else:
            self.hover_coord = None

        # detect game vừa kết thúc -> phát nhạc victory + tính điểm 1 lần
        if self.game.is_over and not self._prev_is_over:
            if self.victory_sound is not None:
                self.victory_sound.play()

            black_score, white_score = self.game.score()
            self.final_scores = (black_score, white_score)

            diff = round(black_score - white_score, 1)

            # nếu chưa có winner_text (từ resign) thì mới generate theo điểm
            if self.winner_text is None:
                if abs(diff) < 1e-3:
                    self.winner_text = "Result: Draw"
                elif diff > 0:
                    self.winner_text = f"Black wins by {diff:.1f}"
                else:
                    self.winner_text = f"White wins by {abs(diff):.1f}"

        # nếu undo từ trạng thái game over về trạng thái đang chơi -> clear kết quả
        if not self.game.is_over and self._prev_is_over:
            self.final_scores = None
            self.winner_text = None
            self.winner_card_rect = None

        self._prev_is_over = self.game.is_over

        # update nút để hiệu ứng hover mượt
        self.undo_button.update(dt)
        self.redo_button.update(dt)
        self.pass_button.update(dt)
        self.resign_button.update(dt)

        if self.game.is_over:
            self.winner_back_button.update(dt)


    # === GRID GEOMETRY ===

    def _get_grid_geometry(self) -> tuple[float, float, float]:
        """
        Trả về (grid_left, grid_top, cell_size).
        """
        size = self.game.board.size
        if size <= 1:
            return self.board_rect.left, self.board_rect.top, 0.0

        if self.use_image_board:
            grid_size = self.board_rect.width * BOARD_INNER_FRAC
            grid_left = self.board_rect.left + self.board_rect.width * BOARD_MARGIN_FRAC
            grid_top = self.board_rect.top + self.board_rect.height * BOARD_MARGIN_FRAC
        else:
            grid_size = self.board_rect.width
            grid_left = self.board_rect.left
            grid_top = self.board_rect.top

        cell = grid_size / (size - 1)
        return grid_left, grid_top, cell

    # === Conversion helpers ===

    def _coord_to_pixel(self, x: int, y: int) -> tuple[int, int]:
        size = self.game.board.size
        if size <= 1:
            return self.board_rect.center

        grid_left, grid_top, cell = self._get_grid_geometry()
        px = grid_left + x * cell
        py = grid_top + y * cell
        return int(round(px)), int(round(py))

    def _pixel_to_coord(self, pos) -> tuple[int, int] | None:
        px, py = pos
        size = self.game.board.size
        if size <= 1:
            return None

        grid_left, grid_top, cell = self._get_grid_geometry()
        if cell <= 0:
            return None

        grid_size = cell * (size - 1)

        # Chỉ nhận trong vùng lưới (khoảng +/-0.5 ô để dễ click biên)
        if not (
            grid_left - cell * 0.5 <= px <= grid_left + grid_size + cell * 0.5
            and grid_top - cell * 0.5 <= py <= grid_top + grid_size + cell * 0.5
        ):
            return None

        rel_x = (px - grid_left) / cell
        rel_y = (py - grid_top) / cell
        x = int(round(rel_x))
        y = int(round(rel_y))
        if 0 <= x < size and 0 <= y < size:
            return x, y
        return None

    # === Button callbacks ===

    def _on_undo(self):
        self.game.undo()

    def _on_redo(self):
        self.game.redo()

    def _on_back(self):
        self.app.change_screen("home")

    def _on_pass(self):
        """Người chơi hiện tại bỏ lượt (Pass)."""
        if self.game.is_over:
            return
        if not self.game.is_human_turn():
            return

        moved = self.game.pass_turn()
        if not moved:
            return

        # nếu là Human vs Bot và sau pass đến lượt bot -> cho bot đi luôn
        if (
            self.game.mode == GameMode.HUMAN_VS_BOT
            and not self.game.is_over
            and not self.game.is_human_turn()
        ):
            self.game._play_bot_turn()

    def _on_resign(self):
        """Người chơi đầu hàng (Resign)."""
        if self.game.is_over:
            return

        # trong Human vs Bot, luôn cho human là người resign
        if self.game.mode == GameMode.HUMAN_VS_BOT:
            loser = self.game.human_color
        else:
            loser = self.game.current_player

        self.game.resign(loser)

        winner = loser.opposite
        loser_name = "Black" if loser == Player.BLACK else "White"
        winner_name = "Black" if winner == Player.BLACK else "White"
        # đặt winner_text sẵn; update() sẽ không override nữa
        self.winner_text = f"{winner_name} wins ({loser_name} resigns)"

    # === Board click logic ===

    def _handle_board_click(self, pos):
        if self.game.is_over:
            return
        if not self.game.is_human_turn():
            return

        coord = self._pixel_to_coord(pos)
        if coord is None:
            return

        x, y = coord
        prev_last_move = self.game.last_move

        # chơi nước đi
        self.game.play_human_move(x, y)

        # nếu last_move thay đổi -> nước đi hợp lệ -> phát âm thanh click
        if self.game.last_move != prev_last_move and self.move_sound is not None:
            self.move_sound.play()

    # === helper: vẽ quân cờ với shading + highlight để dễ nhìn hơn ===
    def _draw_stone(
        self,
        surface: pygame.Surface,
        center: tuple[int, int],
        radius: int,
        player: Player,
        alpha: int = 255,
    ):
        if radius <= 0:
            return

        size = radius * 2 + 6
        stone_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = size // 2
        cy = size // 2

        if player == Player.BLACK:
            base = BLACK_STONE
            r, g, b = base[:3]
            base_col = (max(r, 16), max(g, 18), max(b, 26))
            inner_col = (min(r + 45, 255), min(g + 45, 255), min(b + 70, 255))
            outline_col = (200, 210, 245)
            glow_col = (120, 135, 190, 90)
        else:
            base = WHITE_STONE
            r, g, b = base[:3]
            base_col = (max(r, 230), max(g, 230), max(b, 235))
            inner_col = (255, 255, 255)
            outline_col = (170, 185, 230)
            glow_col = (255, 255, 255, 80)

        # halo nhẹ quanh quân cờ
        pygame.draw.circle(stone_surf, glow_col, (cx, cy), radius + 2)

        # thân + vùng trung tâm sáng hơn
        pygame.draw.circle(stone_surf, base_col, (cx, cy), radius)
        pygame.draw.circle(stone_surf, inner_col, (cx, cy), int(radius * 0.65))

        # highlight góc trên trái
        hl_r = max(2, radius // 4)
        offset = int(radius * 0.45)
        hl_center = (cx - offset, cy - offset)
        pygame.draw.circle(stone_surf, (255, 255, 255, 170), hl_center, hl_r)

        # viền
        pygame.draw.circle(stone_surf, outline_col, (cx, cy), radius, 2)

        # áp dụng alpha tổng thể (cho ghost stone)
        stone_surf.set_alpha(alpha)

        surface.blit(stone_surf, (center[0] - cx, center[1] - cy))

    # === Drawing ===

    def draw(self, surface: pygame.Surface):
        surface.fill(BG_COLOR)
        self._draw_board(surface)
        self._draw_side_panel(surface)
        self._draw_winner_overlay(surface)

    def _draw_board(self, surface: pygame.Surface):
        size = self.game.board.size

        # --- nền board ---
        if self.use_image_board and self.board_surface:
            # board img đã có lưới + tọa độ
            surface.blit(self.board_surface, self.board_rect)
        else:
            # fallback: vẽ gỗ + lưới như cũ
            pygame.draw.rect(surface, WOOD_COLOR, self.board_rect, border_radius=18)
            pygame.draw.rect(
                surface,
                BOARD_BORDER_COLOR,
                self.board_rect,
                width=3,
                border_radius=18,
            )

            if size > 1:
                grid_left, grid_top, cell = self._get_grid_geometry()
                grid_size = cell * (size - 1)

                # grid lines
                for i in range(size):
                    # vertical
                    x = grid_left + i * cell
                    y_start = grid_top
                    y_end = grid_top + grid_size
                    width = 2 if i == 0 or i == size - 1 else 1
                    pygame.draw.line(
                        surface, BOARD_BORDER_COLOR, (x, y_start), (x, y_end), width
                    )

                    # horizontal
                    y = grid_top + i * cell
                    x_start = grid_left
                    x_end = grid_left + grid_size
                    width = 2 if i == 0 or i == size - 1 else 1
                    pygame.draw.line(
                        surface, BOARD_BORDER_COLOR, (x_start, y), (x_end, y), width
                    )

                # star points chỉ cần khi tự vẽ lưới
                self._draw_star_points(surface)

        if size <= 1:
            return

        _, _, cell = self._get_grid_geometry()
        if cell <= 0:
            return

        # === stones thật ===
        for y in range(size):
            for x in range(size):
                v = self.game.board.get(x, y)
                if v == 0:
                    continue
                center = self._coord_to_pixel(x, y)
                radius = int(cell * 0.42)
                player = Player.BLACK if v == Player.BLACK.value else Player.WHITE
                self._draw_stone(surface, center, radius, player, alpha=255)

        # === ghost stone (preview nước đi) ===
        ghost_coord = None
        if (
            not self.game.is_over
            and self.game.is_human_turn()
            and self.hover_coord is not None
        ):
            gx, gy = self.hover_coord
            if 0 <= gx < size and 0 <= gy < size:
                if self.game.board.get(gx, gy) == 0:
                    ghost_coord = (gx, gy)

        if ghost_coord is not None:
            gx, gy = ghost_coord
            center = self._coord_to_pixel(gx, gy)
            radius = int(cell * 0.42)
            self._draw_stone(
                surface, center, radius, self.game.current_player, alpha=130
            )

        # === last move marker ===
        if self.game.last_move is not None and cell > 0:
            lx, ly = self.game.last_move
            center = self._coord_to_pixel(lx, ly)
            pygame.draw.circle(
                surface, LAST_MOVE_HIGHLIGHT, center, int(cell * 0.5), 2
            )

        # coordinates: chỉ vẽ khi KHÔNG dùng image board (PNG đã có sẵn)
        if not self.use_image_board:
            self._draw_coordinates(surface, cell)

    def _draw_star_points(self, surface: pygame.Surface):
        size = self.game.board.size
        if size == 9:
            points = [(2, 2), (6, 2), (2, 6), (6, 6), (4, 4)]
        elif size == 13:
            points = [(3, 3), (9, 3), (3, 9), (9, 9), (6, 6)]
        elif size == 17:
            points = [
                (3, 3), (8, 3), (13, 3),
                (3, 8), (8, 8), (13, 8),
                (3, 13), (8, 13), (13, 13),
            ]
        elif size == 19:
            points = [
                (3, 3), (9, 3), (15, 3),
                (3, 9), (9, 9), (15, 9),
                (3, 15), (9, 15), (15, 15),
            ]
        else:
            return

        for x, y in points:
            cx, cy = self._coord_to_pixel(x, y)
            pygame.draw.circle(surface, BOARD_BORDER_COLOR, (cx, cy), 4)

    def _draw_coordinates(self, surface: pygame.Surface, cell: float):
        size = self.game.board.size
        font = self.app.font_small

        letters = LETTERS[:size]

        # bottom letters
        for x in range(size):
            label = letters[x]
            px, py = self._coord_to_pixel(x, size - 1)
            text_surf = font.render(label, True, TEXT_MUTED)
            text_rect = text_surf.get_rect(center=(px, self.board_rect.bottom + 12))
            surface.blit(text_surf, text_rect)

        # left numbers
        for y in range(size):
            label = str(size - y)
            px, py = self._coord_to_pixel(0, y)
            text_surf = font.render(label, True, TEXT_MUTED)
            text_rect = text_surf.get_rect(center=(self.board_rect.left - 18, py))
            surface.blit(text_surf, text_rect)

    # === helper: chuyển (x, y) -> "D4" ===
    def _coord_label(self, x: int, y: int) -> str:
        size = self.game.board.size
        if size <= 0:
            return "--"
        if not (0 <= x < size and 0 <= y < size):
            return "--"
        letters = LETTERS[:size]
        col = letters[x]
        row = size - y
        return f"{col}{row}"

    def _draw_winner_overlay(self, surface: pygame.Surface):
        """Hiển thị kết quả cuối ván ở giữa màn hình (overlay mờ)."""
        if not (self.game.is_over and self.final_scores is not None):
            self.winner_card_rect = None
            return

        black_score, white_score = self.final_scores
        main_text = self.winner_text or "Game Over"

        # tạo overlay full màn hình
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))  # nền đen mờ

        # card ở giữa
        card_w, card_h = 520, 170
        card_rect = pygame.Rect(
            (WINDOW_WIDTH - card_w) // 2,
            (WINDOW_HEIGHT - card_h) // 2,
            card_w,
            card_h,
        )

        card_bg   = (250, 250, 252, 255)
        border_col = (210, 215, 230, 255)

        pygame.draw.rect(overlay, card_bg, card_rect, border_radius=24)
        pygame.draw.rect(overlay, border_col, card_rect, width=2, border_radius=24)

        # text
        font_title = self.font_panel_big          # to, đậm
        font_body  = self.font_panel_body         # nhỏ hơn, đậm

        main_color  = (20, 22, 30)
        accent_color = (180, 70, 60)
        muted_color = (110, 120, 145)

        # dòng winner (main_text)
        title_surf = font_title.render(main_text, True, accent_color)
        title_rect = title_surf.get_rect(midtop=(card_rect.centerx, card_rect.top + 18))
        overlay.blit(title_surf, title_rect)

        # dòng score: Black xx.x – yy.y White
        score_text = f"Black {black_score:.1f} – {white_score:.1f} White"
        score_surf = font_body.render(score_text, True, main_color)
        score_rect = score_surf.get_rect(
            midtop=(card_rect.centerx, title_rect.bottom + 14)
        )
        overlay.blit(score_surf, score_rect)

        # komi
        komi_text = f"Komi: {self.game.komi:.1f} for White"
        komi_surf = font_body.render(komi_text, True, muted_color)
        komi_rect = komi_surf.get_rect(
            midtop=(card_rect.centerx, score_rect.bottom + 8)
        )
        overlay.blit(komi_surf, komi_rect)

        # không còn hint "Press BACK to return"

        # lưu rect để handle click trong handle_event
        self.winner_card_rect = card_rect.copy()

        # VẼ NÚT RETURN
        if self.game.is_over:
            self.winner_back_button.draw(overlay)

        # blit overlay lên màn hình
        surface.blit(overlay, (0, 0))


    def _draw_side_panel(self, surface: pygame.Surface):
        # ===== PANEL: nền trắng, card kiểu sáng =====
        panel_surf = pygame.Surface(self.side_rect.size, pygame.SRCALPHA)
        w, h = self.side_rect.size

        panel_bg   = (250, 250, 252)   # nền chính gần như trắng
        border_col = (210, 215, 230)   # viền xám nhạt
        header_bg  = (242, 245, 252)   # thanh top hơi xám
        inner_bg   = (238, 241, 248)   # vùng nội dung xám hơn chút

        # card ngoài
        pygame.draw.rect(panel_surf, panel_bg, (0, 0, w, h), border_radius=24)
        pygame.draw.rect(panel_surf, border_col, (0, 0, w, h), width=2, border_radius=24)

        # dải header trên cùng
        top_rect = pygame.Rect(4, 4, w - 8, 70)
        pygame.draw.rect(panel_surf, header_bg, top_rect, border_radius=18)

        # vùng nội dung
        inner_rect = pygame.Rect(10, 80, w - 20, h - 170)
        pygame.draw.rect(panel_surf, inner_bg, inner_rect, border_radius=18)
        pygame.draw.rect(panel_surf, border_col, inner_rect, width=1, border_radius=18)

        # blit panel ra màn hình
        surface.blit(panel_surf, self.side_rect.topleft)

        # ===== TEXT & MÀU CHỮ (tất cả in đậm) =====
        font_body  = self.font_panel_body
        font_hover = self.font_panel_big

        main_text  = (20, 22, 30)      # chữ chính: đen đậm
        muted_text = (110, 120, 145)   # chữ phụ: xám đậm

        # ---- Title "Go" ----
        title_surf = self.app.font_h1.render("Go", True, main_text)
        title_rect = title_surf.get_rect(
            midtop=(self.side_rect.centerx, self.side_rect.top + 18)
        )
        surface.blit(title_surf, title_rect)

        left  = self.side_rect.left + 26
        right = self.side_rect.right - 26
        y     = inner_rect.top + self.side_rect.top + 18

        # ---- Mode + thông tin màu quân ----
        mode_str = (
            "Player vs Player"
            if self.game.mode == GameMode.HUMAN_VS_HUMAN
            else "Player vs AI"
        )
        mode_surf = font_body.render(mode_str, True, main_text)
        mode_rect = mode_surf.get_rect(left=left, top=y)
        surface.blit(mode_surf, mode_rect)
        y = mode_rect.bottom + 6

        # Nếu là vs AI thì show thêm "You: Black / White"
        if self.game.mode == GameMode.HUMAN_VS_BOT:
            human = self.game.human_color
            bot_color = human.opposite

            you_str = f"You: {'Black' if human == Player.BLACK else 'White'}"
            ai_str  = f"AI:   {'Black' if bot_color == Player.BLACK else 'White'}"

            you_surf = font_body.render(you_str, True, main_text)
            you_rect = you_surf.get_rect(left=left, top=y)
            surface.blit(you_surf, you_rect)

            ai_surf = font_body.render(ai_str, True, muted_text)
            ai_rect = ai_surf.get_rect(left=left + 160, top=y)
            surface.blit(ai_surf, ai_rect)

            y = max(you_rect.bottom, ai_rect.bottom) + 10
        else:
            y = mode_rect.bottom + 10

        # separator
        pygame.draw.line(surface, border_col, (left, y), (right, y), 1)
        y += 18

        # ---- Turn: chỉ hiển thị quân cờ lớn ----
        turn_title = font_body.render("Turn", True, muted_text)
        turn_title_rect = turn_title.get_rect(left=left, top=y)
        surface.blit(turn_title, turn_title_rect)

        current_player = self.game.current_player
        flag_radius = 22
        flag_center = (self.side_rect.centerx, turn_title_rect.bottom + 28)
        self._draw_stone(surface, flag_center, flag_radius, current_player, alpha=255)

        y = flag_center[1] + flag_radius + 18

        # ---- Captures ----
        cap_title = font_body.render("Captures", True, muted_text)
        cap_title_rect = cap_title.get_rect(left=left, top=y)
        surface.blit(cap_title, cap_title_rect)
        y = cap_title_rect.bottom + 8

        cap_black = self.game.get_captures(Player.BLACK)
        cap_white = self.game.get_captures(Player.WHITE)

        stone_r_small = 9

        # dòng Đen
        black_center = (left + stone_r_small, y + stone_r_small)
        self._draw_stone(surface, black_center, stone_r_small, Player.BLACK, alpha=255)
        txt_black = font_body.render(f"x {cap_black}", True, main_text)
        rect_black = txt_black.get_rect(left=left + 26, centery=black_center[1])
        surface.blit(txt_black, rect_black)

        # dòng Trắng
        y = rect_black.bottom + 6
        white_center = (left + stone_r_small, y + stone_r_small)
        self._draw_stone(surface, white_center, stone_r_small, Player.WHITE, alpha=255)
        txt_white = font_body.render(f"x {cap_white}", True, main_text)
        rect_white = txt_white.get_rect(left=left + 26, centery=white_center[1])
        surface.blit(txt_white, rect_white)

        y = rect_white.bottom + 14

        # separator
        pygame.draw.line(surface, border_col, (left, y), (right, y), 1)
        y += 18

        # ---- Hover coord (label + value trên cùng một hàng) ----
        if self.hover_coord is not None:
            hx, hy = self.hover_coord
            hover_label = self._coord_label(hx, hy)
        else:
            hover_label = "--"

        hover_title_surf = font_body.render("Hover:", True, muted_text)
        hover_value_surf = font_hover.render(hover_label, True, (10, 12, 20))

        hover_title_rect = hover_title_surf.get_rect(left=left, top=y)
        surface.blit(hover_title_surf, hover_title_rect)

        # giá trị toạ độ nằm cùng hàng, lệch phải một chút
        hover_value_rect = hover_value_surf.get_rect(
            left=hover_title_rect.right + 12,
            centery=hover_title_rect.centery + 1  # chỉnh nhẹ cho cân
        )
        surface.blit(hover_value_surf, hover_value_rect)

        y = max(hover_title_rect.bottom, hover_value_rect.bottom) + 10

        # ---- Last move (label + value trên cùng một hàng, không bị nút che) ----
        if self.game.last_move is not None:
            lx, ly = self.game.last_move
            last_label = self._coord_label(lx, ly)
        else:
            last_label = "--"

        last_title_surf = font_body.render("Last move:", True, muted_text)
        last_value_surf = font_hover.render(last_label, True, main_text)

        last_title_rect = last_title_surf.get_rect(left=left, top=y)
        last_value_rect = last_value_surf.get_rect(
            left=last_title_rect.right + 8,
            centery=last_title_rect.centery,
        )

        # Đảm bảo dòng "Last move" không bị các nút che
        buttons_top = min(
            self.undo_button.rect.top,
            self.pass_button.rect.top,
            self.back_button.rect.top,
        )
        margin = 8  # khoảng cách tối thiểu giữa chữ và hàng nút

        last_row_bottom = max(last_title_rect.bottom, last_value_rect.bottom)
        if last_row_bottom > buttons_top - margin:
            dy = (buttons_top - margin) - last_row_bottom
            last_title_rect.y += dy
            last_value_rect.y += dy

        surface.blit(last_title_surf, last_title_rect)
        surface.blit(last_value_surf, last_value_rect)

        # (Nếu sau này cần thêm text dưới nữa thì cập nhật y)
        y = max(last_title_rect.bottom, last_value_rect.bottom) + 14

        # ---- Buttons ----
        self.undo_button.draw(surface)
        self.redo_button.draw(surface)
        self.pass_button.draw(surface)
        self.resign_button.draw(surface)
        self.back_button.draw(surface)
