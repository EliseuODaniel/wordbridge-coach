"""SM-2 Algorithm implementation for FillTheWord"""

from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from enum import Enum


class MemoryStage(Enum):
    """SM-2 memory stages matching specification"""
    NEW = "new"
    LEARNING = "learning" 
    REVIEW = "review"
    RELEARN = "relearn"
    MATURE = "mature"


class SM2Algorithm:
    """Complete SM-2 algorithm implementation as per specification"""
    
    MIN_EASINESS_FACTOR = 1.3
    DEFAULT_EASINESS_FACTOR = 2.5
    MIN_INTERVAL_DAYS = 1
    
    @classmethod
    def calculate_next_review(
        cls,
        quality: int,
        current_repetitions: int,
        current_easiness_factor: float,
        current_interval_days: int,
    ) -> Dict[str, Any]:
        """
        Calculate next SM-2 values based on quality (0-5)
        
        Args:
            quality: SM-2 quality score 0-5
            current_repetitions: Current number of correct repetitions
            current_easiness_factor: Current easiness factor
            current_interval_days: Current interval in days
            
        Returns:
            Dictionary with updated SM-2 values
        """
        # Validate quality range
        if not 0 <= quality <= 5:
            raise ValueError("Quality must be between 0 and 5")
        
        # Update easiness factor (SM-2 formula)
        new_easiness_factor = current_easiness_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        new_easiness_factor = max(cls.MIN_EASINESS_FACTOR, new_easiness_factor)
        
        # Update repetitions and interval based on quality
        if quality < 3:
            # Failed review - reset repetitions
            new_repetitions = 0
            new_interval_days = cls.MIN_INTERVAL_DAYS
        else:
            # Successful review
            new_repetitions = current_repetitions + 1
            
            if new_repetitions == 1:
                new_interval_days = cls.MIN_INTERVAL_DAYS
            elif new_repetitions == 2:
                new_interval_days = 6
            else:
                new_interval_days = round(current_interval_days * new_easiness_factor)
        
        # Calculate next review time
        next_review_at = datetime.utcnow() + timedelta(days=new_interval_days)
        
        # Determine memory stage
        new_status = cls._calculate_memory_stage(new_repetitions, new_interval_days)
        
        return {
            "repetitions": new_repetitions,
            "easiness_factor": new_easiness_factor,
            "interval_days": new_interval_days,
            "next_review_at": next_review_at,
            "status": new_status
        }
    
    @classmethod
    def _calculate_memory_stage(cls, repetitions: int, interval_days: int) -> MemoryStage:
        """
        Calculate memory stage based on repetitions and interval
        
        Args:
            repetitions: Number of correct repetitions
            interval_days: Current interval in days
            
        Returns:
            MemoryStage enum value
        """
        if repetitions == 0:
            return MemoryStage.NEW
        elif repetitions < 3 and interval_days < 7:
            return MemoryStage.LEARNING
        elif repetitions >= 3 and interval_days >= 7 and interval_days < 21:
            return MemoryStage.REVIEW
        else:
            return MemoryStage.MATURE
    
    @classmethod
    def get_memory_stage_display(cls, stage: MemoryStage) -> int:
        """
        Get display representation for frontend (0-4 bolinhas)
        
        Returns:
            0: cinza (new)
            1-2: amarelo (learning/relearn)
            3: azul (review)
            4: verde (mature)
        """
        stage_mapping = {
            MemoryStage.NEW: 0,
            MemoryStage.LEARNING: 1,
            MemoryStage.RELEARN: 1,
            MemoryStage.REVIEW: 3,
            MemoryStage.MATURE: 4,
        }
        return stage_mapping.get(stage, 0)
    
    @classmethod
    def calculate_quality_from_response(
        cls,
        was_correct: bool,
        response_time_ms: int,
        hints_used: int = 0,
        attempts: int = 1
    ) -> int:
        """
        Calculate SM-2 quality score from user response
        
        Args:
            was_correct: Whether the answer was correct
            response_time_ms: Response time in milliseconds
            hints_used: Number of hints used
            attempts: Number of attempts taken
            
        Returns:
            Quality score 0-5
        """
        if not was_correct:
            # Quality 0-2 for incorrect answers
            if attempts <= 2:
                return 1  # Some recognition
            else:
                return 0  # Complete failure
        
        # Quality 3-5 for correct answers
        quality = 5  # Start with perfect
        
        # Reduce quality based on response time (average response time ~3000ms)
        if response_time_ms > 10000:  # Very slow
            quality -= 2
        elif response_time_ms > 5000:  # Slow
            quality -= 1
        
        # Reduce quality based on hints
        quality -= hints_used
        
        # Reduce quality based on attempts
        if attempts > 1:
            quality -= attempts - 1
        
        return max(3, min(5, quality))  # Ensure 3-5 range for correct answers
    
    @classmethod
    def validate_answer(
        cls,
        user_answer: str,
        correct_answer: str,
        synonyms: list = None
    ) -> Tuple[bool, str]:
        """
        Validate user answer with tolerance
        
        Args:
            user_answer: User's submitted answer
            correct_answer: The correct answer
            synonyms: List of acceptable synonyms
            
        Returns:
            Tuple of (is_correct, normalized_answer)
        """
        if synonyms is None:
            synonyms = []
        
        # Normalize both answers
        normalized_user = cls._normalize_answer(user_answer)
        normalized_correct = cls._normalize_answer(correct_answer)
        
        # Check direct match
        if normalized_user == normalized_correct:
            return True, normalized_correct
        
        # Check synonyms
        for synonym in synonyms:
            if normalized_user == cls._normalize_answer(synonym):
                return True, normalized_correct
        
        return False, normalized_correct
    
    @classmethod
    def _normalize_answer(cls, answer: str) -> str:
        """
        Normalize answer for comparison
        
        - Convert to lowercase
        - Remove leading/trailing whitespace
        - Remove accents
        - Remove articles (a, an, the) if present
        """
        import re
        import unicodedata
        
        # Basic cleanup
        normalized = answer.lower().strip()
        
        # Remove accents
        normalized = unicodedata.normalize('NFD', normalized)
        normalized = ''.join(c for c in normalized if not unicodedata.category(c) == 'Mn')
        
        # Remove articles at the beginning
        articles = ['a ', 'an ', 'the ']
        for article in articles:
            if normalized.startswith(article):
                normalized = normalized[len(article):]
                break
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized


# Example usage and testing
if __name__ == "__main__":
    # Test SM-2 calculation
    result = SM2Algorithm.calculate_next_review(
        quality=5,
        current_repetitions=0,
        current_easiness_factor=2.5,
        current_interval_days=1
    )
    print("SM-2 calculation result:", result)
    
    # Test answer validation
    is_correct, normalized = SM2Algorithm.validate_answer("  The Book  ", "book")
    print(f"Answer validation: {is_correct}, normalized: {normalized}")
