from sqlalchemy import Column, String, Integer, BigInteger, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import backref, declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

def get_naive_utc():
    # Strip the timezone info to create a naive UTC datetime
    # This prevents the asyncpg offset mismatch with TIMESTAMP WITHOUT TIME ZONE
    return datetime.now(timezone.utc).replace(tzinfo=None)

class User(Base):
    __tablename__ = "users"

    telegram_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    language_preference = Column(String, default="fa")
    credits = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_naive_utc)

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    amount = Column(Integer, nullable=False)
    status = Column(String, default="pending") 
    payment_method = Column(String, default="card") 
    receipt_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=get_naive_utc)

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    subject = Column(String, default="")
    status = Column(String, default="open")
    created_at = Column(DateTime, default=get_naive_utc)
    updated_at = Column(DateTime, default=get_naive_utc)

    user = relationship("User", backref="support_tickets")

class SupportMessage(Base):
    __tablename__ = "support_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey("support_tickets.id"), nullable=False)
    sender = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=get_naive_utc)

    ticket = relationship("SupportTicket", backref=backref("messages", order_by="SupportMessage.created_at"))

class Release(Base):
    __tablename__ = "releases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"))
    track_url = Column(String, nullable=False)
    cover_url = Column(String, nullable=False)
    song_name = Column(String, nullable=False)
    artist_name = Column(String, nullable=False)
    producers = Column(Text, nullable=True)
    legal_name = Column(String, nullable=False)
    release_date = Column(String, nullable=False)
    genre = Column(String, nullable=True)
    sub_genre = Column(String, nullable=True)
    mapping_spotify = Column(String, nullable=True)
    mapping_apple = Column(String, nullable=True)
    profile_email = Column(String, nullable=True)
    requires_new_profile = Column(Boolean, default=False)
    
    # Financial and Logic Flags
    is_edit = Column(Boolean, default=False)
    copyright_requested = Column(Boolean, default=False)
    
    # State tracking for the Selenium Bot worker
    status = Column(String, default="pending") 
    created_at = Column(DateTime, default=get_naive_utc)

    user = relationship("User", backref="releases")
