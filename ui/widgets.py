from __future__ import annotations
from typing import Callable, Tuple
import pygame
from config import BUTTON_COLOR, BUTTON_HOVER, BUTTON_TEXT, ACCENT_COLOR


class Button:
    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        text: str,
        font: pygame.font.Font,
        callback: Callable[[], None],
        *,
        base_color=BUTTON_COLOR,
        hover_color=BUTTON_HOVER,
        text_color=BUTTON_TEXT,
        glow: bool = False,
        glow_color: Tuple[int, int, int] | None = None,
        max_scale: float = 1.05,      # scale khi hover
        hover_speed: float = 8.0,     # tốc độ animation hover
    ):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.callback = callback

        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color

        self.is_hovered = False
        self.hover_t = 0.0  # 0 thì bình thường, 1 thì hover max

        self.glow = glow
        self.glow_color = glow_color or base_color

        self.max_scale = max_scale
        self.hover_speed = hover_speed

        self._render_text()

    def _render_text(self):
        self.text_surf = self.font.render(self.text, True, self.text_color)

    def handle_event(self, event: pygame.event.Event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()

    def update(self, dt: float):
        """Cập nhật animation hover theo thời gian."""
        if self.is_hovered:
            self.hover_t = min(1.0, self.hover_t + dt * self.hover_speed)
        else:
            self.hover_t = max(0.0, self.hover_t - dt * self.hover_speed)

    def _lerp_color(self, c1, c2, t: float):
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

    def draw(self, surface: pygame.Surface):
        t = self.hover_t

        # màu chuyển dần base thì hover
        color = self._lerp_color(self.base_color, self.hover_color, t)

        # scale nhẹ khi hover: 1 thì max_scale
        scale = 1.0 + (self.max_scale - 1.0) * t
        base_rect = self.rect
        new_w = int(base_rect.width * scale)
        new_h = int(base_rect.height * scale)
        draw_rect = pygame.Rect(0, 0, new_w, new_h)
        draw_rect.center = base_rect.center

        if self.glow and t > 0:
            glow_size = (draw_rect.width + 22, draw_rect.height + 22)
            glow_surf = pygame.Surface(glow_size, pygame.SRCALPHA)
            r, g, b = self.glow_color
            glow_alpha = int(90 * t)
            pygame.draw.rect(
                glow_surf,
                (r, g, b, glow_alpha),
                glow_surf.get_rect(),
                border_radius=draw_rect.height // 2 + 10,
            )
            glow_rect = glow_surf.get_rect(center=base_rect.center)
            surface.blit(glow_surf, glow_rect)

        pygame.draw.rect(surface, color, draw_rect, border_radius=18)
        pygame.draw.rect(surface, (0, 0, 0), draw_rect, width=1, border_radius=18)

        text_rect = self.text_surf.get_rect(center=draw_rect.center)
        surface.blit(self.text_surf, text_rect)


class OptionButton(Button):
    def __init__(
        self,
        rect: Tuple[int, int, int, int],
        text: str,
        font: pygame.font.Font,
        callback: Callable[[], None],
        *,
        selected: bool = False,
    ):
        super().__init__(rect, text, font, callback)
        self.selected = selected

    def draw(self, surface: pygame.Surface):
        if self.selected:
            self.base_color = ACCENT_COLOR
            self.text_color = (20, 20, 20)
        else:
            self.base_color = BUTTON_COLOR
            self.text_color = BUTTON_TEXT

        self._render_text()

        t = self.hover_t
        color = self._lerp_color(self.base_color, self.hover_color, t)

        scale = 1.0 + 0.04 * t
        base_rect = self.rect
        new_w = int(base_rect.width * scale)
        new_h = int(base_rect.height * scale)
        draw_rect = pygame.Rect(0, 0, new_w, new_h)
        draw_rect.center = base_rect.center

        border_color = (255, 255, 255) if self.selected else (0, 0, 0)

        pygame.draw.rect(surface, color, draw_rect, border_radius=16)
        pygame.draw.rect(surface, border_color, draw_rect, width=2, border_radius=16)

        text_rect = self.text_surf.get_rect(center=draw_rect.center)
        surface.blit(self.text_surf, text_rect)
