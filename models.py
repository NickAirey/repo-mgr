from pydantic import BaseModel
from typing import List, Optional, Union

class File(BaseModel):
    file: Optional[str] = None
    contents: Optional[str] = None

class RepoModel(BaseModel):
    repo_url: str

class TestExecutionRequest(BaseModel):
    file_path: Optional[str] = None
    file_name: str
    test_names: Optional[Union[List[str], str]] = None  # Optional list of specific test names to run
