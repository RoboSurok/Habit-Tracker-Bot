from sqlalchemy import Column, Integer, String, Boolean
from .db_session import SqlAlchemyBase

class Habit(SqlAlchemyBase):
    __tablename__ = 'habits'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, index=True, nullable=False)
    name = Column(String, nullable=False)
    is_done = Column(Boolean, default=False)