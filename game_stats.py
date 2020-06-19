import json


class GameStats:
    """Track statistics for Alien Invasion."""

    def __init__(self, ai_game):
        """Initialize statistics."""
        self.settings = ai_game.settings
        self.reset_stats()

        # Start Alien Invasion in an active state.
        self.game_active = False

        # High score should never be reset.
        self.high_score = 0
        self.load_high_score()

    def reset_stats(self):
        """Initialize statistics that can change during the game."""
        self.ships_left = self.settings.ship_limit
        self.score = 0
        self.level = 1

    def update_high_score(self):
        """ Store the new value of the high score for future games"""
        with open('JSON-Backups/high_score.JSON', 'w') as f:
            json.dump(self.high_score, f)

    def load_high_score(self):
        """ Try to load the current high score if exists, otherwise set to 0"""
        try:
            with open('JSON-Backups/high_score.JSON') as f:
                self.high_score = json.load(f)
        except FileNotFoundError:
            pass
