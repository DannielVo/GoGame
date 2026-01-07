from __future__ import annotations
import pygame
import os
import math
from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    BG_COLOR,
    PANEL_BG,
    TEXT_COLOR,
    TEXT_MUTED,
    ACCENT_COLOR,
    ACCENT_COLOR_2,
)
from ui.widgets import Button, OptionButton
from core.game import GameMode
from core.board import Player


class SetupScreen:
    def __init__(self, app: "GoApp"):
        self.app = app

        # Default selection
        self.selected_size = 9
        self.selected_mode = GameMode.HUMAN_VS_HUMAN
        self.selected_board_style = "wood"      # "wood" | "stone"
        self.selected_color = Player.BLACK      # mặc định chơi Đen (khi vs AI)

        # collections button
        self.size_buttons: list[OptionButton] = []
        self.mode_buttons: list[OptionButton] = []
        self.board_style_buttons: list[OptionButton] = []
        self.color_buttons: list[OptionButton] = []  # Play as Black/White

        self.play_button: Button | None = None
        self.back_button: Button | None = None

        # background & preview
        self.bg_image: pygame.Surface | None = None
        self.bg_rect: pygame.Rect | None = None
        self.board_previews: dict[str, pygame.Surface] = {}  # key: "{style}_{size}"
        self.preview_rect: pygame.Rect | None = None

        # hover state
        self.hovered_board_style: str | None = None
        self.hovered_size: int | None = None  # board size đang được hover

        self.time = 0.0

        self._load_background()
        self._build_ui()
        self._load_board_previews()

    # ==== Helper chung ====
    def _with_click(self, fn):
        def wrapped():
            if hasattr(self.app, "play_click"):
                self.app.play_click()
            fn()
        return wrapped

    # ============ LOAD ASSETS ============

    def _load_background(self):
        """Dùng image2.png làm background, scale vừa màn hình."""
        base_dir = os.path.dirname(os.path.dirname(__file__))
        assets_dir = os.path.join(base_dir, "assets")
        img_path = os.path.join(assets_dir, "image2.png")

        try:
            raw = pygame.image.load(img_path).convert()
            scale_factor = 1.08
            w = int(WINDOW_WIDTH * scale_factor)
            h = int(WINDOW_HEIGHT * scale_factor)
            self.bg_image = pygame.transform.smoothscale(raw, (w, h))
            self.bg_rect = self.bg_image.get_rect(
                center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
            )
        except Exception as e:
            print("Không thể load image2.png:", e)
            self.bg_image = None
            self.bg_rect = None

    def _load_board_previews(self):
        if not self.preview_rect:
            return

        base_dir = os.path.dirname(os.path.dirname(__file__))
        assets_dir = os.path.join(base_dir, "assets")

        size = 9    # preview 9x9 là đủ
        styles = ["wood", "stone"]

        max_w = self.preview_rect.width - 24
        max_h = self.preview_rect.height - 24

        for style in styles:
            filename = f"board_{style}_{size}x{size}.png"
            path = os.path.join(assets_dir, filename)
            key = f"{style}_{size}"

            try:
                img = pygame.image.load(path).convert_alpha()
                img_w, img_h = img.get_size()
                scale = min(max_w / img_w, max_h / img_h)
                new_size = (int(img_w * scale), int(img_h * scale))
                img_scaled = pygame.transform.smoothscale(img, new_size)
                self.board_previews[key] = img_scaled
            except Exception as e:
                print(f"Không thể load preview {filename}:", e)

    # ============ BUILD UI ============

    def _build_ui(self):
        # Panel chính ở giữa
        panel_rect = pygame.Rect(0, 0, 900, 540)
        panel_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        self.panel_rect = panel_rect

        # Preview bên phải
        preview_w, preview_h = 280, 280
        self.preview_rect = pygame.Rect(0, 0, preview_w, preview_h)
        self.preview_rect.midright = (panel_rect.right - 40, panel_rect.centery)

        # ====== BOARD SIZE ======
        size = 9   # chỉ còn 9x9
        size_btn_w, size_btn_h = 120, 50

        # vùng trái (để chừa chỗ cho preview bên phải)
        left_area_left = panel_rect.left + 40
        left_area_right = self.preview_rect.left - 40
        left_area_width = left_area_right - left_area_left

        # layout theo trục dọc (giảm khoảng cách để không đụng Back/Play)
        title_top = panel_rect.top + 28
        sizes_y = title_top + 70           # từ title xuống dòng size
        style_gap_y = 40                   # khoảng cách giữa các cụm
        mode_gap_y = 40
        color_gap_y = 40

        # Vì chỉ có 1 button size nên total_width = size_btn_w
        total_width = size_btn_w
        start_x = left_area_left + (left_area_width - total_width) // 2

        rect = (start_x, sizes_y, size_btn_w, size_btn_h)

        def make_callback(s=size):
            return lambda: self._select_size(s)

        btn = OptionButton(
            rect=rect,
            text=f"{size} x {size}",
            font=self.app.font_body,
            callback=self._with_click(make_callback()),
            selected=(size == self.selected_size),
        )
        btn.board_size = size
        self.size_buttons.append(btn)

        # ====== BOARD STYLE (chất liệu bàn) ======
        styles = [
            ("wood", "Ironwood"),
            ("stone", "Marble Stone"),
        ]
        style_btn_w, style_btn_h = 230, 50
        style_spacing = 16
        total_width_style = len(styles) * style_btn_w + (len(styles) - 1) * style_spacing
        style_start_x = left_area_left + (left_area_width - total_width_style) // 2
        style_y = sizes_y + size_btn_h + style_gap_y

        for idx, (style_id, label) in enumerate(styles):
            rect = (
                style_start_x + idx * (style_btn_w + style_spacing),
                style_y,
                style_btn_w,
                style_btn_h,
            )

            def make_callback_style(st=style_id):
                return lambda: self._select_board_style(st)

            btn = OptionButton(
                rect=rect,
                text=label,
                font=self.app.font_body,
                callback=self._with_click(make_callback_style()),
                selected=(style_id == self.selected_board_style),
            )
            btn.board_style_id = style_id
            self.board_style_buttons.append(btn)

        # ====== GAME MODE ======
        modes = [
            (GameMode.HUMAN_VS_HUMAN, "Player vs Player"),
            (GameMode.HUMAN_VS_BOT, "Player vs AI"),
        ]
        mode_btn_w, mode_btn_h = 230, 50
        mode_spacing = 18
        total_width_mode = len(modes) * mode_btn_w + mode_spacing
        mode_start_x = left_area_left + (left_area_width - total_width_mode) // 2
        mode_y = style_y + style_btn_h + mode_gap_y

        for idx, (mode, label) in enumerate(modes):
            rect = (
                mode_start_x + idx * (mode_btn_w + mode_spacing),
                mode_y,
                mode_btn_w,
                mode_btn_h,
            )

            def make_callback_mode(m=mode):
                return lambda: self._select_mode(m)

            btn = OptionButton(
                rect=rect,
                text=label,
                font=self.app.font_body,
                callback=self._with_click(make_callback_mode()),
                selected=(mode == self.selected_mode),
            )
            btn.mode = mode
            self.mode_buttons.append(btn)

        # ====== PLAY AS (Black / White) – nằm trên Back/Play, không bị che ======
        colors = [
            (Player.BLACK, "Play as Black"),
            (Player.WHITE, "Play as White"),
        ]
        color_btn_w, color_btn_h = 190, 48
        color_spacing = 18
        total_width_color = len(colors) * color_btn_w + color_spacing
        color_start_x = left_area_left + (left_area_width - total_width_color) // 2
        color_y = mode_y + mode_btn_h + color_gap_y   # đã giảm gap, nên không đụng Back/Play

        for idx, (color, label) in enumerate(colors):
            rect = (
                color_start_x + idx * (color_btn_w + color_spacing),
                color_y,
                color_btn_w,
                color_btn_h,
            )

            def make_callback_color(c=color):
                return lambda: self._select_color(c)

            btn = OptionButton(
                rect=rect,
                text=label,
                font=self.app.font_body,
                callback=self._with_click(make_callback_color()),
                selected=(color == self.selected_color),
            )
            btn.player_color = color
            self.color_buttons.append(btn)

        # ====== PLAY & BACK ======
        self.back_button = Button(
            rect=(panel_rect.centerx - 130, panel_rect.bottom - 70, 120, 50),
            text="Back",
            font=self.app.font_body,
            callback=self._with_click(lambda: self.app.change_screen("home")),
        )

        self.play_button = Button(
            rect=(panel_rect.centerx + 10, panel_rect.bottom - 70, 120, 50),
            text="Play",
            font=self.app.font_body,
            callback=self._with_click(self._on_play),
            base_color=ACCENT_COLOR,
            hover_color=ACCENT_COLOR_2,
            text_color=(20, 20, 20),
        )

    # ============ SELECT HANDLERS ============

    def _select_size(self, size: int):
        self.selected_size = size
        for btn in self.size_buttons:
            btn.selected = getattr(btn, "board_size", None) == size

    def _select_mode(self, mode: GameMode):
        self.selected_mode = mode
        for btn in self.mode_buttons:
            btn.selected = getattr(btn, "mode", None) == mode
        # Không cần reset màu; vẫn nhớ lựa chọn cũ khi quay lại Player vs AI

    def _select_board_style(self, style_id: str):
        self.selected_board_style = style_id
        for btn in self.board_style_buttons:
            btn.selected = getattr(btn, "board_style_id", None) == style_id

    def _select_color(self, color: Player):
        self.selected_color = color
        for btn in self.color_buttons:
            btn.selected = getattr(btn, "player_color", None) == color

    def _on_play(self):
        # Chỉ thực sự dùng human_color khi Mode = HUMAN_VS_BOT
        human_color = (
            self.selected_color
            if self.selected_mode == GameMode.HUMAN_VS_BOT
            else Player.BLACK
        )

        self.app.change_screen(
            "game",
            board_size=self.selected_size,
            mode=self.selected_mode,
            board_style=self.selected_board_style,
            human_color=human_color,
        )

    # ============ EVENT / UPDATE / DRAW ============

    def handle_event(self, event: pygame.event.Event):
        # chỉ cho color_buttons nhận event khi Mode = Player vs AI
        buttons = (
            self.size_buttons
            + self.mode_buttons
            + self.board_style_buttons
        )
        if self.selected_mode == GameMode.HUMAN_VS_BOT:
            buttons += self.color_buttons

        for btn in buttons:
            btn.handle_event(event)

        if self.play_button:
            self.play_button.handle_event(event)
        if self.back_button:
            self.back_button.handle_event(event)

    def update(self, dt: float):
        self.time += dt

        buttons = (
            self.size_buttons
            + self.mode_buttons
            + self.board_style_buttons
        )
        if self.selected_mode == GameMode.HUMAN_VS_BOT:
            buttons += self.color_buttons

        for btn in buttons:
            btn.update(dt)

        if self.play_button:
            self.play_button.update(dt)
        if self.back_button:
            self.back_button.update(dt)

        # xác định board_style đang được hover (để show preview)
        mx, my = pygame.mouse.get_pos()

        hovered_style = None
        for btn in self.board_style_buttons:
            if btn.rect.collidepoint((mx, my)):
                hovered_style = getattr(btn, "board_style_id", None)
                break
        self.hovered_board_style = hovered_style

        # xác định size đang hover để đổi preview
        hovered_size = None
        for btn in self.size_buttons:
            if btn.rect.collidepoint((mx, my)):
                hovered_size = getattr(btn, "board_size", None)
                break
        self.hovered_size = hovered_size

    # ---- Background ----
    def _draw_background(self, surface: pygame.Surface):
        if not self.bg_image or not self.bg_rect:
            surface.fill(BG_COLOR)
            return

        mx, my = pygame.mouse.get_pos()
        dx_mouse = (mx - WINDOW_WIDTH / 2) * 0.015
        dy_mouse = (my - WINDOW_HEIGHT / 2) * 0.015

        dx_time = math.sin(self.time * 0.25) * 6
        dy_time = math.cos(self.time * 0.22) * 4

        offset_x = int(dx_mouse + dx_time)
        offset_y = int(dy_mouse + dy_time)

        bg_rect = self.bg_rect.copy()
        bg_rect.centerx += offset_x
        bg_rect.centery += offset_y

        surface.blit(self.bg_image, bg_rect)

    def _draw_board_preview(self, surface: pygame.Surface):
        if not self.preview_rect:
            return

        rect = self.preview_rect

        # nền + viền khung preview
        pygame.draw.rect(surface, (10, 10, 25), rect, border_radius=18)
        pygame.draw.rect(surface, (190, 200, 255), rect, width=2, border_radius=18)

        # chọn style & size để hiển thị
        style_to_show = self.hovered_board_style or self.selected_board_style
        size_to_show = self.hovered_size or self.selected_size

        key = f"{style_to_show}_{size_to_show}"
        img = self.board_previews.get(key)

        if not img:
            # nếu chưa có ảnh thì show text placeholder
            text = f"{style_to_show} {size_to_show}x{size_to_show}\n(Chưa có hình)"
            lines = text.split("\n")
            y = rect.centery - 18
            for line in lines:
                surf = self.app.font_body.render(line, True, (235, 240, 255))
                r = surf.get_rect(center=(rect.centerx, y))
                surface.blit(surf, r)
                y += 28
            return

        img_rect = img.get_rect(center=rect.center)
        surface.blit(img, img_rect)

    # ---- helper vẽ chữ 3D nhỏ gọn cho label ----
    def _blit_label_3d_midbottom(
        self,
        panel: pygame.Surface,
        text: str,
        font: pygame.font.Font,
        center_pos: tuple[int, int],
    ):
        main_color = (250, 252, 255)
        outline_color = (90, 120, 220)
        shadow_color = (0, 0, 0)

        surf_main = font.render(text, True, main_color)
        surf_outline = font.render(text, True, outline_color)
        surf_shadow = font.render(text, True, shadow_color)

        rect_main = surf_main.get_rect(midbottom=center_pos)
        rect_shadow = rect_main.copy()
        rect_shadow.x += 2
        rect_shadow.y += 2

        # shadow
        panel.blit(surf_shadow, rect_shadow)

        # outline 4 hướng
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r = rect_main.copy()
            r.x += ox
            r.y += oy
            panel.blit(surf_outline, r)

        # main
        panel.blit(surf_main, rect_main)

    def draw(self, surface: pygame.Surface):
        # background
        self._draw_background(surface)

        # overlay mờ để panel nổi hơn
        dim = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 90))
        surface.blit(dim, (0, 0))

        # panel chính
        panel = pygame.Surface(self.panel_rect.size, pygame.SRCALPHA)
        panel.fill((12, 16, 32, 235))
        pygame.draw.rect(
            panel,
            (220, 230, 255, 100),
            panel.get_rect(),
            width=2,
            border_radius=22,
        )

        # ===== TITLE 3D =====
        title_text = "Game Setup"
        main_color = (250, 252, 255)
        outline_color = (110, 150, 255)
        shadow_color = (0, 0, 0)

        title_main = self.app.font_h1.render(title_text, True, main_color)
        title_outline = self.app.font_h1.render(title_text, True, outline_color)
        title_shadow = self.app.font_h1.render(title_text, True, shadow_color)

        title_rect = title_main.get_rect(midtop=(panel.get_width() // 2, 20))
        shadow_rect = title_rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3

        # shadow
        panel.blit(title_shadow, shadow_rect)

        # outline quanh chữ
        for ox, oy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            r = title_rect.copy()
            r.x += ox
            r.y += oy
            panel.blit(title_outline, r)

        # main
        panel.blit(title_main, title_rect)

        # ===== TÍNH CỘT TRÁI ĐỂ CĂN CHỮ & NÚT THẲNG HÀNG =====
        left_area_left = 40
        left_area_right = self.preview_rect.left - self.panel_rect.left - 40
        left_area_width = left_area_right - left_area_left
        left_center_x = left_area_left + left_area_width // 2

        # Lấy y hàng nút (global => panel coord)
        size_row_y = self.size_buttons[0].rect.y - self.panel_rect.top
        style_row_y = self.board_style_buttons[0].rect.y - self.panel_rect.top
        mode_row_y = self.mode_buttons[0].rect.y - self.panel_rect.top
        color_row_y = self.color_buttons[0].rect.y - self.panel_rect.top

        # labels 3D
        self._blit_label_3d_midbottom(
            panel,
            "Board Size",
            self.app.font_body,
            (left_center_x, size_row_y - 12),
        )
        self._blit_label_3d_midbottom(
            panel,
            "Board Style",
            self.app.font_body,
            (left_center_x, style_row_y - 12),
        )
        self._blit_label_3d_midbottom(
            panel,
            "Game Mode",
            self.app.font_body,
            (left_center_x, mode_row_y - 12),
        )

        # label "Play as" chỉ hiện khi Player vs AI
        if self.selected_mode == GameMode.HUMAN_VS_BOT:
            self._blit_label_3d_midbottom(
                panel,
                "Play as",
                self.app.font_body,
                (left_center_x, color_row_y - 12),
            )

        # helper vẽ nút lên panel (đổi sang toạ độ local tạm thời)
        def draw_button_on_panel(btn: Button | OptionButton):
            temp_rect = btn.rect.copy()
            btn.rect.x -= self.panel_rect.left
            btn.rect.y -= self.panel_rect.top
            btn.draw(panel)
            btn.rect = temp_rect

        # Nút size / style / mode luôn vẽ
        for btn in self.size_buttons + self.board_style_buttons + self.mode_buttons:
            draw_button_on_panel(btn)

        # Nút chọn màu chỉ vẽ khi Player vs AI
        if self.selected_mode == GameMode.HUMAN_VS_BOT:
            for btn in self.color_buttons:
                draw_button_on_panel(btn)

        # Play & Back
        if self.play_button:
            draw_button_on_panel(self.play_button)
        if self.back_button:
            draw_button_on_panel(self.back_button)

        # blit panel ra màn hình
        surface.blit(panel, self.panel_rect.topleft)

        # vẽ preview (dùng coord global)
        self._draw_board_preview(surface)
