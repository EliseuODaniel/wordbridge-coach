"""Card selection service implementing Spec4 intelligent mixing"""

from typing import Optional, Dict, Any, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime

from app.models import (
    User, Word, Sentence, Card, UserFrequencyProgress, UserSessionStats, ReviewEvent
)
from app.services.vocabulary_progression import VocabularyProgressionService


class CardSelectionService:
    """Service for intelligent card selection with new/review mixing"""

    def __init__(self, db: Session):
        self.db = db
        self.progression_service = VocabularyProgressionService(db)

    def get_next_card_for_user(self, user_id: str, exclude_card_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get next card for user implementing Spec4's getNextCardForUser algorithm
        Mixes new words (25%) with reviews (75%) and reinforces errors

        Args:
            user_id: User identifier
            exclude_card_id: Optional card ID to exclude from selection (avoids immediate repetition)
        """
        # Get user progress and session stats
        progress = self.progression_service.get_or_create_user_progress(user_id)
        session_stats = self.progression_service.get_session_stats_for_today(user_id)

        # Debug logs removidos para produção

        # Calculate new share for today
        new_share = 0
        if session_stats.cards_shown > 0:
            new_share = session_stats.new_cards_shown / session_stats.cards_shown

        # Get review candidates (only from unlocked prefix)
        review_candidates = self.get_due_review_words(
            self.db, user_id, max_count=50
        )

        # Check if we can introduce a new word
        from app.services.vocabulary_progression import TARGET_NEW_SHARE
        can_introduce_new = (
            new_share < TARGET_NEW_SHARE and
            self.progression_service.get_next_new_word_rank(user_id, progress) is not None
        )

        if can_introduce_new:
            # Introduce new word
            next_rank = self.progression_service.get_next_new_word_rank(user_id, progress)
            print(f"DEBUG: get_next_new_word_rank returned: {next_rank}")
            if not next_rank:
                # No more new words available, fall back to review
                return self._get_review_card(user_id, review_candidates, exclude_card_id)

            # Try to find a word starting from next_rank, handling exclude
            max_attempts = 10  # Prevent infinite loops
            current_rank = next_rank

            while current_rank <= min(progress.current_window_end_rank, progress.word_goal_rank) and max_attempts > 0:
                word = self._get_word_by_rank(current_rank, user_id, exclude_card_id)
                print(f"DEBUG: _get_word_by_rank({current_rank}) returned: {word}")

                if word:
                    print(f"DEBUG: Word details - text: '{word.text}', id: {word.id}")
                    # Found a valid word, break the loop
                    break

                # Word not found or was excluded, try next rank
                current_rank += 1
                max_attempts -= 1
                print(f"DEBUG: Word not found at rank {current_rank-1}, trying rank {current_rank}")

            if not word:
                # No word found in the window, fall back to review
                print(f"DEBUG: No word found in ranks {next_rank}-{current_rank-1}, falling back to review")
                return self._get_review_card(user_id, review_candidates, exclude_card_id)

            sentence = self.progression_service.get_sentence_for_word(user_id, word.id)
            card_context = self._build_card_context(word, sentence, is_new=True)
            print(f"DEBUG: card_context card_id: '{card_context.get('card_id', 'MISSING')}'")

            # Record the new card in session stats
            self.progression_service.record_card_shown(user_id, is_new_card=True)

            return card_context

        else:
            # Choose review word
            return self._get_review_card(user_id, review_candidates, exclude_card_id)

    def _get_review_card(self, user_id: str, review_candidates, exclude_card_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get a review card from candidates

        Args:
            user_id: User identifier
            review_candidates: Available review candidates
            exclude_card_id: Optional card ID to exclude from selection
        """
        if not review_candidates:
            # No review candidates available, could introduce new word if possible
            progress = self.progression_service.get_or_create_user_progress(user_id)
            next_rank = self.progression_service.get_next_new_word_rank(user_id, progress)

            if next_rank:
                word = self._get_word_by_rank(next_rank, user_id, exclude_card_id)

                if word:
                    sentence = self.progression_service.get_sentence_for_word(user_id, word.id)
                    card_context = self._build_card_context(word, sentence, is_new=True)
                    self.progression_service.record_card_shown(user_id, is_new_card=True)
                    return card_context
            return None

        # Pick best review word (favoring problematic words)
        # Convert tuples to words for the service
        review_words = [candidate[0] for candidate in review_candidates] if review_candidates else []
        if not review_words:
            return None

        # Filter out excluded word if provided
        if exclude_card_id:
            # Get word_id from the excluded card_id
            from app.models import Card
            excluded_card = self.db.query(Card).filter(Card.id == exclude_card_id).first()
            if excluded_card and excluded_card.sentence and excluded_card.sentence.word_id:
                excluded_word_id = str(excluded_card.sentence.word_id)
                review_words = [word for word in review_words if str(word.id) != excluded_word_id]
                if not review_words:
                    return None

        word = self.progression_service.pick_best_review_word(user_id, review_words)
        sentence = self.progression_service.get_sentence_for_word(user_id, word.id)
        card_context = self._build_card_context(word, sentence, is_new=False)

        # Record the review card in session stats
        self.progression_service.record_card_shown(user_id, is_new_card=False)

        return card_context

    def _get_word_by_rank(self, rank: int, user_id: str = None, exclude_card_id: Optional[str] = None) -> Optional[Word]:
        """Get word by frequency rank with deterministic lookup and proper gating

        Args:
            rank: Target frequency rank
            user_id: User identifier for gating
            exclude_card_id: Optional card ID to exclude from selection (will be converted to word_id)
        """
        from app.models import WordFrequency
        from app.models.user_frequency_progress import UserFrequencyProgress
        from app.models import Language

        # Get user's target language for proper filtering
        target_language_code = "en"  # Default fallback
        max_allowed_rank = None

        if user_id:
            # Get user's language and gating constraints
            user = self.db.query(User).filter(User.id == user_id).first()
            if user and user.target_language_id:
                target_lang = self.db.query(Language).filter(Language.id == user.target_language_id).first()
                if target_lang:
                    target_language_code = target_lang.code

            progress = self.db.query(UserFrequencyProgress).filter(UserFrequencyProgress.user_id == user_id).first()
            if progress:
                max_allowed_rank = min(progress.current_window_end_rank, progress.word_goal_rank)
                max_unlocked_rank = progress.max_contiguous_mastered_rank

                # Critical gating: only allow access to words within unlocked prefix
                # For new users (max_contiguous_mastered_rank = 0), allow access to first available word
                # For users with progress, allow access to words within reasonable range of mastered prefix
                if max_unlocked_rank > 0:
                    # Allow access to words within the mastered prefix AND a reasonable range for sparse data
                    # This handles cases where we have sparse data (e.g., words at ranks 38, 49, 50, etc.)
                    if rank > max_unlocked_rank + 50:  # Allow up to 50 ranks ahead for sparse data
                        print(f"DEBUG: Gating blocked rank {rank} (max_unlocked_rank={max_unlocked_rank}, range limit=50)")
                        return None

        # Try exact rank match first (using lemma like Insights API for consistency)
        query = self.db.query(Word).join(WordFrequency,
            and_(
                func.lower(Word.lemma) == func.lower(WordFrequency.word),
                WordFrequency.language_code == target_language_code
            )
        ).filter(
            WordFrequency.rank == rank
        )

        word = query.first()

        if word:
            # Verificação adicional: garantir que o rank corresponde ao esperado
            # Isso previne problemas de dados inconsistentes no banco
            if user_id and max_allowed_rank and rank > max_allowed_rank:
                print(f"DEBUG: Rank {rank} > max_allowed_rank {max_allowed_rank}, violação de gating!")
                return None

            # Check if this is the excluded word (convert exclude_card_id to word_id)
            if exclude_card_id:
                from app.models import Card as CardModel
                excluded_card = self.db.query(CardModel).filter(CardModel.id == exclude_card_id).first()
                if excluded_card and excluded_card.sentence and excluded_card.sentence.word_id:
                    if str(word.id) == str(excluded_card.sentence.word_id):
                        print(f"DEBUG: Excluded word {word.id} found (from card {exclude_card_id}), returning None")
                        return None

            return word

        # If exact rank not found, try deterministic fallback within allowed window
        if user_id and max_allowed_rank:
            # Find the next available rank within the window
            next_available = self.db.query(WordFrequency).filter(
                and_(
                    WordFrequency.rank >= rank,
                    WordFrequency.rank <= max_allowed_rank,
                    WordFrequency.language_code == target_language_code
                )
            ).order_by(WordFrequency.rank).first()

            if next_available:
                # Find corresponding word (using lemma for consistency)
                word = self.db.query(Word).join(WordFrequency,
                    and_(
                        func.lower(Word.lemma) == func.lower(WordFrequency.word),
                        WordFrequency.language_code == target_language_code
                    )
                ).filter(
                    WordFrequency.rank == next_available.rank
                ).first()
                return word

        # No suitable word found within constraints
        return None

    def _build_card_context(
        self,
        word: Word,
        sentence: Optional[Sentence],
        is_new: bool
    ) -> Dict[str, Any]:
        """
        Build card context for API response with REAL Card ID
        Implements buildCardContext(word, sentence, { isNew: true/false }) from Spec4

        CRITICAL: Always returns a real card_id from an existing Card in the database.
        If Card doesn't exist for the Sentence, creates it on-demand.
        """
        if not sentence:
            # Create fallback sentence
            sentence = self.progression_service._create_fallback_sentence(word.id)

        # CRITICAL: Find or create Card for this sentence
        card = self.db.query(Card).filter(Card.sentence_id == sentence.id).first()

        if not card:
            # Card doesn't exist - create on-demand (Spec4 requirement)
            from app.models import Deck
            import uuid

            # Get or create a default deck for the word's language
            deck = self.db.query(Deck).filter(
                and_(
                    Deck.language_id == word.language_id,
                    Deck.is_active == True
                )
            ).first()

            if not deck:
                # Create a default deck if none exists
                deck = Deck(
                    id=str(uuid.uuid4()),
                    name=f"Default {word.language_id or 'EN'}",
                    language_id=word.language_id,
                    difficulty_level=1,
                    description=f"Auto-generated deck for {word.language_id}",
                    is_active=True
                )
                self.db.add(deck)
                self.db.flush()

            # Create the Card
            card = Card(
                id=str(uuid.uuid4()),
                sentence_id=sentence.id,
                deck_id=deck.id,
                grammar_hint=sentence.grammar_hint or f"{word.part_of_speech}",
                difficulty=word.difficulty or 1,
                gap_start=sentence.gap_start,
                gap_end=sentence.gap_end,
                is_active=True
            )
            self.db.add(card)
            self.db.flush()
            print(f"DEBUG: Created on-demand Card {card.id} for Sentence {sentence.id}")

        # Build context with REAL card_id
        return {
            "card_id": str(card.id),  # CRITICAL: Real Card.id
            "word_id": str(word.id),
            "sentence_id": str(sentence.id),  # Added for Spec4 variety tracking
            "word": word.text,
            "sentence": sentence.text,
            "sentence_translation": sentence.translation or "",
            "grammar_hint": sentence.grammar_hint or f"{word.part_of_speech}",
            "gap": {
                "start": sentence.gap_start,
                "end": sentence.gap_end
            },
            "is_new": is_new,
            "difficulty": word.difficulty,
            "audio_word_url": f"http://localhost:8001/api/tts/word/{card.id}?text={word.text}&lang=en",  # Use card.id for TTS
            "audio_sentence_url": f"http://localhost:8001/api/tts/sentence/{card.id}?text={sentence.text.replace('___', word.text)}&lang=en"
        }

    def record_answer(
        self,
        user_id: str,
        word_id: str,
        sentence_id: str,
        was_correct: bool,
        response_time_ms: int,
        quality: int
    ):
        """
        Record user answer and update progression
        This integrates with existing ReviewEvent system and adds Spec4 progression logic
        """
        # Get word rank for progression update
        from app.models import WordFrequency
        from app.models.word import Word

        # Try to get Word with WordFrequency data
        word = None

        # First try: direct query with WordFrequency join (use MIN rank to get the correct frequency)
        from app.models.word import Word

        # Get the word first
        word_obj = self.db.query(Word).filter(Word.id == word_id).first()
        if word_obj:
            # Get the MIN frequency rank for this word
            wf = self.db.query(func.min(WordFrequency.rank)).filter(
                func.lower(WordFrequency.word) == func.lower(word_obj.lemma),
                WordFrequency.language_code == "en"
            ).scalar()

            if wf:
                word_obj.frequency_rank = wf
                word = word_obj
            else:
                word = None
        else:
            word = None

        # Fallback: try without WordFrequency join and get rank separately
        if not word:
            word = self.db.query(Word).filter(Word.id == word_id).first()
            if word:
                # Try to get frequency rank separately
                wf = self.db.query(WordFrequency).filter(
                    func.lower(WordFrequency.word) == func.lower(word.lemma),
                    WordFrequency.language_code == "en"
                ).first()
                if wf:
                    word.frequency_rank = wf.rank

        if word and was_correct:
            # Update contiguous mastered rank if this is first time correct
            self._check_and_update_first_time_correct(user_id, word_id, getattr(word, 'frequency_rank', None))
            print(f"DEBUG: Updated progression for word '{word.text}' (rank: {getattr(word, 'frequency_rank', 'unknown')})")

        # Note: The actual ReviewEvent creation would be handled by the existing system
        # This method focuses on the Spec4 progression logic

    def get_due_review_words(
        self, db: Session, user_id: str, max_count: int = 50
    ) -> List[Tuple['Word', 'UserCardState', int]]:
        """Get words that are due for review, limited by unlocked rank"""
        from app.models.user_frequency_progress import UserFrequencyProgress
        from app.models.word import Word
        from app.models.user_card_state import UserCardState
        from app.models.word_frequency import WordFrequency

        # Get user's progress to enforce rank gating
        progress = db.query(UserFrequencyProgress).filter(UserFrequencyProgress.user_id == user_id).first()
        max_unlocked_rank = progress.max_contiguous_mastered_rank if progress else 1

        # Use proper SQLAlchemy relationships for joins
        # UserCardState -> Card -> Sentence -> Word -> WordFrequency
        from app.models.card import Card
        from app.models.sentence import Sentence
        query = (
            db.query(Word, UserCardState, WordFrequency.rank)
            .join(Sentence, Word.id == Sentence.word_id)
            .join(Card, Sentence.id == Card.sentence_id)
            .join(UserCardState, Card.id == UserCardState.card_id)
            .join(WordFrequency, Word.text == WordFrequency.word)
            .filter(
                UserCardState.user_id == user_id,
                UserCardState.next_review_at <= datetime.utcnow(),  # Due for review
                WordFrequency.rank <= max_unlocked_rank,  # CRITICAL: Only review unlocked words
            )
            .order_by(WordFrequency.rank)
            .limit(max_count)
        )

        return query.all()

    def _check_and_update_first_time_correct(self, user_id: str, word_id: str, word_rank: int):
        """Check if this is first correct answer and update progression if needed"""
        from app.models import Card

        # Check if user has been correct before - need to join through Card
        previous_correct = self.db.query(ReviewEvent).join(Card).join(Sentence).filter(
            ReviewEvent.user_id == user_id,
            Sentence.word_id == word_id,
            ReviewEvent.was_correct == True
        ).first()

        if not previous_correct and word_rank:
            # First time correct - update progression
            self.progression_service.update_contiguous_mastered_rank(user_id, word_rank)