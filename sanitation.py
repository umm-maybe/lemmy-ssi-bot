import re

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