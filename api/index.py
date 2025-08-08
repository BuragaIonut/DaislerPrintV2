from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/api")
async def root():
    return {"message": "Hello from FastAPI backend!"}

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

# This handler is required for Vercel
handler = Mangum(app)