from __future__ import annotations

import os
import pygame

from config import (
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    PANEL_BG,
    TEXT_COLOR,
)
from ui.widgets import Button, OptionButton

# ================== LUẬT CHUẨN – TIẾNG VIỆT ==================

GUIDE_TEXT_VI = """
HƯỚNG DẪN CƠ BẢN LUẬT CỜ VÂY (GO)
1. Bàn cờ và quân cờ
• Đây là phiên bản cờ vây trên bàn 9x9 - phù hợp để học nhanh và chơi ngắn.
• Một người cầm quân Đen, người còn lại cầm quân Trắng.
• Quân được đặt trên các giao điểm (không di chuyển sau khi đặt).

2. Luật đi quân
• Đen luôn đi trước, sau đó hai bên luân phiên Đen - Trắng.
• Mỗi lượt chỉ được đặt đúng một quân vào một giao điểm trống.
• Không được đặt vào vị trí đã có quân.

3. Khí và bắt quân
• "Khí" của một quân (hoặc nhóm quân nối liền) là các giao điểm trống kề cạnh (trên, dưới, trái, phải) với nhóm đó.
• Khi toàn bộ khí của một nhóm quân bị các quân đối phương chiếm hết, nhóm quân đó bị bắt và bị lấy ra khỏi bàn cờ.
• Quân bị bắt sẽ được giữ lại làm "tù binh" và được cộng vào điểm số sau ván cờ.

4. Nước tự sát và luật ko
• Nước tự sát (đặt quân khiến chính quân hoặc nhóm của mình không còn khí) là không hợp lệ, trừ khi nước đó đồng thời bắt và loại bỏ ít nhất một nhóm quân của đối phương, qua đó tạo khí mới cho nhóm của mình.
• Luật "ko": không được đi một nước khiến toàn bộ hình cờ trên bàn trở lại giống y hệt vị trí chỉ một nước trước đó. Luật này ngăn việc ăn qua ăn lại vô hạn.

5. Kết thúc ván cờ
• Ván cờ thường kết thúc khi cả hai bên lần lượt "bỏ lượt" (pass) liên tiếp, hoặc một bên chủ động xin nhận thua (resign).
• Sau khi kết thúc, hai bên dọn bỏ các nhóm quân đã chết rõ ràng (nếu có) và tiến hành tính điểm.

6. Tính điểm
• "Lãnh thổ" là các giao điểm trống được bao vây hoàn toàn bởi quân của một bên.
• Ở kiểu tính điểm phổ biến hiện nay (luật Nhật/Bắc Mỹ), mỗi bên tính:
  - Số giao điểm lãnh thổ của mình;
  - Cộng với số quân đối phương đã bắt được (tù binh);
  - Cộng thêm "komi" cho Trắng (thường khoảng 6,5-7,5 điểm) để bù việc Đen đi trước.
• Bên có tổng điểm (lãnh thổ + tù binh + komi) cao hơn là người thắng.

7. Gợi ý luyện tập trên bản demo
• Bắt đầu làm quen với hình cờ, khái niệm khí, bắt quân và lãnh thổ.
• Luôn tập "đọc trước" một vài nước để xem nhóm nào có nguy cơ bị bắt trước khi đặt quân.

ĐIỀU KHIỂN TRONG GAME
• Click chuột trái gần một giao điểm trên bàn cờ để đặt quân.
• Nút UNDO: quay lại 1 nước trước đó (kể cả nước của bot).
• Nút REDO: đi tới 1 nước tiếp theo nếu vẫn còn trong lịch sử.
• Nút BACK: quay về màn hình chính.
"""


# ================== OFFICIAL-LIKE RULES – ENGLISH ==================

