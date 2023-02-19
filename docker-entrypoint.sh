#!/bin/bash
echo "Starting Bot..."
echo "Token: $token"
if [[ -n "$token" ]]
then
    python /code/selfhostNoReplitDB.py
else
    echo "TOKEN IS REQUIRED"
fi