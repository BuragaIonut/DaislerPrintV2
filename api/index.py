from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

# Expose routes at the function root so they work behind /api/index
@app.get("/")
async def root():
    return {"message": "Hello from FastAPI backend!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Optional: keep compatibility if hitting /api/* directly in local setups
@app.get("/api")
async def root_api():
    return {"message": "Hello from FastAPI backend!"}

@app.get("/api/health")
async def health_api():
    return {"status": "healthy"}

# This handler is required for Vercel
handler = Mangum(app)