GUIDE_TEXT_EN = """
BASIC GO RULES - QUICK REFERENCE

1. Board and stones
• This demo uses a 9x9 Go board - ideal for quick games and learning.
• One player plays Black, the other White.
• Stones are placed on intersections and remain until captured.

2. Play
• Black plays first, then players alternate turns.
• On your turn, you place exactly one stone on any empty intersection.
• You may not play on a point that is already occupied.

3. Liberties and captures
• A stone (or a connected group of stones) has "liberties": empty adjacent intersections
  (up, down, left, right) next to the group.
• When all liberties of a group are occupied by the opponent, that group is captured
  and all of its stones are removed from the board.
• Captured stones are kept as prisoners and will count toward the final score.

4. Suicide and the ko rule
• A move that leaves your own stone or group with no liberties (suicide) is illegal,
  unless the move immediately captures at least one opposing group and thereby
  creates new liberties for your stones.
• The "ko" rule forbids a move that would recreate the entire board position from
  just one move earlier. This prevents endless capture-recapture loops.

5. Ending the game
• A game usually ends when both players pass in succession, or when one player resigns.
• After the game ends, the players remove any clearly dead groups (if necessary) and then score.

6. Scoring
• Territory consists of empty intersections that are completely surrounded
  by only one player's stones.
• Under the most common modern rules (Japanese / AGA style), each player counts:
  - The number of points of territory they surround;
  - Plus the number of captured enemy stones (prisoners);
  - Plus komi for White (usually around 6.5-7.5 points) to compensate
    for Black's first move advantage.
• The player with the higher total (territory + prisoners + komi) wins.

7. Tips for using this demo
• Start to learn basic shapes, liberties, captures, and territory.
• Practice reading a few moves ahead to see which groups are in danger
  before you play each move.

IN-GAME CONTROLS

• Left-click near an intersection to place a stone.
• UNDO button: step back one move (including bot moves).
• REDO button: step forward one move if a future move exists in the history.
• BACK button: return to the home screen.
"""


