from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from main import run_assistant

app = FastAPI()

class QueryRequest(BaseModel):
    user_input: str

@app.post("/query")
async def query_endpoint(request: QueryRequest, threadid: Optional[str] = Header(None)):
    result = run_assistant(request.user_input, thread_id=threadid)
    return result
