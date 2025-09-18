import os


# New unified backend selector ----------------------------------------------
BACKEND = os.environ.get(
    "EZPOD_BACKEND",
    os.environ.get("EZPOD_BACKEND_AWS_EC2", "runpod"),
)

# Convenience flags used throughout the project
BACKEND_AWS = BACKEND == "aws"
BACKEND_GCP = BACKEND == "gcp"
