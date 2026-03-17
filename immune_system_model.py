"""
Biological Agent-Based Model (ABM) - Immune System Simulation
A Pygame-based strategy game prototype where immune cells intercept pathogens
based on mathematical affinity values.
"""

import pygame
import random
import math

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
CENTER_X = 400
CENTER_Y = 300
FPS = 60

# Difficulty tuning (pathogen pressure)
INITIAL_PATHOGENS = 3
SPAWN_INTERVAL_FRAMES = 180
MAX_ACTIVE_PATHOGENS = 8

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
GREEN = (34, 177, 76)
LIGHT_BLUE = (173, 216, 230)
MEDIUM_BLUE = (100, 149, 237)
DARK_BLUE = (25, 25, 112)
LIGHT_RED = (255, 153, 153)
MEDIUM_RED = (255, 80, 80)
DARK_RED = (180, 0, 0)

# Tissue state
INITIAL_TISSUE_HEALTH = 10
tissue_health = INITIAL_TISSUE_HEALTH
TARGET_DESTROYS_TO_WIN = 20
BINDING_THRESHOLD = 0.2


class Pathogen(pygame.sprite.Sprite):
    """
    Pathogen Agent - Represents invading pathogens in the system.
    
    Visual: Red triangle
    Behavior: Spawns at random edge, moves toward center with Brownian motion
    Property: antigen_type (0.0 - 1.0) - determines interaction with leukocytes
    """
    
    def __init__(self):
        super().__init__()
        
        # Antigen type: A float between 0.0 and 1.0 representing the pathogen's surface markers
        # This determines which leukocytes can bind to and destroy this pathogen
        self.antigen_type = random.uniform(0.0, 1.0)

        # Visual cue for affinity selection:
        # Map antigen values to the nearest receptor band (0.2, 0.5, 0.8)
        # so the player can choose 1/2/3 with strategy instead of guessing.
        affinity_bands = [0.2, 0.5, 0.8]
        nearest_band = min(affinity_bands, key=lambda value: abs(value - self.antigen_type))
        if nearest_band == 0.2:
            self.color = LIGHT_RED
        elif nearest_band == 0.5:
            self.color = MEDIUM_RED
        else:
            self.color = DARK_RED
        
        # Create triangle surface
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        # Draw red triangle pointing upward
        pygame.draw.polygon(self.image, self.color, [(10, 0), (0, 20), (20, 20)])
        
        self.rect = self.image.get_rect()
        
        # Spawn at random edge coordinate
        edge = random.choice(['top', 'bottom', 'left', 'right'])
        if edge == 'top':
            self.rect.x = random.randint(0, SCREEN_WIDTH)
            self.rect.y = 0
        elif edge == 'bottom':
            self.rect.x = random.randint(0, SCREEN_WIDTH)
            self.rect.y = SCREEN_HEIGHT
        elif edge == 'left':
            self.rect.x = 0
            self.rect.y = random.randint(0, SCREEN_HEIGHT)
        else:  # right
            self.rect.x = SCREEN_WIDTH
            self.rect.y = random.randint(0, SCREEN_HEIGHT)
        
        # Movement speed toward center
        self.base_speed = 2.0
        
    def update(self):
        """
        Update pathogen position each frame.
        Moves toward center (400, 300) with Brownian motion jitter.
        """
        # Calculate direction vector toward center
        dx = CENTER_X - self.rect.centerx
        dy = CENTER_Y - self.rect.centery
        
        # Calculate distance to center
        distance = math.sqrt(dx**2 + dy**2)
        
        # Normalize direction vector (avoid division by zero)
        if distance > 0:
            dx_normalized = dx / distance
            dy_normalized = dy / distance
        else:
            dx_normalized = 0
            dy_normalized = 0
        
        # Base movement toward center
        base_movement_x = dx_normalized * self.base_speed
        base_movement_y = dy_normalized * self.base_speed
        
        # Brownian motion: Add random jitter to simulate stochastic movement
        # Jitter is a small random vector added each frame
        jitter_x = random.uniform(-1.5, 1.5)
        jitter_y = random.uniform(-1.5, 1.5)
        
        # Combine directed movement with random walk
        self.rect.x += base_movement_x + jitter_x
        self.rect.y += base_movement_y + jitter_y


