// This is a customized version of the original script:
// https://til.simonwillison.net/llms/streaming-llm-apis
// Adapted for Replicate Streaming API documentation:
// https://replicate.com/docs/topics/predictions/streaming

async function* sseStreamIterator(apiUrl, requestBody, extraHeaders)  {

    // POST.
    let response = await fetch(apiUrl, {
        method: 'POST',
        headers: { ...{'Content-Type': 'application/json'}, ...(extraHeaders || {}) },
        body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    // Await for the body once received the premise.
    const body = await response.json();
    response = await fetch(body.urls.stream, {
        headers: {...{"Accept": "text/event-stream"}, ...(extraHeaders || {}) },
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    // NOTE: This a TextDecoder based implemenataion.
    // In the case of working with UI can use parser API for handling it via events:
    // https://www.npmjs.com/package/eventsource-parser
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    while(true) {
        const {value, done} = await reader.read();
        if (done) break;
        yield decoder.decode(value, { stream: true });

    }
}

async function handleSSE() {
    const apiUrl = 'https://api.replicate.com/v1/models/meta/meta-llama-3-70b-instruct/predictions';
    const requestBody = {
        input: {
            prompt: "What's the color of the sky?",
            stream: true    // Important to mention for sending instruction on fetching data after POST.
        },
    };

    for await (const event of sseStreamIterator(apiUrl, requestBody, {
        "Authorization": "Bearer <API-GOES-HERE>"
    })) {
        console.log(event);
    }
}

handleSSE()
