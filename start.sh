#!/bin/bash

nohup python3 -m uvicorn app:app --reload --host 0.0.0.0 &