"""
Immune Command: Final Visual Update
A Pygame-based Agent-Based Model (ABM) simulating adaptive immunity, 
viral evolution, and autoimmune constraints using 2D image sprites.
"""

import pygame
import random
import math
import os
import asyncio

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CENTER_X = 400
CENTER_Y = 300
FPS = 60
BINDING_THRESHOLD = 0.15 # Strict threshold to require strategy

# Colors (Still used for text/UI)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 177, 76)
RED = (255, 0, 0)

# Game State Variables
INITIAL_TISSUE_HEALTH = 20
TARGET_DESTROYS_TO_WIN = 10
MAX_ATP = 200
CELL_COST = 10

class Pathogen(pygame.sprite.Sprite):
    """
    Invading pathogen. Uses sprite images based on mutated antigen type.
    """
    def __init__(self, parent_antigen=None):
        super().__init__()
        
        # Adaptation Mechanic: Mutate from parent or spawn randomly
        if parent_antigen is not None:
            mutation = random.uniform(-0.1, 0.1)
            self.antigen_type = max(0.0, min(1.0, parent_antigen + mutation))
        else:
            self.antigen_type = random.uniform(0.0, 1.0)

        # Map continuous antigen to the closest visual sprite category
        affinity_bands = [0.2, 0.5, 0.8]
        nearest_band = min(affinity_bands, key=lambda val: abs(val - self.antigen_type))
        
        if nearest_band == 0.2:
            img_path = 'pathogen_1.png'
        elif nearest_band == 0.5:
            img_path = 'pathogen_2.png'
        else:
            img_path = 'pathogen_3.png'
            
        # Load and scale the pathogen image
        try:
            raw_img = pygame.image.load(img_path).convert_alpha()
            self.image = pygame.transform.scale(raw_img, (24, 24))
        except FileNotFoundError:
            print(f"ERROR: Could not find {img_path}. Falling back to shapes.")
            self.image = pygame.Surface((24, 24), pygame.SRCALPHA)
            pygame.draw.polygon(self.image, RED, [(12, 0), (0, 24), (24, 24)])

        self.rect = self.image.get_rect()
        
        # Spawn at random edge
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top': self.rect.center = (random.randint(0, SCREEN_WIDTH), -20)
        elif edge == 'bottom': self.rect.center = (random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT + 20)
        elif edge == 'left': self.rect.center = (-20, random.randint(0, SCREEN_HEIGHT))
        else: self.rect.center = (SCREEN_WIDTH + 20, random.randint(0, SCREEN_HEIGHT))
        
        self.base_speed = 1.5

    def update(self):
        # Directed random walk (Brownian motion toward center)
        dx, dy = CENTER_X - self.rect.centerx, CENTER_Y - self.rect.centery
        dist = math.hypot(dx, dy)
        if dist > 0:
            dx, dy = dx / dist, dy / dist
            
        jitter_x, jitter_y = random.uniform(-1.5, 1.5), random.uniform(-1.5, 1.5)
        self.rect.x += (dx * self.base_speed) + jitter_x
        self.rect.y += (dy * self.base_speed) + jitter_y

class Leukocyte(pygame.sprite.Sprite):
    """Static immune cell placed by the player using custom sprites."""
    def __init__(self, x, y, receptor_type):
        super().__init__()
        self.receptor_type = receptor_type
        self.radius = 15
        self.health = 900  # Health in frames (~15 seconds at 60 FPS)
        self.health_decay = 1  # Lose 1 health per frame
        
        # Select appropriate image based on selected receptor
        if self.receptor_type == 0.2:
            img_path = 'leukocyte_1.png'
        elif self.receptor_type == 0.5:
            img_path = 'leukocyte_2.png'
        else:
            img_path = 'leukocyte_3.png'

        try:
            raw_img = pygame.image.load(img_path).convert_alpha()
            self.image = pygame.transform.scale(raw_img, (self.radius * 2, self.radius * 2))
        except FileNotFoundError:
            print(f"ERROR: Could not find {img_path}. Falling back to shapes.")
            self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (0, 0, 255), (self.radius, self.radius), self.radius)
            
        self.rect = self.image.get_rect(center=(x, y))
    
    def update(self):
        """Decrease health over time and remove if health depleted."""
        self.health -= self.health_decay
        if self.health <= 0:
            self.kill()

class Tissue(pygame.sprite.Sprite):
    """Central tissue to defend, using custom sprite."""
    def __init__(self):
        super().__init__()
        self.radius = 45 # Slightly larger for the central base
        
        try:
            raw_img = pygame.image.load('tissue.png').convert_alpha()
            self.image = pygame.transform.scale(raw_img, (self.radius * 2, self.radius * 2))
        except FileNotFoundError:
            print("ERROR: Could not find tissue.png. Falling back to shapes.")
            self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, GREEN, (self.radius, self.radius), self.radius)
            
        self.rect = self.image.get_rect(center=(CENTER_X, CENTER_Y))

