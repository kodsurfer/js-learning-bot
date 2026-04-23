from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=True)
    level = Column(String, default="beginner")
    goal = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    completed_lessons = relationship("CompletedLesson", back_populates="user", cascade="all, delete-orphan")
    completed_exercises = relationship("CompletedExercise", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, name={self.name})>"


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=False)  # Markdown content
    order = Column(Integer, nullable=False, default=0)
    difficulty = Column(String, default="beginner")  # beginner, intermediate, advanced
    estimated_time = Column(Integer)  # in minutes
    is_active = Column(Boolean, default=True)

    # Relationships
    exercises = relationship("Exercise", back_populates="lesson", cascade="all, delete-orphan")
    completed_lessons = relationship("CompletedLesson", back_populates="lesson")

    def __repr__(self):
        return f"<Lesson(id={self.id}, title={self.title})>"


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    question = Column(Text, nullable=False)
    code_template = Column(Text, nullable=True)
    correct_answer = Column(Text, nullable=False)  # could be JSON for multiple choice
    answer_type = Column(String, default="code")  # code, multiple_choice, text
    options = Column(Text, nullable=True)  # JSON array for multiple choice
    explanation = Column(Text, nullable=True)
    points = Column(Integer, default=10)

    # Relationships
    lesson = relationship("Lesson", back_populates="exercises")
    completed_exercises = relationship("CompletedExercise", back_populates="exercise")

    def __repr__(self):
        return f"<Exercise(id={self.id}, lesson_id={self.lesson_id})>"


class CompletedLesson(Base):
    __tablename__ = "completed_lessons"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons.id"), nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    score = Column(Float, default=0.0)

    # Relationships
    user = relationship("User", back_populates="completed_lessons")
    lesson = relationship("Lesson", back_populates="completed_lessons")

    def __repr__(self):
        return f"<CompletedLesson(user_id={self.user_id}, lesson_id={self.lesson_id})>"


class CompletedExercise(Base):
    __tablename__ = "completed_exercises"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    user_answer = Column(Text, nullable=True)
    is_correct = Column(Boolean, default=False)
    attempts = Column(Integer, default=1)

    # Relationships
    user = relationship("User", back_populates="completed_exercises")
    exercise = relationship("Exercise", back_populates="completed_exercises")

    def __repr__(self):
        return f"<CompletedExercise(user_id={self.user_id}, exercise_id={self.exercise_id})>"


class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_lessons = Column(Integer, default=0)
    completed_lessons = Column(Integer, default=0)
    total_exercises = Column(Integer, default=0)
    completed_exercises = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    last_active = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="progress")

    def __repr__(self):
        return f"<UserProgress(user_id={self.user_id}, completed={self.completed_lessons})>"
      
