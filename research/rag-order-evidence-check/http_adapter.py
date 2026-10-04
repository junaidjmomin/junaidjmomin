"""Optional structured endpoint adapter; never called by the default run."""
import json
import os
import urllib.request


def respond(question, passages, seed):
    endpoint = os.environ['RAG_EVAL_ENDPOINT']
    headers = {'Content-Type': 'application/json'}
    if os.environ.get('RAG_EVAL_TOKEN'):
        headers['Authorization'] = 'Bearer ' + os.environ['RAG_EVAL_TOKEN']
    request = urllib.request.Request(endpoint, json.dumps({
        'question': question, 'passages': passages, 'seed': seed
    }).encode(), headers=headers, method='POST')
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)
