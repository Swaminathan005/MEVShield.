import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import model
from stream import stream_controller

app = FastAPI(title="MEVShield Backend")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "MEVShield Backend is running"}

@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": model.get_model() is not None,
        "model_name": model.get_model_name(),
        "threshold": model.get_optimal_threshold()
    }

# --- Stream Control Endpoints ---
@app.post("/api/start")
async def start_stream():
    stream_controller.start()
    return stream_controller.get_status()

@app.post("/api/pause")
async def pause_stream():
    stream_controller.pause()
    return stream_controller.get_status()

@app.post("/api/reset")
async def reset_stream():
    stream_controller.reset()
    return stream_controller.get_status()

# --- Data Endpoints ---
@app.get("/api/status")
async def get_status():
    return stream_controller.get_status()

@app.get("/api/transactions")
async def get_transactions():
    """
    If the stream is RUNNING, advance by one transaction (if available)
    and then return the current list of predictions (newest first).
    """
    if stream_controller.get_status()["status"] == "RUNNING":
        stream_controller.advance()
    return stream_controller.get_predictions()

@app.get("/api/statistics")
async def get_statistics():
    return stream_controller.get_statistics()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)