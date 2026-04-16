from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI(title="ADAMS Live Backend")

# Enable CORS for Flutter web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to your CSV
CSV_PATH = r"C:\Users\alley\Desktop\AI_Driver_Assistant\ai_engine\logs\driving_history.csv"

# Root
@app.get("/")
def root():
    return {"message": "ADAMS Live Backend Running"}

# Health
@app.get("/health")
def health():
    return {"status": "ok"}

# Latest state
@app.get("/state")
def state():
    try:
        df = pd.read_csv(CSV_PATH)
        latest = df.iloc[-1].to_dict()
        return latest
    except Exception as e:
        return {"error": str(e)}

# Alerts (last 5 rows)
@app.get("/alerts")
def alerts():
    try:
        df = pd.read_csv(CSV_PATH)
        last_rows = df.tail(5).to_dict(orient="records")
        return {"alerts": last_rows}
    except Exception as e:
        return {"error": str(e)}

# Schema (columns of CSV)
@app.get("/schema")
def schema():
    try:
        df = pd.read_csv(CSV_PATH, nrows=0)
        return {"columns": list(df.columns)}
    except Exception as e:
        return {"error": str(e)}