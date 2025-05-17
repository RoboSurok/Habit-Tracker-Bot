import os
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import declarative_base, Session as SessionType


SqlAlchemyBase = declarative_base()
__factory = None


def global_init(db_file: str):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    db_dir = os.path.dirname(db_file)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir)

    conn_str = f"sqlite:///{db_file.strip()}"
    engine = sa.create_engine(conn_str, echo=False)

    __factory = orm.sessionmaker(bind=engine)

    from data import __all_models
    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> SessionType:
    global __factory
    if not __factory:
        raise Exception("Сессия не инициализирована. Сначала вызовите global_init().")
    return __factory()
