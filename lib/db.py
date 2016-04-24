"""
Database model definitions

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
from sqlalchemy.orm import sessionmaker

import settings


Base = declarative_base()
engine = create_engine(settings.DB_URI)
DBSession = sessionmaker(bind=engine)


class Post(Base):

    __tablename__ = 'post'

    id = Column(String, primary_key=True)
    image_file_hash = Column(
        String(40), ForeignKey('image.file_hash'), nullable=False)
    subreddit_name = Column(String(20), nullable=False)
    submitted = Column(DateTime, nullable=False)


class Image(Base):

    __tablename__ = 'image'

    file_hash = Column(String(40), primary_key=True)
    file_ext = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    size = Column(BigInteger, nullable=False)
    enacted = Column(Boolean, nullable=False, default=False, index=True)


def init_db():
    """
    Create the database tables

    """
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@contextmanager
def db_session():
    """
    Context manager for SQLAlchemy sessions

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
