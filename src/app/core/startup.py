from loguru import logger
from pydantic import EmailStr


from app.core.data.crud.user import crud_user
from app.core.data.dto.user import UserCreate


def startup(reset_database: bool = False) -> None:
    """
    System Start Up Process
    """
    logger.info("Booting D-WISE Tool Suite Backend ...")
    from config import conf
    try:
        # start and init services
        __init_services__(reset_database)
        __create_system_user__()

    except Exception as e:
        msg = f"Error while starting the API! Exception: {str(e)}"
        logger.error(msg)
        raise SystemExit(msg)

    logger.info("Started D-WISE Tool Suite Backend!")


def __init_services__(reset_database: bool = False) -> None:
    # import celery app to configure
    from app.docprepro.celery import app
    from app.core.data.repo.repo_service import RepoService
    RepoService()._create_directory_structure()
    # create SQL DBs and Tables # TODO Flo: Alembic
    from app.core.db.sql_service import SQLService
    SQLService()._create_database_and_tables(drop_if_exists=reset_database)


def __create_system_user__() -> None:
    from app.core.db.sql_service import SQLService
    with SQLService().db_session() as db_session:
        if not crud_user.exists(db=db_session, id=1):
            # TODO Flo: this is not nice.. make sure system user cannot be changed, seen from outside, login, etc
            create_dto = UserCreate(email=EmailStr("SYSTEM@DWTS.ORG"),
                                    first_name="SYSTEM",
                                    last_name="USER",
                                    password="SYSTEM")
            crud_user.create(db=db_session, create_dto=create_dto)
