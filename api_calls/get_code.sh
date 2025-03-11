#!/bin/bash

curl -X GET "http://localhost:8000/code" -H "Content-Type: application/json"  -d '{"file": "google.py"}'