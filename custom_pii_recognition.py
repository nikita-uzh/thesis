import requests
import os
import sys
import json

# Azure AI setup details
# lKey and lEndpoint are placeholders for the actual, confidential values. they need to be inserted before running.
LANGUAGE_KEY = os.environ['LANGUAGE_KEY'] if 'LANGUAGE_KEY' in os.environ else 'lKey'
LANGUAGE_ENDPOINT = os.environ['LANGUAGE_ENDPOINT'] if 'LANGUAGE_ENDPOINT' in os.environ else 'lEndpoint'

# defining variable for Azure AI API limit to avoid magic number in code
apiInputLimit = 5


# Azure API call
def run_pii(texts: list, lang='de', start_idx=1):
    # customize entities recognized with 'piiCategories' list to detect non-default categories such as DateTime as well
    body = {'kind': 'PiiEntityRecognition',
            'parameters': {'modelVersion': 'latest',
                           'piiCategories': ['Person', 'PersonType', 'PhoneNumber', 'Organization', 'DateTime',
                                             'Address', 'Email']},
            'analysisInput': {'documents': []}}

    cnt = start_idx
    for text in texts:
        body['analysisInput']['documents'].append({'id': cnt,
                                                   'language': lang,
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

# helper method to extract confidence score from returned json output
def get_confidence_score(string: input):
    resp = run_pii(input)
    content = resp.json()

    for document in content['results']['documents']:
        print('redacted text: ' + document['redactedText'])
        if 'entities' in document:
            for entity in document['entities']:
                cScore = entity.get('confidenceScore', None)
                print('Confidence Score: ' + str(cScore))
        print()


data = open('wikiann_samples.txt', 'r')
# due to API size limit, split file into subsets of max. size apiInputLimit for api calls
for subset in get_subset(data, apiInputLimit):
    input = parse_data(subset)
    get_confidence_score(input)