import re
import yaml

def get_yaml_header(code):
    pattern = r"---([\s\S]+)---"
    matches = re.search(pattern, code)
    if matches is None:
        return None
    header = yaml.load(matches.group(1))
    return header
