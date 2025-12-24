"""
Question Manager Service

Manages question sequence and mapping for real-time interview extraction
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import QuestionnaireQuestion
from app.core.logger import api_logger


class QuestionManager:
    """
    Manages interview questions and progression
    """
    
    # Function to initialize QuestionManager
    def __init__(self, db: Session):
        """
        Initialize question manager
        
        Args:
            db: Database session
        """
        self.db = db
        self.questions: List[QuestionnaireQuestion] = []
        self.current_index = 0
        self._load_questions()
    
    # Function to load questions from database
    def _load_questions(self):
        """Load active questions from database"""
        try:
            self.questions = (
                self.db.query(QuestionnaireQuestion)
                .filter(QuestionnaireQuestion.is_active == True)
                .order_by(QuestionnaireQuestion.question_number)
                .all()
            )
            api_logger.info(f"Loaded {len(self.questions)} questions")
        except Exception as e:
            api_logger.error(f"Error loading questions: {str(e)}")
            self.questions = []
    
    # Function to get current question
    def get_current_question(self) -> Optional[QuestionnaireQuestion]:
        """
        Get the current question
        
        Returns:
            Current question or None if no more questions
        """
        if self.current_index < len(self.questions):
            return self.questions[self.current_index]
        return None
    
    # Function to get next question
    def get_next_question(self) -> Optional[QuestionnaireQuestion]:
        """
        Move to next question and return it
        
        Returns:
            Next question or None if no more questions
        """
        self.current_index += 1
        return self.get_current_question()
    
    # Function to get question by index
    def get_question_by_index(self, index: int) -> Optional[QuestionnaireQuestion]:
        """
        Get question by index
        
        Args:
            index: Question index
            
        Returns:
            Question at index or None
        """
        if 0 <= index < len(self.questions):
            return self.questions[index]
        return None

    # Function to get question by variable name
    def get_question_by_variable_name(self, variable_name: str) -> Optional[QuestionnaireQuestion]:
        """
        Get question by variable name
        
        Args:
            variable_name: Variable name to search
            
        Returns:
            Question object or None
        """
        for q in self.questions:
            if q.variable_name == variable_name:
                return q
        return None
    
    # Function to get all questions
    def get_all_questions(self) -> List[QuestionnaireQuestion]:
        """
        Get all questions
        
        Returns:
            List of all questions
        """
        return self.questions
    
    # Function to reset question index
    def reset(self):
        """Reset to first question"""
        self.current_index = 0
    
    # Function to get progress
    def get_progress(self) -> dict:
        """
        Get current progress
        
        Returns:
            Dict with current index, total questions, and percentage
        """
        total = len(self.questions)
        percentage = (self.current_index / total * 100) if total > 0 else 0
        
        return {
            "current_index": self.current_index,
            "total_questions": total,
            "percentage": round(percentage, 1),
            "is_complete": self.current_index >= total
        }
    
    # Function to set question index
    def set_question_index(self, index: int) -> bool:
        """
        Set current question index
        
        Args:
            index: Question index to set
            
        Returns:
            True if successful, False otherwise
        """
        if 0 <= index < len(self.questions):
            self.current_index = index
            return True
        return False
