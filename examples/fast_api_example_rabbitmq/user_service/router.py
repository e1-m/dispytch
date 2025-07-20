import logging

from fastapi import APIRouter

from user_service.deps import EmitterDep
from user_service.events import UserCreatedEvent
from user_service.schemas import UserOut, UserIn

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post("/", response_model=UserOut)
async def create_user(user: UserIn, emitter: EmitterDep):
    logging.info(f"Doing some work with user {user.name}")
    await emitter.emit(
        UserCreatedEvent(name=user.name)
    )
    return user
