"""Vocabulary progression service implementing Spec4 algorithms"""

from typing import Optional, List, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from app.models import (
    User, Word, Sentence, WordSentence, ReviewEvent,
    UserFrequencyProgress, UserSessionStats, WordFrequency, Language
)
from app.models.sentence import SourceType


WINDOW_STEP = 100
TARGET_NEW_SHARE = 0.25  # ~25% of daily cards should be new


class VocabularyProgressionService:
    """Service for managing vocabulary progression according to Spec4"""

    def __init__(self, db: Session):
        self.db = db

    def _get_user_target_language_code(self, user_id: str) -> str:
        """
        Resolve the user's target language code.

        Falls back to English to preserve previous behavior when the user or
        target language cannot be loaded.
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user or not user.target_language_id:
            return "en"

        target_language = self.db.query(Language).filter(
            Language.id == user.target_language_id
        ).first()
        if not target_language or not target_language.code:
            return "en"

        return target_language.code

    def get_or_create_user_progress(self, user_id: str) -> UserFrequencyProgress:
        """Get or create user frequency progress record"""
        progress = self.db.query(UserFrequencyProgress).filter(
            UserFrequencyProgress.user_id == user_id
        ).first()

        if not progress:
            user = self.db.query(User).filter(User.id == user_id).first()
            progress = UserFrequencyProgress(
                user_id=user_id,
                word_goal_rank=user.word_goal_rank,
                current_window_end_rank=min(100, user.word_goal_rank),
                max_contiguous_mastered_rank=0
            )
            self.db.add(progress)
            self.db.commit()
            self.db.refresh(progress)

        return progress

    def get_sentence_for_word(self, user_id: str, word_id: str, exclude_card_id: Optional[str] = None) -> Optional[Sentence]:
        """
        Get sentence for word, preferring unseen or least used sentences
        Implements getSentenceForWord(userId, wordId) from Spec4 with K=10 variety

        Args:
            user_id: User identifier
            word_id: Word identifier
            exclude_card_id: Optional card ID to exclude (avoids repeating same card)

        Algorithm:
        1. Get all sentence candidates for this word
        2. Filter out exclude_card_id if provided
        3. Query usage stats: count(*) and max(created_at) per sentence_id
        4. "Unseen" = sentences with count == 0 for this user
        5. Choose:
           - If unseen sentences exist: random choice among them
           - Else: least recently used (min max_created_at)
        6. Fallback: create basic sentence + persist + create Card
        """
        # 1. Get all sentence candidates for this word (Sentence.word_id OR WordSentence)
        sentences_via_direct = self.db.query(Sentence).filter(
            Sentence.word_id == word_id
        ).all()

        sentences_via_mapping = self.db.query(Sentence).join(
            WordSentence, WordSentence.sentence_id == Sentence.id
        ).filter(
            WordSentence.word_id == word_id
        ).all()

        # Combine and deduplicate
        all_sentences = {s.id: s for s in sentences_via_direct + sentences_via_mapping}
        candidate_sentence_ids = list(all_sentences.keys())

        if not candidate_sentence_ids:
            # Fallback: create a basic sentence if none exists
            return self._create_fallback_sentence(word_id)

        # 2. Filter out exclude_card_id if provided
        if exclude_card_id:
            # Get sentence_id from excluded card and filter it out
            from app.models import Card
            excluded_card = self.db.query(Card).filter(Card.id == exclude_card_id).first()
            if excluded_card and excluded_card.sentence_id in candidate_sentence_ids:
                candidate_sentence_ids.remove(excluded_card.sentence_id)

                # If no sentences left after exclusion, we have to use the excluded one
                # (soft exclusion - variety will come from next card)
                if not candidate_sentence_ids:
                    return all_sentences[excluded_card.sentence_id]

        # 3. Query usage statistics for each candidate sentence
        # Get count(*) and max(created_at) grouped by sentence_id
        K = 10
        usage_stats = self.db.query(
            ReviewEvent.sentence_id,
            func.count(ReviewEvent.id).label('usage_count'),
            func.max(ReviewEvent.created_at).label('last_used_at')
        ).filter(
            and_(
                ReviewEvent.user_id == user_id,
                ReviewEvent.sentence_id.in_(candidate_sentence_ids),
                ReviewEvent.sentence_id.isnot(None)
            )
        ).group_by(ReviewEvent.sentence_id).all()

        # Build lookup dictionaries
        sentence_counts = {stat.sentence_id: stat.usage_count for stat in usage_stats}
        sentence_last_used = {stat.sentence_id: stat.last_used_at for stat in usage_stats}

        # 4. Separate unseen (count == 0) from seen sentences
        unseen_sentence_ids = [
            sid for sid in candidate_sentence_ids
            if sentence_counts.get(sid, 0) == 0
        ]

        if unseen_sentence_ids:
            # Randomly choose from unseen sentences
            import random
            chosen_id = random.choice(unseen_sentence_ids)
            return all_sentences[chosen_id]

        # 5. If all sentences were seen, get the least recently used
        # Sort candidate_sentence_ids by last_used_at (ascending)
        seen_sentences_with_last_used = [
            (sid, sentence_last_used.get(sid))
            for sid in candidate_sentence_ids
            if sid in sentence_last_used
        ]

        if seen_sentences_with_last_used:
            # Sort by last_used_at ascending (oldest first)
            seen_sentences_with_last_used.sort(key=lambda x: x[1] or datetime.min)
            chosen_id = seen_sentences_with_last_used[0][0]
            return all_sentences[chosen_id]

        # Fallback: random from all candidates (shouldn't reach here normally)
        import random
        return random.choice(list(all_sentences.values()))

    def _create_fallback_sentence(self, word_id: str) -> Sentence:
        """Create a fallback sentence when no sentence exists for a word"""
        word = self.db.query(Word).filter(Word.id == word_id).first()
        if not word:
            raise ValueError(f"Word {word_id} not found")

        # Create a basic sentence
        basic_sentence = Sentence(
            text=f"This is a sentence with the word {word.text}.",
            translation=f"Esta é uma frase com a palavra {word.text}.",
            word_id=word_id,
            language_id=word.language_id,
            type="sentence",  # Legacy column
            gap_start=len("This is a sentence with the word "),
            gap_end=len("This is a sentence with the word ") + len(word.text),
            source_type=SourceType.GENERATED
        )

        self.db.add(basic_sentence)
        self.db.commit()
        self.db.refresh(basic_sentence)

        # Create WordSentence mapping
        mapping = WordSentence(
            word_id=word_id,
            sentence_id=basic_sentence.id,
            is_primary=True
        )
        self.db.add(mapping)
        self.db.commit()

        return basic_sentence

    def get_next_new_word_rank(self, user_id: str, progress: UserFrequencyProgress) -> Optional[int]:
        """
        Get the rank of the next new word to introduce
        Implements getNextNewWordRank(userId, progress) from Spec4
        """
        target_language_code = self._get_user_target_language_code(user_id)

        if progress.max_contiguous_mastered_rank == 0:
            # For new users, find the first rank that has an available word
            start_rank = 1
        else:
            start_rank = progress.max_contiguous_mastered_rank + 1

        # Search for the next available rank within current window and goal
        max_rank = min(progress.current_window_end_rank, progress.word_goal_rank)

        for candidate_rank in range(start_rank, max_rank + 1):
            # Verify word exists at this rank
            word = self.db.query(Word).join(WordFrequency,
                and_(
                    func.lower(Word.lemma) == func.lower(WordFrequency.word),
                    WordFrequency.language_code == target_language_code
                )
            ).filter(
                WordFrequency.rank == candidate_rank
            ).first()

            if word:
                return candidate_rank

        # No available words found in the current window
        return None

    def update_contiguous_mastered_rank(self, user_id: str, word_rank: int):
        """
        Update maxContiguousMasteredRank when user gets word correct for first time
        Implements the prefix advancement logic from Spec4
        """
        target_language_code = self._get_user_target_language_code(user_id)
        progress = self.get_or_create_user_progress(user_id)

        # Special handling for sparse data: if this is the first correct answer,
        # set it as the mastered rank even if it's not rank 1
        if progress.max_contiguous_mastered_rank == 0:
            print(f"DEBUG: Setting initial mastered rank to {word_rank} (first correct answer)")
            progress.max_contiguous_mastered_rank = word_rank
            self.db.commit()
            return

        # Check if this word continues the contiguous sequence
        if word_rank == progress.max_contiguous_mastered_rank + 1:
            # Try to advance the contiguous prefix
            new_rank = word_rank
            while True:
                # Check if there's a word at next rank
                next_rank_candidate = new_rank + 1
                if next_rank_candidate > progress.word_goal_rank:
                    break

                # Check if user has at least one correct for this rank
                has_correct = self.db.query(ReviewEvent).join(
                    Sentence, ReviewEvent.sentence_id == Sentence.id
                ).join(
                    Word, Sentence.word_id == Word.id
                ).join(
                    WordFrequency,
                    and_(
                        func.lower(Word.lemma) == func.lower(WordFrequency.word),
                        WordFrequency.language_code == target_language_code,
                    )
                ).filter(
                    and_(
                        ReviewEvent.user_id == user_id,
                        ReviewEvent.was_correct == True,
                        WordFrequency.rank == next_rank_candidate
                    )
                ).first()

                if not has_correct:
                    break

                new_rank = next_rank_candidate

            progress.max_contiguous_mastered_rank = new_rank

            # Check for window expansion
            if (new_rank >= progress.current_window_end_rank and
                progress.current_window_end_rank < progress.word_goal_rank):
                progress.current_window_end_rank = min(
                    progress.current_window_end_rank + WINDOW_STEP,
                    progress.word_goal_rank
                )

            self.db.commit()

    def get_due_review_words(self, user_id: str, max_rank: int) -> List[Word]:
        """Get words that are due for review within the current window"""
        target_language_code = self._get_user_target_language_code(user_id)
        # This would integrate with the existing SRS system
        # For now, return a simplified list
        return self.db.query(Word).join(
            WordFrequency,
            and_(
                func.lower(Word.lemma) == func.lower(WordFrequency.word),
                WordFrequency.language_code == target_language_code,
            )
        ).filter(
            and_(
                WordFrequency.rank <= max_rank
            )
        ).limit(50).all()

    def pick_best_review_word(self, user_id: str, candidates: List[Word]) -> Word:
        """
        Select the best review word favoring problematic words
        Implements pickBestReviewWord with scoring from Spec4
        """
        if not candidates:
            raise ValueError("No review candidates provided")

        scored_words = []
        for word in candidates:
            score = self._calculate_review_score(user_id, word)
            scored_words.append((score, word))

        # Sort by score (highest first) and return the best
        scored_words.sort(key=lambda x: x[0], reverse=True)
        return scored_words[0][1]

    def _calculate_review_score(self, user_id: str, word: Word) -> float:
        """
        Calculate review score for a word based on overdue, accuracy, and error streak
        Implements the scoring algorithm from Spec4
        """
        from datetime import timedelta

        # Get review statistics for this word
        from app.models import Card
        reviews = self.db.query(ReviewEvent).join(Card).join(Sentence).filter(
            and_(
                ReviewEvent.user_id == user_id,
                Sentence.word_id == word.id
            )
        ).all()

        if not reviews:
            return 1.0  # Neutral score for never-reviewed words

        # Calculate metrics
        total_reviews = len(reviews)
        correct_reviews = sum(1 for r in reviews if r.was_correct)
        accuracy = correct_reviews / max(1, total_reviews)

        # Calculate wrong streak (consecutive wrong answers)
        wrong_streak = 0
        for review in reversed(reviews):
            if not review.was_correct:
                wrong_streak += 1
            else:
                break

        # Calculate overdue days (simplified - would use actual SRS scheduling)
        last_review = max(reviews, key=lambda r: r.created_at)
        overdue_days = max(0, (datetime.now() - last_review.created_at).days)

        # Calculate final score
        error_bonus = 1 - accuracy
        score = 0.6 * overdue_days + 0.3 * error_bonus + 0.1 * wrong_streak

        return score

    def get_session_stats_for_today(self, user_id: str) -> UserSessionStats:
        """Get or create session stats for today"""
        today = date.today()
        stats = self.db.query(UserSessionStats).filter(
            and_(
                UserSessionStats.user_id == user_id,
                UserSessionStats.date == today
            )
        ).first()

        if not stats:
            stats = UserSessionStats(
                user_id=user_id,
                date=today,
                cards_shown=0,
                new_cards_shown=0
            )
            self.db.add(stats)
            self.db.commit()
            self.db.refresh(stats)

        return stats

    def record_card_shown(self, user_id: str, is_new_card: bool):
        """Record that a card was shown in today's session"""
        stats = self.get_session_stats_for_today(user_id)
        stats.cards_shown += 1
        if is_new_card:
            stats.new_cards_shown += 1
        self.db.commit()
