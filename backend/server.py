from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

app = FastAPI(title="ADAMS Live Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_PATH = r"C:\Users\alley\Desktop\AI_Driver_Assistant\logs\driving_history.csv"


def _to_bool(value):
    return str(value).strip().lower() in ("true", "1", "yes")


def normalize_row(row: dict):
    msg = str(
        row.get("spoken_text")
        or row.get("speech")
        or row.get("ai_text")
        or row.get("message")
        or ""
    ).strip()

    trigger = str(row.get("trigger", "")).strip()

    driver_state = str(
        row.get("driver_state")
        or row.get("driverState")
        or trigger
        or msg
        or "Monitoring"
    ).strip()

    buzzer_value = row.get("buzzer", row.get("buzzer_active", False))

    return {
        "timestamp": str(row.get("timestamp", "")),
        "input": str(row.get("input", "")),
        "level": str(row.get("level", "INFO")),
        "message": msg,
        "spoken_text": msg,
        "buzzer": _to_bool(buzzer_value),
        "driver_state": driver_state,
        "source_path": CSV_PATH,
    }


@app.get("/")
def root():
    return {"message": "ADAMS Live Backend Running"}


@app.get("/health")
def health():
    try:
        df = pd.read_csv(CSV_PATH, engine="python", on_bad_lines="skip")
        return {
            "status": "ok",
            "rows_loaded": len(df),
            "csv_path": CSV_PATH,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.get("/state")
def state():
    try:
        df = pd.read_csv(CSV_PATH, engine="python", on_bad_lines="skip")
        if df.empty:
            return {
                "timestamp": "",
                "input": "",
                "level": "INFO",
                "message": "No data yet",
                "spoken_text": "No data yet",
                "buzzer": False,
                "driver_state": "Monitoring",
                "source_path": CSV_PATH,
            }

        latest = df.iloc[-1].to_dict()
        return normalize_row(latest)

    except Exception as e:
        return {"error": str(e)}


@app.get("/alerts")
def alerts():
    try:
        df = pd.read_csv(CSV_PATH, engine="python", on_bad_lines="skip")
        if df.empty:
            return []

        last_rows = df.tail(10).to_dict(orient="records")
        return [normalize_row(row) for row in reversed(last_rows)]

    except Exception as e:
        return [{
            "timestamp": "",
            "input": "",
            "level": "ERROR",
            "message": str(e),
            "spoken_text": str(e),
            "buzzer": False,
            "driver_state": "Error",
            "source_path": CSV_PATH,
        }]


@app.get("/schema")
def schema():
    try:
        df = pd.read_csv(CSV_PATH, engine="python", on_bad_lines="skip", nrows=0)
        return {"columns": list(df.columns)}
    except Exception as e:
        return {"error": str(e)}