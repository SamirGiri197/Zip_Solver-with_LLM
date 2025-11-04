import os
import time
from typing import List, Optional, Tuple, Set
from core.board import Board, Coord

# ---------------- classical solver ----------------

def _ordered_neighbors(board: Board, cell: Coord, used: Set[Coord], diag: bool) -> List[Coord]:
    # Warnsdorff-like heuristic: try cells with the fewest onward options first
    opts = [nb for nb in board.neighbors(cell[0], cell[1], diag) if nb not in used]
    opts.sort(key=lambda nb: sum(1 for x in board.neighbors(nb[0], nb[1], diag) if x not in used))
    return opts

def solve_backtracking(board: Board, diag: bool, time_limit: float = 8.0) -> Optional[List[Coord]]:
    """Find a 1..k path consistent with givens."""
    start_time = time.time()
    giv = board.givens()  # Maps actual step → coordinate
    k = board.k

    # starting candidates
    starts = [giv[1]] if 1 in giv else [(r, c) for r in range(board.n) for c in range(board.n)]

    used: Set[Coord] = set()
    path: List[Coord] = []

    def dfs(step: int) -> bool:
        if time.time() - start_time > time_limit:
            return False
        if step > k:
            return True
        target = giv.get(step)  # Get target for actual step
        last = path[-1]
        cands: List[Coord]
        if target:
            # must step to that target if it's adjacent and free
            cands = [target] if target not in used and target in board.neighbors(last[0], last[1], diag) else []
        else:
            cands = _ordered_neighbors(board, last, used, diag)

        for cell in cands:
            if cell in used:
                continue
            display_val = board.grid[cell[0]][cell[1]]
            # Convert display value to actual step and check
            if display_val:
                if board.display_to_step:
                    actual_step = board.display_to_step.get(display_val)
                    if actual_step and actual_step != step:
                        continue
                else:
                    # Fallback: direct comparison
                    if display_val != step:
                        continue
            used.add(cell); path.append(cell)
            if dfs(step + 1):
                return True
            path.pop(); used.remove(cell)
        return False

    for s in starts:
        used.clear(); path.clear()
        used.add(s); path.append(s)
        if dfs(2):
            return path
    return None

def count_solutions(board: Board, diag: bool, limit: int = 2, time_limit: float = 8.0) -> int:
    """Count up to 'limit' solutions (early stop)."""
    start_time = time.time()
    giv = board.givens()  # Maps actual step → coordinate
    k = board.k

    starts = [giv[1]] if 1 in giv else [(r, c) for r in range(board.n) for c in range(board.n)]

    used: Set[Coord] = set()
    path: List[Coord] = []
    count = 0

    def dfs(step: int) -> bool:
        nonlocal count
        if time.time() - start_time > time_limit:
            return True
        if step > k:
            count += 1
            return count >= limit
        last = path[-1]
        target = giv.get(step)  # Get target for actual step
        if target:
            candidates = [target] if target not in used and target in board.neighbors(last[0], last[1], diag) else []
        else:
            candidates = _ordered_neighbors(board, last, used, diag)
        for cell in candidates:
            if cell in used:
                continue
            display_val = board.grid[cell[0]][cell[1]]
            # Convert display value to actual step and check
            if display_val:
                if board.display_to_step:
                    actual_step = board.display_to_step.get(display_val)
                    if actual_step and actual_step != step:
                        continue
                else:
                    # Fallback: direct comparison
                    if display_val != step:
                        continue
            used.add(cell); path.append(cell)
            if dfs(step + 1):
                return True
            path.pop(); used.remove(cell)
        return False

    for s in starts:
        used.clear(); path.clear()
        used.add(s); path.append(s)
        if dfs(2) or count >= limit:
            break
    return count


# ---------------- optional LLM helper ----------------
class LLMSolver:
    """
    Optional heuristic: call an LLM to propose a sequence of moves.
    This class is SAFE: if there is no API key or a call fails, it returns None.
    """
    def __init__(self):
        self.enabled = os.getenv("OPENAI_API_KEY") and True
        self.provider = "openai" if self.enabled and 'openai' in globals() else "none"

    def solve(self, board: Board, diag: bool) -> Optional[List[Coord]]:
        # For now: disabled unless you wire your own client and prompt.
        return None