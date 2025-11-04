import json
import os
import logging
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

class LLMSolver:
    def __init__(self):
        self.provider = None
        self.model = None
        
    def set_provider(self, provider_name: str):
        """Set the LLM provider."""
        if provider_name not in LLM_PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        config = LLM_PROVIDERS[provider_name]
        if not config.get("enabled"):
            raise ValueError(f"Provider {provider_name} is disabled")
        
        self.provider = provider_name
        self.model = config.get("model")
        logger.info(f"LLM provider set to: {provider_name} (model: {self.model})")
    
    def _prepare_prompt_data(self, board, path: List[Tuple[int, int]]) -> tuple:
        """Prepare common data for prompts"""
        # Get available neighbors
        if not path:
            available_neighbors = []
        else:
            current = path[-1]
            available_neighbors = [
                (r, c) for r, c in board.neighbors(current[0], current[1], board.diag)
                if (r, c) not in path
            ]
        
        neighbors_str = "\n".join([f"  ({r}, {c})" for r, c in available_neighbors])
        if not neighbors_str:
            neighbors_str = "  NONE - Game stuck!"
        
        # Prepare clues
        clues = board.givens()
        clues_str = "CLUES TO VISIT IN ORDER:\n"
        for step, (r, c) in sorted(clues.items()):
            visited = "✓" if (r, c) in path else " "
            clues_str += f"  {visited} Clue {step}: ({r}, {c})\n"
        
        current_pos = path[-1] if path else (0, 0)
        
        # Build grid visualization
        grid_visual = []
        for r in range(board.n):
            row_str = ""
            for c in range(board.n):
                if (r, c) in path:
                    row_str += f"[P]"
                elif board.grid[r][c] > 0:
                    row_str += f"[{board.grid[r][c]:2}]"
                else:
                    row_str += "[ ]"
            grid_visual.append(row_str)
        grid_str = "\n".join(grid_visual)
        
        # Build raw grid array (actual numbers)
        grid_array = []
        for r in range(board.n):
            row_arr = []
            for c in range(board.n):
                if (r, c) in path:
                    row_arr.append("P")
                elif board.grid[r][c] > 0:
                    row_arr.append(str(board.grid[r][c]))
                else:
                    row_arr.append(".")
            grid_array.append(row_arr)
        
        # Format array as table
        grid_array_str = "GRID ARRAY (P=path, .=empty, #=clue):\n"
        for row in grid_array:
            grid_array_str += " ".join(f"{cell:>2}" for cell in row) + "\n"
        
        return neighbors_str, clues_str, current_pos, grid_str, grid_array_str
    
    def solve_with_gemini(self, board, path: List[Tuple[int, int]], next_number: int) -> Optional[Dict]:
        """Solve using Google Gemini."""
        if not GEMINI_AVAILABLE:
            logger.error("Gemini not available. Install: pip install google-generativeai")
            return None
        
        try:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                logger.error("GEMINI_API_KEY environment variable not set")
                return None
            
            genai.configure(api_key=api_key)
            model_name = LLM_PROVIDERS["gemini"].get("model", "gemini-2.0-flash")
            model = genai.GenerativeModel(model_name)

            # Prepare common data
            neighbors_str, clues_str, current_pos, grid_str, grid_array_str = self._prepare_prompt_data(board, path)
            
            prompt = f"""ZIP PUZZLE RULES:
                1. Fill ALL {board.k} cells in a continuous path
                2. Start at clue 1, visit clues in order (1→2→3→...), end at highest clue
                3. Move only to adjacent cells (up, down, left, right), diagonal move are not allowed
                4. Cannot revisit cells
                5. Between clues, fill any empty cells

                {grid_array_str}

                VISUAL BOARD:
                {grid_str}

                CLUES TO VISIT IN ORDER:
                {clues_str}

                CURRENT POSITION: ({current_pos[0]}, {current_pos[1]})
                CELLS FILLED: {len(path)}/{board.k}
                AVAILABLE NEXT MOVES: {neighbors_str}

                What is your next move and why?"""
            
            logger.info(f"Calling Gemini API with model {LLM_PROVIDERS['gemini']}")
            logger.info(f"PROMPT FOR MOVE {len(path) + 1}:")
            logger.info(prompt)
            
            response = model.generate_content(prompt)
            response_text = response.text
            
            # Log the FULL response
            logger.info("="*80)
            logger.info(f"LLM RESPONSE (Move {len(path) + 1}):")
            logger.info(response_text)
            
            # Log to wandb
            if WANDB_AVAILABLE:
                try:
                    wandb.log({
                        "provider": "gemini",
                        "model": LLM_PROVIDERS['gemini'],
                        "response_length": len(response_text),
                        "grid_size": board.n,
                        "path_length": len(path)
                    })
                except:
                    pass
            
            # Try to extract JSON or parse response
            try:
                # First try to find JSON in response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    import re
                    json_str = re.sub(r'//.*?(?=\n|$)', '', json_str)
                    result = json.loads(json_str)
                    if result and 'next_move' in result:
                        logger.info(f"Parsed move: ({result['next_move']['row']}, {result['next_move']['col']})")
                        return result
                
                # If no JSON found, try to parse coordinates from text
                import re
                # Look for patterns like "move to (x, y)" or "next move is (x, y)"
                move_patterns = [
                    r'move to \((\d+),\s*(\d+)\)',
                    r'next move[:\s]+\((\d+),\s*(\d+)\)',
                    r'move:\s*\((\d+),\s*(\d+)\)',
                    r'cell \((\d+),\s*(\d+)\)',
                ]
                
                for pattern in move_patterns:
                    match = re.search(pattern, response_text, re.IGNORECASE)
                    if match:
                        row, col = int(match.group(1)), int(match.group(2))
                        logger.info(f"Parsed move from text: ({row}, {col})")
                        return {"next_move": {"row": row, "col": col}, "reason": response_text[:100]}
                
                # Fallback: get ALL coordinates and pick the one that's NOT the current position
                coords = re.findall(r'\((\d+),\s*(\d+)\)', response_text)
                if coords:
                    current_pos_tuple = (path[-1][0], path[-1][1]) if path else None
                    for row_str, col_str in coords:
                        row, col = int(row_str), int(col_str)
                        if current_pos_tuple is None or (row, col) != current_pos_tuple:
                            logger.info(f"Parsed move (fallback): ({row}, {col})")
                            return {"next_move": {"row": row, "col": col}, "reason": response_text[:100]}
                
                logger.warning("Could not parse move from response")
                return None
                
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(f"Failed to parse response: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Error calling Gemini: {e}")
            return None
    
    def solve_with_ollama(self, board, path: List[Tuple[int, int]], next_number: int) -> Optional[Dict]:
        """Solve using Ollama (local LLM)."""
        if not OLLAMA_AVAILABLE:
            logger.error("Ollama not available. Install: pip install ollama")
            return None
        
        try:
            model = LLM_PROVIDERS["ollama"]["model"]
            
            # Prepare common data
            neighbors_str, clues_str, current_pos, grid_str, grid_array_str = self._prepare_prompt_data(board, path)
            
            prompt = f"""ZIP PUZZLE RULES:
                1. Fill ALL {board.k} cells in a continuous path
                2. Start at clue 1, visit clues in order (1→2→3→...), end at highest clue
                3. Move only to adjacent cells (up, down, left, right), diagonal move are not allowed
                4. Cannot revisit cells
                5. Between clues, fill any empty cells

                {grid_array_str}

                VISUAL BOARD:
                {grid_str}

                CLUES TO VISIT IN ORDER:
                {clues_str}

                CURRENT POSITION: ({current_pos[0]}, {current_pos[1]})
                CELLS FILLED: {len(path)}/{board.k}
                AVAILABLE NEXT MOVES: {neighbors_str}

                What is your next move and why?"""
            
            logger.info(f"Calling Ollama with model: {model}")
            logger.info(f"PROMPT FOR MOVE {len(path) + 1}:")
            logger.info(prompt)
            
            # Use ollama chat function
            messages = [{"role": "user", "content": prompt}]
            response: ChatResponse = chat(model=model, messages=messages, stream=False)
            response_text = response.message.content
            
            # Log the FULL response
            logger.info("="*80)
            logger.info(f"LLM RESPONSE (Move {len(path) + 1}):")
            logger.info(response_text)
            
            # Log to wandb
            if WANDB_AVAILABLE:
                try:
                    wandb.log({
                        "provider": "ollama",
                        "model": model,
                        "response_length": len(response_text),
                        "grid_size": board.n,
                        "path_length": len(path)
                    })
                except:
                    pass
            
            # Try to extract JSON or parse response
            try:
                # First try to find JSON in response
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response_text[json_start:json_end]
                    import re
                    json_str = re.sub(r'//.*?(?=\n|$)', '', json_str)
                    result = json.loads(json_str)
                    if result and 'next_move' in result:
                        logger.info(f"Parsed move: ({result['next_move']['row']}, {result['next_move']['col']})")
                        return result
                
                # If no JSON found, try to parse coordinates from text
                import re
                # Look for patterns like "move to (x, y)" or "next move is (x, y)"
                move_patterns = [
                    r'move to \((\d+),\s*(\d+)\)',
                    r'next move[:\s]+\((\d+),\s*(\d+)\)',
                    r'move:\s*\((\d+),\s*(\d+)\)',
                    r'cell \((\d+),\s*(\d+)\)',
                ]
                
                for pattern in move_patterns:
                    match = re.search(pattern, response_text, re.IGNORECASE)
                    if match:
                        row, col = int(match.group(1)), int(match.group(2))
                        logger.info(f"Parsed move from text: ({row}, {col})")
                        return {"next_move": {"row": row, "col": col}, "reason": response_text[:100]}
                
                # Fallback: get ALL coordinates and pick the one that's NOT the current position
                coords = re.findall(r'\((\d+),\s*(\d+)\)', response_text)
                if coords:
                    current_pos_tuple = (path[-1][0], path[-1][1]) if path else None
                    for row_str, col_str in coords:
                        row, col = int(row_str), int(col_str)
                        if current_pos_tuple is None or (row, col) != current_pos_tuple:
                            logger.info(f"Parsed move (fallback): ({row}, {col})")
                            return {"next_move": {"row": row, "col": col}, "reason": response_text[:100]}
                
                logger.warning("Could not parse move from response")
                return None
                
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                logger.warning(f"Failed to parse response: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def solve(self, board, path: List[Tuple[int, int]], next_number: int) -> Optional[Dict]:
        """Solve using the selected provider."""
        if not self.provider:
            logger.error("No LLM provider selected")
            return None
        
        logger.info(f"Starting LLM solve with provider: {self.provider}")
        
        for attempt in range(MAX_LLM_RETRIES):
            try:
                if self.provider == "gemini":
                    return self.solve_with_gemini(board, path, next_number)
                elif self.provider == "ollama":
                    return self.solve_with_ollama(board, path, next_number)
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{MAX_LLM_RETRIES} failed: {e}")
                if attempt == MAX_LLM_RETRIES - 1:
                    logger.error(f"All retry attempts failed")
                    return None
        
        return None

# Global instance
llm_solver = LLMSolver()