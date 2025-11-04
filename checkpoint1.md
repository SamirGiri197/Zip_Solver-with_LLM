## Prompt
prompt = f"""ZIP PUZZLE RULES: <br>
                1. Fill ALL {board.k} cells in a continuous path<br>
                2. Start at clue 1, visit clues in order (1→2→3→...), end at highest clue<br>
                3. Move only to adjacent cells (up, down, left, right), diagonal move are not allowed<br>
                4. Cannot revisit cells<br>
                5. Between clues, fill any empty cells<br>
                
                    GRID ARRAY (P=path, .=empty, #=clue):
                     .  3  2  .
                     .  .  .  P
                     .  .  5  6
                     .  4  .  .
                  
                  
                    VISUAL BOARD:
                    [ ][ 3][ 2][ ]
                    [ ][ ][ ][P]
                    [ ][ ][ 5][ 6]
                    [ ][ 4][ ][ ]
                  
                    CLUES TO VISIT IN ORDER:
                    ✓ Clue 1: (1, 3)
                    Clue 2: (0, 1)
                    Clue 3: (2, 3)
                  
                  
                    CURRENT POSITION: (1, 3)
                    CELLS FILLED: 1/16
                    AVAILABLE NEXT MOVES:   (0, 3)
                                            (2, 3)
                                            (1, 2)
                  
                    What is your next move and why?"""
                
## Response from LLM

  Okay, let's analyze the situation.

  **Current Position:** (1, 3) - We've just filled Clue 1.
  **Next Clue:** Clue 2 (0, 1)
  **Available Moves:** (0, 3), (2, 3), (1, 2)

To reach Clue 2 at (0, 1), we need to move from our current position (1, 3) to (0, 3).

**Therefore, my next move is to move to (0, 3).**

**Reasoning:**

This move takes us directly to the cell adjacent to our current position, fulfilling the requirements of the puzzle. We must visit the clues in order, so reaching the next clue is the priority
