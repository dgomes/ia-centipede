import pygame
from collections import deque

LIVE:int = -1
NAVIGATOR_PANEL_WIDTH = 200

def draw_navigator_panel(display,SCALE, WIDTH, HEIGHT):
    x = int(SCALE * WIDTH) + 10

    panel_font = pygame.font.Font(None, 24)
    pygame.draw.rect(display, (40, 40, 40), (int(SCALE * WIDTH), 0, 180, int(SCALE * HEIGHT)))

    controls = [
        "Controls:",
        "<- go back",
        "-> go forward",
        "SPACE Pause/Replay",
        "Enter  Go live",
    ]

    y = 20
    for line in controls:
        if line:
            text = panel_font.render(line, True, (255, 255, 255))  # White text
            display.blit(text, (x, y))
        y += 30

class FrameNavigator:
    def __init__(self, buffer_size:int=100) -> None:
        self.buffer = deque(maxlen=buffer_size)
        self.current_index:int = LIVE
        self.isPaused:bool = False
        self.has_moved:bool = False

    def add_frame(self, game_state) -> None:
        """Add new frame to buffer"""
        start = len(self.buffer)
        self.buffer.append(game_state)
        end = len(self.buffer)
        if self.current_index != -1 and (start == end):
            self.current_index = max(0,self.current_index-1)

    def go_back(self, times:int = 1) -> bool:
        """Go to previous frame"""
        # TODO: use times
        # try to move buffer to left
        if not self.buffer or (self.current_index == 0):
            return False

        if self.current_index == -1:
            self.current_index = len(self.buffer) - 1
        elif self.current_index > 0:
            self.current_index -= 1

        self.isPaused = True
        return True

    def go_forward(self, times:int = 1) -> bool:
        """Go to next frame"""
        # TODO: use times
        # try to move buffer to right
        if not self.buffer:
            return False

        if self.current_index == -1:
            return False # live

        if self.current_index < len(self.buffer) -1:
            self.current_index += 1

        else:
            # back to live
            self.current_index = -1
            self.isPaused = False

        return True

    def get_current_frame(self):
        """Get current frame from pointer"""
        if not self.buffer:
            return None
        if -1 <= self.current_index < len(self.buffer):
            # return frame
            i = self.current_index
            if not (self.isPaused or self.is_live()):
                self.current_index+=1
            return self.buffer[i]

        return None

    def toggle_pause(self):
        """Toggle pause mode"""
        if self.current_index == -1:
            self.current_index = len(self.buffer) - 1

        self.isPaused = not self.isPaused

    def pause(self):
        """Pause the process"""

        if not self.buffer:
            return None

        self.current_index = len(self.buffer) - 1

    def is_live(self) -> bool:
        """Check if the navigator is live"""
        if not self.buffer or self.current_index >= 0:
            return False
        return True

    def go_live(self) -> bool:
        """Set navigator to live"""
        if not self.buffer:
            return False
        self.current_index = -1
        return True

    def get_info(self) -> str:
        if self.isPaused:
            return "Paused"
        if self.current_index == -1:
            return "Live"
        return "Replay"
