"""
Sausage Man: Legends of Midgard
================================
Main entry point. Run this file to start the game.

Requirements:
    pip install pygame numpy pandas matplotlib seaborn

Controls:
    WASD / Arrow Keys  - Move
    Left Click         - Shoot / Attack
    E                  - Pick up item
    I                  - Open inventory
    ESC                - Pause / Back
    M                  - Toggle sound on/off
"""

import pygame
from game_manager import GameManager


def main():

    pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
    pygame.init()

    if not pygame.mixer.get_init():
        print("[Audio] ไม่พบอุปกรณ์เสียง – เกมจะทำงานโดยไม่มีเสียง")

    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("Sausage Man: Legends of Midgard")
    pygame.display.set_icon(pygame.Surface((32, 32)))

    game = GameManager(screen)
    game.run()

    pygame.quit()


if __name__ == "__main__":
    main()
