#!/usr/bin/env python3
"""
Game logic and scoring for Wildlife Camera Trap Game.
"""

import os
import requests
import threading
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

def get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key from multiple sources (environment variable, .env file, or .gemini-key file)."""
    
    # Try environment variable first (highest priority)
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print(f"DEBUG: Found API key from environment variable (length: {len(api_key)})")
        return api_key.strip()
    
    # Try .gemini-key file
    try:
        with open('.gemini-key', 'r') as f:
            api_key = f.read().strip()
            if api_key:
                print(f"DEBUG: Found API key from .gemini-key file (length: {len(api_key)})")
                return api_key
    except FileNotFoundError:
        print("DEBUG: .gemini-key file not found")
    except Exception as e:
        print(f"Warning: Error reading .gemini-key file: {e}")
    
    print("DEBUG: No API key found in any source")
    return None

def get_gemini_model_name() -> str:
    """Get Gemini model name from multiple sources (environment variable, .env file, or .gemini-config file)."""
    
    # Try environment variable first (highest priority)
    model_name = os.getenv('GEMINI_MODEL_NAME')
    if model_name:
        print(f"DEBUG: Found model name from environment variable: {model_name}")
        return model_name.strip()
    
    # Try .gemini-config file
    try:
        with open('.gemini-config', 'r') as f:
            model_name = f.read().strip()
            if model_name:
                print(f"DEBUG: Found model name from .gemini-config file: {model_name}")
                return model_name
    except FileNotFoundError:
        print("DEBUG: .gemini-config file not found, using default")
    except Exception as e:
        print(f"Warning: Error reading .gemini-config file: {e}")
    
    # Default model
    default_model = "gemini-2.5-pro"
    print(f"DEBUG: Using default model name: {default_model}")
    return default_model

# Scoring system - points awarded by taxonomic level
SCORE_VALUES = {
    'variety': 10,
    'subspecies': 10,
    'species': 10,
    'subgenus': 8,
    'genus': 5,
    'tribe': 4,
    'subfamily': 4,
    'family': 3,
    'superfamily': 2,
    'infraorder': 2,
    'suborder': 2,
    'order': 2,
    'superorder': 1,
    'infraclass': 1,
    'subclass': 1,
    'class': 1,
    'superclass': 0,
    'subphylum': 0,
    'phylum': 0,
    'kingdom': 0
}

# Taxonomic hierarchy (most specific to least specific)
TAXONOMIC_HIERARCHY = [
    'variety', 'subspecies', 'species', 'subgenus', 'genus', 'tribe',
    'subfamily', 'family', 'superfamily', 'infraorder', 'suborder',
    'order', 'superorder', 'infraclass', 'subclass', 'class',
    'superclass', 'subphylum', 'phylum', 'kingdom'
]

def get_taxonomic_path(taxon: Dict) -> Dict[str, str]:
    """Extract the complete taxonomic path from a taxon record."""
    path = {}
    
    # Map database column names to standard names
    column_mapping = {
        'order_': 'order'  # Handle SQL keyword issue
    }
    
    for level in TAXONOMIC_HIERARCHY:
        column = column_mapping.get(level, level)
        value = taxon.get(column)
        if value and str(value).strip():
            path[level] = str(value).strip()
    
    return path

def calculate_score(correct_taxon: Dict, guess_taxon: Dict) -> Tuple[int, str, str]:
    """
    Calculate score based on taxonomic matching.
    
    Returns:
        Tuple of (points_earned, matching_level, explanation)
    """
    
    correct_path = get_taxonomic_path(correct_taxon)
    guess_path = get_taxonomic_path(guess_taxon)
    
    # Find the highest matching taxonomic level
    matching_level = None
    matching_name = None
    
    for level in TAXONOMIC_HIERARCHY:
        if level in correct_path and level in guess_path:
            if correct_path[level].lower() == guess_path[level].lower():
                matching_level = level
                matching_name = correct_path[level]
                break
    
    if matching_level:
        points = SCORE_VALUES.get(matching_level, 0)
        explanation = f"Correct {matching_level}: {matching_name}"
        return points, matching_level, explanation
    else:
        return 0, None, "No taxonomic match found"

def calculate_score_by_name(correct_taxon: Dict, guess_name: str) -> Tuple[int, str, str]:
    """
    Calculate score when user guesses by name directly.
    
    Returns:
        Tuple of (points_earned, matching_level, explanation)
    """
    
    guess_name_lower = guess_name.lower().strip()
    correct_path = get_taxonomic_path(correct_taxon)
    
    # Check common name first
    if correct_taxon.get('common_name'):
        if correct_taxon['common_name'].lower().strip() == guess_name_lower:
            # Award points based on the most specific level of the correct taxon
            most_specific = correct_taxon.get('most_specific_level')
            if most_specific:
                points = SCORE_VALUES.get(most_specific, 0)
                explanation = f"Correct common name for {most_specific}: {correct_taxon['most_specific_name']}"
                return points, most_specific, explanation
    
    # Check each taxonomic level
    for level in TAXONOMIC_HIERARCHY:
        if level in correct_path:
            if correct_path[level].lower() == guess_name_lower:
                points = SCORE_VALUES.get(level, 0)
                explanation = f"Correct {level}: {correct_path[level]}"
                return points, level, explanation
    
    return 0, None, f"'{guess_name}' does not match any taxonomic level"

def get_correct_answer_display(taxon: Dict) -> str:
    """Get a formatted display string for the correct answer."""
    
    most_specific_name = taxon.get('most_specific_name', 'Unknown')
    common_name = taxon.get('common_name')
    
    # Start with common name (scientific name)
    if common_name:
        display = f"{common_name} ({most_specific_name})"
    else:
        display = most_specific_name
    
    # Add taxonomic context on separate lines
    path = get_taxonomic_path(taxon)
    context_lines = []
    
    # Add class, order, family in that order (if available)
    for level in ['class', 'order', 'family']:
        if level in path and path[level]:
            context_lines.append(f"{level}: {path[level]}")
    
    if context_lines:
        display += "<br>" + "<br>".join(context_lines)
    
    return display

def get_fun_fact(taxon: Dict) -> Optional[str]:
    """Get a fun fact about the taxon using Gemini API."""
    
    api_key = get_gemini_api_key()
    if not api_key:
        print("DEBUG: get_fun_fact - No API key available")
        return None
    
    # Determine what to ask about
    most_specific_name = taxon.get('most_specific_name')
    common_name = taxon.get('common_name')
    
    if not most_specific_name:
        print("DEBUG: get_fun_fact - No most_specific_name available")
        return None
    
    # Construct query
    query_name = common_name if common_name else most_specific_name
    print(f"DEBUG: get_fun_fact - Requesting fact for: {query_name}")
    
    try:
        # Use Gemini API to get fun fact
        model_name = get_gemini_model_name()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        prompt = f"Give me one interesting, brief fun fact about {query_name}. Keep it to 1-2 sentences and focus on behavior, habitat, or unique characteristics. Do not mention taxonomy or classification."
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        print(f"DEBUG: get_fun_fact - API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"DEBUG: get_fun_fact - Response data keys: {list(data.keys())}")
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                print(f"DEBUG: get_fun_fact - Success: {text[:100]}...")
                return text.strip()
            else:
                print("DEBUG: get_fun_fact - No candidates in response")
        else:
            print(f"DEBUG: get_fun_fact - API error status {response.status_code}: {response.text}")
        
    except Exception as e:
        print(f"ERROR: get_fun_fact - Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    
    print("DEBUG: get_fun_fact - Returning None")
    return None

def get_hint(taxon: Dict) -> Optional[str]:
    """Get a hint about the taxon using Gemini API without revealing taxonomic names."""
    
    api_key = get_gemini_api_key()
    if not api_key:
        print("DEBUG: get_hint - No API key available")
        return None
    
    # Determine what to ask about
    most_specific_name = taxon.get('most_specific_name')
    common_name = taxon.get('common_name')
    most_specific_level = taxon.get('most_specific_level', 'species')
    
    if not most_specific_name:
        print("DEBUG: get_hint - No most_specific_name available")
        return None
    
    # Use scientific name for more accurate results
    query_name = most_specific_name
    print(f"DEBUG: get_hint - Requesting hint for: {query_name}")
    
    try:
        # Use Gemini API to get hint
        model_name = get_gemini_model_name()
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        
        prompt = f"""The user is looking at an image of {query_name} and trying to guess what it is. Provide an interesting fact about this taxon that will help them identify it, but follow these rules strictly:

