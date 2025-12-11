import time
import logging
from typing import List, Dict, Optional, Tuple
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
    is_valid: bool              # Move to empty cell, not diagonal, follows adjacency rules
    is_bad: bool                # Move to visited cell or diagonal
    is_correct: bool            # Follows the solver's optimal path
    is_on_clue: bool           # Landed on a numbered clue cell
    clue_number: Optional[int] # Which clue number (if any)
    expected_row: int          # Where solver path expected to go
    expected_col: int          # Where solver path expected to go
    latency_ms: float          # Response time in milliseconds
    reasoning: str             # LLM's reasoning (truncated)
    confidence: float          # LLM confidence score (0-1)
    parsing_success: bool      # Was LLM response properly parsed
    response_length: int       # Length of LLM response in characters

@dataclass
class GameMetrics:
    """Track comprehensive game metrics for LLM evaluation"""
    board_size: int
    total_cells: int
    total_moves: int
    puzzle_completed: bool
    completion_time_seconds: float
    moves: List[MoveMetrics]
    solver_path: List[Tuple[int, int]]  # Reference path for comparison
    llm_path: List[Tuple[int, int]]     # Actual path taken by LLM
    
    # Core Movement Metrics
    valid_moves: int = 0           # Moves to empty cells following adjacency
    bad_moves: int = 0             # Moves to visited/diagonal cells
    correct_moves: int = 0         # Moves following solver path
    clue_hits: int = 0             # Successful clue visits
    
    # Performance Metrics
    move_efficiency: float = 0.0    # valid_moves / total_moves
    path_accuracy: float = 0.0      # correct_moves / total_moves  
    completion_ratio: float = 0.0   # cells_filled / total_cells
    average_latency_ms: float = 0.0
    
    # Quality Metrics
    parsing_success_rate: float = 0.0  # Successfully parsed responses
    reasoning_quality: float = 0.0     # Average reasoning length (proxy for thought)
    consistency_score: float = 0.0     # How consistent moves are with strategy
    
    # Advanced Metrics
    early_error_rate: float = 0.0      # Errors in first 25% of moves
    late_error_rate: float = 0.0       # Errors in last 25% of moves
    recovery_rate: float = 0.0         # Recovery after bad moves
    optimal_deviation: float = 0.0     # Average distance from optimal path
    
    def calculate_all_metrics(self):
        """Calculate all derived metrics from move data"""
        if not self.moves:
            return
            
        # Basic counts
        self.valid_moves = sum(1 for m in self.moves if m.is_valid)
        self.bad_moves = sum(1 for m in self.moves if m.is_bad)
        self.correct_moves = sum(1 for m in self.moves if m.is_correct)
        self.clue_hits = sum(1 for m in self.moves if m.is_on_clue)
        
        # Core performance metrics
        self.move_efficiency = (self.valid_moves / self.total_moves) if self.total_moves > 0 else 0.0
        
        # Path accuracy calculation based on completion status
        if self.puzzle_completed:
            # If completed, all valid moves are "correct" regardless of solver path
            self.path_accuracy = self.move_efficiency
            self.correct_moves = self.valid_moves  # Update correct moves count
        else:
            # If failed, compare against solver path
            self.path_accuracy = (self.correct_moves / self.total_moves) if self.total_moves > 0 else 0.0
        
        self.completion_ratio = len(self.llm_path) / self.total_cells if self.total_cells > 0 else 0.0
        
        # Latency metrics
        if self.moves:
            self.average_latency_ms = sum(m.latency_ms for m in self.moves) / len(self.moves)
        
        # Quality metrics
        parsing_successes = sum(1 for m in self.moves if m.parsing_success)
        self.parsing_success_rate = (parsing_successes / self.total_moves) if self.total_moves > 0 else 0.0
        
        # Reasoning quality (proxy: average reasoning length)
        reasoning_lengths = [len(m.reasoning) for m in self.moves if m.reasoning]
        self.reasoning_quality = sum(reasoning_lengths) / len(reasoning_lengths) if reasoning_lengths else 0.0
        
        # Advanced metrics
        self._calculate_advanced_metrics()
    
    def _calculate_advanced_metrics(self):
        """Calculate advanced performance metrics"""
        if len(self.moves) < 4:
            return
            
        # Early vs late error rates
        early_count = len(self.moves) // 4
        late_start = 3 * len(self.moves) // 4
        
        early_moves = self.moves[:early_count]
        late_moves = self.moves[late_start:]
        
        if early_moves:
            early_errors = sum(1 for m in early_moves if m.is_bad)
            self.early_error_rate = early_errors / len(early_moves)
        
        if late_moves:
            late_errors = sum(1 for m in late_moves if m.is_bad)
            self.late_error_rate = late_errors / len(late_moves)
        
        # Recovery rate: valid moves after bad moves
        recovery_opportunities = 0
        recoveries = 0
        
        for i in range(len(self.moves) - 1):
            if self.moves[i].is_bad:
                recovery_opportunities += 1
                if self.moves[i + 1].is_valid:
                    recoveries += 1
        
        self.recovery_rate = (recoveries / recovery_opportunities) if recovery_opportunities > 0 else 1.0
        
        # Optimal deviation: average Manhattan distance from expected position
        deviations = []
        for move in self.moves:
            if move.expected_row >= 0 and move.expected_col >= 0:  # Valid expected position
                deviation = abs(move.row - move.expected_row) + abs(move.col - move.expected_col)
                deviations.append(deviation)
        
        self.optimal_deviation = sum(deviations) / len(deviations) if deviations else 0.0
        
        # Consistency score: how often consecutive moves follow a logical pattern
        consistent_sequences = 0
        total_sequences = len(self.moves) - 1
        
        for i in range(total_sequences):
            current_move = self.moves[i]
            next_move = self.moves[i + 1]
            
            # Check if moves are logically connected (adjacent, towards clue, etc.)
            if self._is_consistent_sequence(current_move, next_move):
                consistent_sequences += 1
        
        self.consistency_score = (consistent_sequences / total_sequences) if total_sequences > 0 else 1.0
    
    def _is_consistent_sequence(self, move1: MoveMetrics, move2: MoveMetrics) -> bool:
        """Check if two consecutive moves form a consistent sequence"""
        # Moves are consistent if they're adjacent and both valid
        if not (move1.is_valid and move2.is_valid):
            return False
        
        # Check adjacency (including diagonal for this consistency check)
        row_diff = abs(move2.row - move1.row)
        col_diff = abs(move2.col - move1.col)
        
        return (row_diff <= 1 and col_diff <= 1 and (row_diff + col_diff) > 0)
    
    def get_performance_grade(self) -> str:
        """Get overall performance grade A-F"""
        score = (
            self.move_efficiency * 0.3 +
            self.path_accuracy * 0.3 +
            self.completion_ratio * 0.2 +
            self.parsing_success_rate * 0.1 +
            (1.0 - self.early_error_rate) * 0.1
        )
        
        if score >= 0.9: return "A"
        elif score >= 0.8: return "B" 
        elif score >= 0.7: return "C"
        elif score >= 0.6: return "D"
        else: return "F"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging"""
        return {
            # Basic info
            "board_size": self.board_size,
            "total_cells": self.total_cells,
            "total_moves": self.total_moves,
            "puzzle_completed": self.puzzle_completed,
            "completion_time_seconds": self.completion_time_seconds,
            
            # Core metrics
            "valid_moves": self.valid_moves,
            "bad_moves": self.bad_moves,
            "correct_moves": self.correct_moves,
            "clue_hits": self.clue_hits,
            
            # Performance percentages
            "move_efficiency_percent": round(self.move_efficiency * 100, 1),
            "path_accuracy_percent": round(self.path_accuracy * 100, 1),
            "completion_percent": round(self.completion_ratio * 100, 1),
            "average_latency_ms": round(self.average_latency_ms, 1),
            
            # Quality metrics
            "parsing_success_rate_percent": round(self.parsing_success_rate * 100, 1),
            "reasoning_quality_score": round(self.reasoning_quality, 1),
            "consistency_score_percent": round(self.consistency_score * 100, 1),
            
            # Advanced metrics
            "early_error_rate_percent": round(self.early_error_rate * 100, 1),
            "late_error_rate_percent": round(self.late_error_rate * 100, 1),
            "recovery_rate_percent": round(self.recovery_rate * 100, 1),
            "optimal_deviation_avg": round(self.optimal_deviation, 2),
            "performance_grade": self.get_performance_grade(),
            
            # Detailed move data
            "moves_details": [asdict(m) for m in self.moves]
        }

class LLMMetricsCollector:
    """Enhanced metrics collector for LLM evaluation"""
    
    def __init__(self):
        self.game_metrics: Optional[GameMetrics] = None
        self.move_start_time: float = 0
        self.game_start_time: float = 0
        self.solver_path: List[Tuple[int, int]] = []
        self.current_move_number: int = 0
    
    def start_game(self, board_size: int, solver_path: List[Tuple[int, int]] = None):
        """Initialize metrics for a new game"""
        self.game_start_time = time.time()
        self.current_move_number = 0
        self.solver_path = solver_path or []
        
        self.game_metrics = GameMetrics(
            board_size=board_size,
            total_cells=board_size * board_size,
            total_moves=0,
            puzzle_completed=False,
            completion_time_seconds=0.0,
            moves=[],
            solver_path=self.solver_path.copy(),
            llm_path=[]
        )
        logger.info(f"LLM evaluation started for {board_size}x{board_size} board")
    
    def start_move(self):
        """Start timing a move"""
        self.move_start_time = time.time()
        self.current_move_number += 1
    
    def record_move(self, row: int, col: int, is_valid: bool, current_path: List[Tuple[int, int]], 
                   reasoning: str = "", confidence: float = 0.5, parsing_success: bool = True, 
                   response_length: int = 0):
        """Record a move with comprehensive metrics"""
        if not self.game_metrics:
            return
        
        latency_ms = (time.time() - self.move_start_time) * 1000
        self.game_metrics.total_moves += 1
        
        # Determine if move is bad (visited or invalid position)
        attempted_cell = (row, col)
        is_bad = (
            attempted_cell in current_path or  # Already visited
            not is_valid or                   # Invalid move (out of bounds, not adjacent)
            row < 0 or col < 0               # Invalid coordinates
        )
        
        # Determine if move is correct (follows solver path)
        expected_row, expected_col = -1, -1
        is_correct = False
        
        if len(current_path) < len(self.solver_path):
            expected_row, expected_col = self.solver_path[len(current_path)]
            is_correct = (row == expected_row and col == expected_col)
        
        # Update LLM path if valid move
        if is_valid and not is_bad:
            self.game_metrics.llm_path.append((row, col))
        
        # Check if on clue (this would need board state - simplified for now)
        is_on_clue = False  # Will be updated by caller if needed
        clue_number = None
        
        move_metric = MoveMetrics(
            move_number=self.current_move_number,
            row=row,
            col=col,
            is_valid=is_valid and not is_bad,
            is_bad=is_bad,
            is_correct=is_correct,
            is_on_clue=is_on_clue,
            clue_number=clue_number,
            expected_row=expected_row,
            expected_col=expected_col,
            latency_ms=latency_ms,
            reasoning=reasoning[:100],  # Truncate reasoning
            confidence=confidence,
            parsing_success=parsing_success,
            response_length=response_length
        )
        
        self.game_metrics.moves.append(move_metric)
        
        logger.info(f"Move {self.current_move_number}: ({row}, {col}) - "
                   f"Valid: {move_metric.is_valid}, Correct: {is_correct}, "
                   f"Latency: {latency_ms:.0f}ms")
    
    def update_move_clue_info(self, move_index: int, is_on_clue: bool, clue_number: int = None):
        """Update clue information for a move (called after board state check)"""
        if (self.game_metrics and 0 <= move_index < len(self.game_metrics.moves)):
            self.game_metrics.moves[move_index].is_on_clue = is_on_clue
            self.game_metrics.moves[move_index].clue_number = clue_number
    
    def end_game(self, success: bool) -> GameMetrics:
        """End game and calculate all metrics"""
        if not self.game_metrics:
            return None
        
        self.game_metrics.puzzle_completed = success
        self.game_metrics.completion_time_seconds = time.time() - self.game_start_time
        self.game_metrics.calculate_all_metrics()
        
        logger.info(f"Game ended - Success: {success}, "
                   f"Efficiency: {self.game_metrics.move_efficiency:.1%}, "
                   f"Accuracy: {self.game_metrics.path_accuracy:.1%}")
        return self.game_metrics
    
    def log_to_wandb(self, llm_provider: str, model_name: str = ""):
        """Log metrics to wandb with detailed breakdown"""
        if not self.game_metrics or not WANDB_AVAILABLE:
            return
        
        try:
            metrics_dict = self.game_metrics.to_dict()
            
            # Log main metrics with provider info
            wandb.log({
                # Game info
                "llm_provider": llm_provider,
                "model_name": model_name,
                "board_size": self.game_metrics.board_size,
                "puzzle_completed": self.game_metrics.puzzle_completed,
                "completion_time_seconds": self.game_metrics.completion_time_seconds,
                
                # Core performance
                "moves/total": self.game_metrics.total_moves,
                "moves/valid": self.game_metrics.valid_moves,
                "moves/bad": self.game_metrics.bad_moves,
                "moves/correct": self.game_metrics.correct_moves,
                "moves/clue_hits": self.game_metrics.clue_hits,
                
                # Key percentages
                "performance/move_efficiency": self.game_metrics.move_efficiency,
                "performance/path_accuracy": self.game_metrics.path_accuracy,
                "performance/completion_ratio": self.game_metrics.completion_ratio,
                "performance/grade": self.game_metrics.get_performance_grade(),
                
                # Latency
                "latency/average_ms": self.game_metrics.average_latency_ms,
                
                # Quality
                "quality/parsing_success_rate": self.game_metrics.parsing_success_rate,
                "quality/reasoning_quality": self.game_metrics.reasoning_quality,
                "quality/consistency_score": self.game_metrics.consistency_score,
                
                # Advanced
                "advanced/early_error_rate": self.game_metrics.early_error_rate,
                "advanced/late_error_rate": self.game_metrics.late_error_rate,
                "advanced/recovery_rate": self.game_metrics.recovery_rate,
                "advanced/optimal_deviation": self.game_metrics.optimal_deviation,
            })
            
            logger.info("Comprehensive metrics logged to wandb")
        except Exception as e:
            logger.error(f"Error logging to wandb: {e}")
    
    def get_detailed_summary(self) -> str:
        """Get comprehensive human-readable summary"""
        if not self.game_metrics:
            return "No game metrics available"
        
        m = self.game_metrics
        
        return f"""
