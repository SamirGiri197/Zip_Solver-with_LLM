#!/usr/bin/env python3
"""
ZIP Puzzle LLM Testing Script (Final GUI-Compatible Version)

FEATURES:
    ✓ Headless and GUI mode
    ✓ GUI mode shows the board & LLM solving animation
    ✓ Automatic termination of each game after LLM win/stuck/timeout
    ✓ Batch loop: GUI → quit → next game → GUI → quit → next game...
    ✓ Metrics logged per game into llm_metrics_collector
    ✓ Metrics + summary aggregated into ONE wandb run
"""

import time
import argparse
import logging
import sys
import os
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# wandb (optional)
try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False

# ZIP imports
from config.config import BOARD_SIZES, ADJACENCY_8_WAY
from config.llm_config import LLM_PROVIDERS, ENABLE_WANDB, WANDB_PROJECT
from core.generator import generate_unique_puzzle
from core.board import Board, validate_path

# FIXED imports
from LLM_configuration.llm_manager import llm_solver
from evaluation.eval import llm_metrics_collector

# GUI Engine
from UI.GUI import Game


# ------------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------------

DEFAULT_NUM_RUNS = 5
DEFAULT_BOARD_SIZE = 5
DEFAULT_PROVIDER = "ollama"
DEFAULT_MAX_MOVES = 100
DEFAULT_TIMEOUT = 300


# ------------------------------------------------------------
# ARGUMENT PARSER
# ------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run ZIP Puzzle LLM Tests (GUI-capable)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--num-runs", type=int, default=DEFAULT_NUM_RUNS)
    parser.add_argument("--board-size", type=int, default=DEFAULT_BOARD_SIZE,
                        choices=BOARD_SIZES)

    enabled = [name for name, cfg in LLM_PROVIDERS.items() if cfg.get("enabled")]
    parser.add_argument("--llm-provider", type=str, default=DEFAULT_PROVIDER,
                        choices=enabled)

    parser.add_argument("--run-name", type=str)

    parser.add_argument(
        "--gui", type=str, default="false",
        help="Use GUI mode? (true/false)"
    )

    parser.add_argument(
        "--log-level", type=str, default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"]
    )

    parser.add_argument("--max-moves", type=int, default=DEFAULT_MAX_MOVES)
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)

    return parser.parse_args()


# ------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------

def setup_logging(level, provider=None, board_size=None):
    import datetime
    logger = logging.getLogger()

    # Remove old handlers
    for h in list(logger.handlers):
        logger.removeHandler(h)

    logger.setLevel(getattr(logging, level))

    # Create readable timestamp
    timestamp = datetime.datetime.now().strftime("%m%d%Y_%H-%M")

    # Build filename using requested format
    provider = provider or "unknown"
    board_str = f"{board_size}x{board_size}" if board_size else "NxN"

    log_filename = f"{provider}-{board_str}-{timestamp}.log"

    # Create handlers
    file_handler = logging.FileHandler(log_filename)
    stream_handler = logging.StreamHandler()

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

# ------------------------------------------------------------
# PUZZLE GENERATION
# ------------------------------------------------------------

def generate_puzzle(board_size: int):
    import config.config as cfg
    if not hasattr(cfg, "CLUE_START"):
        cfg.CLUE_START, cfg.CLUE_MAX = cfg.get_clue_bounds(board_size)

    grid, solution, mapping = generate_unique_puzzle(
        n=board_size,
        diag=ADJACENCY_8_WAY
    )
    inverse = {v: k for k, v in mapping.items()}

    board = Board(
        grid=grid,
        k=board_size * board_size,
        diag=ADJACENCY_8_WAY,
        display_to_step=mapping,
        step_to_display=inverse
    )
    return board, solution


# ------------------------------------------------------------
# SINGLE GAME — GUI MODE
# ------------------------------------------------------------