class Leukocyte(pygame.sprite.Sprite):
    """
    Leukocyte (White Blood Cell) Agent - Represents immune cells.
    
    Visual: Blue circle
    Behavior: Static placement (does not move)
    Property: receptor_type (0.0 - 1.0) - determines which pathogens it can bind to
    """
    
    def __init__(self, x, y, receptor_type):
        """
        Initialize a leukocyte at a specific position with a receptor type.
        
        Args:
            x (int): X-coordinate position
            y (int): Y-coordinate position
            receptor_type (float): Receptor specificity (0.0 - 1.0)
                                   Must match pathogen's antigen_type for binding
        """
        super().__init__()
        
        # Receptor type: A float between 0.0 and 1.0 representing receptor specificity
        # This determines which pathogens this leukocyte can recognize and destroy
        self.receptor_type = receptor_type

        # Store the exact antigen interval this leukocyte can bind to:
        # |receptor - antigen| < 0.2  ->  antigen in (receptor-0.2, receptor+0.2)
        self.binding_min = max(0.0, self.receptor_type - BINDING_THRESHOLD)
        self.binding_max = min(1.0, self.receptor_type + BINDING_THRESHOLD)

        # Color-code leukocyte by receptor band so the cell color matches 1/2/3 selection.
        # This makes each placed cell's role obvious at a glance.
        affinity_bands = [0.2, 0.5, 0.8]
        nearest_band = min(affinity_bands, key=lambda value: abs(value - self.receptor_type))
        if nearest_band == 0.2:
            self.color = LIGHT_BLUE
        elif nearest_band == 0.5:
            self.color = MEDIUM_BLUE
        else:
            self.color = DARK_BLUE
        
        # Create blue circle surface
        self.radius = 15
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)

        # Fill with receptor color and add outline for contrast.
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius)
        pygame.draw.circle(self.image, BLACK, (self.radius, self.radius), self.radius, 2)
        
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
    
    def update(self):
        """
        Leukocytes are static and do not move.
        This method can be extended later for additional behaviors.
        """
        pass


class Tissue(pygame.sprite.Sprite):
    """
    Central Tissue target that pathogens try to reach.

    Visual: Large green circle at the simulation center
    Behavior: Static object used for collision checks and health loss
    """

    def __init__(self, x, y, radius=40):
        super().__init__()
        self.radius = radius

        # Draw a centered green circle on a transparent surface
        diameter = self.radius * 2
        self.image = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.circle(self.image, GREEN, (self.radius, self.radius), self.radius)

        self.rect = self.image.get_rect()
        self.rect.center = (x, y)

    def update(self):
        """Tissue is static and does not move."""
        pass


def check_affinity(leukocyte, pathogen):
    """
    Calculate the binding affinity between a leukocyte and a pathogen.
    
    This function uses a mathematical model where immune cells have receptors
    that must closely match pathogen antigens for successful binding and destruction.
    
    Mathematical Model:
    - Affinity = |receptor_type - antigen_type|
    - If affinity < 0.2 (20% difference): Strong binding → Pathogen destroyed
    - If affinity >= 0.2: Weak/no binding → Pathogen escapes
    
    This models the "lock and key" mechanism of the adaptive immune system,
    where specificity is crucial for pathogen recognition.
    
    Args:
        leukocyte (Leukocyte): The immune cell checking for binding
        pathogen (Pathogen): The pathogen being evaluated
    
    Returns:
        bool: True if pathogen is destroyed (affinity < 0.2), False otherwise
    """
    # Calculate absolute difference between receptor and antigen
    # This represents how well the receptor "fits" the antigen
    affinity_difference = abs(leukocyte.receptor_type - pathogen.antigen_type)
    
    # If difference is small enough, binding occurs and pathogen is destroyed
    if affinity_difference < BINDING_THRESHOLD:
        return True  # Strong affinity - pathogen destroyed
    else:
        return False  # Weak affinity - pathogen escapes


