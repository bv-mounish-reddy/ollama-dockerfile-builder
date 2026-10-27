# Ollama Dockerfile Builder

Generate a Dockerfile for an app with a local Ollama coding model, then build and run it with Docker.

## Prerequisites

- Python 3 (no extra packages needed)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/), running
- [Ollama](https://ollama.com/download), running

Download the coding model:

```bash
ollama pull qwen2.5-coder:3b
```

## Generate, build, and run

```bash
# Generate a Dockerfile for the app
python3 dockerfile_gen.py ./testapp --model qwen2.5-coder:3b

# Build the image
docker build -t myapp ./testapp

# Run the container in the background
docker run -d --name myapp-container -p 5001:5000 myapp
```

Open http://localhost:5001.

`5000` is the port the app listens on inside the container. `5001` is the port on your computer. macOS uses 5000 for AirPlay Receiver, so a different host port avoids a conflict.

## Make changes and rebuild

Edit files in `testapp/`. If dependencies or the app structure changed, regenerate the Dockerfile first; otherwise rebuild directly. Replace the existing container with one from the new image:

```bash
python3 dockerfile_gen.py ./testapp --model qwen2.5-coder:3b  # only when needed
docker build -t myapp ./testapp
docker rm -f myapp-container
docker run -d --name myapp-container -p 5001:5000 myapp
```

## Useful commands

```bash
docker logs myapp-container     # view app output
docker stop myapp-container     # stop the container
docker rm myapp-container       # delete the container
docker image ls                 # list images
```