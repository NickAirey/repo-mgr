#!/bin/bash

nohup python -m uvicorn app:app --reload --host 0.0.0.0 &