def run_single_game_gui(game_id, board_size, provider, max_moves, timeout, logger):
    logger.info(f"=== GAME {game_id+1} — GUI MODE — {provider} ===")

    board, solution = generate_puzzle(board_size)

    game = Game(
        board=board,
        solution=solution,
        board_size=board_size,
        game_mode="llm",
        llm_provider=provider
    )

    # Enable batch automation
    game.llm_auto_quit = True
    game.llm_max_moves = max_moves
    game.llm_timeout = timeout

    # Start solving in background thread
    solver_thread = threading.Thread(
        target=lambda: game.solve_with_llm(provider),
        daemon=True
    )
    solver_thread.start()

    # GUI loop (returns when auto-quit triggers)
    game.run()

    # Collect final metrics AFTER GUI closes
    metrics = llm_metrics_collector.game_metrics

    return {
        "game_id": game_id + 1,
        "success": bool(game.is_won),
        "moves": len(game.path),
        "completion_time": game.final_time if hasattr(game, "final_time") else 0,
        "move_efficiency": getattr(metrics, "move_efficiency", 0),
        "path_accuracy": getattr(metrics, "path_accuracy", 0),
        "board_size": board_size,
        "llm_provider": provider,
    }


# ------------------------------------------------------------
# SINGLE GAME — HEADLESS MODE
# ------------------------------------------------------------

def run_single_game_headless(game_id, board_size, provider, max_moves, timeout, logger):
    logger.info(f"=== GAME {game_id+1} — HEADLESS MODE — {provider} ===")

    board, solution = generate_puzzle(board_size)
    givens = board.givens()

    if 1 not in givens:
        raise RuntimeError("Puzzle missing clue 1!")

    path = [givens[1]]
    move_count = 0
    is_won = False
    stuck_count = 0
    max_stuck = 3
    start_time = time.time()

    llm_metrics_collector.start_game(board_size, solution)
    llm_solver.set_provider(provider)

    while not is_won and move_count < max_moves and stuck_count < max_stuck:

        if time.time() - start_time > timeout:
            logger.warning("Timeout reached.")
            break

        move_count += 1

        llm_metrics_collector.start_move()
        result = llm_solver.solve(board, path, len(path) + 1)

        if not result or "next_move" not in result:
            stuck_count += 1
            continue

        r, c = result["next_move"]["row"], result["next_move"]["col"]
        cell = (r, c)

        is_valid = (
            cell not in path
            and cell in board.neighbors(path[-1][0], path[-1][1], board.diag)
        )

        llm_metrics_collector.record_move(
            row=r,
            col=c,
            is_valid=is_valid,
            path_before=path.copy(),
            reason=result.get("reason", ""),
            confidence=result.get("confidence", 0.5),
            parsing_success=result.get("parsing_success", True),
            response_length=result.get("response_length", 0),
        )

        if is_valid:
            path.append(cell)
            stuck_count = 0
            if len(path) == board.k:
                ok, _ = validate_path(board, path)
                if ok:
                    is_won = True
        else:
            stuck_count += 1

    metrics = llm_metrics_collector.end_game(is_won)

    return {
        "game_id": game_id + 1,
        "success": is_won,
        "moves": move_count,
        "path_length": len(path),
        "completion_time": time.time() - start_time,
        "move_efficiency": getattr(metrics, "move_efficiency", 0),
        "path_accuracy": getattr(metrics, "path_accuracy", 0),
        "board_size": board_size,
        "llm_provider": provider,
    }


# ------------------------------------------------------------
# BATCH RUNNER
# ------------------------------------------------------------

