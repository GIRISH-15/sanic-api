If you update code in github, refreash github...
explanation of the process:
Let’s go through everything you wrote and explain what it is and why it exists — piece by piece.
I’ll group it into:
    1. App code (Sanic app)
    2. Packaging (requirements.txt + Dockerfile)
    3. Local testing (docker build/run)
    4. Git + GitHub
    5. DockerHub
    6. EC2 setup
    7. Deployment script on EC2
    8. GitHub Secrets
    9. GitHub Actions CI/CD workflow
    10. Test & verify

1️⃣ app.py – Your Web Application
from sanic import Sanic
from sanic.response import json

app = Sanic("MySanicApp")
    • from sanic import Sanic
Imports the Sanic application class – it’s like Flask(__name__) in Flask.
    • from sanic.response import json
Imports a helper function to return JSON HTTP responses.
    • app = Sanic("MySanicApp")
Creates a Sanic app instance with the name "MySanicApp".
This app object is what defines routes and runs the server.

@app.get("/")
async def index(request):
    return json({"message": "Hello from Sanic + Docker + EC2"})
    • @app.get("/")
This is a route decorator. It tells Sanic:
        ◦ When a GET request comes to / (root URL),
        ◦ run the index function.
    • async def index(request):
Sanic is async, so handlers are async.
        ◦ request contains info about the HTTP request (headers, params, etc.).
    • return json({...})
Sends a JSON response to the client:
      {"message": "Hello from Sanic + Docker + EC2"}
      This is your main success proof when someone hits the API.

@app.get("/health")
async def health(request):
    return json({"status": "ok", "version": "1.0.0"})
    • Another endpoint: /health
    • Purpose:
        ◦ Check if app is alive and healthy.
        ◦ Can be used by monitoring tools or load balancers.
    • Returning:
      {"status": "ok", "version": "1.0.0"}
      This is a simple healthcheck API – very common in real systems.

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False)
    • This block only runs when you do python app.py directly.
    • host="0.0.0.0" → accept incoming traffic from any IP, not just localhost
(important for Docker + EC2).
    • port=8000 → app listens on port 8000.
    • debug=False → production-like mode, no debug reloader.
Why this whole file?
This is your business logic / application. Everything else (Docker, Git, CI/CD) is just to package and deploy this.

2️⃣ requirements.txt – Tell Python What to Install
sanic==23.12.0
    • This tells pip which Python packages are needed.
    • Exact version is pinned so that:
        ◦ Local machine, Docker container, and EC2 all use same version.
        ◦ Avoid “works on my machine, fails in container” problems.
Why?
Docker image needs to know which dependencies to install during build.

3️⃣ Dockerfile – How to Build the Container Image
FROM python:3.11-slim
    • Base image = official Python 3.11 slim version.
    • “slim” → smaller image → faster pulls & builds.

WORKDIR /app
    • Sets working directory inside the container to /app.
    • All subsequent commands (COPY, RUN, CMD) will run from here.
    • This is like cd /app inside the container.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
    • COPY requirements.txt .
Copies only requirements.txt from your computer into /app inside the container.
    • RUN pip install --no-cache-dir -r requirements.txt
Installs all dependencies inside the image.
We copy requirements.txt first so that Docker can cache this layer:
If only app.py changes but requirements.txt is same, Docker reuses this part.

COPY . .
    • Copies all remaining project files (app.py, etc.) into /app in the image.
So now the container has:
    • /app/app.py
    • /app/requirements.txt
    • etc.

EXPOSE 8000
    • Documentation for Docker / tools: this container listens on port 8000.
    • Not a firewall; your docker run -p 8000:8000 actually exposes it.

CMD ["python", "app.py"]
    • This tells Docker:
When this container starts, run:
      python app.py
    • That starts the Sanic server inside the container.
Why the whole Dockerfile?
It defines a repeatable, portable environment so the same app runs the same way:
    • On your laptop
    • On EC2
    • Anywhere Docker runs

4️⃣ Local Docker Commands – Testing Before Deployment
docker build -t sanic-api:1.0.0 .
    • Build an image from the current directory (.)
    • Tag it as sanic-api:1.0.0
        ◦ sanic-api is name
        ◦ 1.0.0 is version tag

docker run -d -p 8000:8000 --name sanic-api sanic-api:1.0.0
    • -d → run in background (detached)
    • -p 8000:8000 → map:
        ◦ host port 8000 → container port 8000
    • --name sanic-api → easy name to manage container
    • sanic-api:1.0.0 → image to run

curl http://localhost:8000
curl http://localhost:8000/health
    • Hit the app through Docker port mapping and check responses.
    • If this works → your Dockerization is correct.

5️⃣ Git & GitHub Commands – Version Control & Remote Repo
git init
    • Start a Git repository in the folder.
git add .
git commit -m "Initial commit - Sanic API with Docker"
    • git add . → stage all files.
    • git commit → save a snapshot.
git branch -M main
    • Ensure the main branch is called main.
git remote add origin https://github.com/GIRISH-15/sanic-api.git
git push -u origin main
    • remote add origin → connect local repo to GitHub repo.
    • git push → send code to GitHub.
Why?
CI/CD tools (GitHub Actions) watch this repo and trigger pipelines on push.

