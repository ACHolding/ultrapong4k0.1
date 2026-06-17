#!/usr/bin/env python3.14
# -*- coding: utf-8 -*-
# files=off | pr
"""ultrapong 0.1 my take — Python 3.14 + pygame-ce, procedural audio, 60 FPS."""

WINDOW_TITLE = "pong my take 0.1"

import array
import math
import os
import random
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
import pygame

# --- Initialization ---
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=256)

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption(WINDOW_TITLE)

clock = pygame.time.Clock()
FPS = 60

# --- Colors (Synthwave / Arcade Theme) ---
BG_COLOR = (12, 8, 24)
UI_WHITE = (255, 255, 255)
UI_NEON_BLUE = (0, 240, 255)
UI_NEON_PINK = (255, 0, 127)
UI_GRAY = (60, 60, 80)

# --- Fonts ---
font_logo = pygame.font.SysFont("Impact", 80)
font_large = pygame.font.SysFont("Arial", 64, bold=True)
font_medium = pygame.font.SysFont("Arial", 32, bold=True)
font_small = pygame.font.SysFont("Arial", 20)

# --- Procedural Audio Generation ---
def make_sound(frequency, duration, volume=0.4, sweep=0):
    sample_rate = 44100
    num_samples = int(sample_rate * duration)
    samples = array.array('h')
    for i in range(num_samples):
        t = float(i) / sample_rate
        current_freq = frequency + (sweep * t)
        env = math.exp(-8.0 * t)
        value = int(32267 * volume * env * math.sin(2 * math.pi * current_freq * t))
        samples.append(value)
    return pygame.mixer.Sound(buffer=samples.tobytes())

sfx_hit = make_sound(700, 0.05, sweep=100)
sfx_score = make_sound(200, 0.3, sweep=-50)
sfx_select = make_sound(900, 0.03)

# --- Game Setup ---
WIN_SCORE = 5
STATE = "MENU"
MENU_OPTIONS = ["PLAY GAME", "EXIT GAME"]
menu_index = 0

PADDLE_W, PADDLE_H = 15, 90
BALL_SIZE = 12

# Left player, Right AI
player_paddle = pygame.Rect(40, HEIGHT//2 - PADDLE_H//2, PADDLE_W, PADDLE_H)
ai_paddle = pygame.Rect(WIDTH - 40 - PADDLE_W, HEIGHT//2 - PADDLE_H//2, PADDLE_W, PADDLE_H)
ball = pygame.Rect(WIDTH//2 - BALL_SIZE//2, HEIGHT//2 - BALL_SIZE//2, BALL_SIZE, BALL_SIZE)

player_score = 0
ai_score = 0
ball_dx, ball_dy = 5, 5

def reset_ball(dir_x):
    global ball, ball_dx, ball_dy
    ball.center = (WIDTH//2, HEIGHT//2)
    ball_dx = 5 * dir_x
    ball_dy = random.choice([-4, -3, 3, 4])

def reset_game():
    global player_score, ai_score
    player_score = 0
    ai_score = 0
    player_paddle.y = HEIGHT//2 - PADDLE_H//2
    ai_paddle.y = HEIGHT//2 - PADDLE_H//2
    reset_ball(random.choice([-1, 1]))

def draw_text(text, font, color, x, y, center=False):
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center: rect.center = (x, y)
    else: rect.topleft = (x, y)
    screen.blit(surf, rect)

# --- Main Loop ---
running = True
while running:
    # 1. Events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.KEYDOWN:
            if STATE == "MENU":
                if event.key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
                    menu_index = 1 - menu_index  # Toggle between 0 and 1
                    sfx_select.play()
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    sfx_select.play()
                    if MENU_OPTIONS[menu_index] == "PLAY GAME":
                        reset_game()
                        STATE = "PLAYING"
                    else:
                        running = False
                        
            elif STATE == "GAMEOVER":
                if event.key == pygame.K_y:
                    sfx_select.play()
                    reset_game()
                    STATE = "PLAYING"
                elif event.key == pygame.K_n:
                    sfx_select.play()
                    running = False

    # 2. Logic
    if STATE == "PLAYING":
        # Player Movement (W/S or UP/DOWN)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            player_paddle.y -= 7
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            player_paddle.y += 7
        player_paddle.clamp_ip(screen.get_rect())

        # Simple AI Movement (Right Side)
        if ai_paddle.centery < ball.centery - 10:
            ai_paddle.y += 5
        elif ai_paddle.centery > ball.centery + 10:
            ai_paddle.y -= 5
        ai_paddle.clamp_ip(screen.get_rect())

        # Ball Movement
        ball.x += ball_dx
        ball.y += ball_dy

        # Wall Collisions
        if ball.top <= 0 or ball.bottom >= HEIGHT:
            ball_dy *= -1
            sfx_hit.play()

        # Paddle Collisions
        if ball.colliderect(player_paddle) and ball_dx < 0:
            ball_dx = abs(ball_dx) + 0.4  # Speed up slightly
            ball_dy += random.uniform(-1.5, 1.5)
            sfx_hit.play()
        elif ball.colliderect(ai_paddle) and ball_dx > 0:
            ball_dx = -(abs(ball_dx) + 0.4)
            ball_dy += random.uniform(-1.5, 1.5)
            sfx_hit.play()

        # Score Limits
        if ball.left <= 0:
            ai_score += 1
            sfx_score.play()
            if ai_score >= WIN_SCORE: STATE = "GAMEOVER"
            else: reset_ball(1)
        elif ball.right >= WIDTH:
            player_score += 1
            sfx_score.play()
            if player_score >= WIN_SCORE: STATE = "GAMEOVER"
            else: reset_ball(-1)

    # 3. Rendering
    screen.fill(BG_COLOR)

    if STATE == "MENU":
        # Logo rendering
        draw_text("ULTRAPONG", font_logo, UI_NEON_PINK, WIDTH//2, 160, center=True)
        
        # Options
        for i, option in enumerate(MENU_OPTIONS):
            color = UI_NEON_BLUE if i == menu_index else UI_GRAY
            text = f"> {option} <" if i == menu_index else option
            draw_text(text, font_medium, color, WIDTH//2, 340 + i * 60, center=True)

    elif STATE == "PLAYING":
        # Center line
        for y in range(0, HEIGHT, 30):
            pygame.draw.rect(screen, UI_GRAY, (WIDTH//2 - 2, y, 4, 15))
        
        # UI Scores
        draw_text(str(player_score), font_large, UI_NEON_BLUE, WIDTH//4, 40, center=True)
        draw_text(str(ai_score), font_large, UI_NEON_PINK, 3 * WIDTH//4, 40, center=True)
        
        # Entities
        pygame.draw.rect(screen, UI_NEON_BLUE, player_paddle, border_radius=4)
        pygame.draw.rect(screen, UI_NEON_PINK, ai_paddle, border_radius=4)
        pygame.draw.rect(screen, UI_WHITE, ball, border_radius=2)

    elif STATE == "GAMEOVER":
        winner = "PLAYER 1" if player_score >= WIN_SCORE else "AI"
        color = UI_NEON_BLUE if winner == "PLAYER 1" else UI_NEON_PINK
        
        draw_text(f"{winner} WINS!", font_large, color, WIDTH//2, HEIGHT//2 - 100, center=True)
        draw_text("PLAY AGAIN? (Y / N)", font_medium, UI_WHITE, WIDTH//2, HEIGHT//2, center=True)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()