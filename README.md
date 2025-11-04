# 🧩 ZIP Puzzle Solver with LLM Integration

An interactive **ZIP Puzzle game** built with **Python + PyGame**, powered by **Large Language Models (LLMs)** such as **Google Gemini** and **Ollama (Local Models)** for intelligent puzzle-solving.  
The game combines visual playability, AI reasoning, and analytics through **Weights & Biases (WandB)** logging.

---

## 🚀 Features

- 🎮 **Interactive PyGame GUI** with real-time grid drawing
- 🧠 **AI-assisted solving** using LLMs (Gemini / Ollama)
- 🧩 **Backtracking solver** for fallback and hints
- 📈 **Game analytics** via [Weights & Biases (wandb.ai)](https://wandb.ai/)
- 🧰 Adjustable board sizes (3x3 – 10x10+)
- ⚙️ Configurable LLM providers and models
- 💾 Local leaderboard tracking
- 🎨 Gradient visuals, animations, and hints
## Requirements

- Python 3.12+
- Pygame

## Installation

```bash
git clone https://github.com/SamirGiri197/Zip_Solver-with_LLM.git

# Install dependencies
pip install -r requirements.txt
# or
npm install
```

### LLM API Setup

1. Sign up for an LLM provider (e.g., OpenAI, Anthropic, Google Gemini)
2. Generate your API key
3. Set up environment variable:

```bash
export LLM_API_KEY="your_api_key_here"
# or on Windows:
set LLM_API_KEY=your_api_key_here
```

4. Alternatively, create a `.env` file in the project root:

## How to Run Program
```bash 
cd/src
python main.py
```

## How to change LLM configurations
1. Go to config/llm_config.py
2. update LLM_PROVIDERS

## How to Change Prompt
1. Goto src/llm_configuration/llm_manager.py
2. Find Prompt = """ ............ """ and make changes as required.

### Example Promompt
prompt = f"""ZIP PUZZLE RULES: <br>
                1. Fill ALL {board.k} cells in a continuous path<br>
                2. Start at clue 1, visit clues in order (1→2→3→...), end at highest clue<br>
                3. Move only to adjacent cells (up, down, left, right), diagonal move are not allowed<br>
                4. Cannot revisit cells<br>
                5. Between clues, fill any empty cells<br>

                {grid_array_str}

                VISUAL BOARD:
                {grid_str}

                CLUES TO VISIT IN ORDER:
                {clues_str}

                CURRENT POSITION: ({current_pos[0]}, {current_pos[1]})
                CELLS FILLED: {len(path)}/{board.k}
                AVAILABLE NEXT MOVES: {neighbors_str}

                What is your next move and why?"""
                
  It passes the rules of the game, board state and asks for what is the next move and why?

  Both the ollama and gemini been able connect some numbers but failed to solve the puzzle correctly.

## How to Play

1. Launch the game
2. Examine the grid and identify all numbered cells
3. Click or drag to create a path starting from 1
4. Continue connecting each number in sequence
5. Ensure your path fills every cell in the grid
6. If you want to solve autonomously using LLM, click on LLM button then select the model you want to use.

## Project Structure

```
zip-game/
├── src/
│   ├── config/
│   ├── ui/
│   └── core/
├── tests/
├── assets/
├── README.md
└── requirements.txt
```

## Example Puzzle

```
┌───┬───┬───┐
│ 1 │   │ 3 │
├───┼───┼───┤
│   │ 2 │   │
├───┼───┼───┤
│ 4 │   │   │
└───┴───┴───┘
```

Connect: 1 → 2 → 3 → 4 while filling all cells.



## Performance

- **Solver algorithm**: LLM-based reasoning engine with structured prompting
- **Average solving time**: Depends on LLM API response time (typically 1-5 seconds)
- **Supports grid sizes**: 3x3 to 10x10+
- **LLM Provider Support**: Google Gemini, ollama
- **Optimization**: Caching of solutions for identical puzzle configurations


## License

This project is licensed under the [MIT License](LICENSE) - see the LICENSE file for details.

## Inspiration

Inspired by LinkedIn's Zip puzzle game - a daily puzzle challenge for millions of professionals.

## Resources

- [LinkedIn Zip Game](https://www.linkedin.com/games/zip)
- [Pathfinding Algorithms](https://en.wikipedia.org/wiki/Pathfinding)
- [Backtracking Algorithm](https://en.wikipedia.org/wiki/Backtracking)

## Contact

For questions or feedback, feel free to open an issue or contact [your info here].

---

**Have fun solving puzzles! 🧩**
