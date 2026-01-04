from os.path import dirname, basename, join

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
from arelight.run.infer import create_infer_parser


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

    def setup_collection_name(value):
        # Considering Predefined name if the latter has been declared.
        if value is not None:
            return value
        # Use the name of the file.
        if args.from_files is not None:
            return basename(args.from_files[0]) if len(args.from_files) == 1 else "from-many-files"
        if args.from_dataframe is not None:
            return basename(args.from_dataframe[0])

        return "samples"

    parser = create_infer_parser()

    # Parsing arguments.
    args = parser.parse_args()

    # Other parameters.
    predict_table_name = "bulk_chain"
    collection_name = setup_collection_name(value=args.collection_name)
    output_dir = dirname(args.output_template) if dirname(args.output_template) != "" else args.output_template
    collection_target_func = lambda data_type: join(output_dir, "-".join([collection_name, data_type.name.lower()]))

    # Init NER model.
    ner_model_type = dynamic_init(class_filepath=args.ner_provider)

    # Init Translator model.
    translate_model = dynamic_init(class_filepath=args.translate_provider) \
        if args.translate_provider is not None else None

    # Stream output from logging.
    pipeline, settings = create_inference_pipeline(
        args=args,
        files_iter=["input.txt"],
        predict_table_name=predict_table_name,
        collection_target_func=collection_target_func,
        translator_args={
            "model": translate_model() if translate_model is not None else None,
            "src": args.translate_text.split(':')[0] if args.translate_text is not None else None,
            "dest": args.translate_text.split(':')[1] if args.translate_text is not None else None,
        },
        ner_args={
            "model": ner_model_type(model=args.ner_model_name),
            "obj_filter": None if args.ner_types is None else lambda s_obj: s_obj.ObjectType in args.ner_types,
            "chunk_limit": 128
        },
        inference_args={
            "model": "meta/meta-llama-3-70b-instruct",
            "class_name": "replicate_104.py",
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
            }
        }
    )

    # TODO. This is temporary for supporting legacy backend settings.
    if args.backend == "d3js_graphs":
        labels_fmt = {a: v for a, v in map(lambda item: item.split(":"), args.d3js_label_names.split(','))}
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
