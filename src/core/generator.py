import random
from typing import List, Tuple, Dict, Set, Optional
from core.board import Board, Coord
from core.solver import count_solutions
import config.config as config


def _random_saw_cover_all(n: int, diag: bool) -> Optional[List[Coord]]:
    """Generate a full Hamiltonian path (self-avoiding walk) covering all cells."""
    k = n * n
    cells = [(r, c) for r in range(n) for c in range(n)]
    start = random.choice(cells)
    path, used = [start], {start}

    def onward_degree(cell: Coord) -> int:
        r, c = cell
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if diag:
            moves += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        deg = 0
        for dr, dc in moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr < n and 0 <= nc < n and (nr, nc) not in used:
                deg += 1
        return deg

    def neighbors(r: int, c: int):
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if diag:
            moves += [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        res = [(r + dr, c + dc) for dr, dc in moves if 0 <= r + dr < n and 0 <= c + dc < n and (r + dr, c + dc) not in used]
        random.shuffle(res)
        res.sort(key=onward_degree)
        return res

    def dfs() -> bool:
        if len(path) == k:
            return True
        for nb in neighbors(*path[-1]):
            used.add(nb)
            path.append(nb)
            if dfs():
                return True
            path.pop()
            used.remove(nb)
        return False

    return path if dfs() else None


def _grid_with_clues_from_path(n: int, path: List[Coord], clue_indices: Set[int]) -> List[List[int]]:
    grid = [[0] * n for _ in range(n)]
    for step, (r, c) in enumerate(path, start=1):
        if step in clue_indices:
            grid[r][c] = step
    return grid


def _create_display_grid(grid: List[List[int]], clue_indices: Set[int]) -> Tuple[List[List[int]], Dict[int, int]]:
    n = len(grid)
    display_grid = [[0] * n for _ in range(n)]
    mapping = {actual: i + 1 for i, actual in enumerate(sorted(clue_indices))}
    for r in range(n):
        for c in range(n):
            val = grid[r][c]
            if val in mapping:
                display_grid[r][c] = mapping[val]
    return display_grid, mapping


def _generate_puzzle_fast(n: int, diag: bool):
    attempts = 0
    while attempts < config.MAX_GEN_ATTEMPTS:
        attempts += 1
        path = _random_saw_cover_all(n, diag)
        if not path:
            continue

        k = n * n
        clue_set = {1, k}
        extras = list(range(2, k))
        random.shuffle(extras)
        start_clues, max_clues = config.get_clue_bounds(n)
        for idx in extras[:start_clues - 2]:
            clue_set.add(idx)
            
        grid = _grid_with_clues_from_path(n, path, clue_set)
        display_grid, mapping = _create_display_grid(grid, clue_set)
        return display_grid, path, mapping
    raise RuntimeError("Fast generator failed to build Hamiltonian path.")


def generate_unique_puzzle(n: int, diag: bool):
    if config.FAST_MODE and n >= config.FAST_MODE_THRESHOLD:
        return _generate_puzzle_fast(n, diag)

    attempts = 0
    while attempts < config.MAX_GEN_ATTEMPTS:
        attempts += 1
        path = _random_saw_cover_all(n, diag)
        if not path:
            continue
        k = n * n
        start_clues, max_clues = config.get_clue_bounds(n)

        clue_set = {1, k}
        extras = list(range(2, k))
        random.shuffle(extras)
        for idx in extras[:config.CLUE_START - 2]:
            clue_set.add(idx)

        more = [i for i in range(2, k) if i not in clue_set]
        random.shuffle(more)
        while True:
            grid = _grid_with_clues_from_path(n, path, clue_set)
            board = Board(grid=grid, k=k, diag=diag)
            count = count_solutions(board, diag=diag, limit=2, time_limit=config.SOLVER_TIME_LIMIT)
            if count == 1:
                display_grid, mapping = _create_display_grid(grid, clue_set)
                return display_grid, path, mapping
            if len(clue_set) >= max_clues or not more:
                break
            clue_set.add(more.pop())
    raise RuntimeError("Failed to generate unique puzzle. Try smaller n or longer limits.")