6️⃣ EC2 Setup Commands
On EC2:
sudo dnf update -y
    • Updates system packages to latest (similar to apt update && upgrade).
sudo dnf install docker -y
    • Installs Docker engine on EC2.
sudo systemctl start docker
    • Start Docker service.
sudo usermod -aG docker ec2-user
    • Adds ec2-user to docker group so you can run docker without sudo.
Why?
EC2 becomes a machine that can pull Docker images and run containers.

7️⃣ deploy_sanic.sh – Deployment Script on EC2
File: ~/deploy/deploy_sanic.sh
#!/bin/bash
set -e
    • #!/bin/bash → tells the system this is a bash script.
    • set -e → exit script if any command fails. Prevents silent errors.

IMAGE="girishsatya/sanic-api:latest"
CONTAINER="sanic-api"
    • Two variables:
        ◦ IMAGE = name of the Docker image to deploy
        ◦ CONTAINER = Docker container name to use
Makes it easy to change later if needed.

docker pull $IMAGE
    • Pulls the latest version of the image from DockerHub.

docker rm -f $CONTAINER || true
    • Remove any existing container with same name:
        ◦ docker rm -f → forcibly stop & remove
        ◦ || true → if container doesn’t exist, don’t fail the script

docker run -d --name $CONTAINER -p 8000:8000 $IMAGE
    • Run the new container using:
        ◦ name = sanic-api
        ◦ port map = host 8000 → container 8000
        ◦ image from DockerHub

docker ps
    • List running containers to verify deployment.
Why script?
So GitHub Actions (or you manually) can deploy with a single command, instead of typing multiple docker commands.

8️⃣ GitHub Secrets – Secure Configuration
You stored these values:
    • DOCKERHUB_USERNAME → Docker Hub login username
    • DOCKERHUB_TOKEN → Docker Hub access token (instead of plain password)
    • EC2_HOST → e.g. 3.110.219.214
    • EC2_USER → ec2-user
    • EC2_SSH_KEY → private key for SSH to EC2
Why secrets?
    • YAML workflow is public in repo; secrets must not be hard-coded.
    • GitHub secrets hide them and inject them securely at runtime.

9️⃣ GitHub Actions Workflow – CI/CD Logic
File: .github/workflows/ci-cd.yml
Header
name: CI-CD Sanic API
    • Human-readable name for the workflow.
on:
  push:
    branches: ["main"]
    • Trigger: whenever code is pushed to main branch.

Job Definition
jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    • Defines a job named build-and-deploy.
    • Runs on a GitHub-hosted Ubuntu Linux VM.

Step 1 – Checkout Code
    steps:
    - uses: actions/checkout@v4
    • Clones your repo into the runner.
    • Without this, there is no code to build.

Step 2 – Setup Docker Buildx
    - uses: docker/setup-buildx-action@v3
    • Prepares Docker Buildx, which supports advanced builds.
    • Often needed for docker/build-push-action.

Step 3 – Login to Docker Hub
    - uses: docker/login-action@v3
      with:
        username: ${{ secrets.DOCKERHUB_USERNAME }}
        password: ${{ secrets.DOCKERHUB_TOKEN }}
    • Logs into DockerHub from the GitHub runner.
    • Uses secrets, not plaintext.
    • Required to push images.

Step 4 – Build & Push Docker Image
    - uses: docker/build-push-action@v5
      with:
        context: .
        push: true
        tags: |
          girishsatya/sanic-api:latest
    • context: . → build from repo root (where Dockerfile is).
    • push: true → push the built image to Docker Hub.
    • tags: ... → image name and tag.
Result:
New image available at docker.io/girishsatya/sanic-api:latest

Step 5 – Deploy to EC2 via SSH
    - uses: appleboy/ssh-action@v1.0.0
      with:
        host: ${{ secrets.EC2_HOST }}
        username: ${{ secrets.EC2_USER }}
        key: ${{ secrets.EC2_SSH_KEY }}
        script: |
          chmod +x ~/deploy/deploy_sanic.sh
          ~/deploy/deploy_sanic.sh
    • appleboy/ssh-action → GitHub Action that can SSH into a server.
    • Uses:
        ◦ host = EC2 IP
        ◦ username = ec2-user
        ◦ key = private key
    • script: | → commands that will run on the EC2 machine:
      chmod +x ~/deploy/deploy_sanic.sh
      ~/deploy/deploy_sanic.sh
What happens on EC2:
    1. Make sure script is executable
    2. Run script → pulls latest image → stops old container → runs new container
Why this whole workflow?
This is the heart of CI/CD:
    • CI: Build & push image on every commit.
    • CD: Automatically deploy new version to EC2.

🔟 Phase 8 – Testing CI/CD
git commit -am "Updated message"
git push
    • Any change to app.py (like changing the "message")
triggers the entire pipeline:
    1. GitHub Actions triggers on push
    2. Builds new image
    3. Pushes to Docker Hub
    4. SSH to EC2
    5. Runs new container
Then you verify with:
http://<EC2_PUBLIC_IP>:8000/
http://<EC2_PUBLIC_IP>:8000/health
If the message changed, it proves that:
    • New code → new image → new container on EC2, automatically.
That’s full CI/CD working. ✅

