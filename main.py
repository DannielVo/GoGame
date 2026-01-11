from __future__ import annotations
import sys
import os
try:
    import pygame  
except ImportError:
    import pygame_ce as pygame  

from config import WINDOW_WIDTH, WINDOW_HEIGHT, FPS
from ui.home_screen import HomeScreen
from ui.setup_screen import SetupScreen
from ui.game_screen import GameScreen
from ui.guide_screen import GuideScreen
from core.game import GameMode
from core.board import Player

class GoApp:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Go")
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        # Fonts
        self.font_title = pygame.font.SysFont("segoeui", 72, bold=True)
        self.font_h1 = pygame.font.SysFont("segoeui", 32, bold=True)
        self.font_body = pygame.font.SysFont("segoeui", 22)
        self.font_small = pygame.font.SysFont("segoeui", 18)

        # Music
        self.music_on = False
        self.click_sound: pygame.mixer.Sound | None = None

        self._init_music()
        self._init_sounds()

        self.current_screen = HomeScreen(self)

    def change_screen(self, name: str, **kwargs):
        if name == "home":
            self.current_screen = HomeScreen(self)
        elif name == "setup":
            self.current_screen = SetupScreen(self)
        elif name == "guide":
            self.current_screen = GuideScreen(self)
        elif name == "game":
            board_size   = kwargs.get("board_size", 19)
            mode         = kwargs.get("mode", GameMode.HUMAN_VS_HUMAN)
            board_style  = kwargs.get("board_style", "wood")
            human_color  = kwargs.get("human_color", Player.BLACK)  

            self.current_screen = GameScreen(
                self,
                board_size=board_size,
                mode=mode,
                board_style=board_style,
                human_color=human_color,  # <-- truyền xuống GameScreen
            )

    def _init_music(self):
        """Load và bắt đầu phát nhạc nền (loop)."""
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        music_path = os.path.join(assets_dir, "music.mp3")  

        try:
            pygame.mixer.init()
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0.45)
            pygame.mixer.music.play(-1)  # loop vô hạn
            self.music_on = True
        except Exception as e:
            print("Không thể khởi tạo nhạc nền:", e)
            self.music_on = False

    def _init_sounds(self):
        """Load hiệu ứng click cho nút."""
        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        click_path = os.path.join(assets_dir, "click.mp3")

        if not os.path.exists(click_path):
            print("Không tìm thấy click.wav, bỏ qua hiệu ứng click.")
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.click_sound = pygame.mixer.Sound(click_path)
            self.click_sound.set_volume(0.6)
        except Exception as e:
            print("Không thể load âm click:", e)
            self.click_sound = None

    def play_click(self):
        """Phát tiếng click khi nhấn nút."""
        if self.click_sound is not None:
            self.click_sound.play()

    def toggle_music(self):
        """Bật/tắt nhạc nền, dùng cho nút Music."""
        if not pygame.mixer.get_init():
            return

        if self.music_on:
            pygame.mixer.music.pause()
            self.music_on = False
        else:
            pygame.mixer.music.unpause()
            self.music_on = True

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.current_screen.handle_event(event)

            self.current_screen.update(dt)
            self.current_screen.draw(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = GoApp()
    app.run()
