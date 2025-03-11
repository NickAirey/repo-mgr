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
    match = re.search(match_str, text, re.DOTALL)
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


def convert_to_dict(json_string):
    """
    Convert a JSON string with escaped characters into a Python dictionary.
    
    Args:
        json_string (str): The JSON string to convert
        
    Returns:
        dict: The parsed dictionary
    """
    try:
        # First, handle the outer quotes
        if json_string.startswith("'") and json_string.endswith("'"):
            json_string = json_string[1:-1]
        elif json_string.startswith('"') and json_string.endswith('"'):
            json_string = json_string[1:-1]
        
        # Replace actual newlines that might be in the string
        json_string = json_string.replace("\n", "")
        
        # Replace \\n escape sequences with actual newlines
        json_string = json_string.replace("\\n", "\n")
        
        # Handle double backslashes in escape sequences (like \\")
        # Replace them with a temporary marker
        temp_marker = "___BACKSLASH___"
        json_string = json_string.replace("\\\\", temp_marker)
        
        # Replace escaped quotes with proper JSON escaped quotes
        json_string = json_string.replace('\\"', '"')
        
        # Restore backslashes
        json_string = json_string.replace(temp_marker, "\\")
        
        # Parse the JSON string
        import json
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Failed to parse: {json_string}")
        
        # Try a more aggressive approach
        try:
            # Use regex to extract the content between outer braces
            import re
            match = re.search(r'\{.*\}', json_string, re.DOTALL)
            if match:
                cleaned_json = match.group(0)
                # Fix any remaining issues
                cleaned_json = cleaned_json.replace("\\", "")
                return json.loads(cleaned_json)
        except Exception as fallback_error:
            print(f"Fallback parsing failed: {fallback_error}")
        
        # If all else fails, manually parse the key-value pairs
        try:
            print("Attempting manual parsing...")
            result = {}
            # Extract "name" value
            name_match = re.search(r'"name":\s*"([^"]+)"', json_string)
            if name_match:
                result["name"] = name_match.group(1)
            
            # Extract "code" value - this is more complex
            code_match = re.search(r'"code":\s*"(.*?)(?:"\s*\}$)', json_string, re.DOTALL)
            if code_match:
                code = code_match.group(1)
                # Clean up the code
                code = code.replace("\\n", "\n").replace('\\"', '"')
                result["code"] = code
            
            return result
        except Exception as manual_error:
            print(f"Manual parsing failed: {manual_error}")
            
        return None
    except Exception as e:
        print(f"Error processing string: {e}")
        return None