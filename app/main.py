from fastapi import FastAPI
from app.routes import sections, tasks, resources, blocks, traffic
from app.routes import dashboard
from app.routes import alerts
from app.routes import auth

app = FastAPI(title="ThinkSync Backend")

app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(alerts.router, prefix="/api", tags=["alerts"])
app.include_router(dashboard.router, prefix="/api", tags=["dashboard"])
app.include_router(sections.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(resources.router, prefix="/api")
app.include_router(blocks.router, prefix="/api")
app.include_router(traffic.router, prefix="/api")


@app.get("/api/health")
def health_check():
    return {"status": "ok"}