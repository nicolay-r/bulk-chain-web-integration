# This is a server implmentation using FastAPI framework and pydandic.
# READ: https://medium.com/@vyshali.enukonda/how-to-get-around-runtimeerror-this-event-loop-is-already-running-3f26f67e762e
import nest_asyncio
import orjson
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from bulk_chain.core.utils import dynamic_init
from bulk_chain.api import iter_content

nest_asyncio.apply()
app = FastAPI()

llm =dynamic_init(class_filepath="replicate_104.py")(
    api_token="API_TOKEN",
    model_name="meta/meta-llama-3-70b-instruct"
)

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

    # Set up the data iterator with the question
    YOUR_DATA_IT = [{"question": question}]

    content_it = iter_content(
        # 1. Your schema.              
        schema=[
            {"prompt": "{question}", "out": "response" },
        ],
        # 2. Your third-party model implementation.
        llm=llm,
        infer_mode="batch_async", 
        return_mode="chunk",
        # 4. Your iterator of dictionaries
        input_dicts_it=YOUR_DATA_IT,
        event_loop=None,
    )
        
    for batch in content_it:
        for data in batch:
            # Stream each chunk as a server-sent event
            yield f"event: done\ndata: {orjson.dumps({'data': data['response']}).decode()}\n\n"


@app.post('/stream-with-post')
async def stream_response_from_llm_post(question: Question):
    return StreamingResponse(stream_answer(question=question.question), media_type='text/event-stream')
