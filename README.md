Things your computer needs installed on it outside of the python dependencies:

- runpodctl
  - set it up with your runpod API key and (this one may not be necessary?) give runpod your computer's pubkey
- tmux
- rsync

To create pods from the python:

- in runpod:
   1. create a template
     - make an environment variable PUBLIC_KEY and set it to your computer's pubkey
     - exposed ports are also important ![alt text](image-1.png) 
   2. create a network volume

- set the template_id and volume_id in the PodCreationConfig


