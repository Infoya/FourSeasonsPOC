from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from main import run_assistant

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    user_input: str

@app.post("/query")
async def query_endpoint(request: QueryRequest, threadid: Optional[str] = Header(None)):
    result = run_assistant(request.user_input, thread_id=threadid)
    print(result)
    return result
