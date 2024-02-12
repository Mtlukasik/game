import pygame
import random

# Initialize Pygame
pygame.init()

# Screen dimensions
screen_width = 800
screen_height = 600

# Colors
black = (0, 0, 0)
white = (255, 255, 255)

# Set up the display
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Shooting Game")

# Player properties
player_width = 40
player_height = 20
player_x = screen_width // 2 - player_width // 2
player_y = screen_height - player_height - 10
player_velocity = 5

# Bullet properties
bullet_width = 5
bullet_height = 10
bullet_velocity = 7
bullets = [] # List to keep track of bullets

# Target properties
target_width = 60
target_height = 20
targets = [] # List to keep track of targets

# Game loop flag
running = True

# Clock to control game frame rate
clock = pygame.time.Clock()

def draw_player(x, y):
    pygame.draw.rect(screen, white, (x, y, player_width, player_height))

def draw_bullet(x, y):
    pygame.draw.rect(screen, white, (x, y, bullet_width, bullet_height))

def draw_target(x, y):
    pygame.draw.rect(screen, white, (x, y, target_width, target_height))

def game_loop():
    global player_x, running
    
    # Main game loop
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        # Key handling
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= player_velocity
        if keys[pygame.K_RIGHT] and player_x < screen_width - player_width:
            player_x += player_velocity
        if keys[pygame.K_SPACE]:
            # Shoot a bullet
            bullets.append([player_x + player_width // 2 - bullet_width // 2, player_y])
        
        # Move bullets
        for bullet in bullets:
            bullet[1] -= bullet_velocity
            if bullet[1] < 0:
                bullets.remove(bullet)
        
        # Generate targets randomly
        if random.randint(1, 20) == 1:
            targets.append([random.randint(0, screen_width - target_width), 0])
        
        # Check for bullet hitting target
        for target in targets:
            target[1] += 1
            for bullet in bullets:
                if bullet[0] in range(target[0], target[0] + target_width) and bullet[1] in range(target[1], target[1] + target_height):
                    bullets.remove(bullet)
                    targets.remove(target)
                    break
        
        # Drawing
        screen.fill(black)
        draw_player(player_x, player_y)
        for bullet in bullets:
            draw_bullet(bullet[0], bullet[1])
        for target in targets:
            draw_target(target[0], target[1])
        
        pygame.display.flip()
        clock.tick(30)

# Run the game loop
game_loop()

# Quit Pygame
pygame.quit()