=== LLM PERFORMANCE ANALYSIS ===
Board: {m.board_size}x{m.board_size} | Completion: {'SUCCESS ✓' if m.puzzle_completed else 'FAILED ✗'}
Time: {m.completion_time_seconds:.1f}s | Grade: {m.get_performance_grade()}

=== CORE METRICS ===
Total Moves: {m.total_moves}
Valid Moves: {m.valid_moves} ({m.move_efficiency:.1%})
Bad Moves: {m.bad_moves}
Correct Moves: {m.correct_moves} ({m.path_accuracy:.1%})
Clue Hits: {m.clue_hits}

=== PERFORMANCE ANALYSIS ===
Move Efficiency: {m.move_efficiency:.1%} (valid moves / total moves)
Path Accuracy: {m.path_accuracy:.1%} ({'optimal path following' if not m.puzzle_completed else 'completion success'})
Completion: {m.completion_ratio:.1%} of puzzle filled
Avg Latency: {m.average_latency_ms:.0f}ms per move

=== QUALITY METRICS ===
Response Parsing: {m.parsing_success_rate:.1%} success rate
Reasoning Quality: {m.reasoning_quality:.0f} avg chars
Move Consistency: {m.consistency_score:.1%}

=== ADVANCED ANALYSIS ===
Early Error Rate: {m.early_error_rate:.1%} (first 25% of moves)
Late Error Rate: {m.late_error_rate:.1%} (last 25% of moves)
Recovery Rate: {m.recovery_rate:.1%} (bounce back from errors)
Optimal Deviation: {m.optimal_deviation:.2f} avg distance from best path

=== INSIGHTS ===
{'Strong performance - LLM solved efficiently' if m.puzzle_completed and m.move_efficiency > 0.8
 else 'Good efficiency but failed to complete' if m.move_efficiency > 0.7
 else 'Struggled with move selection' if m.move_efficiency < 0.5
 else 'Moderate performance with room for improvement'}
"""

# Global enhanced collector
llm_metrics_collector = LLMMetricsCollector()