import re
from detoxify import Detoxify
import torch

# Set up Detoxify
cuda_available = torch.cuda.is_available()
detox = Detoxify('unbiased-small', device='cuda' if cuda_available else 'cpu')

def bad_keyword(text, negative_keywords):
    for keyword in negative_keywords:
        if text.find(keyword) > -1:
            return True
    return False

def is_toxic(text,thresholds):
    try:
        scores = detox.predict(text)
    except Exception as e:
        print(e)
        return True
    if scores:
        for attribute in thresholds.keys():
            score = scores[attribute]
            print(f"{attribute}: {score}")
            if score > thresholds[attribute]:
                return True
    else:
        # err on the side of blocking
        return True
    return False


def clean_text(generated_text):
    # look for any '!!!'; take the part before it
    clean_text = generated_text.split('!!!')[0]
    # look for last newline
    truncate = clean_text.rfind('\n')
    if truncate > -1:
        clean_text = clean_text[:truncate]
        return clean_text
    # if we can't find a newline, look for terminal punctuation
    pmatch = re.search(r'[?.!]', clean_text)
    if pmatch:
        trimpart = re.split(r'[?.!"]', clean_text)[-1]
        clean_text = clean_text.replace(trimpart, '')
        return clean_text
    return clean_text
