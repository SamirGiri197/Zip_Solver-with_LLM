import time
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class MoveMetrics:
    """Track metrics for a single LLM move"""
    move_number: int
    row: int
    col: int
    is_valid: bool
    is_on_clue: bool
    clue_number: Optional[int]
    latency_ms: float
    reasoning: str
    confidence: float

@dataclass
class GameMetrics:
    """Track overall game metrics"""
    board_size: int
    total_cells: int
    total_moves: int
    successful_completion: bool
    completion_time_seconds: float
    moves: List[MoveMetrics]
    
    # Calculated metrics
    valid_moves: int = 0
    invalid_moves: int = 0
    bad_moves: int = 0  # Moves that could get stuck
    clue_hits: int = 0
    average_latency_ms: float = 0.0
    clue_accuracy: float = 0.0
    move_efficiency: float = 0.0
    success_ratio: float = 0.0
    
    def calculate_metrics(self, clue_count: int):
        """Calculate derived metrics"""
        self.valid_moves = sum(1 for m in self.moves if m.is_valid)
        self.invalid_moves = sum(1 for m in self.moves if not m.is_valid)
        self.bad_moves = self.invalid_moves
        self.clue_hits = sum(1 for m in self.moves if m.is_on_clue)
        
        if self.moves:
            self.average_latency_ms = sum(m.latency_ms for m in self.moves) / len(self.moves)
        
        # Clue accuracy: how many clues were hit vs total clues
        self.clue_accuracy = (self.clue_hits / clue_count * 100) if clue_count > 0 else 0
        
        # Move efficiency: valid moves / total moves
        self.move_efficiency = (self.valid_moves / self.total_moves * 100) if self.total_moves > 0 else 0
        
        # Success ratio: 1.0 if completed, 0.0 if not
        self.success_ratio = 1.0 if self.successful_completion else 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging"""
        return {
            "board_size": self.board_size,
            "total_cells": self.total_cells,
            "total_moves": self.total_moves,
            "successful_completion": self.successful_completion,
            "completion_time_seconds": self.completion_time_seconds,
            "valid_moves": self.valid_moves,
            "invalid_moves": self.invalid_moves,
            "bad_moves": self.bad_moves,
            "clue_hits": self.clue_hits,
            "average_latency_ms": self.average_latency_ms,
            "clue_accuracy_percent": self.clue_accuracy,
            "move_efficiency_percent": self.move_efficiency,
            "success_ratio": self.success_ratio,
            "moves_details": [asdict(m) for m in self.moves]
        }

class MetricsCollector:
    """Collect and log game metrics"""
    
    def __init__(self):
        self.game_metrics: Optional[GameMetrics] = None
        self.move_start_time: float = 0
        self.game_start_time: float = 0
    
    def start_game(self, board_size: int):
        """Initialize metrics for a new game"""
        self.game_start_time = time.time()
        self.game_metrics = GameMetrics(
            board_size=board_size,
            total_cells=board_size * board_size,
            total_moves=0,
            successful_completion=False,
            completion_time_seconds=0.0,
            moves=[]
        )
        logger.info(f"Game metrics started for {board_size}x{board_size} board")
    
    def start_move(self):
        """Start timing a move"""
        self.move_start_time = time.time()
    
    def record_move(self, row: int, col: int, is_valid: bool, is_on_clue: bool,
                   clue_number: Optional[int], reasoning: str, confidence: float):
        """Record a move"""
        if not self.game_metrics:
            return
        
        latency_ms = (time.time() - self.move_start_time) * 1000
        self.game_metrics.total_moves += 1
        
        move = MoveMetrics(
            move_number=self.game_metrics.total_moves,
            row=row,
            col=col,
            is_valid=is_valid,
            is_on_clue=is_on_clue,
            clue_number=clue_number,
            latency_ms=latency_ms,
            reasoning=reasoning[:100],  # Truncate reasoning
            confidence=confidence
        )
        self.game_metrics.moves.append(move)
        
        logger.info(f"Move {move.move_number}: ({row}, {col}) - Valid: {is_valid}, "
                   f"Latency: {latency_ms:.0f}ms, Confidence: {confidence:.2f}")
    
    def end_game(self, success: bool, clue_count: int):
        """End game and calculate metrics"""
        if not self.game_metrics:
            return
        
        self.game_metrics.successful_completion = success
        self.game_metrics.completion_time_seconds = time.time() - self.game_start_time
        self.game_metrics.calculate_metrics(clue_count)
        
        logger.info(f"Game ended - Success: {success}, Time: {self.game_metrics.completion_time_seconds:.1f}s")
        return self.game_metrics
    
    def log_to_wandb(self, llm_provider: str):
        """Log metrics to wandb"""
        if not self.game_metrics or not WANDB_AVAILABLE:
            return
        
        try:
            metrics_dict = self.game_metrics.to_dict()
            
            # Log main metrics
            wandb.log({
                "game/board_size": self.game_metrics.board_size,
                "game/total_moves": self.game_metrics.total_moves,
                "game/successful_completion": self.game_metrics.successful_completion,
                "game/completion_time_seconds": self.game_metrics.completion_time_seconds,
                "metrics/valid_moves": self.game_metrics.valid_moves,
                "metrics/invalid_moves": self.game_metrics.invalid_moves,
                "metrics/bad_moves": self.game_metrics.bad_moves,
                "metrics/clue_hits": self.game_metrics.clue_hits,
                "metrics/average_latency_ms": self.game_metrics.average_latency_ms,
                "metrics/clue_accuracy_percent": self.game_metrics.clue_accuracy,
                "metrics/move_efficiency_percent": self.game_metrics.move_efficiency,
                "metrics/success_ratio": self.game_metrics.success_ratio,
                "llm_provider": llm_provider,
            })
            
            logger.info("Metrics logged to wandb successfully")
        except Exception as e:
            logger.error(f"Error logging to wandb: {e}")
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        if not self.game_metrics:
            return "No game metrics available"
        
        m = self.game_metrics
        return f"""
=== GAME SUMMARY ===
Board Size: {m.board_size}x{m.board_size}
Total Moves: {m.total_moves}
Completion: {'SUCCESS ✓' if m.successful_completion else 'FAILED ✗'}
Time: {m.completion_time_seconds:.1f}s

=== METRICS ===
Valid Moves: {m.valid_moves}/{m.total_moves}
Bad Moves: {m.bad_moves}
Clue Hits: {m.clue_hits}
Move Efficiency: {m.move_efficiency:.1f}%
Clue Accuracy: {m.clue_accuracy:.1f}%
Avg Latency: {m.average_latency_ms:.0f}ms
Success Ratio: {m.success_ratio:.1%}
"""

# Global collector
metrics_collector = MetricsCollector()