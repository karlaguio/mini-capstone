"""
Immune Command: Final Visual Update
A Pygame-based Agent-Based Model (ABM) simulating adaptive immunity, 
viral evolution, and autoimmune constraints using 2D images.
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

# Colors 
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
        # Health in frames (~15 seconds at 60 FPS)
        self.health = 900
        # Lose 1 health per frame
        self.health_decay = 1  
        
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
        # Slightly larger for the central base
        self.radius = 45 
        
        try:
            raw_img = pygame.image.load('tissue.png').convert_alpha()
            self.image = pygame.transform.scale(raw_img, (self.radius * 2, self.radius * 2))
        except FileNotFoundError:
            print("ERROR: Could not find tissue.png. Falling back to shapes.")
            self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(self.image, GREEN, (self.radius, self.radius), self.radius)
            
        self.rect = self.image.get_rect(center=(CENTER_X, CENTER_Y))

# THIS IS THE MAIN GAME LOOP
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
    font = pygame.font.Font('SairaStencil-Medium.ttf', 24)
    large_font = pygame.font.Font('SairaStencil-Medium.ttf', 48)

    all_sprites, pathogens, leukocytes = pygame.sprite.Group(), pygame.sprite.Group(), pygame.sprite.Group()
    tissue = Tissue()

    # State variables
    tissue_health = INITIAL_TISSUE_HEALTH
    destroyed_count = 0
    atp = 100
    current_selected_affinity = 0.5
    # INSTRUCTIONS, START, PLAYING, WON, LOST
    game_state = "INSTRUCTIONS"  

    # UI Options
    options = [
        {"key": pygame.K_1, "val": 0.2, "name": "Type 1 (0.2)"},
        {"key": pygame.K_2, "val": 0.5, "name": "Type 2 (0.5) [DANGER: AUTOIMMUNE]"},
        {"key": pygame.K_3, "val": 0.8, "name": "Type 3 (0.8)"}
    ]

    atp_timer = 0
    spawn_timer = 0
    forbidden_cell_alert_timer = 0  # For showing forbidden cell type message

    instructions_button_rect = pygame.Rect(CENTER_X - 130, SCREEN_HEIGHT - 95, 260, 56)
    start_button_rect = pygame.Rect(CENTER_X - 100, CENTER_Y + 40, 200, 56)
    restart_button_rect = pygame.Rect(CENTER_X - 120, SCREEN_HEIGHT - 50, 240, 56)

    def reset_round_state():
        """Reset all gameplay state for a fresh run."""
        nonlocal tissue, tissue_health, destroyed_count, atp
        nonlocal current_selected_affinity, game_state, atp_timer, spawn_timer, forbidden_cell_alert_timer
        forbidden_cell_alert_timer = 0

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
                            forbidden_cell_alert_timer = 120  # Show alert for 2 seconds at 60 FPS

        if game_state == "PLAYING":
            # Timers
            atp_timer += 1
            if atp_timer >= 30: # 2 ATP per second
                atp = min(MAX_ATP, atp + 1)
                atp_timer = 0
            
            # Forbidden cell alert timer
            if forbidden_cell_alert_timer > 0:
                forbidden_cell_alert_timer -= 1
                
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
        
        # Forbidden cell alert (in-game notification)
        if game_state == "PLAYING" and forbidden_cell_alert_timer > 0:
            alpha = int((forbidden_cell_alert_timer / 120) * 255)  # Fade out effect
            alert_text = font.render("⚠ AUTOIMMUNE! Type 2 damages your tissue!", True, RED)
            alert_surface = pygame.Surface((alert_text.get_width() + 20, alert_text.get_height() + 10), pygame.SRCALPHA)
            pygame.draw.rect(alert_surface, (0, 0, 0, alpha), alert_surface.get_rect(), border_radius=5)
            alert_surface.blit(alert_text, (10, 5))
            screen.blit(alert_surface, (CENTER_X - alert_surface.get_width() // 2, SCREEN_HEIGHT - 120))

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
            win_line1 = large_font.render("TISSUE SAVED!", True, GREEN)
            win_line2 = large_font.render("INFECTION CLEARED.", True, GREEN)
            screen.blit(win_line1, win_line1.get_rect(center=(CENTER_X, CENTER_Y - 40)))
            screen.blit(win_line2, win_line2.get_rect(center=(CENTER_X, CENTER_Y + 10)))
        elif game_state == "LOST":
            # White semi-transparent overlay for entire lost screen
            overlay_surface = pygame.Surface((800, 500), pygame.SRCALPHA)
            pygame.draw.rect(overlay_surface, (255, 255, 255, 220), overlay_surface.get_rect(), border_radius=10)
            screen.blit(overlay_surface, (0, CENTER_Y - 150))
            
            # Title text on two lines for better fit
            title_line1 = large_font.render("SYSTEM FAILURE.", True, RED)
            title_line2 = large_font.render("TISSUE DESTROYED.", True, RED)
            screen.blit(title_line1, title_line1.get_rect(center=(CENTER_X, CENTER_Y - 90)))
            screen.blit(title_line2, title_line2.get_rect(center=(CENTER_X, CENTER_Y - 40)))
            
            # Educational information about game mechanics
            small_font = pygame.font.Font(None, 18)
            extra_small_font = pygame.font.Font(None, 16)
            
            # Title for educational section
            screen.blit(font.render("What Happened: The Immunology Behind Your Loss", True, BLACK), (40, CENTER_Y + 20))
            
            # Stochastic Viral Adaptation (expanded)
            screen.blit(small_font.render("Stochastic Viral Adaptation:", True, GREEN), (50, CENTER_Y + 50))
            screen.blit(extra_small_font.render("Pathogens don't all spawn the same. They arrive with random 'antigen' values (0.0-1.0),", True, BLACK), (70, CENTER_Y + 70))
            screen.blit(extra_small_font.render("creating natural diversity. When your leukocytes destroy them, survivors reproduce with", True, BLACK), (70, CENTER_Y + 85))
            screen.blit(extra_small_font.render("mutated offspring, evolving toward your immune defenses. Adaptation is evolutionary.", True, BLACK), (70, CENTER_Y + 100))
            
            # Affinity Thresholds (expanded)
            screen.blit(small_font.render("Affinity Thresholds (Binding Specificity):", True, GREEN), (50, CENTER_Y + 125))
            screen.blit(extra_small_font.render("Your leukocytes only destroy pathogens when the 'fit' is perfect: |Receptor - Antigen| ≤ 0.15.", True, BLACK), (70, CENTER_Y + 145))
            screen.blit(extra_small_font.render("Type 1 (0.2) targets pathogens near 0.2. Type 3 (0.8) targets near 0.8. Choose wisely!", True, BLACK), (70, CENTER_Y + 160))
            
            # Resource Constraint & Autoimmunity (expanded)
            screen.blit(small_font.render("Resource Constraint & Autoimmunity Risk:", True, GREEN), (50, CENTER_Y + 185))
            screen.blit(extra_small_font.render("ATP is limited. Type 2 (0.5) is dangerous: it damages your own tissue by 3 HP each time", True, BLACK), (70, CENTER_Y + 205))
            screen.blit(extra_small_font.render("deployed! This represents autoimmune disease, your immune system attacking itself.", True, BLACK), (70, CENTER_Y + 220))
            screen.blit(extra_small_font.render(" Balance offense, defense, and the cost of aggression.", True, BLACK), (70, CENTER_Y + 235))
            
            # Restart button (positioned at bottom)
            pygame.draw.rect(screen, GREEN, restart_button_rect, border_radius=10)
            pygame.draw.rect(screen, BLACK, restart_button_rect, 2, border_radius=10)
            restart_text = font.render("RESTART", True, WHITE)
            screen.blit(restart_text, restart_text.get_rect(center=restart_button_rect.center))

        pygame.display.flip()

        # Important for browser runtimes: yield control every frame so the tab stays responsive.
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())