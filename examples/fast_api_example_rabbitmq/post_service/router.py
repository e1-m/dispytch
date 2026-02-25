import logging

from fastapi import APIRouter

from .deps import EmitterDep
from .events import PostCreatedEvent
from .schemas import PostOut, PostIn

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)


@router.post("/", response_model=PostOut)
async def create_post(post: PostIn, emitter: EmitterDep):
    logging.info(f"Doing some work with post {post.title}")
    await emitter.emit(
        PostCreatedEvent(
            title=post.title,
            content=post.content,
        )
    )
    return post
