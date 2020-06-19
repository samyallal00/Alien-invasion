import sys
from time import sleep

import pygame
from settings import Settings
from ship import Ship
from Bullet import Bullet
from alien import Alien
from game_stats import GameStats
from button import Button
from scoreboard import Scoreboard


class AlienInvasion:
    """Overall class to manage game assets and behavior."""

    def __init__(self):
        """Initialize the game, and create game resources."""
        pygame.init()
        # Set up the window screen, and background image
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.image = pygame.image.load('images/ufo-4987627_1920.bmp')
        self.image = pygame.transform.scale(self.image, (self.screen.get_width(), self.screen.get_height()))
        self.rect = self.image.get_rect()

        # Control the settings of the game via Settings class
        self.settings = Settings()
        self.settings.screen_width = self.screen.get_rect().width
        self.settings.screen_height = self.screen.get_rect().height

        pygame.display.set_caption("Alien Invasion")
        self.music = self.settings.bg_music()

        # Manipulate game statistics & Scoreboard.
        self.stats = GameStats(self)
        self.sb = Scoreboard(self)

        # Create the actors of the game
        self.ship = Ship(self)
        self.bullets = pygame.sprite.Group()
        self.aliens = pygame.sprite.Group()
        self._create_fleet()

        # Make the Play button.
        self.play_button = Button(self, "Play")

        # flags
        self.keep_firing = False

    def run_game(self):
        """Start the main loop for the game."""
        """ Main Function of the game."""
        while True:
            self._check_events()
            if self.stats.game_active:
                self.ship.update()
                self._update_bullets()
                self._update_aliens()
                self._fire_bullet()
            self._update_screen()

    def _check_events(self):
        """ Watch for keyboard and mouse events. """
        for event in pygame.event.get():
            # Press x on top to quit
            if event.type == pygame.QUIT:
                sys.exit()
            # Check if any key is pressed down or released
            elif event.type == pygame.KEYDOWN:
                self._check_keydown_events(event)
            elif event.type == pygame.KEYUP:
                self._check_keyup_events(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                self._check_play_button(mouse_pos)

    def _check_play_button(self, mouse_pos):
        """Start a new game when the player clicks Play."""
        button_clicked = self.play_button.rect.collidepoint(mouse_pos)
        if button_clicked and not self.stats.game_active:
            # initialize the game settings every time
            self.settings.initialize_dynamic_settings()
            # Reset the game statistics and prep the scoreboard.
            self.stats.reset_stats()
            self.stats.game_active = True
            self.sb.prep_score()
            self.sb.prep_level()
            self.sb.prep_ships()

            # Get rid of any remaining aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()
            # Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()
            # Hide the mouse cursor.
            pygame.mouse.set_visible(False)

    def _check_keydown_events(self, event):
        """Respond to key presses."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = True
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = True
        elif event.key == pygame.K_q:
            sys.exit(0)
        elif event.key == pygame.K_SPACE:
            self.keep_firing = True

    def _check_keyup_events(self, event):
        """Respond to key releases."""
        if event.key == pygame.K_RIGHT:
            self.ship.moving_right = False
        elif event.key == pygame.K_LEFT:
            self.ship.moving_left = False
        elif event.key == pygame.K_SPACE:
            self.keep_firing = False

    def _fire_bullet(self):
        """Create a new bullet and add it to the bullets group."""
        if self.keep_firing and len(self.bullets) < self.settings.max_num_bullets:
            new_bullet = Bullet(self)
            self.bullets.add(new_bullet)

    def _update_bullets(self):
        """ Update the bullets positions """
        self.bullets.update()
        # Get rid of bullets that have disappeared.
        for bullet in self.bullets.copy():
            if bullet.rect.bottom <= 0:
                self.bullets.remove(bullet)

        # Check if any bullet collided with alien
        self._check_bullet_alien_collisions()

    def _check_bullet_alien_collisions(self):
        """Respond to bullet-alien collisions."""
        # Remove any bullets and aliens that have collided.
        # Check for any bullets that have hit aliens.
        # If so, get rid of the bullet and the alien.
        collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)

        # If there is a collision, loop through the dict and increase score
        # check if the high score has been attained, and update it if so
        if collisions:
            for aliens in collisions.values():
                self.stats.score += self.settings.alien_points * len(aliens)
            self.sb.prep_score()
            self.sb.check_high_score()

        # If all aliens have been destroyed
        if not self.aliens:
            # Start a new level, by doing the following
            # Destroy existing bullets and create new fleet.
            self.bullets.empty()
            self._create_fleet()
            self.settings.increase_speed()
            # Increase level.
            self.stats.level += 1
            self.sb.prep_level()

    def _create_fleet(self):
        """Create the fleet of aliens."""
        # Make an alien.
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size
        # see how much space we have to fit in some number of aliens
        available_space_x = self.settings.screen_width - (2 * alien_width)
        number_aliens_x = available_space_x // (2 * alien_width)

        ship_height = self.ship.rect.height
        # see how much space we have to fit in some number of aliens
        available_space_y = (self.settings.screen_height - (4 * alien_height) - ship_height)
        number_rows = available_space_y // (2 * alien_height)

        # Create all rows and columns of aliens.
        for row_number in range(number_rows):
            for alien_number in range(number_aliens_x):
                self._create_alien(alien_number, row_number)

    def _create_alien(self, alien_number, row_number):
        # Create an alien and place it in the row.
        alien = Alien(self)
        alien_width, alien_height = alien.rect.size

        # set up the aliens position accordingly
        alien.x = alien_width + 2 * alien_width * alien_number
        alien.rect.x = alien.x
        alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number

        # Add it to the group of aliens through the sprite class
        self.aliens.add(alien)

    def _update_aliens(self):
        """ Check if the fleet is at an edge, then update the positions of all aliens in the fleet. """
        self._check_fleet_edges()
        self.aliens.update()

        # Look for alien-ship collisions.
        if pygame.sprite.spritecollideany(self.ship, self.aliens):
            self._ship_hit()

        # Look for aliens hitting the bottom of the screen.
        self._check_aliens_bottom()

    def _check_fleet_edges(self):
        """Respond appropriately if any aliens have reached an edge."""
        for alien in self.aliens.sprites():
            if alien.check_edges():
                self._change_fleet_direction()
                break

    def _change_fleet_direction(self):
        """Drop the entire fleet and change the fleet's direction."""
        for alien in self.aliens.sprites():
            alien.rect.y += self.settings.fleet_drop_speed
        self.settings.fleet_direction *= -1

    def _ship_hit(self):
        """Respond to the ship being hit by an alien."""
        # If no more lives, then end the game by setting the flag
        if self.stats.ships_left == 0:
            self.stats.game_active = False
            pygame.mouse.set_visible(True)
        else:
            # Decrement ships_left.
            self.stats.ships_left -= 1
            self.sb.prep_ships()
            # Get rid of any remaining aliens and bullets.
            self.aliens.empty()
            self.bullets.empty()

            # Create a new fleet and center the ship.
            self._create_fleet()
            self.ship.center_ship()

            # Pause for 0.7 seconds.
            sleep(0.7)

    def _check_aliens_bottom(self):
        """Check if any aliens have reached the bottom of the screen."""
        screen_rect = self.screen.get_rect()
        for alien in self.aliens.sprites():
            if alien.rect.bottom >= screen_rect.bottom:
                # Treat this the same as if the ship got hit.
                self._ship_hit()
                break

    def _update_screen(self):
        """ Redraw the screen during each pass through the loop. """
        self.screen.fill(self.settings.bg_color)
        self.screen.blit(self.image, self.rect)
        # draw the ship on the screen
        self.ship.blitme()
        # Draw the bullets on the screen
        for bullet in self.bullets.sprites():
            bullet.draw_bullet()
        # Draw the group of aliens
        self.aliens.draw(self.screen)
        # show the scoreboard on screen
        self.sb.show_score()

        # Draw the play button if the game is inactive.
        if not self.stats.game_active:
            self.play_button.draw_button()

        # Make the most recently drawn screen visible.
        pygame.display.flip()


if __name__ == '__main__':
    # Make a game instance, and run the game.
    ai = AlienInvasion()
    ai.run_game()
