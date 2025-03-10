from fastapi import FastAPI, HTTPException,Response
from pydantic import BaseModel
import logging
import uvicorn
import os
from git import Repo
from typing import Optional

logging.basicConfig(level=logging.INFO)

class File(BaseModel):
    file: Optional[str] = None
    contents: Optional[str] = None

class RepoModel(BaseModel):
    repo_url: str

app = FastAPI()

logger = logging.getLogger(__name__)
logger.info("API is starting up")
logger.info(uvicorn.Config.asgi_version)

current_repo = { "repo": ""}
local_path = "/Users/nairey3/tmp2"


@app.get("/")
async def root():
    logger.info('current repo: '+current_repo["repo"])
    return current_repo


@app.post("/code/init")
async def root(repo: RepoModel):
    try: 
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        current_repo["repo"] = repo.repo_url
        logger.info("checking out repo: "+repo.repo_url)

        Repo.clone_from(repo.repo_url, local_path) 
    except Exception as e:
        logger.error(f"Failed to clone repository. Error: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to clone repository. Error: {e}"
        )
    return current_repo


@app.get("/code")
async def read_item(item: File):
    logger.info("requested file: "+item.file+" from local dir "+local_path)
    if os.path.isfile(local_path+os.path.sep + item.file):
        logger.info("File exists")

        with open(local_path+os.path.sep + item.file, 'r') as file:
            file_contents = file.read()
            return Response(content=file_contents, media_type="text/plain")
    else:
        logger.error("File does not exist: "+item.file)
        raise HTTPException(
            status_code=400,
            detail="file does not exist"
        )

@app.post("/code")
async def create_code(item: File):
    file_name = "test.py"
    logger.info("writing file: "+local_path+os.path.sep + file_name)
    logger.info("received contents: "+item.contents)

    with open(local_path+os.path.sep + file_name, 'w') as file:
        file.write(item.contents)

    return {
        "writing to": file_name,
        "received code:": item
    }
