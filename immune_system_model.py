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

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)


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
        
        # Create triangle surface
        self.image = pygame.Surface((20, 20), pygame.SRCALPHA)
        # Draw red triangle pointing upward
        pygame.draw.polygon(self.image, RED, [(10, 0), (0, 20), (20, 20)])
        
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
        
        # Create blue circle surface
        self.radius = 15
        self.image = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(self.image, BLUE, (self.radius, self.radius), self.radius)
        
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
    
    def update(self):
        """
        Leukocytes are static and do not move.
        This method can be extended later for additional behaviors.
        """
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
    
    # Binding threshold: 0.2 represents the maximum difference for successful binding
    # In biological terms, this is the "specificity threshold"
    BINDING_THRESHOLD = 0.2
    
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
    
    # Place some leukocytes with different receptor types
    leukocyte1 = Leukocyte(200, 300, 0.3)
    leukocyte2 = Leukocyte(400, 300, 0.5)
    leukocyte3 = Leukocyte(600, 300, 0.8)
    
    leukocytes.add(leukocyte1, leukocyte2, leukocyte3)
    all_sprites.add(leukocyte1, leukocyte2, leukocyte3)
    
    # Spawn initial pathogens
    for _ in range(5):
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
        
        # Spawn new pathogens periodically
        spawn_timer += 1
        if spawn_timer > 120:  # Every 2 seconds
            pathogen = Pathogen()
            pathogens.add(pathogen)
            all_sprites.add(pathogen)
            spawn_timer = 0
        
        # Update all sprites
        all_sprites.update()
        
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
                    print(f"Pathogen destroyed! Leukocyte receptor: {leukocyte.receptor_type:.2f}, "
                          f"Pathogen antigen: {pathogen.antigen_type:.2f}, "
                          f"Affinity: {abs(leukocyte.receptor_type - pathogen.antigen_type):.2f}")
        
        # Draw everything
        screen.fill(WHITE)
        all_sprites.draw(screen)
        
        # Display info
        font = pygame.font.Font(None, 24)
        pathogen_count_text = font.render(f"Pathogens: {len(pathogens)}", True, BLACK)
        screen.blit(pathogen_count_text, (10, 10))
        
        pygame.display.flip()
    
    pygame.quit()
