from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    telegram_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    language_preference = Column(String, default="fa")
    credits = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    amount = Column(Integer, nullable=False)
    status = Column(String, default="pending") 
    payment_method = Column(String, default="card") 
    receipt_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="transactions")

class Release(Base):
    __tablename__ = "releases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    track_url = Column(String, nullable=False)
    cover_url = Column(String, nullable=False)
    song_name = Column(String, nullable=False)
    artist_name = Column(String, nullable=False)
    legal_name = Column(String, nullable=False)
    release_date = Column(String, nullable=False)
    mapping_spotify = Column(String, nullable=True)
    mapping_apple = Column(String, nullable=True)
    requires_new_profile = Column(Boolean, default=False)
    
    # Financial and Logic Flags
    is_edit = Column(Boolean, default=False)
    copyright_requested = Column(Boolean, default=False)
    
    # State tracking for the Selenium Bot worker
    status = Column(String, default="pending") 
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", backref="releases")