# Example usage and testing
if __name__ == "__main__":
    # Create display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Immune System ABM - Prototype")
    clock = pygame.time.Clock()
    
    # Create sprite groups
    all_sprites = pygame.sprite.Group()
    pathogens = pygame.sprite.Group()
    leukocytes = pygame.sprite.Group()

    # Add central tissue target (win/loss object)
    tissue = Tissue(CENTER_X, CENTER_Y, radius=40)
    all_sprites.add(tissue)

    # Player-selected receptor type used when placing new leukocytes
    current_selected_affinity = 0.5

    # Track loss state
    game_over = False
    game_won = False
    destroyed_count = 0

    # Debug overlay: show exact antigen values above pathogens
    show_antigen_labels = False

    # UI layout for receptor selection squares at screen bottom
    ui_square_size = 40
    ui_gap = 15
    ui_y = SCREEN_HEIGHT - ui_square_size - 15
    ui_start_x = 20

    affinity_options = [
        {"key": pygame.K_1, "value": 0.2, "color": LIGHT_BLUE},
        {"key": pygame.K_2, "value": 0.5, "color": MEDIUM_BLUE},
        {"key": pygame.K_3, "value": 0.8, "color": DARK_BLUE},
    ]

    option_rects = []
    for index, option in enumerate(affinity_options):
        rect_x = ui_start_x + index * (ui_square_size + ui_gap)
        option_rects.append(pygame.Rect(rect_x, ui_y, ui_square_size, ui_square_size))
    
    # Spawn initial pathogens (reduced to make early game manageable)
    for _ in range(INITIAL_PATHOGENS):
        pathogen = Pathogen()
        pathogens.add(pathogen)
        all_sprites.add(pathogen)
    
    # Game loop
    running = True
    spawn_timer = 0
    
    while running:
        clock.tick(FPS)
        
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                # Restart key: clears board and restores tissue health
                if event.key == pygame.K_r:
                    tissue_health = INITIAL_TISSUE_HEALTH
                    game_over = False
                    game_won = False
                    destroyed_count = 0

                    # Remove all existing pathogens and placed leukocytes
                    pathogens.empty()
                    leukocytes.empty()

                    # Keep only tissue in the all_sprites group, then re-seed pathogens
                    all_sprites.empty()
                    all_sprites.add(tissue)

                    for _ in range(INITIAL_PATHOGENS):
                        pathogen = Pathogen()
                        pathogens.add(pathogen)
                        all_sprites.add(pathogen)

                    # Reset spawn timer so cadence restarts cleanly
                    spawn_timer = 0

                # Debug toggle for exact pathogen antigen labels
                elif event.key == pygame.K_d:
                    show_antigen_labels = not show_antigen_labels

                # Affinity hotkeys: 1 -> 0.2, 2 -> 0.5, 3 -> 0.8
                for option in affinity_options:
                    if event.key == option["key"]:
                        current_selected_affinity = option["value"]
                        break
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not game_over:
                # Left click places a static leukocyte at the mouse position
                mouse_x, mouse_y = event.pos
                new_leukocyte = Leukocyte(mouse_x, mouse_y, current_selected_affinity)
                leukocytes.add(new_leukocyte)
                all_sprites.add(new_leukocyte)
        
        # Spawn new pathogens periodically
        spawn_timer += 1
        if spawn_timer > SPAWN_INTERVAL_FRAMES and not game_over and not game_won:
            # Only spawn if below active-pathogen cap
            if len(pathogens) < MAX_ACTIVE_PATHOGENS:
                pathogen = Pathogen()
                pathogens.add(pathogen)
                all_sprites.add(pathogen)
            spawn_timer = 0
        
        # Update all sprites
        all_sprites.update()

        # Check pathogen collision with central tissue
        # Distance math: if center distance <= tissue radius, pathogen reached tissue
        for pathogen in list(pathogens):
            dx = pathogen.rect.centerx - tissue.rect.centerx
            dy = pathogen.rect.centery - tissue.rect.centery
            distance_to_tissue_center = math.sqrt(dx**2 + dy**2)

            if distance_to_tissue_center <= tissue.radius:
                pathogen.kill()
                tissue_health -= 1

                # Loss condition: when health reaches 0, stop spawning and show Game Over
                if tissue_health <= 0:
                    tissue_health = 0
                    game_over = True
        
        # Check for collisions and affinity
        for leukocyte in leukocytes:
            # Check collision with pathogens
            hit_pathogens = pygame.sprite.spritecollide(leukocyte, pathogens, False)
            for pathogen in hit_pathogens:
                # Check if affinity allows binding
                if check_affinity(leukocyte, pathogen):
                    # Pathogen destroyed!
                    pathogen.kill()
                    all_sprites.remove(pathogen)
                    destroyed_count += 1

                    # Win condition: destroy enough pathogens before tissue health reaches zero
                    if destroyed_count >= TARGET_DESTROYS_TO_WIN:
                        game_won = True
                    print(f"Pathogen destroyed! Leukocyte receptor: {leukocyte.receptor_type:.2f}, "
                          f"Pathogen antigen: {pathogen.antigen_type:.2f}, "
                          f"Affinity: {abs(leukocyte.receptor_type - pathogen.antigen_type):.2f}")
        
        # Draw everything
        screen.fill(WHITE)
        all_sprites.draw(screen)
        
        # Display HUD info
        font = pygame.font.Font(None, 24)
        title_font = pygame.font.Font(None, 36)

        pathogen_count_text = font.render(f"Pathogens: {len(pathogens)}", True, BLACK)
        screen.blit(pathogen_count_text, (10, 10))

        tissue_health_text = font.render(f"Tissue Health: {tissue_health}", True, BLACK)
        screen.blit(tissue_health_text, (10, 35))

        selected_text = font.render(f"Selected Receptor: {current_selected_affinity:.1f}", True, BLACK)
        screen.blit(selected_text, (10, 60))

        win_progress_text = font.render(f"Destroyed: {destroyed_count}/{TARGET_DESTROYS_TO_WIN}", True, BLACK)
        screen.blit(win_progress_text, (10, 85))

        # Draw affinity selection UI squares
        for index, option in enumerate(affinity_options):
            rect = option_rects[index]
            pygame.draw.rect(screen, option["color"], rect)

            # Highlight currently selected receptor option
            border_color = BLACK
            border_width = 4 if option["value"] == current_selected_affinity else 2
            pygame.draw.rect(screen, border_color, rect, border_width)

            key_label = font.render(str(index + 1), True, WHITE)
            key_label_rect = key_label.get_rect(center=rect.center)
            screen.blit(key_label, key_label_rect)

        ui_help_text = font.render("1/2/3 select receptor, Click place cell, R restart", True, BLACK)
        screen.blit(ui_help_text, (210, ui_y + 10))

        # Affinity legend for pathogen colors (nearest match guidance)
        legend_text = font.render("Pathogen shades: Light = 0.2  Medium = 0.5  Dark = 0.8", True, BLACK)
        screen.blit(legend_text, (210, ui_y - 18))

        debug_text = font.render(f"D: Antigen Labels {'ON' if show_antigen_labels else 'OFF'}", True, BLACK)
        screen.blit(debug_text, (10, 110))

        # Optional debug overlay: exact antigen values above each pathogen.
        # This makes the affinity math explicit so players can learn the mapping.
        if show_antigen_labels:
            label_font = pygame.font.Font(None, 18)
            for pathogen in pathogens:
                antigen_label = label_font.render(f"{pathogen.antigen_type:.2f}", True, BLACK)
                label_rect = antigen_label.get_rect(center=(pathogen.rect.centerx, pathogen.rect.top - 8))
                screen.blit(antigen_label, label_rect)

        # Show each leukocyte's receptor and capture interval directly above it.
        # Example: R0.5 [0.3-0.7] means this cell destroys pathogens with antigen in that range.
        leukocyte_label_font = pygame.font.Font(None, 18)
        for leukocyte in leukocytes:
            range_text = (
                f"R{leukocyte.receptor_type:.1f} "
                f"[{leukocyte.binding_min:.1f}-{leukocyte.binding_max:.1f}]"
            )
            leukocyte_label = leukocyte_label_font.render(range_text, True, BLACK)
            leukocyte_label_rect = leukocyte_label.get_rect(
                center=(leukocyte.rect.centerx, leukocyte.rect.top - 10)
            )
            screen.blit(leukocyte_label, leukocyte_label_rect)

        if game_over:
            game_over_text = title_font.render("GAME OVER", True, RED)
            game_over_rect = game_over_text.get_rect(center=(CENTER_X, CENTER_Y - 70))
            screen.blit(game_over_text, game_over_rect)
        elif game_won:
            win_text = title_font.render("YOU WIN", True, GREEN)
            win_rect = win_text.get_rect(center=(CENTER_X, CENTER_Y - 70))
            screen.blit(win_text, win_rect)
        
        pygame.display.flip()
    
    pygame.quit()
