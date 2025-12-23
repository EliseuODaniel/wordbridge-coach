"""UserSessionStats model for daily session statistics"""

from sqlalchemy import Column, Integer, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class UserSessionStats(BaseModel):
    """Daily session statistics for each user"""

    __tablename__ = "user_session_stats"

    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    date = Column(Date, nullable=False)  # "YYYY-MM-DD"
    cards_shown = Column(Integer, nullable=False, default=0)
    new_cards_shown = Column(Integer, nullable=False, default=0)

    # Relationships
    user = relationship("User", back_populates="session_stats")

    # Ensure one record per user per day
    __table_args__ = (
        {"schema": None},
    )