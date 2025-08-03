# This is a server implmentation using FastAPI framework and pydandic.
import orjson
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

app.add_middleware(
     CORSMiddleware,
     allow_origins=['*'],
     allow_credentials=False,
     allow_methods=['*'],
     allow_headers=['*']
)

class Question(BaseModel):
    question: str

async def stream_answer(question):
    # YOUR CODE WITH LLM OR OTHER STREAMING SERVICE GOES HERE.
    CATEGORY = "sentence"
    CHUNKS = ["This", "is", "a", "streamed", "response", "that", "would", "be", "received"]
    for chunk in CHUNKS:
        # THIS IS A TEMPLATE OF THE OUTPUT CHUNK [json-serialized to support of `\n` and other characters]
        # https://medium.com/@thiagosalvatore/the-line-break-problem-when-using-server-sent-events-sse-1159632d09a0
        # Requires installation of orjson.
        yield f"event: {CATEGORY}\ndata: {orjson.dumps({'data': chunk}).decode()}\n\n"


@app.post('/stream-with-post')
async def stream_response_from_llm_post(question: Question):
    return StreamingResponse(stream_answer(question=question.question), media_type='text/event-stream')
