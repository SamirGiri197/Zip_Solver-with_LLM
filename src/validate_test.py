#!/usr/bin/env python3
"""
Quick validation test for ZIP LLM testing setup

Run this first to validate your configuration before running full batch tests.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------
# MODULE IMPORT TESTS
# ---------------------------------------------------------

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    try:
        from config.config import BOARD_SIZES, ADJACENCY_8_WAY
        print("✅ config.config imported")

        from config.llm_config import LLM_PROVIDERS
        print("✅ config.llm_config imported")

        from core.generator import generate_unique_puzzle
        print("✅ core.generator imported")

        from core.board import Board, validate_path
        print("✅ core.board imported")

        # FIXED: correct import path
        from LLM_configuration.llm_manager import llm_solver
        print("✅ llm_manager imported")

        # FIXED: correct evaluation import
        from evaluation.eval import llm_metrics_collector
        print("✅ evaluation.eval imported")

        print("✅ All imports successful!")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


# ---------------------------------------------------------
# LLM CONFIG TEST
# ---------------------------------------------------------

def test_llm_config():
    """Test LLM configuration"""
    print("\nTesting LLM configuration...")
    from config.llm_config import LLM_PROVIDERS

    enabled_providers = [
        name for name, cfg in LLM_PROVIDERS.items() if cfg.get("enabled")
    ]

    if not enabled_providers:
        print("❌ No LLM providers enabled!")
        return False

    print(f"✅ Enabled providers: {enabled_providers}")

    for provider in enabled_providers:
        cfg = LLM_PROVIDERS[provider]
        print(f"  {provider}: {cfg.get('name')} - {cfg.get('model')}")

        # Check API key when needed
        if 'api_key_env' in cfg:
            api_key = os.getenv(cfg['api_key_env'])
            if api_key:
                print(f"    ✅ API key found for {cfg['api_key_env']}")
            else:
                print(f"    ⚠️  API key missing for {cfg['api_key_env']}")

    return True


# ---------------------------------------------------------
# PUZZLE GENERATION TEST
# ---------------------------------------------------------

def test_puzzle_generation():
    """Test puzzle generation"""
    print("\nTesting puzzle generation...")
    try:
        from core.generator import generate_unique_puzzle
        from core.board import Board

        # Ensure clue bounds exist
        import config.config as cfg
        if not hasattr(cfg, "CLUE_START"):
            cfg.CLUE_START, cfg.CLUE_MAX = cfg.get_clue_bounds(3)

        # Try generating a small puzzle
        grid, solution, mapping = generate_unique_puzzle(n=3, diag=False)

        board = Board(
            grid=grid,
            k=9,
            diag=False,
            display_to_step=mapping,
            step_to_display={v: k for k, v in mapping.items()}
        )

        print(f"✅ Generated 3x3 puzzle with {len(board.givens())} clues")
        print(f"✅ Solution path length: {len(solution)}")

        return True

    except Exception as e:
        print(f"❌ Puzzle generation error: {e}")
        return False


# ---------------------------------------------------------
# LLM CONNECTION TEST
# ---------------------------------------------------------

def test_llm_connection():
    """Test LLM connection"""
    print("\nTesting LLM connection...")
    try:
        from config.llm_config import LLM_PROVIDERS

        # FIXED: proper import
        from LLM_configuration.llm_manager import llm_solver

        enabled_providers = [
            name for name, cfg in LLM_PROVIDERS.items() if cfg.get("enabled")
        ]

        if not enabled_providers:
            print("❌ No providers to test")
            return False

        provider = enabled_providers[0]
        print(f"Testing provider: {provider}")

        llm_solver.set_provider(provider)
        print(f"✅ LLM provider {provider} set successfully")

        return True

    except Exception as e:
        print(f"❌ LLM connection error: {e}")
        return False


# ---------------------------------------------------------
# WANDB TEST
# ---------------------------------------------------------

def test_wandb():
    """Test Wandb availability"""
    print("\nTesting Wandb...")
    try:
        import wandb
        print("✅ Wandb available")

        from config.llm_config import ENABLE_WANDB
        if ENABLE_WANDB:
            print("✅ Wandb enabled in config")
        else:
            print("⚠️  Wandb disabled in config")

        return True

    except ImportError:
        print("⚠️  Wandb not installed (pip install wandb)")
        return True  # Not critical


# ---------------------------------------------------------
# MAIN RUNNER
# ---------------------------------------------------------

def main():
    print("🔍 ZIP LLM Testing Validation")
    print("=" * 50)

    tests = [
        ("Module Imports", test_imports),
        ("LLM Configuration", test_llm_config),
        ("Puzzle Generation", test_puzzle_generation),
        ("LLM Connection", test_llm_connection),
        ("Wandb Setup", test_wandb),
    ]

    results = []
    for name, func in tests:
        try:
            ok = func()
            results.append((name, ok))
        except Exception as e:
            print(f"❌ {name} failed with exception: {e}")
            results.append((name, False))

    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)

    for name, ok in results:
        status = "✅ PASS" if ok else "❌ FAIL"
        print(f"{status} {name}")

    all_passed = all(ok for _, ok in results)
    if all_passed:
        print("\n🎉 All tests passed! Ready to run ZIP LLM tests.")
        print("\nNext steps:")
        print("1. Set missing API keys if any")
        print("2. Run: python zip_llm_tests.py --num-runs 1 --board-size 3")
    else:
        print("\n⚠️  Some tests failed. Fix issues before running full tests.")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