def run_batch(num_runs, board_size, provider, gui_mode, max_moves, timeout, logger):
    results = []
    success_count = 0

    cumulative_eff = 0.0
    cumulative_acc = 0.0

    for i in range(num_runs):

        print("\n" + "=" * 50)
        print(f"▶ STARTING RUN {i+1} OF {num_runs}")
        print("=" * 50)

        llm_metrics_collector.start_game(board_size)

        if gui_mode:
            result = run_single_game_gui(i, board_size, provider, max_moves, timeout, logger)
        else:
            result = run_single_game_headless(i, board_size, provider, max_moves, timeout, logger)

        # Save result
        results.append(result)

        # Access game metrics dict
        gm = llm_metrics_collector.game_metrics
        gm_dict = gm.to_dict() if gm else {}

        # Extract metrics for averaging
        eff = gm.move_efficiency if gm else 0
        acc = gm.path_accuracy if gm else 0

        cumulative_eff += eff
        cumulative_acc += acc

        # Success rate
        if result["success"]:
            success_count += 1

        # Print detailed metrics for this run
        print("\n📊 METRICS FOR RUN", i+1)
        print("-" * 40)
        for k, v in gm_dict.items():
            if k != "moves_details":
                print(f"{k:20}: {v}")

        # Print cumulative averages so far
        print("\n📈 AVERAGES AFTER", i+1, "RUNS")
        print("-" * 40)
        print(f"Avg Move Efficiency: {(cumulative_eff / (i+1)):.3f}")
        print(f"Avg Path Accuracy:   {(cumulative_acc / (i+1)):.3f}")
        print(f"Success Rate:        {(success_count / (i+1)):.3f}")

        logger.info(f"[{i+1}/{num_runs}] Current success rate={success_count/(i+1):.1%}")

        # wandb logging per-run
        if WANDB_AVAILABLE and ENABLE_WANDB:
            wandb.log({
                "run/id": i+1,
                "run/success": result["success"],
                "run/move_efficiency": eff,
                "run/path_accuracy": acc,
                "run/success_rate_so_far": success_count/(i+1)
            })

    # FINAL SUMMARY RETURN
    return {
        "summary": {
            "runs": num_runs,
            "successes": success_count,
            "success_rate": success_count / num_runs,
            "avg_efficiency": cumulative_eff / num_runs,
            "avg_accuracy": cumulative_acc / num_runs,
            "board_size": board_size,
            "llm_provider": provider,
        },
        "results": results
    }


# ------------------------------------------------------------
# SUMMARY
# ------------------------------------------------------------

def print_summary(stats, logger):
    s = stats["summary"]
    logger.info("=" * 60)
    logger.info("ZIP PUZZLE — LLM TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Games:       {s['runs']}")
    logger.info(f"Solved:      {s['successes']}")
    logger.info(f"Success %:   {s['success_rate']:.1%}")
    logger.info(f"Board Size:  {s['board_size']}x{s['board_size']}")
    logger.info(f"Provider:    {s['llm_provider']}")
    logger.info("=" * 60)


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():
    args = parse_args()
    logger = setup_logging(
    args.log_level,
    provider=args.llm_provider,
    board_size=args.board_size
)

    gui_mode = args.gui.lower() in ("true", "1", "yes")

    if not args.run_name:
        args.run_name = f"{args.llm_provider}-{args.board_size}x{args.board_size}-{args.num_runs}runs"

    # setup wandb
    if ENABLE_WANDB and WANDB_AVAILABLE:
        wandb.init(
            project=WANDB_PROJECT,
            name=args.run_name,
            config={
                "board_size": args.board_size,
                "llm_provider": args.llm_provider,
                "num_runs": args.num_runs,
                "gui_mode": gui_mode,
            },
        )

    stats = run_batch(
        args.num_runs,
        args.board_size,
        args.llm_provider,
        gui_mode,
        args.max_moves,
        args.timeout,
        logger,
    )

    print_summary(stats, logger)

    # Save results
    import json
    fname = f"zip_llm_results_{args.run_name}.json"
    with open(fname, "w") as f:
        json.dump(stats, f, indent=2)

    logger.info(f"Saved results to {fname}")

    if WANDB_AVAILABLE:
        wandb.finish()

    return 0


if __name__ == "__main__":
    sys.exit(main())
