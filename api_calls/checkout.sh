#!/bin/bash

curl -X POST "http://localhost:8000/code/init" -H "Content-Type: application/json"  -d '{"repo_url":"https://github.com/Bhavish051/Python-example.git" }'