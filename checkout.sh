#!/bin/bash

curl -X GET "http://localhost:8080/code/init" -H "Content-Type: application/json" -d '{"repo_url":"https://github.com/Bhavish051/Python-example.git" }'