1. DO NOT use the scientific name ({query_name})
2. DO NOT use the common name if it exists
3. DO NOT mention the name of any parent taxonomic groups (family, order, class names)
4. DO provide distinctive physical features, behaviors, or characteristics
5. You CAN reference size comparisons to common objects or general terms like "largest in its group"
6. Keep it to 1-2 sentences
7. Make it helpful for identification

For example, instead of saying "this is the largest cat species" say "this is the largest species in its family" or describe distinctive features like stripe patterns, body size, or unique behaviors."""
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=20)
        print(f"DEBUG: get_hint - API response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"DEBUG: get_hint - Response data keys: {list(data.keys())}")
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                print(f"DEBUG: get_hint - Success: {text[:100]}...")
                return text.strip()
            else:
                print("DEBUG: get_hint - No candidates in response")
        else:
            print(f"DEBUG: get_hint - API error status {response.status_code}: {response.text}")
        
    except Exception as e:
        print(f"ERROR: get_hint - Exception occurred: {e}")
        import traceback
        traceback.print_exc()
    
    print("DEBUG: get_hint - Returning None")
    return None

def get_scoring_explanation() -> str:
    """Get explanation of the scoring system for the UI."""
    
    explanation = "Scoring System:\n"
    
    # Group by point values
    score_groups = {}
    for level, points in SCORE_VALUES.items():
        if points not in score_groups:
            score_groups[points] = []
        score_groups[points].append(level.title())
    
    # Sort by points (highest first)
    for points in sorted(score_groups.keys(), reverse=True):
        levels = score_groups[points]
        explanation += f"• {points} points: {', '.join(levels)}\n"
    
    explanation += "\nYou earn points for the most specific correct taxonomic level in your guess."
    
    return explanation

def format_score_result(points: int, matching_level: str, explanation: str, 
                       correct_answer: str, fun_fact: Optional[str] = None) -> Dict:
    """Format the complete scoring result for the UI."""
    
    result = {
        'points_earned': points,
        'matching_level': matching_level,
        'explanation': explanation,
        'correct_answer': correct_answer,
        'fun_fact': fun_fact,
        'has_fun_fact': fun_fact is not None
    }
    
    # Add encouragement message based on score
    if points >= 10:
        result['message'] = "Excellent! Perfect identification!"
    elif points >= 5:
        result['message'] = f"Great job! You guessed the correct {matching_level}!"
    elif points >= 3:
        result['message'] = f"Good work! You guessed the correct {matching_level}!"
    elif points >= 1:
        result['message'] = f"Not bad! You got the {matching_level}!"
    else:
        result['message'] = "Keep trying! Every guess helps you learn!"
    
    return result

class GameSession:
    """Manage game session state."""
    
    def __init__(self, session_id: str, taxa_list: list, questions_per_game: int = 10):
        self.session_id = session_id
        self.taxa_list = taxa_list[:questions_per_game]  # Limit to game length
        self.current_question = 0
        self.total_score = 0
        self.question_results = []
        self.questions_per_game = questions_per_game
        self.fun_facts_cache = {}  # Cache for pre-fetched fun facts
        self.hints_cache = {}  # Cache for hints
        self.current_fun_fact_request = None  # Track current background request
        self.fun_fact_fetch_index = 0  # Track which question we're fetching fun facts for
        
        # Start sequential fun fact fetching in background
        self._start_sequential_fun_fact_fetching()
    
    def get_current_taxon(self) -> Optional[Dict]:
        """Get the taxon for the current question."""
        if self.current_question < len(self.taxa_list):
            return self.taxa_list[self.current_question]
        return None
    
    def _start_sequential_fun_fact_fetching(self):
        """Start sequential fun fact fetching in background."""
        def sequential_fetcher():
            try:
                for question_index in range(len(self.taxa_list)):
                    # Check if we should stop (game might be over)
                    if question_index >= len(self.taxa_list):
                        break
                        
                    taxon = self.taxa_list[question_index]
                    print(f"DEBUG: sequential_fetcher - Starting fetch for question {question_index}")
                    
                    # Store current request info
                    self.fun_fact_fetch_index = question_index
                    
                    try:
                        fun_fact = get_fun_fact(taxon)
                        self.fun_facts_cache[question_index] = fun_fact
                        print(f"DEBUG: sequential_fetcher - Cached fun fact for question {question_index}: {'✓' if fun_fact else '✗'}")
                    except Exception as e:
                        print(f"ERROR: sequential_fetcher - Failed to fetch fun fact for question {question_index}: {e}")
                        # Continue to next question on error
                        continue
                        
                print("DEBUG: sequential_fetcher - Completed all fun fact fetching")
                        
            except Exception as e:
                print(f"ERROR: sequential_fetcher - Unexpected error: {e}")
                import traceback
                traceback.print_exc()
                
        # Start the sequential fetcher thread
        self.current_fun_fact_request = threading.Thread(target=sequential_fetcher, daemon=True)
        self.current_fun_fact_request.start()
        print("DEBUG: _start_sequential_fun_fact_fetching - Started sequential fetcher thread")
    
    def get_hint(self) -> Optional[str]:
        """Get a hint for the current question."""
        current_taxon = self.get_current_taxon()
        if not current_taxon:
            print("DEBUG: GameSession.get_hint - No current taxon available")
            return None
            
        # Check cache first
        if self.current_question in self.hints_cache:
            hint = self.hints_cache[self.current_question]
            print(f"DEBUG: GameSession.get_hint - Using cached hint for question {self.current_question}: {'✓' if hint else '✗'}")
            return hint
        
        # Generate hint
        print(f"DEBUG: GameSession.get_hint - Generating new hint for question {self.current_question}")
        hint = get_hint(current_taxon)
        self.hints_cache[self.current_question] = hint
        print(f"DEBUG: GameSession.get_hint - Generated hint: {'✓' if hint else '✗'}")
        return hint
    
    def submit_answer(self, guess_taxon: Dict, guess_name: str) -> Dict:
        """Submit an answer and calculate score."""
        
        current_taxon = self.get_current_taxon()
        if not current_taxon:
            return {'error': 'No current question'}
        
        # Calculate score
        if guess_taxon:
            points, level, explanation = calculate_score(current_taxon, guess_taxon)
        else:
            points, level, explanation = calculate_score_by_name(current_taxon, guess_name)
        
        # Get correct answer display
        correct_answer = get_correct_answer_display(current_taxon)
        
        # Get fun fact (use cached version if available, don't wait if not ready)
        fun_fact = self.fun_facts_cache.get(self.current_question)
        print(f"DEBUG: submit_answer - Fun fact for question {self.current_question}: {'cached' if fun_fact is not None else 'not available'}")
        
        # Format result (never wait for fun fact)
        result = format_score_result(points, level, explanation, correct_answer, fun_fact)
        
        # Update session state
        self.total_score += points
        self.question_results.append({
            'question_num': self.current_question + 1,
            'taxon': current_taxon,
            'guess': guess_name,
            'points': points,
            'explanation': explanation
        })
        
        self.current_question += 1
        
        # Add session info to result
        result.update({
            'total_score': self.total_score,
            'current_question': self.current_question,
            'questions_remaining': max(0, len(self.taxa_list) - self.current_question),
            'is_game_complete': self.current_question >= len(self.taxa_list)
        })
        
        return result
    
    def is_complete(self) -> bool:
        """Check if the game is complete."""
        return self.current_question >= len(self.taxa_list)
    
    def get_final_score(self) -> Dict:
        """Get final game results."""
        
        if not self.is_complete():
            return {'error': 'Game not complete'}
        
        return {
            'total_score': self.total_score,
            'questions_answered': len(self.question_results),
            'average_score': self.total_score / len(self.question_results) if self.question_results else 0,
            'question_results': self.question_results,
            'max_possible_score': len(self.taxa_list) * 10  # Assuming 10 is max per question
        }