class GuideScreen:
    def __init__(self, app: "GoApp"):
        self.app = app
        self.language = "vi"
        self.current_text = GUIDE_TEXT_VI

        # Background image
        self._load_background()

        # Panel bên phải
        panel_width = int(WINDOW_WIDTH * 0.45)
        panel_height = WINDOW_HEIGHT - 120
        panel_x = WINDOW_WIDTH - panel_width - 60
        panel_y = 60
        self.panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)

        # Font text
        self.text_font = self.app.font_body

        # Layout dọc: title -> language buttons -> text
        self.lang_btn_height = 36
        self.lang_buttons_top = (
            self.panel_rect.top + 20 + self.app.font_title.get_height() + 20
        )

        text_top = self.lang_buttons_top + self.lang_btn_height + 20
        text_bottom_margin = 40

        self.text_rect = pygame.Rect(
            self.panel_rect.left + 30,
            text_top,
            self.panel_rect.width - 60,
            self.panel_rect.bottom - text_top - text_bottom_margin,
        )

        # Nền đen mờ cho toàn bộ vùng text (rộng hơn text_rect một chút)
        padding_x = 12
        padding_y = 10
        self.text_bg_rect = pygame.Rect(
            self.text_rect.left - padding_x,
            self.text_rect.top - padding_y,
            self.text_rect.width + 2 * padding_x,
            self.text_rect.height + 2 * padding_y,
        )
        # Đảm bảo vẫn nằm trong panel
        if self.text_bg_rect.left < self.panel_rect.left + 16:
            self.text_bg_rect.left = self.panel_rect.left + 16
        if self.text_bg_rect.right > self.panel_rect.right - 16:
            self.text_bg_rect.width = self.panel_rect.right - 16 - self.text_bg_rect.left
        if self.text_bg_rect.top < self.lang_buttons_top + self.lang_btn_height + 10:
            self.text_bg_rect.top = self.lang_buttons_top + self.lang_btn_height + 10
        if self.text_bg_rect.bottom > self.panel_rect.bottom - 20:
            self.text_bg_rect.height = self.panel_rect.bottom - 20 - self.text_bg_rect.top

        # Scrollbar
        self.scrollbar_width = 8
        self.scrollbar_rect = pygame.Rect(
            self.text_rect.right + 10,
            self.text_rect.top,
            self.scrollbar_width,
            self.text_rect.height,
        )
        self.thumb_rect = self.scrollbar_rect.copy()
        self.thumb_rect.height = 40

        self.scroll_offset = 0
        self.max_scroll = 0
        self.dragging_thumb = False
        self.drag_start_y = 0
        self.thumb_start_y = 0

        # Animation: panel fade-in
        self.panel_visible_t = 0.0  # 0 thì ẩn, 1 thì hiện hoàn toàn

        # Trạng thái thu nhỏ/phóng to
        self.guide_visible = True

        # Buttons
        self.back_button = Button(
            rect=(40, WINDOW_HEIGHT - 80, 160, 50),
            text="Back",
            font=self.app.font_body,
            callback=self._with_click(lambda: self.app.change_screen("home")),
        )

        self._build_language_buttons()
        self._build_music_button()
        self._build_toggle_button()

        # Chuẩn bị layout text
        self.lines: list[str] = []
        self._rebuild_text_layout()


    # ============ CLICK SOUND WRAPPER ============

    def _with_click(self, fn):
        """Gói callback lại để luôn phát tiếng click trước khi chạy hành động."""
        def wrapped():
            if hasattr(self.app, "play_click"):
                self.app.play_click()
            fn()
        return wrapped


    # ============ INITIALIZATION HELPERS ============

    def _load_background(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))  
        assets_dir = os.path.join(base_dir, "assets")
        img_path = os.path.join(assets_dir, "image1.png")

        self.bg_image = pygame.image.load(img_path).convert()
        self.bg_image = pygame.transform.smoothscale(
            self.bg_image, (WINDOW_WIDTH, WINDOW_HEIGHT)
        )

    def _build_language_buttons(self):
        pr = self.panel_rect
        btn_w = 120
        btn_h = self.lang_btn_height
        spacing = 10

        vi_rect = (pr.right - 2 * btn_w - spacing - 10, self.lang_buttons_top, btn_w, btn_h)
        en_rect = (pr.right - btn_w - 10, self.lang_buttons_top, btn_w, btn_h)

        self.vi_button = OptionButton(
            rect=vi_rect,
            text="Tiếng Việt",
            font=self.app.font_small,
            callback=self._with_click(lambda: self._set_language("vi")),
            selected=True,
        )
        self.en_button = OptionButton(
            rect=en_rect,
            text="English",
            font=self.app.font_small,
            callback=self._with_click(lambda: self._set_language("en")),
            selected=False,
        )

    def _build_music_button(self):
        music_label = "Music: On" if self.app.music_on else "Music: Off"
        self.music_button = Button(
            rect=(WINDOW_WIDTH - 300, 20, 130, 40),  # đẩy sang trái chút để chừa chỗ cho Guide
            text=music_label,
            font=self.app.font_small,
            callback=self._with_click(self._toggle_music),
        )

    def _build_toggle_button(self):
        """Nút thu nhỏ/phóng to guide."""
        # Khi guide đang mở: nút nhỏ "-" ở góc trên bên phải panel
        self.toggle_button = Button(
            rect=(self.panel_rect.right - 40, self.panel_rect.top + 10, 30, 30),
            text="-",
            font=self.app.font_small,
            callback=self._with_click(self._toggle_guide_visibility),
        )

    def _toggle_music(self):
        self.app.toggle_music()
        self.music_button.text = "Music: On" if self.app.music_on else "Music: Off"
        self.music_button._render_text()

    def _toggle_guide_visibility(self):
        """Thu nhỏ/phóng to toàn bộ panel guide."""
        self.guide_visible = not self.guide_visible
        if self.guide_visible:
            # mở lại panel thì đặt lại vị trí & text nút
            self.panel_visible_t = 0.0  # để fade-in lại
            self.toggle_button.text = "–"
            self.toggle_button.rect = pygame.Rect(
                self.panel_rect.right - 40,
                self.panel_rect.top + 10,
                30,
                30,
            )
        else:
            # thu nhỏ thì nút "Guide" cùng hàng với Music
            guide_height = self.music_button.rect.height
            guide_y = self.music_button.rect.y
            guide_width = 100
            margin = 10
            self.toggle_button.text = "Guide"
            self.toggle_button.rect = pygame.Rect(
                self.music_button.rect.right + margin,
                guide_y,
                guide_width,
                guide_height,
            )
        self.toggle_button._render_text()


    # ============ LANGUAGE & TEXT LAYOUT ============

    def _set_language(self, lang: str):
        self.language = lang
        if lang == "vi":
            self.current_text = GUIDE_TEXT_VI
            self.vi_button.selected = True
            self.en_button.selected = False
        else:
            self.current_text = GUIDE_TEXT_EN
            self.vi_button.selected = False
            self.en_button.selected = True

        self.scroll_offset = 0
        self._rebuild_text_layout()

    def _wrap_text(self, text: str, font: pygame.font.Font, max_width: int) -> list[str]:
        lines: list[str] = []
        for raw_line in text.splitlines():
            if not raw_line.strip():
                lines.append("")
                continue

            words = raw_line.split(" ")
            current = words[0]
            for word in words[1:]:
                test = current + " " + word
                w, _ = font.size(test)
                if w <= max_width:
                    current = test
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
        return lines

    def _rebuild_text_layout(self):
        font = self.text_font
        self.lines = self._wrap_text(self.current_text, font, self.text_rect.width)

        line_height = font.get_linesize()
        total_height = len(self.lines) * (line_height + 4)  # thêm spacing
        self.total_text_height = total_height

        visible_height = self.text_rect.height
        if total_height <= visible_height:
            self.max_scroll = 0
            self.scroll_offset = 0
        else:
            self.max_scroll = total_height - visible_height
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))

        self._update_thumb_rect()

    def _update_thumb_rect(self):
        sb = self.scrollbar_rect
        if self.max_scroll <= 0:
            self.thumb_rect = pygame.Rect(sb.left, sb.top, sb.width, sb.height)
            self.thumb_visible = False
            return

        self.thumb_visible = True
        ratio = self.text_rect.height / self.total_text_height
        thumb_height = max(30, int(sb.height * ratio))
        max_thumb_move = sb.height - thumb_height
        if self.max_scroll > 0:
            thumb_offset = int(max_thumb_move * (self.scroll_offset / self.max_scroll))
        else:
            thumb_offset = 0

        self.thumb_rect = pygame.Rect(
            sb.left,
            sb.top + thumb_offset,
            sb.width,
            thumb_height,
        )


    # ============ EVENT HANDLING ============

    def handle_event(self, event: pygame.event.Event):
        self.back_button.handle_event(event)
        self.music_button.handle_event(event)
        self.toggle_button.handle_event(event)

        if not self.guide_visible:
            # guide đang thu nhỏ thì không nhận event cho panel/text/scroll
            return

        self.vi_button.handle_event(event)
        self.en_button.handle_event(event)

        if event.type == pygame.MOUSEWHEEL:
            if self.total_text_height > self.text_rect.height:
                self.scroll_offset -= event.y * 40
                self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
                self._update_thumb_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if getattr(self, "thumb_visible", False) and self.thumb_rect.collidepoint(
                event.pos
            ):
                self.dragging_thumb = True
                self.drag_start_y = event.pos[1]
                self.thumb_start_y = self.thumb_rect.y

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_thumb = False

        elif event.type == pygame.MOUSEMOTION and self.dragging_thumb:
            dy = event.pos[1] - self.drag_start_y
            sb = self.scrollbar_rect
            thumb_h = self.thumb_rect.height
            max_thumb_move = sb.height - thumb_h

            new_y = self.thumb_start_y + dy
            new_y = max(sb.top, min(sb.top + max_thumb_move, new_y))
            self.thumb_rect.y = new_y

            thumb_offset = new_y - sb.top
            if max_thumb_move > 0:
                self.scroll_offset = int(
                    (thumb_offset / max_thumb_move) * self.max_scroll
                )
            else:
                self.scroll_offset = 0

    def update(self, dt: float):
        # chỉ animate panel khi đang hiển thị
        if self.guide_visible:
            self.panel_visible_t = min(1.0, self.panel_visible_t + dt * 1.0)
        else:
            self.panel_visible_t = 0.0

        self.back_button.update(dt)
        self.vi_button.update(dt)
        self.en_button.update(dt)
        self.music_button.update(dt)
        self.toggle_button.update(dt)


    # ============ DRAW HELPERS ============

    def _draw_text_with_clipping(self, surface: pygame.Surface):
        font = self.text_font
        line_height = font.get_linesize()
        line_step = line_height + 4

        surface.set_clip(self.text_rect)

        y = self.text_rect.top - self.scroll_offset
        for line in self.lines:
            if y + line_step < self.text_rect.top:
                y += line_step
                continue
            if y > self.text_rect.bottom:
                break

            # Bóng chữ + chữ trắng
            shadow_surf = font.render(line, True, (0, 0, 0))
            text_surf = font.render(line, True, (255, 255, 255))
            surface.blit(shadow_surf, (self.text_rect.left + 2, y + 2))
            surface.blit(text_surf, (self.text_rect.left, y))

            y += line_step

        surface.set_clip(None)


    # ============ MAIN DRAW ============

    def draw(self, surface: pygame.Surface):
        # nền image luôn full
        surface.blit(self.bg_image, (0, 0))

        # Nếu guide đang hiển thị thì vẽ panel + text
        if self.guide_visible:
            panel_layer = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)

            # Panel semi-transparent bên phải
            pr = self.panel_rect
            panel_surf = pygame.Surface(pr.size, pygame.SRCALPHA)
            panel_surf.fill((*PANEL_BG, 200))  # hơi đậm cho contrast tổng thể
            pygame.draw.rect(
                panel_surf,
                (255, 255, 255, 60),
                panel_surf.get_rect(),
                2,
                border_radius=20,
            )
            panel_layer.blit(panel_surf, pr.topleft)

            # Title: "Hướng dẫn" / "Guide"
            title_text = "Hướng dẫn" if self.language == "vi" else "Guide"
            title_surf = self.app.font_title.render(title_text, True, (255, 255, 255))
            title_shadow = self.app.font_title.render(title_text, True, (0, 0, 0))
            title_rect = title_surf.get_rect(midtop=(pr.centerx, pr.top + 20))
            panel_layer.blit(title_shadow, (title_rect.x + 2, title_rect.y + 2))
            panel_layer.blit(title_surf, title_rect.topleft)

            # Language buttons
            self.vi_button.draw(panel_layer)
            self.en_button.draw(panel_layer)

            # Khối nền đen mờ bao phủ toàn bộ vùng text
            text_bg_surf = pygame.Surface(self.text_bg_rect.size, pygame.SRCALPHA)
            text_bg_surf.fill((0, 0, 0, 170))  # đen mờ đậm thì chữ rất rõ
            pygame.draw.rect(
                text_bg_surf,
                (255, 255, 255, 40),
                text_bg_surf.get_rect(),
                1,
                border_radius=12,
            )
            panel_layer.blit(text_bg_surf, self.text_bg_rect.topleft)

            # Text + scroll (trên nền đen mờ)
            self._draw_text_with_clipping(panel_layer)

            # Scrollbar
            if self.total_text_height > self.text_rect.height:
                pygame.draw.rect(
                    panel_layer,
                    (60, 70, 130),
                    self.scrollbar_rect,
                    border_radius=4,
                )
                if getattr(self, "thumb_visible", True):
                    pygame.draw.rect(
                        panel_layer,
                        (220, 230, 255),
                        self.thumb_rect,
                        border_radius=4,
                    )

            # Áp dụng fade-in
            alpha = int(255 * self.panel_visible_t)
            panel_layer.set_alpha(alpha)
            surface.blit(panel_layer, (0, 0))

        # Back, Music, Toggle luôn vẽ trực tiếp (kể cả khi thu nhỏ)
        self.back_button.draw(surface)
        self.music_button.draw(surface)
        self.toggle_button.draw(surface)
