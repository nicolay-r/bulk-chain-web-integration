// This is a custom implementation of the POST-based stream fetching for streaming via FastAPI
// https://stackoverflow.com/questions/78826168/how-to-stream-llm-response-from-fastapi-to-react

async function* streamIterator(apiUrl, requestBody, extraHeaders)  {

    let response = await fetch(apiUrl, {
        method: 'POST',
        headers: { ...{'Content-Type': 'application/json'}, ...(extraHeaders || {}) },
        body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
    }

    // NOTE: Below you can use parser API for handling:
    // https://www.npmjs.com/package/eventsource-parser
    // Or see the original repo: https://github.com/msimoni18/so-stream-llm-response-fastapi-react
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    while(true) {
        const {value, done} = await reader.read();
        if (done) break; 
        yield decoder.decode(value);
    }
}

async function handleStream() {
    const apiUrl = 'http://localhost:4000/stream-with-post';
    const requestBody = {
        question: "What's the color of the sky?"
    };

    for await (const data of streamIterator(apiUrl, requestBody, {})) {
        console.log(data);
    }
}

handleStream()
