"""
Database model definitions and helper functions.

"""
from contextlib import contextmanager

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    create_engine,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

import settings


Base = declarative_base()
engine = create_engine(settings.DB_URI)
DBSession = sessionmaker(bind=engine)


class Post(Base):

    __tablename__ = 'post'

    name = Column(String, primary_key=True)
    image_file_hash = Column(String(40),
                             ForeignKey('image.file_hash', ondelete='cascade'),
                             nullable=False)
    subreddit_name = Column(String(20), nullable=False, index=True)
    submitted = Column(DateTime, nullable=False)
    enacted = Column(Boolean, nullable=False, default=False, index=True)

    image = relationship("Image", lazy='joined', backref="posts")


class Image(Base):

    __tablename__ = 'image'

    file_hash = Column(String(40), primary_key=True)
    file_ext = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    size = Column(BigInteger, nullable=False)

    @property
    def file_name(self):
        return self.file_hash + self.file_ext


def init_db():
    """
    Drop existing tables if needed and create new ones.

    """
    drop_tables()
    create_tables()


def create_tables():
    """
    Create the database tables.

    """
    Base.metadata.create_all(engine)


def drop_tables():
    """
    Drop the database tables.

    """
    Base.metadata.drop_all(engine)


@contextmanager
def session_manager():
    """
    Context manager for getting/committing/closing a SQLAlchemy db session.

    :rtype: DBSession

    """
    session = DBSession()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
