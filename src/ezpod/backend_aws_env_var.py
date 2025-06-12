import os


BACKEND_AWS = os.environ.get("EZPOD_BACKEND_AWS_EC2", "runpod") == "aws"
# BACKEND_AWS = True
