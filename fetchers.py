import re
import os
import requests
import requests_cache

# Cache requests to avoid repeated network calls
requests_cache.install_cache('requests_cache', expire_after=3600*24)

file_index = 0 

def parse_latex_tag(latex_tag):
    # Regular expression pattern to extract command, environment, and options
    pattern = r'\\(\w+){([^[\]{}]*)}(\[.*?\])?'

    # Extracting command, environment, and options using regex
    matches = re.match(pattern, latex_tag)

    if matches:
        command = matches.group(1)
        environment = matches.group(2)
        options = matches.group(3)
        return {
            "Command": command,
            "Environment": environment,
            "Options": options if options else None
        }
    else:
        return None
# Tags that are removed from the LaTeX content
JUNK_BEGIN_END_TAGS = [
    'center',
    'column',
    'columns', 
    'document',
    'frame',
    'itemize',
    'nparagraph',
    'slideshow',
]
JUNK_TAGS = [
    'documentclass',
    'importmodule',
    'tociftopnotes',
    'libinput',
    'mhgraphics',
    'nvideonugget',
    'symdecl',
] 

SHOW_OPTIONS_TAGS = [
    'begin',
]

SHOW_ENVIRONMENT_TAGS = [
    'frametitle',
]

def clear_cache():
    requests_cache.clear()

def get_raw_stex_url(archive: str, filename: str):
    return f"https://gl.mathhub.info/{archive}/-/raw/main/source/{filename}"
# https://gl.mathhub.info/courses/jacobs/GenICT/course/-/blob/main/source/python/slides/strings.en.tex

def get_raw_stex(archive: str, filename: str):
    url = get_raw_stex_url(archive, filename)
    return requests.get(url).text

def transform_line(line: str, debug=False):
    line = line.strip()
    if line.startswith('%'):
        return None
    for tag in JUNK_TAGS:
        if line.startswith('\\' + tag):
            return '%% removed: ' + line if debug else None
    return line
    

def replace_inputref_line(fallback_archive: str, line: str):
    line = line.strip()


    match = re.match(r'\\inputref\*?(?:\[(.*?)\])?\{(.*?)\}', line)
    if match:
        archive, filename = match.groups()
        if archive is None:
           archive = fallback_archive
        return f'File: [{archive}]{{{filename}}}]\n' +  get_recursive_stex(archive, filename + '.tex')
    return line

def replace_inputref(archive: str, text: str):
    return '\n'.join([replace_inputref_line(archive, line) for line in text.split('\n')])

def transform_line(line: str, debug=False):
    line = line.strip()
    if line.startswith('%'):
        return None
    for tag in JUNK_TAGS:
        if line.startswith('\\' + tag):
            return '%% removed: ' + line if debug else None
        return line
    for tag in SHOW_OPTIONS_TAGS:
        if line.startswith('\\' + tag):
            parsed = parse_latex_tag(line)
            options = parsed['Options']
            if options is None:
                options = ''
            if debug:
                return options + f' was ....{line}....'
            return options

    for tag in SHOW_ENVIRONMENT_TAGS:
        if line.startswith('\\' + tag):
            parsed = parse_latex_tag(line)
            if parsed is None:
                continue
            env = parsed['Environment']
            if env is None:
                env = ''
            if debug:
                return env + f' was ....{line}....'
            return env
    return line

def cleanup_stex(text: str):
    return '\n'.join([transform_line(line) for line in text.split('\n')
                     if transform_line(line) is not None])

# def cleanup_stex(text: str):
    # Remove LaTeX comments
    text = re.sub(r'%.*$', '', text, flags=re.MULTILINE)
    
    # Remove LaTeX commands and environments
    text = re.sub(r'\\(providecommand|documentclass|gdef|maketitle|inputref|tociftopnotes|usemodule|input|classoptions|usepackage|title|author|date|frametitle|begin|end|chapter|section|subsection|paragraph|subparagraph)\{.*?\}', '', text)
    
    # Remove any remaining LaTeX braces and brackets
    text = re.sub(r'\{.*?\}', '', text)  # Curly braces
    text = re.sub(r'\[.*?\]', '', text)  # Square brackets
    
    # Remove any LaTeX commands that might still be present
    text = re.sub(r'\\[a-zA-Z]+', '', text)
    
    # Remove any stray asterisks or symbols
    text = re.sub(r'\*', '', text)
    
    # Clean up multiple spaces and newlines
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()

    return text

# This function is designed to only fetch content for a specific archive and filename
def get_stex_content(archive: str, filename: str) -> str:
    url = f"https://gl.mathhub.info/{archive}/-/raw/main/source/{filename}"
    print(f"Fetching content from URL: {url}")
    
    response = requests.get(url)
    
    if response.status_code == 200:
        raw_content = response.text
        cleaned_content = cleanup_stex(raw_content)
        return cleaned_content
    elif response.status_code == 404:
        raise Exception(f"File not found at {url}. Please check the archive and filepath.")
    else:
        raise Exception(f"Failed to fetch content. Status code: {response.status_code}")



# Original recursive function for fetching content and its dependencies
def get_recursive_stex(archive: str, filename: str) -> str:
    stex = cleanup_stex(get_raw_stex(archive, filename))
    return replace_inputref(archive, stex)

if __name__ == "__main__":
    # Example of fetching specific content without recursion
    content = get_stex_content(archive="courses/FAU/IWGS/course", filename="course/notes/notes-part1.tex")
    # print(content)
 
    # Example of recursive fetching
    # content = get_recursive_stex(archive="courses/FAU/IWGS/course", filename="course/notes/notes-part1.tex")
    # print(content)
 