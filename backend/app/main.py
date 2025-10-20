from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logging_config import setup_logging
from app.services.scheduler import start_scheduler, stop_scheduler
from app.api.routes import auth, user, sources, youtube, rss, webhooks, newsletters, voice, crawl, trends, content, drafts, feedback, email, dashboard, llm_usage, preferences

# Setup colored logging
setup_logging(level="INFO", use_colors=True)



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="A daily feed curator and newsletter drafting assistant for independent creators",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to CreatorPulse API",
        "version": "1.0.0",
        "docs": f"{settings.BACKEND_URL}/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }



app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/api/user", tags=["User"])
app.include_router(sources.router, prefix="/api/sources", tags=["Sources"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
app.include_router(newsletters.router, prefix="/api/newsletters", tags=["Newsletters"])
app.include_router(voice.router, prefix="/api/voice", tags=["Voice Analysis"])
app.include_router(crawl.router, prefix="/api/crawl", tags=["Crawling"])
app.include_router(trends.router, prefix="/api/trends", tags=["Trends"])
app.include_router(content.router, prefix="/api/content", tags=["Content"])
app.include_router(drafts.router, prefix="/api/drafts", tags=["Drafts"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])
app.include_router(email.router, prefix="/api/email", tags=["Email"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(preferences.router, prefix="/api/user", tags=["Preferences"])
app.include_router(llm_usage.router, prefix="/api/llm/usage", tags=["LLM Usage"])

# Conditionally import Twitter routes if tweepy is available
try:
    from app.api.routes import twitter
    app.include_router(twitter.router, prefix="/api/twitter", tags=["Twitter"])
except (ImportError, ModuleNotFoundError) as e:
    print(f"Warning: Twitter routes not available: {e}")

app.include_router(youtube.router, prefix="/api/youtube", tags=["YouTube"])
app.include_router(rss.router, prefix="/api/sources/rss", tags=["RSS"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
