import requests
import os
import sys
import json
from transformers import pipeline

# Azure AI setup details
# lKey and lEndpoint are placeholders for the actual, confidential values. they need to be inserted before running.
LANGUAGE_KEY = os.environ['LANGUAGE_KEY'] if 'LANGUAGE_KEY' in os.environ else 'lKey'
LANGUAGE_ENDPOINT = os.environ['LANGUAGE_ENDPOINT'] if 'LANGUAGE_ENDPOINT' in os.environ else 'lEndpoint'

# defining variable for Azure AI API limit to avoid magic number in code
apiInputLimit = 5


# default only allows for max. 512 tokens, manually increased it to 1024 tokens
translator = pipeline("translation", model="Helsinki-NLP/opus-mt-en-de", max_length=1024)


# Azure API call
def run_pii(texts: list, start_idx=1):
    body = {'kind': 'PiiEntityRecognition',
            'language': 'de',
            'parameters': {'modelVersion': 'latest'},
            'analysisInput': {'documents': []}}

    cnt = start_idx
    for text in texts:
        body['analysisInput']['documents'].append({'id': cnt,
                                                   'text': text})
        cnt += 1

    return requests.post(url=f'{LANGUAGE_ENDPOINT}/language/:analyze-text?api-version=2023-04-01', json=body,
                         headers={"Content-Type": "application/json", "Ocp-Apim-Subscription-Key": LANGUAGE_KEY})

# helper method to split data into subsets due to API input limit
def get_subset(data, apiInputLimit):
    phrases = data.readlines()
    for currentIndex in range(0, len(phrases), apiInputLimit):
        yield phrases[currentIndex: currentIndex + apiInputLimit]

# helper method to parse data input
def parse_data(phrases: list):
    input = []
    for phrase in phrases:
        input.append(phrase.strip())
    return input

# helper method to return translation by the opus model
def translate_data(phrases: list):
    translatedList = []
    for phrase in phrases:
        translation = translator(phrase)
        # extracting the translation part from the output
        translatedList.append(translation[0]['translation_text'])
    return translatedList

# helper method to extract confidence score from returned json output
def get_confidence_score(string: input):
    resp = run_pii(input)
    content = resp.json()

    print(content)
    for document in content['results']['documents']:
        if 'entities' in document:
            for entity in document['entities']:
                print('text: ' + entity['text'])
                cScore = entity.get('confidenceScore', None)
                print('Confidence Score: ' + str(cScore))
                print()
        print()


data = open('patient_info_and_summary.txt', 'r')
# due to API size limit, split file into subsets of max. size apiInputLimit for api calls
for subset in get_subset(data, apiInputLimit):
    input = parse_data(subset)
    translatedList = translate_data(input)
    print(translatedList)
    print()
    get_confidence_score(translatedList)