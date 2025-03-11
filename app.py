import json
import re
import subprocess
from fastapi import FastAPI, HTTPException,Response
import logging
import uvicorn
import os
from git import Repo

from utils.models import *
from utils.utils import convert_to_dict, extract_output_tags, parse_pytest_output

logging.basicConfig(level=logging.INFO)


app = FastAPI()

logger = logging.getLogger(__name__)
logger.info("API is starting up")
logger.info(uvicorn.Config.asgi_version)

current_repo = { "repo": ""}

current_directory = os.getcwd()
logger.info(f"current dir: {current_directory}")

# Get the parent directory
parent_dir = os.path.dirname(current_directory)

repo_path = os.path.join(parent_dir, "repo")
logger.info("local path: "+repo_path)


@app.get("/")
async def root():
    logger.info('current repo: '+current_repo["repo"])
    return current_repo


@app.post("/code/init")
async def root(repo: RepoModel):
    try: 
        if not os.path.exists(repo_path):
            os.makedirs(repo_path)

        current_repo["repo"] = repo.repo_url
        logger.info("checking out repo: "+repo.repo_url)

        Repo.clone_from(repo.repo_url, repo_path) 
    except Exception as e:
        logger.error(f"Failed to clone repository. Error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to clone repository. Error: {e}"
        )
    return current_repo


@app.get("/code")
async def read_item(item: File):
    # Get code from repo
    logger.info("requested file: " + item.file + " from local dir " + repo_path)
    if os.path.isfile(repo_path + os.path.sep + item.file):
        logger.info("File exists")

        with open(repo_path+os.path.sep + item.file, 'r') as file:
            file_contents = file.read()
            return Response(content=file_contents, media_type="text/plain")
    else:
        logger.error("File does not exist: " + item.file)
        raise HTTPException(
            status_code=400,
            detail="file does not exist"
        )

@app.post("/code")
async def create_code(item: File):
    if not item.file or not item.contents:
        raise HTTPException(status_code=400, detail="Both file name and contents are required")
    
    # Extract code json
    contents_str = extract_output_tags(item.contents, 'output')    
    if not contents_str:
        raise HTTPException(status_code=400, detail="Payload incorrect - missing <output> code </output>")

    # Extract just the code
    contents_dict = convert_to_dict(contents_str)

    # Extract test name from the contents
    test_name_match = re.search(r'def\s+(test_\w+)', item.contents)
    if not test_name_match:
        raise HTTPException(status_code=400, detail="Could not find a test function in the contents")
    
    test_name = test_name_match.group(1)
    file_name = f"test_{item.file}" if not item.file.startswith("test_") else item.file
    file_path = os.path.join(repo_path, file_name)
    
    # Check if the file exists
    if os.path.exists(file_path):
        logger.info(f"File {file_path} exists, checking for test {test_name}")
        
        # Read existing file content
        with open(file_path, 'r') as file:
            existing_content = file.read()
        
        # Check if the test already exists in the file
        test_pattern = re.compile(r'def ' + re.escape(test_name) + r'.*?(?=def|\Z)', re.DOTALL)
        test_match = test_pattern.search(existing_content)
        
        if test_match:
            # Replace the existing test with the new content
            logger.info(f"Replacing existing test {test_name}")
            updated_content = test_pattern.sub(contents_dict['code'], existing_content)
            with open(file_path, 'w') as file:
                file.write(updated_content)
            return {
                "status": "updated",
                "file": file_name,
                "test": test_name
            }
        else:
            # Append the new test to the file
            logger.info(f"Appending new test {test_name} to existing file")
            with open(file_path, 'a') as file:
                # Add a newline if the file doesn't end with one
                if existing_content and not existing_content.endswith('\n'):
                    file.write('\n\n')
                else:
                    file.write('\n')
                file.write(contents_dict['code'])
            return {
                "status": "appended",
                "file": file_name,
                "test": test_name
            }
    else:
        # Create new file with the test content
        logger.info(f"Creating new file {file_path} with test {test_name}")
        with open(file_path, 'w') as file:
            file.write(contents_dict['code'])
        return {
            "status": "created",
            "file": file_name,
            "test": test_name
        } 

@app.post("/run-test")
async def execute_testcase(request: TestExecutionRequest):
        # Check if file_name is a full path or just a filename
    if os.path.isabs(request.file_name) or (os.path.sep in request.file_name):
        # file_name contains path information
        full_path = request.file_name
        file_name = os.path.basename(request.file_name)
        directory = os.path.dirname(request.file_name)
        
        # If file_path is also provided, log a warning that it will be ignored
        if request.file_path:
            logger.warning(f"Both file_path and full path in file_name provided. Using path from file_name: {directory}")
    else:
        # file_name is just a name, use file_path if provided
        file_name = request.file_name
        if request.file_path:
            directory = request.file_path
        else:
            directory = repo_path
        full_path = os.path.join(directory, file_name)
    
    # Ensure filename has test_ prefix
    if not os.path.basename(file_name).startswith("test_"):
        base_dir = os.path.dirname(full_path)
        base_name = os.path.basename(full_path)
        new_name = f"test_{base_name}"
        full_path = os.path.join(base_dir, new_name)
        file_name = new_name
    
    # Check if the file exists
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail=f"Test file not found: {full_path}")
    
    try:
        # Build the pytest command
        cmd = ["python", "-m", "pytest", full_path, "-v"]
        
        # Add specific test names if provided
        if request.test_names:
            # Clear the initial file path as we'll specify test functions individually
            cmd = ["python", "-m", "pytest", "-v"]
            for test_name in request.test_names:
                # Format: file_path::test_function_name
                cmd.append(f"{full_path}::{test_name}")
        
        # Execute the pytest command
        logger.info(f"Executing test command: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(full_path)  # Run in the directory of the test file
        )
        
        # Parse the output to extract test results
        test_results = parse_pytest_output(result.stdout)
        
        return {
            "status": "executed",
            "file": file_name,
            "full_path": full_path,
            "returncode": result.returncode,
            "success": result.returncode == 0,
            "test_results": test_results,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        logger.error(f"Error executing test file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to execute test: {str(e)}")


@app.get('/list')
async def list_files():
    return {
        "repo_path": [os.path.join(repo_path,"Job_scheduling.py")],
    }