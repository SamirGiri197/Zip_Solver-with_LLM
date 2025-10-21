## Installation

```bash
git clone https://github.com/SamirGiri197/Zip_Solver-with_LLM.git
cd zip-game

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

## Requirements

- Python 3.11+

## How to Play

1. Launch the game
2. Examine the grid and identify all numbered cells
3. Click or drag to create a path starting from 1
4. Continue connecting each number in sequence
5. Ensure your path fills every cell in the grid
6. Complete the puzzle before time runs out (if applicable)

## Project Structure

```
zip-game/
├── src/
│   ├── game/
│   ├── ui/
│   └── solver/
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


## Contributing

We welcome contributions! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Performance

- **Solver algorithm**: LLM-based reasoning engine with structured prompting
- **Average solving time**: Depends on LLM API response time (typically 1-5 seconds)
- **Supports grid sizes**: 3x3 to 10x10+
- **LLM Provider Support**: OpenAI GPT-4, Anthropic Claude, Google Gemini, and more
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
