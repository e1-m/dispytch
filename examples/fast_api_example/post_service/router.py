import logging

from fastapi import APIRouter

from post_service.deps import EmitterDep
from post_service.events import PostCreatedEvent
from post_service.schemas import PostOut, PostIn

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
