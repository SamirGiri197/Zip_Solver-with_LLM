import json
import os
import logging
import re
from typing import Optional, Dict, List, Tuple
from datetime import datetime

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

try:
    from ollama import chat, ChatResponse
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    import wandb
    WANDB_AVAILABLE = True
except ImportError:
    WANDB_AVAILABLE = False

from config.llm_config import (
    LLM_PROVIDERS, ENABLE_WANDB, 
    LOG_FILE, LOG_LEVEL, MAX_LLM_RETRIES, LLM_TIMEOUT
)

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Setup wandb
if ENABLE_WANDB and WANDB_AVAILABLE:
    try:
        wandb.init(project="zip-puzzle-llm", name=f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        logger.info("wandb initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize wandb: {e}")
        WANDB_AVAILABLE = False

class ZipPuzzlePromptEngine:
    """Expert-engineered prompt system for ZIP puzzle solving"""
    
    @staticmethod
    def create_board_state(board, path: List[Tuple[int, int]]) -> Dict[str, str]:
        """Create comprehensive board state information for LLM"""
        n = board.n
        
        # 1. Create numbered coordinate grid
        coordinate_grid = []
        for r in range(n):
            row_coords = []
            for c in range(n):
                row_coords.append(f"({r},{c})")
            coordinate_grid.append("  ".join(row_coords))
        coordinate_info = "\n".join(coordinate_grid)
        
        # 2. List all clue numbers and their exact positions
        clues = board.givens()
        clue_positions = []
        sorted_clues = sorted(clues.items())  # Sort by step number
        for step, (r, c) in sorted_clues:
            clue_positions.append(f"Clue {step}: position ({r},{c})")
        clue_info = "\n".join(clue_positions)
        
        # 3. Current path taken so far
        if path:
            path_info = " -> ".join([f"({r},{c})" for r, c in path])
            current_pos = f"({path[-1][0]},{path[-1][1]})"
        else:
            path_info = "No moves made yet"
            current_pos = "Not started"
        
        # 4. Visual grid showing current state
        visual_grid = []
        for r in range(n):
            row = []
            for c in range(n):
                if (r, c) in path:
                    # Show path order number
                    path_index = path.index((r, c)) + 1
                    row.append(f"[{path_index:2}]")
                elif board.grid[r][c] > 0:
                    # Show clue number
                    row.append(f" {board.grid[r][c]:2} ")
                else:
                    # Empty cell
                    row.append("  . ")
            visual_grid.append(" ".join(row))
        visual_state = "\n".join(visual_grid)
        
        # 5. Available next moves (adjacent empty cells)
        available_moves = []
        if path:
            current = path[-1]
            neighbors = board.neighbors(current[0], current[1], False)  # No diagonal
            for r, c in neighbors:
                if (r, c) not in path:  # Not visited
                    available_moves.append(f"({r},{c})")
        else:
            # If no path, can start at clue 1
            if 1 in clues:
                start_pos = clues[1]
                available_moves.append(f"({start_pos[0]},{start_pos[1]})")
        
        next_moves = ", ".join(available_moves) if available_moves else "None (stuck!)"
        
        # 6. Progress information
        total_cells = n * n
        cells_filled = len(path)
        progress = f"{cells_filled}/{total_cells} cells filled"
        
        return {
            "coordinate_grid": coordinate_info,
            "clue_positions": clue_info,
            "current_path": path_info,
            "current_position": current_pos,
            "visual_state": visual_state,
            "available_moves": next_moves,
            "progress": progress,
            "board_size": f"{n}x{n}",
            "total_cells": str(total_cells)
        }
    
    @staticmethod
    def generate_expert_prompt(board, path: List[Tuple[int, int]]) -> str:
        """Generate expert-engineered prompt for optimal LLM performance with thinking process"""
        
        state = ZipPuzzlePromptEngine.create_board_state(board, path)
        
        prompt = f"""You are solving a ZIP PUZZLE. This is a path-finding puzzle where you must visit every cell exactly once.

=== PUZZLE RULES ===
1. Fill ALL {state['total_cells']} cells in one continuous path
2. Start at clue number 1
3. Visit ALL clue numbers in ascending order: 1 -> 2 -> 3 -> ... -> highest
4. End your path at the highest numbered clue
5. Move only horizontally or vertically (NO diagonal moves)
6. Never revisit a cell you've already been to
7. Fill empty cells between clues as needed

=== BOARD INFORMATION ===
Board Size: {state['board_size']}
Coordinate System: Each position is (row, column) starting from (0,0)

Coordinate Grid:
{state['coordinate_grid']}

=== CLUE LOCATIONS ===
{state['clue_positions']}

=== CURRENT GAME STATE ===
Progress: {state['progress']}
Current Position: {state['current_position']}
Path Taken: {state['current_path']}

Visual Board State:
{state['visual_state']}
Legend: [1],[2],etc = your path order | 1,2,etc = clue numbers | . = empty cell

=== YOUR TASK ===
Available Next Moves: {state['available_moves']}

THINK STEP BY STEP AND EXPLAIN YOUR REASONING:

1. ANALYSIS: Where am I now and what's my current situation?

2. STRATEGY: What clue number should I visit next? Where is it located?

3. EVALUATION: For each available move, what are the pros and cons?

4. DECISION: Which move is best and why?

Provide your reasoning in the following format:

THINKING:
[Your detailed analysis here]

MOVE: (row,col)

Example response:
THINKING:
I am currently at position (1,2) and have filled 3 out of 9 cells. Looking at the clues, I need to visit clue 2 next, which is at position (2,1). From my current position, I can move to (1,1), (1,3), (0,2), or (2,2). The move to (1,1) gets me closer to clue 2 and doesn't block any future paths. Moving to (1,3) would take me away from clue 2. Therefore, (1,1) is the optimal choice.

MOVE: (1,1)

Solve the puzzle step by step, providing your THINKING and MOVE each time. Remember to consider future implications of your current move on completing the entire puzzle. You must returen your move in coordinate system (row, column). and it only have positive co-ordinates similar to the Matrix form"""

        return prompt

class LLMSolver:
    """Enhanced LLM solver with thinking process and multiple API support"""
    
    def __init__(self):
        self.provider = None
        self.model = None
        self.prompt_engine = ZipPuzzlePromptEngine()
        
    def set_provider(self, provider_name: str):
        """Set the LLM provider"""
        if provider_name not in LLM_PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        config = LLM_PROVIDERS[provider_name]
        if not config.get("enabled"):
            raise ValueError(f"Provider {provider_name} is disabled")
        
        self.provider = provider_name
        self.model = config.get("model")
        logger.info(f"LLM provider set to: {provider_name} (model: {self.model})")
    
    def _call_gemini_api(self, prompt: str) -> str:
        """Call Gemini API"""
        if not GEMINI_AVAILABLE:
            raise RuntimeError("Gemini not available. Install: pip install google-generativeai")
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        model_name = LLM_PROVIDERS["gemini"].get("model", "gemini-2.0-flash")
        model = genai.GenerativeModel(model_name)
        
        response = model.generate_content(prompt)
        return response.text
    
    def _call_ollama_api(self, prompt: str) -> str:
        """Call Ollama API"""
        if not OLLAMA_AVAILABLE:
            raise RuntimeError("Ollama not available. Install: pip install ollama")
        
        model = LLM_PROVIDERS["ollama"]["model"]
        messages = [{"role": "user", "content": prompt}]
        response: ChatResponse = chat(model=model, messages=messages, stream=False)
        return response.message.content
    
    def _call_openai_api(self, prompt: str) -> str:
        """Call OpenAI ChatGPT API"""
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI not available. Install: pip install openai")
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable not set")
        
        client = openai.OpenAI(api_key=api_key)
        model_name = LLM_PROVIDERS["openai"].get("model", "gpt-4")
        
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are an expert puzzle solver. Analyze the ZIP puzzle carefully and provide detailed reasoning for your moves."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=1000,
            max_tokens=1000,
            temperature=1  # Lower temperature for more consistent reasoning
        )
        
        return response.choices[0].message.content
    
    def _call_claude_api(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        if not CLAUDE_AVAILABLE:
            raise RuntimeError("Claude not available. Install: pip install anthropic")
        
        api_key = os.getenv("CLAUDE_API_KEY")
        if not api_key:
            raise RuntimeError("CLAUDE_API_KEY environment variable not set")
        
        client = anthropic.Anthropic(api_key=api_key)
        model_name = LLM_PROVIDERS["claude"].get("model", "claude-3-sonnet-20240229")
        
        response = client.messages.create(
            model=model_name,
            max_tokens=1000,
            temperature=1,
            system="You are an expert puzzle solver. Analyze the ZIP puzzle carefully and provide detailed reasoning for your moves.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
    
    def _call_llm_api(self, prompt: str) -> str:
        """Unified API call method"""
        try:
            if self.provider == "gemini":
                return self._call_gemini_api(prompt)
            elif self.provider == "ollama":
                return self._call_ollama_api(prompt)
            elif self.provider == "openai":
                return self._call_openai_api(prompt)
            elif self.provider == "claude":
                return self._call_claude_api(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
        except Exception as e:
            logger.error(f"API call failed: {e}")
            raise
    
    def _extract_thinking_and_move(self, response_text: str) -> Tuple[str, Optional[Tuple[int, int]]]:
        """Extract thinking process and coordinates from LLM response"""
        
        thinking = ""
        coordinates = None
        
        # Strategy 1: Look for structured THINKING: and MOVE: format
        thinking_match = re.search(r'THINKING:\s*(.*?)\s*MOVE:', response_text, re.DOTALL | re.IGNORECASE)
        if thinking_match:
            thinking = thinking_match.group(1).strip()
        
        # Strategy 2: Look for MOVE: pattern
        move_match = re.search(r'MOVE:\s*\((\d+),\s*(\d+)\)', response_text, re.IGNORECASE)
        if move_match:
            try:
                coordinates = (int(move_match.group(1)), int(move_match.group(2)))
            except ValueError:
                pass
        
        # Strategy 3: If no structured format, extract thinking from full response
        if not thinking:
            # Remove coordinate patterns to get thinking
            thinking_text = re.sub(r'\((\d+),\s*(\d+)\)', '', response_text)
            thinking_text = re.sub(r'MOVE:', '', thinking_text, flags=re.IGNORECASE)
            thinking = thinking_text.strip()
        
        # Strategy 4: Fallback coordinate extraction if MOVE: pattern not found
        if not coordinates:
            coord_patterns = [
                r'\((\d+),\s*(\d+)\)',           # (1,2) or (1, 2)
                r'\((\d+)\s*,\s*(\d+)\)',       # (1 ,2) or (1 , 2)
                r'(\d+)\s*,\s*(\d+)',           # 1,2 or 1, 2
                r'row\s*(\d+).*?col\s*(\d+)',   # row 1 col 2
                r'(\d+)\s+(\d+)',               # 1 2
            ]
            
            for pattern in coord_patterns:
                matches = re.findall(pattern, response_text, re.IGNORECASE)
                if matches:
                    try:
                        coordinates = (int(matches[0][0]), int(matches[0][1]))
                        break
                    except (ValueError, IndexError):
                        continue
        
        return thinking, coordinates
    
    def _log_thinking_process(self, move_number: int, thinking: str, coordinates: Optional[Tuple[int, int]]):
        """Log the LLM's thinking process in detail"""
        
        logger.info("=" * 80)
        logger.info(f"🧠 LLM THINKING PROCESS - Move {move_number}")
        logger.info("=" * 80)
        logger.info(f"Provider: {self.provider}")
        logger.info(f"Model: {self.model}")
        logger.info("-" * 40)
        logger.info("REASONING:")
        logger.info(thinking)
        logger.info("-" * 40)
        if coordinates:
            logger.info(f"DECISION: Move to {coordinates}")
        else:
            logger.info("DECISION: No valid move extracted")
        logger.info("=" * 80)
        
        # Also print to console for immediate visibility
        print(f"\n🧠 {self.provider.upper()} THINKING (Move {move_number}):")
        print("-" * 50)
        print(thinking)
        print("-" * 50)
        if coordinates:
            print(f"💡 DECISION: {coordinates}")
        else:
            print("❌ DECISION: Could not extract move")
        print()
    
    def solve(self, board, path: List[Tuple[int, int]], next_number: int) -> Optional[Dict]:
        """Solve using expert prompt engineering with detailed thinking process"""
        
        if not self.provider:
            raise ValueError("No LLM provider selected")
        
        move_number = len(path) + 1
        logger.info(f"🎯 Generating move {move_number} with {self.provider}")
        
        # Generate expert prompt
        prompt = self.prompt_engine.generate_expert_prompt(board, path)
        
        logger.info(f"📋 EXPERT PROMPT for Move {move_number}:")
        logger.info("=" * 60)
        logger.info(prompt)
        logger.info("=" * 60)
        
        # Try multiple times with retries
        for attempt in range(MAX_LLM_RETRIES):
            try:
                # Call LLM
                response_text = self._call_llm_api(prompt)
                
                logger.info(f"📝 LLM RAW RESPONSE (Attempt {attempt + 1}):")
                logger.info("-" * 40)
                logger.info(response_text)
                logger.info("-" * 40)
                
                # Extract thinking and coordinates
                thinking, coordinates = self._extract_thinking_and_move(response_text)
                
                # Log thinking process in detail
                self._log_thinking_process(move_number, thinking, coordinates)
                
                if coordinates:
                    row, col = coordinates
                    logger.info(f"✅ SUCCESSFULLY PARSED MOVE: ({row}, {col})")
                    
                    return {
                        "next_move": {"row": row, "col": col},
                        "thinking": thinking,
                        "reason": thinking[:200] + "..." if len(thinking) > 200 else thinking,
                        "confidence": 0.8,
                        "parsing_success": True,
                        "raw_response": response_text,
                        "response_length": len(response_text),
                        "full_thinking": thinking
                    }
                else:
                    logger.warning(f"❌ Could not parse coordinates from response")
                    if attempt == MAX_LLM_RETRIES - 1:
                        return {
                            "parsing_success": False,
                            "raw_response": response_text,
                            "response_length": len(response_text),
                            "reason": "Failed to parse coordinates",
                            "thinking": thinking,
                            "full_thinking": thinking
                        }
            
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed: {e}")
                if attempt == MAX_LLM_RETRIES - 1:
                    return {
                        "parsing_success": False,
                        "raw_response": f"Error: {str(e)}",
                        "response_length": 0,
                        "reason": f"API Error: {str(e)}",
                        "thinking": f"Error occurred: {str(e)}",
                        "full_thinking": f"Error occurred: {str(e)}"
                    }
        
        return None

# Global instance
llm_solver = LLMSolver()