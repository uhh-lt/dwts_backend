from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from loguru import logger
from uvicorn import Config, Server

from api.endpoints import general, project, user, source_document, code
from app.core.data.crud.crud_base import NoSuchElementError
from app.core.db.sql_service import SQLService
from config import conf

# create the FastAPI app
app = FastAPI(
    title="D-WISE Tool Suite Backend API",
    description="The REST API for the D-WISE Tool Suite Backend",
    version="alpha_mwp_1"
)

# Handle CORS
# TODO Flo: Handle CORS via ReverseProxy in FrontEnd!
origins = [
    "http://localhost",
    "http://localhost:8080",
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include the endpoint routers
app.include_router(general.router)
app.include_router(user.router)
app.include_router(project.router)
app.include_router(source_document.router)
app.include_router(code.router)


# add custom exception handlers
@app.exception_handler(NoSuchElementError)
async def no_such_element_error_handler(request, exc: NoSuchElementError):
    return PlainTextResponse(str(exc), status_code=404)


@app.exception_handler(NotImplementedError)
async def no_such_element_error_handler(request, exc: NotImplementedError):
    return PlainTextResponse(str(exc), status_code=501)


@app.on_event("startup")
def startup_event():
    try:
        logger.info("Booting D-WISE Tool Suite Backend ...")
        SQLService()._create_database_and_tables(drop_if_exists=False)
        logger.info("Started D-WISE Tool Suite Backend!")

    except Exception as e:
        msg = f"Error while starting the API! Exception: {str(e)}"
        logger.error(msg)
        raise SystemExit(msg)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting Down D-WISE Tool Suite Backend!")


if __name__ == "__main__":
    # read port from config
    port = int(conf.api.port)
    assert port is not None and isinstance(port, int) and port > 0, \
        "The API port has to be a positive integer! E.g. 8081"

    server = Server(
        Config(
            "main:app",
            host="0.0.0.0",
            port=port,
            log_level=conf.logging.level.lower(),
            debug=True,
            reload=True
        ),
    )

    server.run()