# --- Main Game Loop ---
async def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Immune Command - Final Capstone")
    clock = pygame.time.Clock()
    
    # Try to load custom background, else just use a color
    try:
        background_img = pygame.image.load('background.png').convert()
        background_img = pygame.transform.scale(background_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    except FileNotFoundError:
        print("ERROR: Could not find background.png. Using white background.")
        background_img = None

    # UI Fonts
    # Tip: If you downloaded a cute font, change 'None' to 'YourFontName.ttf'
    font = pygame.font.Font(None, 24)
    large_font = pygame.font.Font(None, 48)

    all_sprites, pathogens, leukocytes = pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()
    tissue = Tissue()

    # State variables
    tissue_health = INITIAL_TISSUE_HEALTH
    destroyed_count = 0
    atp = 100
    current_selected_affinity = 0.5
    game_state = "INSTRUCTIONS"  # INSTRUCTIONS, START, PLAYING, WON, LOST

    # UI Options
    options = [
        {"key": pygame.K_1, "val": 0.2, "name": "Type 1 (0.2)"},
        {"key": pygame.K_2, "val": 0.5, "name": "Type 2 (0.5) [DANGER: AUTOIMMUNE]"},
        {"key": pygame.K_3, "val": 0.8, "name": "Type 3 (0.8)"}
    ]

    atp_timer = 0
    spawn_timer = 0

    instructions_button_rect = pygame.Rect(CENTER_X - 130, SCREEN_HEIGHT - 95, 260, 56)
    start_button_rect = pygame.Rect(CENTER_X - 100, CENTER_Y + 40, 200, 56)
    restart_button_rect = pygame.Rect(CENTER_X - 120, CENTER_Y + 50, 240, 56)

    def reset_round_state():
        """Reset all gameplay state for a fresh run."""
        nonlocal tissue, tissue_health, destroyed_count, atp
        nonlocal current_selected_affinity, game_state, atp_timer, spawn_timer

        all_sprites.empty()
        pathogens.empty()
        leukocytes.empty()

        tissue = Tissue()
        all_sprites.add(tissue)

        tissue_health = INITIAL_TISSUE_HEALTH
        destroyed_count = 0
        atp = 100
        current_selected_affinity = 0.5
        atp_timer = 0
        spawn_timer = 0
        game_state = "PLAYING"

        for _ in range(2):
            p = Pathogen()
            pathogens.add(p)
            all_sprites.add(p)

    while True:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if game_state == "INSTRUCTIONS" and instructions_button_rect.collidepoint(event.pos):
                    game_state = "START"
                    continue
                if game_state == "START" and start_button_rect.collidepoint(event.pos):
                    reset_round_state()
                    continue
                if game_state == "LOST" and restart_button_rect.collidepoint(event.pos):
                    reset_round_state()
                    continue
            
            if game_state == "PLAYING":
                if event.type == pygame.KEYDOWN:
                    for opt in options:
                        if event.key == opt["key"]: current_selected_affinity = opt["val"]
                
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if atp >= CELL_COST:
                        atp -= CELL_COST
                        new_cell = Leukocyte(event.pos[0], event.pos[1], current_selected_affinity)
                        leukocytes.add(new_cell); all_sprites.add(new_cell)
                        
                        # AUTOIMMUNITY MECHANIC: Tissue is 0.5. Placing 0.5 damages tissue.
                        if current_selected_affinity == 0.5:
                            tissue_health -= 3
                            print("AUTOIMMUNE DAMAGE: Placed forbidden cell type!")

        if game_state == "PLAYING":
            # Timers
            atp_timer += 1
            if atp_timer >= 30: # 2 ATP per second
                atp = min(MAX_ATP, atp + 1)
                atp_timer = 0
                
            spawn_timer += 1
            if spawn_timer >= 150: # New pathogen every 2.5 seconds
                p = Pathogen()
                pathogens.add(p); all_sprites.add(p)
                spawn_timer = 0

            all_sprites.update()

            # Pathogen hits tissue
            for p in list(pathogens):
                if math.hypot(p.rect.centerx - CENTER_X, p.rect.centery - CENTER_Y) <= tissue.radius:
                    p.kill()
                    tissue_health -= 1
                    # VIRAL ADAPTATION: Successful pathogen spawns mutated offspring
                    for _ in range(2):
                        offspring = Pathogen(parent_antigen=p.antigen_type)
                        pathogens.add(offspring); all_sprites.add(offspring)

            # Leukocyte vs Pathogen
            for cell in leukocytes:
                hit_list = pygame.sprite.spritecollide(cell, pathogens, False)
                for p in hit_list:
                    if abs(cell.receptor_type - p.antigen_type) <= BINDING_THRESHOLD:
                        p.kill()
                        destroyed_count += 1

            # Win/Loss Check
            if tissue_health <= 0: game_state = "LOST"
            elif destroyed_count >= TARGET_DESTROYS_TO_WIN: game_state = "WON"

        # Drawing: Use background image if available, else solid color
        if background_img:
            screen.blit(background_img, (0, 0))
        else:
            screen.fill(WHITE)
            
        all_sprites.draw(screen)

        # HUD and overlays
        if game_state in ("PLAYING", "WON", "LOST"):
            hud_bg = pygame.Surface((SCREEN_WIDTH, 65))
            hud_bg.set_alpha(200)
            hud_bg.fill(WHITE)
            screen.blit(hud_bg, (0, 0))

            screen.blit(font.render(f"Health: {tissue_health}  |  ATP: {atp}/{MAX_ATP}  |  Kills: {destroyed_count}/{TARGET_DESTROYS_TO_WIN}", True, BLACK), (10, 10))
            screen.blit(font.render(f"Selected: {current_selected_affinity} (Cost: {CELL_COST} ATP)", True, BLACK), (10, 35))

            help_bg = pygame.Surface((SCREEN_WIDTH, 30))
            help_bg.set_alpha(200)
            help_bg.fill(WHITE)
            screen.blit(help_bg, (0, SCREEN_HEIGHT - 30))
            screen.blit(font.render("Press 1, 2, 3 to select cell type. Click to place.", True, BLACK), (10, SCREEN_HEIGHT - 25))

        if game_state == "INSTRUCTIONS":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 210))
            screen.blit(overlay, (0, 0))

            screen.blit(large_font.render("HOW TO PLAY", True, BLACK), (CENTER_X - 135, 45))
            screen.blit(font.render("1) Press 1, 2, or 3 to select a leukocyte receptor type.", True, BLACK), (80, 115))
            screen.blit(font.render("2) Click to place leukocytes and intercept incoming pathogens.", True, BLACK), (80, 145))
            screen.blit(font.render("3) Protect the tissue in the center until you reach the kill target.", True, BLACK), (80, 175))
            screen.blit(font.render("Warning: Type 2 (0.5) costs autoimmunity damage to tissue.", True, RED), (80, 205))

            screen.blit(font.render("Immunology Fun Facts", True, GREEN), (80, 255))
            screen.blit(font.render("- Neutrophils are first responders and can trap microbes in NETs.", True, BLACK), (80, 285))
            screen.blit(font.render("- B cells create antibodies that bind specific antigens.", True, BLACK), (80, 315))
            screen.blit(font.render("- Memory cells help the immune system respond faster next time.", True, BLACK), (80, 345))
            screen.blit(font.render("- Inflammation is protective, but too much can damage tissue.", True, BLACK), (80, 375))

            pygame.draw.rect(screen, GREEN, instructions_button_rect, border_radius=10)
            pygame.draw.rect(screen, BLACK, instructions_button_rect, 2, border_radius=10)
            continue_text = font.render("CONTINUE TO START", True, WHITE)
            screen.blit(continue_text, continue_text.get_rect(center=instructions_button_rect.center))

        if game_state == "START":
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((255, 255, 255, 185))
            screen.blit(overlay, (0, 0))

            screen.blit(large_font.render("IMMUNE COMMAND", True, BLACK), (CENTER_X - 165, CENTER_Y - 90))
            screen.blit(font.render("Defend the central tissue from pathogens.", True, BLACK), (CENTER_X - 165, CENTER_Y - 40))

            pygame.draw.rect(screen, GREEN, start_button_rect, border_radius=10)
            pygame.draw.rect(screen, BLACK, start_button_rect, 2, border_radius=10)
            start_text = font.render("START", True, WHITE)
            screen.blit(start_text, start_text.get_rect(center=start_button_rect.center))

        if game_state == "WON":
            screen.blit(large_font.render("TISSUE SAVED! INFECTION CLEARED.", True, GREEN), (100, CENTER_Y - 20))
        elif game_state == "LOST":
            screen.blit(large_font.render("SYSTEM FAILURE. TISSUE DESTROYED.", True, RED), (80, CENTER_Y - 40))
            pygame.draw.rect(screen, GREEN, restart_button_rect, border_radius=10)
            pygame.draw.rect(screen, BLACK, restart_button_rect, 2, border_radius=10)
            restart_text = font.render("RESTART", True, WHITE)
            screen.blit(restart_text, restart_text.get_rect(center=restart_button_rect.center))

        pygame.display.flip()

        # Important for browser runtimes: yield control every frame so the tab stays responsive.
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())