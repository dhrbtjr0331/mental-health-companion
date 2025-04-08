from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
import requests
import sqlite3
import os

app = FastAPI()

DB_PATH = "database.db"
# Create DB if it does not exist
if not os.path.exists(DB_PATH):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry TEXT,
                happiness INTEGER,
                sadness INTEGER,
                anger INTEGER,
                tiredness INTEGER,
                anxiety INTEGER,
                calmness INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

# --------------------Data models--------------------
class JournalEntry(BaseModel):
    entry: str
    happiness: int
    sadness: int
    anger: int
    tiredness: int
    anxiety: int
    calmness: int

class SuggestionRequest(BaseModel):
    entry: str

class JournalResponse(BaseModel):
    id: int
    entry: str
    happiness: int
    sadness: int
    anger: int
    tiredness: int
    anxiety: int
    calmness: int
    timestamp: str

# Route: POST /suggestions
@app.post("/suggestions")
def get_coping_suggestions(request: SuggestionRequest):
    try:
        # Prompt engineering
        prompt = f"Here is a jornal entry: '{request.entry}' What are 3 coping strategies you would recommend?"

        # Payload for llama-server
        payload = {
            "prompt": prompt,
            "n_predict": 100, 
            "temperature": 0.7,
            "stop": ["\n\n"]
        }

        # Send request to local LLaMA server
        response = requests.post("http://localhost:8080/completion", json=payload)
        response.raise_for_status()
        result = response.json()

        return {
            "suggestions": result.get("content", "").strip()
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error communicating with LLaMA server: {e}")

# Route: POST /journal
@app.post("/journal")
def save_journal(entry: JournalEntry):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO journal (entry, happiness, sadness, anger, tiredness, anxiety, calmness) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (entry.entry, entry.happiness, entry.sadness, entry.anger, entry.tiredness, entry.anxiety, entry.calmness)
            )
            conn.commit()
        return {"message": "Journal entry saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Route: GET /mood
@app.get("/mood", response_model=List[JournalResponse])
def get_moods():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, entry, happiness, sadness, anger, tiredness, anxiety, calmness, timestamp FROM journal ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "entry": row[1],
                    "happiness": row[2],
                    "sadness": row[3],
                    "anger": row[4],
                    "tiredness": row[5],
                    "anxiety": row[6],
                    "calmness": row[7],
                    "timestamp": row[8]
                } for row in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
