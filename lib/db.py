"""
Database model definitions

"""
from contextlib import contextmanager

from sqlalchemy import (
    Column,
    create_engine,
    ForeignKey,
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

    id = Column(String(64), primary_key=True)
    image_id = Column(String(40), ForeignKey('image.id'), nullable=False)
    subreddit_name = Column(String(20), nullable=False, index=True)


class Image(Base):

    __tablename__ = 'image'

    id = Column(String(40), primary_key=True)


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
