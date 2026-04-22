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
"""

import pygame
from game_manager import GameManager


def main():
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1024, 768))
    pygame.display.set_caption("Sausage Man: Legends of Midgard")
    pygame.display.set_icon(pygame.Surface((32, 32)))

    game = GameManager(screen)
    game.run()

    pygame.quit()


if __name__ == "__main__":
    main()
