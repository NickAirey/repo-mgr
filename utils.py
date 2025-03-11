import json
import re


def extract_output_tags(text: str, tags: str) -> dict:
    """
    Extract code between <output> tags and return a dictionary with indexes as keys.
    
    Args:
        text (str): Input text containing <output> tags.
        tags (str): The tag name to search for (e.g., 'output').
    Returns:
        dict: A dictionary where keys are indexes (starting from 1) and values are extracted code blocks.
    """
    match_str = fr"<{tags}>(.*?)</{tags}>"
    match = re.findall(match_str, text, re.DOTALL)
    return json.dumps(match.group(1).strip()) if match else None


def parse_pytest_output(output: str):
    """
    Parse pytest output to extract individual test results
    """
    test_results = []
    
    # Regular expression to match test results in pytest verbose output
    test_pattern = re.compile(r'(\w+)::(test_\w+)\s+(\w+)\s+\[([\d\.]+)s\]')
    
    for line in output.split('\n'):
        match = test_pattern.search(line)
        if match:
            module, test_name, status, duration = match.groups()
            test_results.append({
                "test_name": test_name,
                "status": status.lower(),
                "duration": float(duration)
            })
    
    return test_results