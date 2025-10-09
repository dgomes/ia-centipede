import pygame
from collections import deque

LIVE:int = -1

class FrameNavigator:
    def __init__(self, buffer_size:int=100) -> None:
        self.buffer = deque(maxlen=buffer_size)
        self.current_index:int = LIVE
        self.paused:bool = False
        self.has_moved:bool = False

    def add_frame(self, game_state) -> None:
        """Add new frame to buffer"""
        self.buffer.append(game_state)
        if self.current_index == -1:
            return

        # keep a valid index
        self.current_index = max(0,self.current_index-1)

    def go_back(self, times:int = 1) -> bool:
        """Go to previous frame"""
        # try to move buffer to left
        if not self.buffer or (self.current_index == 0):
            return False

        if self.current_index == -1:
            self.current_index = len(self.buffer) - 1
        elif self.current_index > 0:
            self.current_index -= 1

        self.paused = True
        return True



    def go_forward(self, times:int = 1) -> bool:
        """Go to next frame"""
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
            self.paused = False

        return True

    def get_current_frame(self):
        """Get current frame from pointer"""
        if not self.buffer:
            return None
        if -1 <= self.current_index < len(self.buffer):
            # return frame
            return self.buffer[self.current_index]

        return None

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
