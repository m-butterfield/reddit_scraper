"""
Database model definitions

"""
import os

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

    @property
    def file_path(self):
        return os.path.join(settings.IMAGES_FOLDER_PATH, self.file_name)


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
