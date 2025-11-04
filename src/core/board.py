from dataclasses import dataclass
from typing import List, Tuple, Dict, Optional, Set

Coord = Tuple[int, int]

@dataclass
class Board:
    grid: List[List[int]]          # 0 = blank; >0 are fixed givens (display numbers)
    k: int                         # target length (must equal n*n for ZIP rules)
    diag: bool = False             # True = 8-way moves; False = 4-way
    display_to_step: Optional[Dict[int, int]] = None  # maps display number → actual step
    step_to_display: Optional[Dict[int, int]] = None  # maps actual step → display number

    @property
    def n(self) -> int:
        return len(self.grid)

    def in_bounds(self, r: int, c: int) -> bool:
        return 0 <= r < self.n and 0 <= c < self.n

    def neighbors(self, r: int, c: int, diag: Optional[bool] = None) -> List[Coord]:
        if diag is None:
            diag = self.diag
        deltas = [(-1,0),(1,0),(0,-1),(0,1)]
        if diag:
            deltas += [(-1,-1),(-1,1),(1,-1),(1,1)]
        out = []
        for dr, dc in deltas:
            nr, nc = r+dr, c+dc
            if self.in_bounds(nr, nc):
                out.append((nr, nc))
        return out

    def givens(self) -> Dict[int, Coord]:
        """Returns mapping of actual step → coordinate."""
        m: Dict[int, Coord] = {}
        for r in range(self.n):
            for c in range(self.n):
                display_val = self.grid[r][c]
                if display_val:
                    # Convert display number to actual step
                    if self.display_to_step:
                        actual_step = self.display_to_step.get(display_val)
                        if actual_step:
                            m[actual_step] = (r, c)
                    else:
                        # Fallback: assume display == step (backward compat)
                        m[display_val] = (r, c)
        return m


def validate_path(board: Board, path: List[Coord], diag: Optional[bool] = None) -> Tuple[bool, str]:
    """Validate a full 1..k path against board rules & givens.
    
    Strict ZIP rules:
    - Must start at 1
    - Must visit all clue numbers in ascending order (1, 2, 3, ...)
    - Must END at the highest clue number (no extra cells after)
    - All cells before reaching the highest clue must form a valid path
    """
    if diag is None:
        diag = board.diag
    if len(path) != board.k:
        return False, f"Expected {board.k} steps, got {len(path)}"
    
    seen: Set[Coord] = set()
    clue_positions = {}  # Map display_num → position in path where user placed it
    
    for i, cell in enumerate(path):
        if cell in seen:
            return False, f"Cell {cell} repeated"
        if not board.in_bounds(*cell):
            return False, f"Cell {cell} out of bounds"
        if i > 0 and cell not in board.neighbors(*path[i-1], diag):
            return False, f"Step {i}->{i+1} not adjacent"
        seen.add(cell)
        
        # Record clue positions
        display_val = board.grid[cell[0]][cell[1]]
        if display_val:
            clue_positions[display_val] = i + 1
    
    # Must have at least clue 1
    if 1 not in clue_positions:
        return False, "Must start at clue 1"
    
    # Must start at position 1
    if clue_positions[1] != 1:
        return False, "Clue 1 must be at the start"
    
    # Get all clues in order
    sorted_clues = sorted(clue_positions.keys())
    
    # Verify clues are in ascending order by position
    for j in range(1, len(sorted_clues)):
        if clue_positions[sorted_clues[j]] <= clue_positions[sorted_clues[j-1]]:
            return False, f"Clues out of order"
    
    # Check that clues are CONSECUTIVE (1, 2, 3, ... without gaps)
    for i, clue in enumerate(sorted_clues):
        if clue != i + 1:
            return False, f"Missing or skipped clue number {i + 1}"
    
    # Must END at the highest clue number (no cells after highest clue)
    highest_clue = sorted_clues[-1]
    highest_clue_pos = clue_positions[highest_clue]
    if highest_clue_pos != len(path):
        return False, f"Path must end at clue {highest_clue}, not continue beyond it"
    
    return True, "OK"