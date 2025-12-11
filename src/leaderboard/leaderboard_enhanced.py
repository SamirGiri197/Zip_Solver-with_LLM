import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from config.config import LEADERBOARD_FILE, LEADERBOARD_MAX_ENTRIES, DIFFICULTY_MULTIPLIER

@dataclass
class EnhancedScore:
    """Enhanced score tracking for both human and LLM players"""
    player_name: str
    board_size: int
    time_seconds: int
    timestamp: str
    player_type: str  # "human" or "llm"
    model_name: Optional[str] = None  # For LLMs: "gpt-4", "claude-3-sonnet", etc.
    move_efficiency: Optional[float] = None  # For LLMs: valid_moves / total_moves
    path_accuracy: Optional[float] = None    # For LLMs: path following accuracy
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def score(self) -> float:
        """Calculate enhanced score with LLM bonuses"""
        base_multiplier = DIFFICULTY_MULTIPLIER.get(self.board_size, 1.0)
        # Avoid division by zero
        t = max(1, self.time_seconds)
        base_score = (1000 / t) * base_multiplier
        
        # LLM bonus based on performance metrics
        if self.player_type != "human" and self.move_efficiency is not None and self.path_accuracy is not None:
            efficiency_bonus = self.move_efficiency * 0.3  # Up to 30% bonus
            accuracy_bonus = self.path_accuracy * 0.2     # Up to 20% bonus
            total_bonus = 1.0 + efficiency_bonus + accuracy_bonus
            return base_score * total_bonus
        
        return base_score
    
    def display_name(self) -> str:
        """Get formatted display name"""
        if self.player_type == "human":
            return self.player_name
        return f"{self.player_name} ({self.model_name or 'Unknown'})"
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, d: Dict) -> 'EnhancedScore':
        return cls(**d)

class EnhancedLeaderboard:
    """Enhanced leaderboard supporting both human and LLM players with categorization"""
    
    def __init__(self):
        self.scores: List[EnhancedScore] = []
        self.load()
    
    def load(self):
        """Load leaderboard from file"""
        if os.path.exists(LEADERBOARD_FILE):
            try:
                with open(LEADERBOARD_FILE, 'r') as f:
                    data = json.load(f)
                    self.scores = []
                    for d in data:
                        # Handle migration from old format
                        if isinstance(d, dict):
                            if 'player_type' not in d:
                                d['player_type'] = 'human'
                            self.scores.append(EnhancedScore.from_dict(d))
            except Exception as e:
                print(f"[Leaderboard] Error loading: {e}")
                self.scores = []
    
    def save(self):
        """Save leaderboard to file"""
        try:
            data = [s.to_dict() for s in self.scores]
            with open(LEADERBOARD_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Leaderboard] Error saving: {e}")
    
    def add_human_score(self, player_name: str, board_size: int, time_seconds: int) -> int:
        """Add score for human player"""
        score = EnhancedScore(
            player_name=player_name,
            board_size=board_size,
            time_seconds=time_seconds,
            timestamp=datetime.now().isoformat(),
            player_type="human"
        )
        return self._add_score_internal(score)
    
    def add_llm_score(self, player_type: str, model_name: str, board_size: int, 
                     time_seconds: int, move_efficiency: float, path_accuracy: float) -> int:
        """Add score for LLM player"""
        score = EnhancedScore(
            player_name=player_type, # e.g. "openai", "claude"
            board_size=board_size,
            time_seconds=time_seconds,
            timestamp=datetime.now().isoformat(),
            player_type="llm",
            model_name=model_name,
            move_efficiency=move_efficiency,
            path_accuracy=path_accuracy
        )
        return self._add_score_internal(score)
    
    def _add_score_internal(self, score: EnhancedScore) -> int:
        """Internal method to add score, sort, and return rank"""
        self.scores.append(score)
        # Sort by score descending
        self.scores.sort(key=lambda s: s.score(), reverse=True)
        
        # Keep manageable size (per category filtering happens on display)
        if len(self.scores) > LEADERBOARD_MAX_ENTRIES * 20:
             self.scores = self.scores[:LEADERBOARD_MAX_ENTRIES * 20]
        
        self.save()
        
        # Calculate rank within its specific category and board size
        category_scores = self.get_scores_by_category(score.board_size, score.player_type, score.player_name)
        for i, s in enumerate(category_scores):
            if (s.player_name == score.player_name and 
                s.timestamp == score.timestamp and 
                s.time_seconds == score.time_seconds):
                return i + 1
        return -1

    def get_available_board_sizes(self) -> List[int]:
        """Return sorted list of board sizes that have data"""
        sizes = set(s.board_size for s in self.scores)
        return sorted(list(sizes))

    def get_scores_by_category(self, board_size: int, player_type: str, provider_name: str = None) -> List[EnhancedScore]:
        """Filter scores by board size and type/provider"""
        filtered = [s for s in self.scores if s.board_size == board_size]
        
        if player_type == "overall":
            return filtered
        
        if player_type == "human":
            filtered = [s for s in filtered if s.player_type == "human"]
        elif player_type == "llm":
            filtered = [s for s in filtered if s.player_type == "llm"]
            if provider_name:
                # Filter specific LLM provider (e.g., "openai", "claude")
                filtered = [s for s in filtered if s.player_name.lower() == provider_name.lower()]
        
        return sorted(filtered, key=lambda s: s.score(), reverse=True)

    def get_leaderboard_data(self, board_size: int) -> Dict[str, List[EnhancedScore]]:
        """Get top 5 scores for all required categories for a specific board size"""
        data = {}
        
        # 1. Overall
        data["overall"] = self.get_scores_by_category(board_size, "overall")[:5]
        
        # 2. Human Only
        data["human"] = self.get_scores_by_category(board_size, "human")[:5]
        
        # 3. Specific LLMs
        llm_providers = ["openai", "claude", "gemini", "ollama"]
        for provider in llm_providers:
            data[provider] = self.get_scores_by_category(board_size, "llm", provider)[:5]
            
        return data

# Global instance required by other files
enhanced_leaderboard = EnhancedLeaderboard()