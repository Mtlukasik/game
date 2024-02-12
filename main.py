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
red = (255, 0, 0)  # Color for text

# Set up the display
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Precision Shooting Game with Display Info")

# Player properties
player_width = 40
player_height = 20
player_x = screen_width // 2 - player_width // 2
player_y = screen_height - player_height - 10
player_velocity = 5

# Bullet properties
bullet_width = 5
bullet_height = 10
bullet_velocity = 10
bullets = []  # List to keep track of bullets

# Target properties
target_width = 60
target_height = 20
target_x = random.randint(0, screen_width - target_width)
target_y = random.randint(50, 100)  # Keep target within a specific range from the top
target_velocity = 3
target_direction = random.choice([-1, 1])  # Target moves left or right initially

# Scoring
score = 0

# Game loop flag
running = True

# Clock to control game frame rate
clock = pygame.time.Clock()

# Font for displaying text
font = pygame.font.SysFont(None, 24)

def draw_text(text, x, y, color=white):
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))

def draw_player(x, y):
    pygame.draw.rect(screen, white, (x, y, player_width, player_height))

def draw_bullet(x, y):
    pygame.draw.rect(screen, white, (x, y, bullet_width, bullet_height))

def draw_target(x, y):
    pygame.draw.rect(screen, white, (x, y, target_width, target_height))

def move_target():
    global target_x, target_direction
    target_x += target_velocity * target_direction
    # Reverse direction upon reaching screen bounds
    if target_x <= 0 or target_x >= screen_width - target_width:
        target_direction *= -1

def reset_target():
    global target_x, target_y, target_direction
    target_x = random.randint(0, screen_width - target_width)
    target_y = random.randint(50, 100)
    target_direction = random.choice([-1, 1])

def calculate_score(bullet, target_center_x):
    global score
    # Score based on distance to target center
    bullet_center_x = bullet[0] + bullet_width // 2
    distance = abs(bullet_center_x - target_center_x)
    score_increment = max(0, (target_width / 2 - distance) / (target_width / 2))
    score += score_increment
def game_loop():
    global player_x, score, running
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player_x > 0:
            player_x -= player_velocity
        if keys[pygame.K_RIGHT] and player_x < screen_width - player_width:
            player_x += player_velocity
        if keys[pygame.K_SPACE]:
            # Append a bullet with an initial minimal vertical distance set to None
            bullets.append([player_x + player_width // 2 - bullet_width // 2, player_y, None])

        for bullet in bullets[:]:
            bullet[1] -= bullet_velocity
            # Check if bullet aligns with target horizontally
            if target_y - 5 <= bullet[1] <= target_y +5:
                # Calculate horizontal distance between bullet and target
                horizontal_distance = abs(bullet[0] - target_x)
                # Update minimal distance if it's smaller or not set
                if bullet[2] is None or horizontal_distance < bullet[2]:
                    bullet[2] = horizontal_distance  # Update minimal distance
                    print(f"Updated minimal distance: {bullet[2]}")

            # Remove bullet if it leaves the screen, and update score based on minimal distance if recorded
            if bullet[1] < 0:
                if bullet[2] is not None:
                    # Increment score based on minimal distance
                    score += - bullet[2]
                    print(f"min(0,-bullet[2]): {min(0,-bullet[2])}")
                bullets.remove(bullet)
            # Bullet hits the target
            elif target_x < bullet[0] < target_x + target_width and target_y < bullet[1] < target_y + target_height:
                # Direct hit can have its own scoring mechanism or use the minimal distance
                score += 100  # Direct hit score, for example
                bullets.remove(bullet)
                reset_target()

        move_target()

        screen.fill(black)
        draw_player(player_x, player_y)
        for bullet in bullets:
            draw_bullet(bullet[0], bullet[1])
        draw_target(target_x, target_y)

        # Display score and object parameters
        draw_text(f"Score: {score:.2f}", 5, 5)
        draw_text(f"Target: ({target_x}, {target_y})", 5, 30)
        for i, bullet in enumerate(bullets):
            draw_text(f"Bullet {i}: ({bullet[0]}, {bullet[1]})", 5, 55 + i*25, red)

        pygame.display.flip()
        clock.tick(30)



game_loop()
pygame.quit()
