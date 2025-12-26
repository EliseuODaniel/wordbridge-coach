"""All database models"""

# Import models in dependency order to avoid mapper issues
from app.models.base import BaseModel
from app.models.language import Language
from app.models.word import Word  # Word before Sentence
from app.models.word_frequency import WordFrequency
from app.models.word_theme import WordTheme
from app.models.word_theme_mapping import WordThemeMapping
from app.models.deck import Deck
from app.models.sentence import Sentence  # Sentence depends on Word and Language
from app.models.word_sentence import WordSentence  # Word-Sentence mapping
from app.models.card import Card  # Card depends on Sentence and Deck
from app.models.user import User
from app.models.user_card_state import UserCardState, MemoryStage
from app.models.user_word_stats import UserWordStats
from app.models.user_theme_stats import UserThemeStats
from app.models.user_daily_stats import UserDailyStats
from app.models.user_session_stats import UserSessionStats
from app.models.user_frequency_progress import UserFrequencyProgress
from app.models.review_event import ReviewEvent
from app.models.chat_conversation import ChatConversation
from app.models.chat_message import ChatMessage, MessageRole
from app.models.chat_lesson_history import ChatLessonHistory
from app.models.user_llm_preferences import UserLLMPreferences

__all__ = [
    "BaseModel",
    "Language",
    "Deck",
    "Word",
    "WordFrequency",
    "WordTheme",
    "WordThemeMapping",
    "Sentence",
    "WordSentence",
    "Card",
    "User",
    "UserCardState",
    "MemoryStage",
    "UserWordStats",
    "UserThemeStats",
    "UserDailyStats",
    "UserSessionStats",
    "UserFrequencyProgress",
    "ReviewEvent",
    "ChatConversation",
    "ChatMessage",
    "MessageRole",
    "ChatLessonHistory",
    "UserLLMPreferences",
]
