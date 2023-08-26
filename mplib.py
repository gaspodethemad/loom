# TODO BEFORE PUSH: delete this file, build mplib package from https://github.com/gaspodethemad/mplib, install via pip.

import openai
import numpy as np
from usearch.index import Index

import os
import json

# Initialize usearch index
# TODO: look into usearch multi-index lookups for when we have multiple types (desc, trace, prompt, etc)

PATH_INDEX_DESC = './index_desc.usearch'
PATH_INDEX_TRACE = './index_trace.usearch'
PATH_MP_LIST = './mp_list.json'
EMBEDDING_MODEL = 'text-embedding-ada-002'

# overwrite these if environment variables are present
if 'MPLIB_INDEX_DESC' in os.environ:
    PATH_INDEX_DESC = os.environ.get('MPLIB_INDEX_DESC')
if 'MPLIB_INDEX_TRACE' in os.environ:
    PATH_INDEX_TRACE = os.environ.get('MPLIB_INDEX_TRACE')
if 'MPLIB_MP_LIST' in os.environ:
    PATH_MP_LIST = os.environ.get('MPLIB_MP_LIST')
if 'MPLIB_EMBEDDING_MODEL' in os.environ:
    EMBEDDING_MODEL = os.environ.get('MPLIB_EMBEDDING_MODEL')

# set OpenAI API key & organization
openai.api_key = os.environ.get("OPENAI_API_KEY", None)
openai.organization = os.environ.get("OPENAI_ORGANIZATION", None)

index_desc = Index(
    ndim=1536,
    metric='cos',
    dtype='f32'
)

index_trace= Index(
    ndim=1536,
    metric='cos',
    dtype='f32'
)

if os.path.exists(PATH_INDEX_DESC):
    index_desc.load(PATH_INDEX_DESC)

if os.path.exists(PATH_INDEX_TRACE):
    index_trace.load(PATH_INDEX_TRACE)

mp_list = {}

if os.path.exists(PATH_MP_LIST):
    with open(PATH_MP_LIST, 'r') as f:
        mp_list = json.load(f)
        
def add(mp):
    """
    Adds a metaprocess `dict` into the `usearch.index.Index` `index_desc`.
    :mp: `dict`
    :return: `None`
    """

    # get MP description
    desc = mp['description']

    # embed description
    desc_embedding = openai.Embedding.create(model=EMBEDDING_MODEL, input=[desc])['data'][0]['embedding']

    # convert to numpy array
    desc_v = np.array(desc_embedding)

    # get MP id
    mp_id = mp["id"]

    # add index to MP
    mp_index = next_index()

    # add MP to list
    mp_list[mp_id] = mp.copy()
    mp_list[mp_id]["index"] = mp_index

    # add description & metaprocess to index_desc
    index_desc.add(mp_index, desc_v)

    # add trace & metaprocess to index_trace
    if 'traces' in mp:
        response = openai.Embedding.create(model=EMBEDDING_MODEL, input=mp['traces'])
        trace_embeddings = [np.array(e["embedding"]) for e in response["data"]]
        trace_v = np.mean(trace_embeddings, 0) # average traces

        index_trace.add(mp_index, trace_v)

    # save index_desc
    index_desc.save(PATH_INDEX_DESC)

    # save index_trace
    index_trace.save(PATH_INDEX_TRACE)

    # save metaprocess list
    with open(PATH_MP_LIST, 'w') as f:
        json.dump(mp_list, f)

def search(desc, k=5):
    # create query embedding
    desc_embedding = openai.Embedding.create(model=EMBEDDING_MODEL, input=[desc])['data'][0]['embedding']

    # convert to numpy array
    desc_embedding = np.array(desc_embedding)

    # search index_desc for MP
    matches = index_desc.search(desc_embedding, k)

    return [(mp_list[match.key], match.distance) for match in matches]

def update(mp):
    """
    Updates or adds a metaprocess stored in mplib.
    :param mp: a metaprocess stored in the mplib
    :return: None
    """
    if mp["id"] not in mp_list:
        add(mp)
        return
    
    # if description has updates, update description and vector
    if mp["description"] != mp_list[mp["id"]]["description"]:
        description_v = np.array(openai.Embedding.create(model=EMBEDDING_MODEL, input=[mp["description"]])['data'][0]['embedding'])
        index_desc.remove(mp["id"]["index"])
        index_desc.add(mp["id"]["index"], description_v)

        # update mp (preserve index)
        mp_index = mp_list[mp["id"]]["index"]
        mp_list[mp["id"]] = mp.copy()
        mp_list[mp["id"]]["index"] = mp_index

    # if available, add traces
    if "traces" in mp:
        if "traces" not in mp_list[mp["id"]]:
            add_traces(mp)
    else:
        # just update the metaprocess itself
        mp_index = mp_list[mp["id"]]["index"]
        mp_list[mp["id"]] = mp.copy()
        mp_list[mp["id"]]["index"] = mp_index

# TODO: add only new traces
def add_traces(mp):
    """
    Adds an MP to index_trace.
    :param mp: a metaprocess with "traces"
    :return: None
    """

    if "traces" not in mp:
        return

    response = openai.Embedding.create(model=EMBEDDING_MODEL, input=mp['traces'])
    trace_embeddings = [np.array(e["embedding"]) for e in response["data"]]
    trace_v = np.mean(trace_embeddings, 0) # average traces

    index_trace.add(mp["id"]["index"], trace_v)

    if mp["id"] not in mp_list:
        mp_list[mp["id"]] = mp
        mp_list[mp["id"]]["index"] = next_index()

def next_index():
    """Returns a new index value for a metaprocess"""
    if len(mp_list) == 0:
        return 0
    indices = [mp["index"] for mp in mp_list.values()]
    i = 0
    while i in indices:
        i += 1
    return i