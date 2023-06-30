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
    scores = detox.predict(text)
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
    generated_text = generated_text.split('!!!')[0]
    # look for last newline
    truncate = generated_text.rfind('\n')
    if truncate > -1:
        cleanStr = generated_text[:truncate]
        return cleanStr
    # if we can't find a newline, look for terminal punctuation
    pmatch = re.search(r'[?.!]', generated_text)
    if pmatch:
        trimpart = re.split(r'[?.!"]', generated_text)[-1]
        cleanStr = generated_text.replace(trimpart, '')
        return cleanStr
    return None
