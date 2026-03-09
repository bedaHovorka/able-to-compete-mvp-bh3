from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, Text, Uuid, Table, UniqueConstraint
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid
from app.utils.database import Base


class CardPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Association table for many-to-many between cards and labels
card_labels = Table(
    "card_labels",
    Base.metadata,
    Column("card_id", Uuid(as_uuid=True), ForeignKey("cards.id", ondelete="CASCADE"), primary_key=True),
    Column("label_id", Uuid(as_uuid=True), ForeignKey("labels.id", ondelete="CASCADE"), primary_key=True),
)


class Board(Base):
    __tablename__ = "boards"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True, index=True)
    user_id = Column(Uuid(as_uuid=True), nullable=True)

    lists = relationship("List", back_populates="board", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="board", cascade="all, delete-orphan")
    labels = relationship("Label", back_populates="board", cascade="all, delete-orphan")


class List(Base):
    __tablename__ = "lists"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(Uuid(as_uuid=True), ForeignKey("boards.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    position = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    board = relationship("Board", back_populates="lists")
    cards = relationship("Card", back_populates="list", cascade="all, delete-orphan")


class Card(Base):
    __tablename__ = "cards"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    list_id = Column(Uuid(as_uuid=True), ForeignKey("lists.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(Integer, nullable=False, default=0)
    due_date = Column(DateTime, nullable=True)
    completed = Column(Boolean, default=False)
    priority = Column(
        SQLEnum("low", "medium", "high", "critical", name="cardpriority"),
        nullable=False,
        server_default="medium"
    )
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    list = relationship("List", back_populates="cards")
    labels = relationship("Label", secondary="card_labels", back_populates="cards")
    comments = relationship("Comment", back_populates="card", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_id = Column(Uuid(as_uuid=True), ForeignKey("cards.id"), nullable=False, index=True)
    user_id = Column(Uuid(as_uuid=True), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    card = relationship("Card", back_populates="comments")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(Uuid(as_uuid=True), ForeignKey("boards.id"), nullable=False, index=True)
    user_id = Column(Uuid(as_uuid=True), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Uuid(as_uuid=True), nullable=False)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    board = relationship("Board", back_populates="activities")


class Label(Base):
    __tablename__ = "labels"
    __table_args__ = (UniqueConstraint("board_id", "name", name="uq_label_board_name"),)

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    board_id = Column(Uuid(as_uuid=True), ForeignKey("boards.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    board = relationship("Board", back_populates="labels")
    cards = relationship("Card", secondary="card_labels", back_populates="labels")
