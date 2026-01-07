from __future__ import annotations

import pygame
import os
import math
import random

from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    BG_COLOR,
    TEXT_COLOR,
    TEXT_MUTED,
    ACCENT_COLOR,
    ACCENT_COLOR_2,
)
from ui.widgets import Button


class HomeScreen:
    def __init__(self, app: "GoApp"):
        self.app = app
        self.buttons = []

        self.time = 0.0  # dùng chung cho animation
        self.stones: list[dict] = []

        self._load_background()
        self._init_stones()
        self._build_ui()

    # ==== helper chung cho tất cả nút ====
    def _with_click(self, fn):
        def wrapped():
            if hasattr(self.app, "play_click"):
                self.app.play_click()
            fn()
        return wrapped

    # ================== UI ==================
    def _build_ui(self):
        center_x = WINDOW_WIDTH // 2
        title_y = 180

        self.title_text = "GO GAME"
        self.title_layers = []

        shadow_deep = self.app.font_title.render(self.title_text, True, (0, 0, 0))
        shadow_deep_rect = shadow_deep.get_rect(center=(center_x + 5, title_y + 7))
        self.title_layers.append((shadow_deep, shadow_deep_rect))

        outline_dark = self.app.font_title.render(
            self.title_text, True, (15, 25, 55)
        )
        outline_dark_rect = outline_dark.get_rect(center=(center_x + 3, title_y + 4))
        self.title_layers.append((outline_dark, outline_dark_rect))

        mid_color = self.app.font_title.render(self.title_text, True, ACCENT_COLOR)
        mid_color_rect = mid_color.get_rect(center=(center_x + 1, title_y + 1))
        self.title_layers.append((mid_color, mid_color_rect))

        main = self.app.font_title.render(self.title_text, True, TEXT_COLOR)
        main_rect = main.get_rect(center=(center_x, title_y))
        self.title_layers.append((main, main_rect))

        # rect gốc của title
        self.title_rect = main_rect

        # ===== 3 NÚT BẰNG NHAU, XẾP DỌC =====
        btn_width = 260
        btn_height = 60
        spacing = 18
        start_y = title_y + 160

        self.start_button = Button(
            rect=(
                center_x - btn_width // 2,
                start_y,
                btn_width,
                btn_height,
            ),
            text="Start",
            font=self.app.font_h1,
            callback=self._with_click(lambda: self.app.change_screen("setup")),
            base_color=ACCENT_COLOR,
            hover_color=ACCENT_COLOR_2,
            text_color=(20, 20, 20),
            glow=True,
            glow_color=ACCENT_COLOR_2,
            max_scale=1.15,
            hover_speed=9.0,
        )

        self.guide_button = Button(
            rect=(
                center_x - btn_width // 2,
                start_y + (btn_height + spacing),
                btn_width,
                btn_height,
            ),
            text="Guide",
            font=self.app.font_body,
            callback=self._with_click(lambda: self.app.change_screen("guide")),
        )

        self.quit_button = Button(
            rect=(
                center_x - btn_width // 2,
                start_y + 2 * (btn_height + spacing),
                btn_width,
                btn_height,
            ),
            text="Quit",
            font=self.app.font_body,
            # thay vì thoát luôn, bật popup xác nhận
            callback=self._with_click(self._on_quit_clicked),
        )

        self.buttons = [self.start_button, self.guide_button, self.quit_button]

        # Lưu vị trí gốc để float
        self._start_base_y = self.start_button.rect.y
        self._guide_base_y = self.guide_button.rect.y
        self._quit_base_y = self.quit_button.rect.y

        # ===== NÚT MUSIC ON/OFF ở góc trên bên phải =====
        music_label = "Music: On" if self.app.music_on else "Music: Off"
        self.music_button = Button(
            rect=(WINDOW_WIDTH - 160, 20, 130, 40),
            text=music_label,
            font=self.app.font_small,
            callback=self._with_click(self._toggle_music),
        )

        # ===== QUIT CONFIRM DIALOG =====
        self.show_quit_confirm = False
        self._build_quit_confirm()

    def _build_quit_confirm(self):
        """Panel xác nhận thoát game"""
        panel_w, panel_h = 520, 220
        self.quit_panel_rect = pygame.Rect(0, 0, panel_w, panel_h)
        self.quit_panel_rect.center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

        btn_w, btn_h = 160, 52
        spacing = 30
        cx = self.quit_panel_rect.centerx
        y = self.quit_panel_rect.bottom - 70

        yes_rect = (cx - spacing // 2 - btn_w, y, btn_w, btn_h)
        no_rect = (cx + spacing // 2, y, btn_w, btn_h)

        self.quit_yes_button = Button(
            rect=yes_rect,
            text="Exit now",
            font=self.app.font_body,
            callback=self._with_click(self._confirm_quit),
        )
        self.quit_no_button = Button(
            rect=no_rect,
            text="Stay longer",
            font=self.app.font_body,
            callback=self._with_click(self._cancel_quit),
        )

    # ================== BACKGROUND & STONES ==================
    def _load_background(self):
        """
        Load background và scale to hơn 1 chút để parallax không lộ viền.
        """
        base_dir = os.path.dirname(os.path.dirname(__file__))
        assets_dir = os.path.join(base_dir, "assets")
        img_path = os.path.join(assets_dir, "home_bg.jpg")

        raw = pygame.image.load(img_path).convert()
        scale_factor = 1.12  # phóng to nhẹ
        w = int(WINDOW_WIDTH * scale_factor)
        h = int(WINDOW_HEIGHT * scale_factor)
        self.bg_image = pygame.transform.smoothscale(raw, (w, h))

        # dùng rect để dễ canh giữa + offset parallax
        self.bg_rect = self.bg_image.get_rect(
            center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        )

    def _init_stones(self):
        """
        Tạo nhiều viên cờ trôi lơ lửng (đen & trắng) + trạng thái để tương tác,
        phân bố chủ yếu hai bên trái/phải.
        Tất cả viên cờ có cùng kích thước.
        """
        self.stones = []

        num_stones = 14          # 14 viên
        stone_radius = 18        # mọi viên cờ cùng radius = 18
        center_x = WINDOW_WIDTH // 2

        for i in range(num_stones):
            is_white = (i % 2 == 0)
            radius = stone_radius

            # chọn bên trái hoặc phải (nửa trái, nửa phải)
            left_side = (i < num_stones // 2)
            if left_side:
                base_x = random.randint(60, center_x - 220)
            else:
                base_x = random.randint(center_x + 220, WINDOW_WIDTH - 60)

            # y tự do, tránh đè sát mép
            base_y = random.randint(80, WINDOW_HEIGHT - 80)

            # tốc độ & biên độ khác nhau chút cho tự nhiên
            speed = random.uniform(0.45, 0.95)
            amp_y = random.randint(14, 24)
            amp_x = amp_y * random.uniform(0.4, 0.7)
            phase = random.uniform(0, math.tau)

            # trạng thái động cho viên cờ
            self.stones.append(
                {
                    "base_x": base_x,
                    "base_y": base_y,
                    "radius": radius,
                    "is_white": is_white,
                    "speed": speed,
                    "amp_x": amp_x,
                    "amp_y": amp_y,
                    "phase": phase,
                    # vị trí hiện tại (để vẽ & va chạm)
                    "x": float(base_x),
                    "y": float(base_y),
                    # vận tốc khi bị "đá văng"
                    "vx": 0.0,
                    "vy": 0.0,
                    # thời gian còn lại của trạng thái bị đá văng
                    "kick_timer": 0.0,
                }
            )

    # ================== LOGIC ==================
    def _toggle_music(self):
        self.app.toggle_music()
        self.music_button.text = "Music: On" if self.app.music_on else "Music: Off"
        self.music_button._render_text()

    def _on_quit_clicked(self):
        """Khi bấm nút Quit: mở popup xác nhận, không thoát liền."""
        self.show_quit_confirm = True

    def _confirm_quit(self):
        """User xác nhận thoát"""
        self.app.running = False

    def _cancel_quit(self):
        """User ở lại """
        self.show_quit_confirm = False

    def _on_quit(self):
        self._on_quit_clicked()

    def handle_event(self, event: pygame.event.Event):
        # nếu đang mở dialog confirm, chỉ xử lý trong dialog
        if self.show_quit_confirm:
            self.quit_yes_button.handle_event(event)
            self.quit_no_button.handle_event(event)

            # bấm ESC để đóng popup
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self._cancel_quit()
            return

        # nút bình thường
        for btn in self.buttons:
            btn.handle_event(event)
        self.music_button.handle_event(event)

        # click vào viên cờ để đá văng
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            for stone in self.stones:
                dx = mx - stone["x"]
                dy = my - stone["y"]
                dist_sq = dx * dx + dy * dy
                r = stone["radius"]
                if dist_sq <= r * r:
                    # hướng từ click thì viên cờ (đá văng ra xa khỏi con trỏ)
                    dir_x = stone["x"] - mx
                    dir_y = stone["y"] - my
                    length = math.hypot(dir_x, dir_y) or 1.0
                    dir_x /= length
                    dir_y /= length

                    # cho văng mạnh hơn một chút
                    speed = random.uniform(320.0, 520.0)
                    stone["vx"] = dir_x * speed
                    stone["vy"] = dir_y * speed

                    # thời gian bay tự do lâu hơn
                    stone["kick_timer"] = random.uniform(0.55, 1.1)
                    break  # 1 click chỉ đá 1 viên

    def update(self, dt: float):
        # thời gian dùng cho mọi animation
        self.time += dt

        # ===== float các nút lên xuống nhẹ (chỉ khi không show dialog) =====
        if not self.show_quit_confirm:
            float_amp = 6
            speed = 1.4

            self.start_button.rect.y = self._start_base_y + int(
                math.sin(self.time * speed) * float_amp
            )
            self.guide_button.rect.y = self._guide_base_y + int(
                math.sin(self.time * speed + 0.8) * float_amp * 0.7
            )
            self.quit_button.rect.y = self._quit_base_y + int(
                math.sin(self.time * speed + 1.6) * float_amp * 0.5
            )

        # update hiệu ứng hover/glow trong Button
        for btn in self.buttons:
            btn.update(dt)
        self.music_button.update(dt)

        if self.show_quit_confirm:
            self.quit_yes_button.update(dt)
            self.quit_no_button.update(dt)

        # ===== update các viên cờ =====
        for stone in self.stones:
            speed = stone["speed"]
            amp_x = stone["amp_x"]
            amp_y = stone["amp_y"]
            phase = stone["phase"]

            t = self.time * speed + phase
            target_x = stone["base_x"] + math.cos(t) * amp_x
            target_y = stone["base_y"] + math.sin(t) * amp_y

            if stone["kick_timer"] > 0.0:
                # bay tự do với vận tốc + ma sát
                stone["x"] += stone["vx"] * dt
                stone["y"] += stone["vy"] * dt

                # ma sát làm giảm tốc dần (nhưng vẫn đàn hồi mạnh)
                friction = 0.82 ** (dt * 60.0)
                stone["vx"] *= friction
                stone["vy"] *= friction

                # giới hạn trong màn hình và nảy lại nếu chạm biên
                r = stone["radius"]
                if stone["x"] < r:
                    stone["x"] = r
                    stone["vx"] *= -0.7
                elif stone["x"] > WINDOW_WIDTH - r:
                    stone["x"] = WINDOW_WIDTH - r
                    stone["vx"] *= -0.7

                if stone["y"] < r:
                    stone["y"] = r
                    stone["vy"] *= -0.7
                elif stone["y"] > WINDOW_HEIGHT - r:
                    stone["y"] = WINDOW_HEIGHT - r
                    stone["vy"] *= -0.7

                stone["kick_timer"] -= dt
                if stone["kick_timer"] <= 0.0:
                    stone["kick_timer"] = 0.0
                    # neo lại quỹ đạo lơ lửng mới tại vị trí hiện tại
                    stone["base_x"] = stone["x"]
                    stone["base_y"] = stone["y"]
                    stone["phase"] = random.uniform(0, math.tau)
            else:
                # trạng thái bình thường: đi theo quỹ đạo sin
                stone["x"] = target_x
                stone["y"] = target_y

    # ================== DRAW HELPERS ==================
    def _draw_parallax_background(self, surface: pygame.Surface):
        # parallax nhẹ: vừa theo thời gian, vừa theo vị trí chuột
        mx, my = pygame.mouse.get_pos()
        dx_mouse = (mx - WINDOW_WIDTH / 2) * 0.02
        dy_mouse = (my - WINDOW_HEIGHT / 2) * 0.02

        dx_time = math.sin(self.time * 0.3) * 8
        dy_time = math.cos(self.time * 0.25) * 6

        offset_x = int(dx_mouse + dx_time)
        offset_y = int(dy_mouse + dy_time)

        bg_rect = self.bg_rect.copy()
        bg_rect.centerx += offset_x
        bg_rect.centery += offset_y

        surface.blit(self.bg_image, bg_rect)

    def _draw_stones(self, surface: pygame.Surface):
        """
        Vẽ các viên cờ trôi lơ lửng
        """
        for stone in self.stones:
            x = stone["x"]
            y = stone["y"]
            r = stone["radius"]
            is_white = stone["is_white"]

            stone_color = (235, 235, 235) if is_white else (25, 25, 25)
            pygame.draw.circle(surface, stone_color, (int(x), int(y)), r)

            # highlight nhỏ trên viên cờ cho bóng bẩy
            highlight_radius = int(r * 0.5)
            highlight_surf = pygame.Surface(
                (highlight_radius * 2, highlight_radius * 2), pygame.SRCALPHA
            )
            pygame.draw.circle(
                highlight_surf,
                (255, 255, 255, 130),
                (highlight_radius, highlight_radius),
                highlight_radius,
            )
            surface.blit(
                highlight_surf,
                (
                    int(x - r * 0.3) - highlight_radius,
                    int(y - r * 0.5) - highlight_radius,
                ),
            )

    # ================== MAIN DRAW ==================
    def draw(self, surface: pygame.Surface):
        # background parallax
        self._draw_parallax_background(surface)

        # overlay tối nhẹ
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        surface.blit(overlay, (0, 0))

        # stones trôi lơ lửng (trên overlay, dưới UI)
        self._draw_stones(surface)

        # ===== highlight động phía trên title =====
        highlight_surf = pygame.Surface(
            (self.title_rect.width, self.title_rect.height), pygame.SRCALPHA
        )
        pulse = (math.sin(self.time * 2.0) + 1.0) / 2.0  # 0..1
        highlight_alpha = int(25 + 35 * pulse)
        pygame.draw.ellipse(
            highlight_surf,
            (255, 255, 255, highlight_alpha),
            highlight_surf.get_rect(),
        )

        title_dy = int(math.sin(self.time * 1.3) * 4)
        highlight_rect = highlight_surf.get_rect(
            center=(self.title_rect.centerx, self.title_rect.centery - 8 + title_dy)
        )
        surface.blit(highlight_surf, highlight_rect)

        # Layer of titles and offets
        for surf, base_rect in self.title_layers:
            rect = base_rect.copy()
            rect.y += title_dy
            surface.blit(surf, rect)

        # 3 main buttons
        for btn in self.buttons:
            btn.draw(surface)

        # Music button
        self.music_button.draw(surface)

        # ===== Dialog confirm =====
        if self.show_quit_confirm:
            # dim nền
            dim = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 150))
            surface.blit(dim, (0, 0))

            # panel chính
            pygame.draw.rect(
                surface,
                (20, 24, 40),
                self.quit_panel_rect,
                border_radius=18,
            )
            pygame.draw.rect(
                surface,
                (200, 210, 255),
                self.quit_panel_rect,
                2,
                border_radius=18,
            )

            
            title_surf = self.app.font_h1.render(
                "Exit?", True, (255, 255, 255)
            )
            title_rect = title_surf.get_rect(
                midtop=(self.quit_panel_rect.centerx, self.quit_panel_rect.top + 20)
            )
            surface.blit(title_surf, title_rect)

            msg = "Are you sure you want to exit?"
            lines = msg.split("\n")
            y = title_rect.bottom + 20
            for line in lines:
                text_surf = self.app.font_body.render(line, True, (220, 225, 250))
                text_rect = text_surf.get_rect(
                    midtop=(self.quit_panel_rect.centerx, y)
                )
                surface.blit(text_surf, text_rect)
                y += 32

            self.quit_yes_button.draw(surface)
            self.quit_no_button.draw(surface)
