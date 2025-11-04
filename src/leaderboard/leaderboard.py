import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from config.config import LEADERBOARD_FILE, LEADERBOARD_MAX_ENTRIES, DIFFICULTY_MULTIPLIER

class Score:
    def __init__(self, player_name: str, board_size: int, time_seconds: int, timestamp: str = None):
        self.player_name = player_name
        self.board_size = board_size
        self.time_seconds = time_seconds
        self.timestamp = timestamp or datetime.now().isoformat()
        
    def score(self) -> float:
        """Calculate score: lower time = higher score. Adjusted by board difficulty."""
        multiplier = DIFFICULTY_MULTIPLIER.get(self.board_size, 1.0)
        return (1000 / (self.time_seconds + 1)) * multiplier
    
    def to_dict(self) -> Dict:
        return {
            "player_name": self.player_name,
            "board_size": self.board_size,
            "time_seconds": self.time_seconds,
            "timestamp": self.timestamp,
            "score": self.score()
        }
    
    @staticmethod
    def from_dict(d: Dict) -> 'Score':
        return Score(d["player_name"], d["board_size"], d["time_seconds"], d["timestamp"])
    
    def __repr__(self) -> str:
        return f"{self.player_name:15} | {self.board_size}x{self.board_size} | {self.time_seconds:3}s | {self.score():.1f}"

class Leaderboard:
    def __init__(self):
        self.scores: List[Score] = []
        self.load()
    
    def load(self):
        """Load leaderboard from file."""
        if os.path.exists(LEADERBOARD_FILE):
            try:
                with open(LEADERBOARD_FILE, 'r') as f:
                    data = json.load(f)
                    self.scores = [Score.from_dict(d) for d in data]
            except Exception as e:
                print(f"[Leaderboard] Error loading: {e}")
                self.scores = []
    
    def save(self):
        """Save leaderboard to file."""
        try:
            data = [s.to_dict() for s in self.scores]
            with open(LEADERBOARD_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Leaderboard] Error saving: {e}")
    
    def add_score(self, player_name: str, board_size: int, time_seconds: int) -> int:
        """Add score and return rank (1 = top). Returns -1 if not in top entries."""
        score = Score(player_name, board_size, time_seconds)
        self.scores.append(score)
        self.scores.sort(key=lambda s: s.score(), reverse=True)
        
        # Keep only top entries
        self.scores = self.scores[:LEADERBOARD_MAX_ENTRIES]
        self.save()
        
        # Find rank
        for i, s in enumerate(self.scores):
            if s.player_name == player_name and s.timestamp == score.timestamp:
                return i + 1
        return -1
    
    def get_leaderboard(self, board_size: Optional[int] = None) -> List[Score]:
        """Get leaderboard, optionally filtered by board size."""
        if board_size:
            return [s for s in self.scores if s.board_size == board_size]
        return self.scores
    
    def clear(self):
        """Clear leaderboard."""
        self.scores = []
        self.save()