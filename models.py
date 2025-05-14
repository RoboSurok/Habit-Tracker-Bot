from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


class Habit(Base):
    __tablename__ = 'habits'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    name = Column(String)
    is_done = Column(Boolean, default=False)


engine = create_engine('sqlite:///habits.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)