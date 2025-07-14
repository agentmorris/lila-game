#!/usr/bin/env python3
"""
Game logic and scoring for Wildlife Camera Trap Game.
"""

import os
import requests
from typing import Dict, Optional, Tuple

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
    'superclass': 1,
    'subphylum': 1,
    'phylum': 1,
    'kingdom': 1
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
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return None
    
    # Determine what to ask about
    most_specific_name = taxon.get('most_specific_name')
    common_name = taxon.get('common_name')
    
    if not most_specific_name:
        return None
    
    # Construct query
    query_name = common_name if common_name else most_specific_name
    
    try:
        # Use Gemini API to get fun fact
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={api_key}"
        
        prompt = f"Give me one interesting, brief fun fact about {query_name}. Keep it to 1-2 sentences and focus on behavior, habitat, or unique characteristics. Do not mention taxonomy or classification."
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'candidates' in data and len(data['candidates']) > 0:
                text = data['candidates'][0]['content']['parts'][0]['text']
                return text.strip()
        
    except Exception as e:
        print(f"Error getting fun fact: {e}")
    
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
    
    def get_current_taxon(self) -> Optional[Dict]:
        """Get the taxon for the current question."""
        if self.current_question < len(self.taxa_list):
            return self.taxa_list[self.current_question]
        return None
    
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
        
        # Get fun fact
        fun_fact = get_fun_fact(current_taxon)
        
        # Format result
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