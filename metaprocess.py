import openai
import os
import json
from util.gpt_util import logprobs_to_probs

import mplib

def metaprocess(input, input_transform, prompt_template, generation_settings, output_transform):
    # print(f"Input: '{input}'\n")
    transformed_input = input_transform(input)
    # print(f"Transformed input: '{transformed_input}'\n")
    prompt = prompt_template(transformed_input)
    # print(f"Prompt: '{prompt}'\n")
    # output = model_call(prompt)
    output = call_model(prompt, **generation_settings)
    # print(f"Output: '{output}'\n")
    transformed_output = output_transform(output)
    # print(f"Transformed output: '{transformed_output}'")
    return transformed_output

def call_model_completion(prompt, engine="ada", n=1, temperature=1, max_tokens=20, logprobs=0, stop=None):
    openai.api_key = os.environ.get("OPENAI_API_KEY", None)
    response = openai.Completion.create(
        engine=engine,
        prompt=prompt,
        n=n,
        temperature=temperature,
        max_tokens=max_tokens,
        logprobs=logprobs,
        stop=stop
    )
    return response

def call_model_chat(prompt, engine="gpt-3.5-turbo", n=1, temperature=1, max_tokens=20, logprobs=0, stop=None):
    openai.api_key = os.environ.get("OPENAI_API_KEY", None)
    response = openai.ChatCompletion.create(
        model=engine,
        messages=[{"role":"user","content":prompt}],
        n=n,
        temperature=temperature,
        max_tokens=max_tokens,
        stop=stop
    )
    return response

def call_model(prompt, **generation_settings):
    # get engine type from generation_settings
    engine = generation_settings['engine']
    # if the engine type is a chatbot, call the different API
    if engine in ["gpt-3.5-turbo", "gpt-3.5-turbo-16k", "gpt-4"]:
        return call_model_chat(prompt, **generation_settings)
    else:
        return call_model_completion(prompt, **generation_settings)

def get_completion_text(response):
    return response.choices[0].text

def get_chat_completion_text(response):
    return response.choices[0].message.content

def get_completion_branches(response):
    # returns an array of text of completion branches
    return [choice.text for choice in response.choices]

def get_chat_completion_branches(response):
    # returns an array of text of chat completion branches
    return [choice.message.content for choice in response.choices]

def get_judgement_probability(response, yes_tokens=["Yes", "yes", "Y", "y", " Yes", " yes", " Y", " y"], no_tokens=["No", "no", "N", "n", " No", " no", " N", " n"]):
    # gets the probability of the first token of the response being a yes or no
    logprobs = response.choices[0]['logprobs']['top_logprobs'][0]
    yes_tokens = [token for token in yes_tokens if token in logprobs]
    no_tokens = [token for token in no_tokens if token in logprobs]
    yes_probability = sum([logprobs_to_probs(logprobs.get(token, 0)) for token in yes_tokens])
    no_probability = sum([logprobs_to_probs(logprobs.get(token, 0)) for token in no_tokens])
    return yes_probability / (yes_probability + no_probability)


metaprocess_headers = {}

metaprocesses = {
    # "author_attribution": author_attribution,
    #"detect_swearing": detect_swearing
}

# load metaprocess headers from files
for filename in os.listdir("./config/metaprocesses/headers"):
    if filename.endswith(".json"):
        with open(f"./config/metaprocesses/headers/{filename}", "r") as f:
            data = json.load(f)
        name = filename.split(".")[0]
        metaprocess_headers[name] = data["prompt"]

# load metaprocesses from files
for filename in os.listdir("./config/metaprocesses"):
    if filename.endswith(".json"):
        with open(f"./config/metaprocesses/{filename}", "r") as f:
            data = json.load(f)
        name = filename.split(".")[0]
        metaprocesses[name] = {
            "id": data["id"] if "id" in data else None,
            "description": data["description"],
            "input_transform": data["input_transform"],
            "prompt_template": data["prompt_template"],
            "output_transform": data["output_transform"],
            "generation_settings": data["generation_settings"],
            "output_type": data["output_type"]
        }

        # update (or add) to mplib index
        mplib.update(metaprocesses[name])

def save_metaprocess(metaprocess_name, data):
    with open(f"./config/metaprocesses/{metaprocess_name}.json", "w") as f:
        json.dump(data, f, indent=4)
        
    # update (or add) to mplib index
    if "id" not in data or data["id"] == None:
        data["id"] = metaprocess_name.lower().replace(" ","_")
    mplib.update(data)

def execute_metaprocess(metaprocess_name, input):
    metaprocess_data = metaprocesses[metaprocess_name]
    return metaprocess(
        input,
        input_transform=eval(metaprocess_data["input_transform"]),
        prompt_template=eval(metaprocess_data["prompt_template"]),
        generation_settings=metaprocess_data["generation_settings"],
        output_transform=eval(metaprocess_data["output_transform"])
    )