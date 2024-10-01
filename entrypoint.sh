#!/bin/sh

# Install dependencies from requirements file if available
if [ -f "$REQ_FILE" ]; then
  echo "Installing dependencies from $REQ_FILE"
  pip install --no-cache-dir -r "$REQ_FILE"
else
  echo "No requirements file found at $REQ_FILE"
fi

# Start Dagster gRPC server
dagster api grpc -h 0.0.0.0 -p 4000 -f "$REPO_FILE"
