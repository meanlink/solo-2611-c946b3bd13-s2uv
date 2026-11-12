from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.database import Base, engine
from src.middlewares.errors import unhandled_error_handler
from src.middlewares.rate_limit import RateLimitMiddleware
from src.migrations import ensure_columns
from src.routes import analyses, analysis_runs, audit, auth, datasets, health, reviews, runs, workspace
from src.services.errors import ReviewConflictError


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_columns(engine)
    yield


app = FastAPI(title="交易异常复核台", lifespan=lifespan)


@app.exception_handler(ReviewConflictError)
async def review_conflict_handler(request, exc: ReviewConflictError):
    # 409 带回服务端最新版本与最新结论，前端提示冲突且不覆盖前人判断。
    return JSONResponse(
        status_code=409,
        content={
            "detail": exc.message,
            "conflict": True,
            "current_version": exc.current_version,
            "latest_decision": exc.latest_decision,
        },
    )
app.add_middleware(RateLimitMiddleware, limit=180, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_exception_handler(Exception, unhandled_error_handler)

for router in (health.router, auth.router, workspace.router, datasets.router,
               analyses.router, analysis_runs.router, runs.router, reviews.router,
               audit.router):
    app.include_router(router, prefix="/api")
