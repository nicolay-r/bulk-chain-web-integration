import nest_asyncio
from os.path import join

import orjson
from bulk_chain.core.utils import dynamic_init
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from arekit.common.data.input.providers.text.single import BaseSingleTextProvider
from arekit.common.pipeline.base import BasePipelineLauncher
from arelight.api import create_inference_pipeline
from arelight.pipelines.demo.labels.formatter import CustomLabelsFormatter
from arelight.run.utils import merge_dictionaries
from arelight.pipelines.result import PipelineResult


nest_asyncio.apply()
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
    

async def stream_answer(text):

    def class_to_int(text):
        if 'positive' in text.lower():
            return 1
        elif 'negative' in text.lower():
            return -1 
        return 0

    # Other parameters.
    predict_table_name = "bulk_chain"
    collection_name = "test_samples"
    output_dir = "./"
    collection_target_func = lambda data_type: join(output_dir, "-".join([collection_name, data_type.name.lower()]))

    # Init NER model.
    ner_model_type = dynamic_init(class_filepath="providers/dp_130.py")

    # Init Translator model.
    translate_model = dynamic_init(class_filepath="providers/googletrans_402.py")

    # Stream output from logging.
    pipeline, settings = create_inference_pipeline(
        sampling_args={
            "sentence_parser": "nltk:english",
            "terms_per_context": 50,
            "docs_limit": 1, 
            "csv_sep": ',',
            "csv_column": "text",
        },
        files_iter=["input.txt"],
        predict_table_name=predict_table_name,
        collection_target_func=collection_target_func,
        translator_args={
            "model": translate_model() if translate_model is not None else None,
            "src": "auto",
            "dest": "en"
        },
        ner_args={
            "model": ner_model_type(model="ner_ontonotes_bert_mult"),
            "obj_filter": lambda s_obj: s_obj.ObjectType in ["ORG", "PERSON", "LOC", "GPE"],
            "chunk_limit": 128
        },
        inference_args={
            "model": "meta/meta-llama-3-70b-instruct",
            "class_name": "providers/replicate_104.py",
            "api_key": "API-KEY",
            "task_kwargs": {
                "schema": [{
                    "prompt": f"Given text: {{{BaseSingleTextProvider.TEXT_A}}}" +
                              f"TASK: Classify sentiment attitude of [SUBJECT] to [OBJECT]: "
                              f"positive, "
                              f"negative, "
                              f"neutral.",
                    "out": "response"
                }],
                "classify_func": lambda row: class_to_int(row['response']),
                'labels_fmt': "u:0,p:1,n:2"
            }
        },
        batch_size=1,
    )

    # TODO. This is temporary for supporting legacy backend settings.
    d3js_label_names = "p:pos,n:neg,u:neu"
    labels_fmt = {a: v for a, v in map(lambda item: item.split(":"), d3js_label_names.split(','))}
    settings.append({
        "labels_formatter": CustomLabelsFormatter(**labels_fmt),
        "d3js_collection_name": collection_name,
        "d3js_collection_description": collection_name,
        "d3js_graph_output_dir": output_dir
    })

    # Launch application.
    BasePipelineLauncher.run(
        pipeline=pipeline,
        pipeline_ctx=PipelineResult(merge_dictionaries(settings)),
        has_input=False)

    event = "completed"
    chunk = "done!"
    yield f"event: {event}\ndata: {orjson.dumps({'data': chunk}).decode()}\n\n"


@app.post('/stream-with-post')
async def stream_response_from_llm_post(question: Question):
    return StreamingResponse(stream_answer(text=question.question), media_type='text/event-stream')
