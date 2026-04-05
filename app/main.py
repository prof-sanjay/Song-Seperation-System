import logging
from fastapi import FastAPI
from api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

app = FastAPI(
    title="Audio Separation API",
    description="Scalable Audio Pipeline Backend using FastAPI with unified architecture",
    version="1.0.0"
)

# Connect decoupled routing logics
app.include_router(router, prefix="/api")

@app.get("/")
def health_check():
    """
    Base level liveness check for Cloud deployments (e.g. Azure App Service / AKS ping logic).
    """
    return {"status": "healthy", "service": "Audio Separation API"}
