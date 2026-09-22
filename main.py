from fastapi import FastAPI, Depends
from pyrate_limiter import Duration, Limiter, Rate
from fastapi_limiter.depends import RateLimiter
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis

from src.routes import contacts, users, auth
from src.conf.config import settings


app = FastAPI()


app.include_router(
    contacts.router,
    prefix="/api",
)

app.include_router(
    users.router,
    prefix="/api",
)

app.include_router(
    auth.router,
    prefix="/api",
)


origins = [
    "http://localhost:3000"
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/",
    dependencies=[
        Depends(
            RateLimiter(
                limiter=Limiter(
                    Rate(5, Duration.SECOND * 10)
                )
            )
        )
    ]
)
async def read_root():
    """
    Returns a basic response from the root endpoint.

    The endpoint is used to check whether the FastAPI application
    is running and accessible. Access to the endpoint is limited
    to a maximum of 5 requests within 10 seconds.

    :return: A welcome message confirming that the application
        is running.
    :rtype: dict
    """
    
    return {
        "message": "Hello World"
    }
