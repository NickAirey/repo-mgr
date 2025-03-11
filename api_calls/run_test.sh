#!/bin/bash

curl -X POST "http://localhost:8000/run-test" -H "Content-Type: application/json" -d '{"file_name": "test_Job_scheduling.py"}'