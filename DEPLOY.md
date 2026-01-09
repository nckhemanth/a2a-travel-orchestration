# Deploying A2A Travel Orchestration to Hugging Face Spaces (Free)

This guide will help you deploy your full multi-agent application to **Hugging Face Spaces** for free. This is the best option because it supports Docker, allowing us to run all 4 components (UI + 3 Agents) in a single "Space".

## Prerequisites
1.  A [Hugging Face Account](https://huggingface.co/join) (Free)
2.  Your `OPENAI_API_KEY`

## Step 1: Create a New Space
1.  Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **"Create new Space"**.
2.  **Space Name**: `travel-orchestrator` (or similar)
3.  **License**: `MIT`
4.  **Select the Space SDK**: Choose **Docker**.
5.  **Choose a Docker Template**: Select **Blank**.
6.  **Space Hardware**: Keep it on **CPU Basic (Free)**.
7.  Click **Create Space**.

## Step 2: Configure Secrets
The agents need your OpenAI or Euri Key to function.
1.  In your new Space, go to **Settings**.
2.  Scroll to **"Variables and secrets"**.
3.  Click **"New secret"**.
    *   **Name**: `OPENAI_API_KEY` (OR `EUR_API_KEY`)
    *   **Value**: (Paste your actual sk-... or euri-... key)
4.  Click **Save**.

## Step 3: Upload Files
You will upload your project files to the "Files" tab of your Space.
You can do this via the Web UI (uploading file by file or dragging a folder) or via Git (recommended).

### Option A: Upload via Web UI (Simple)
Upload the following files/folders to the root of your Space:
-   `Dockerfile` (I will create this)
-   `entrypoint.sh` (I will create this)
-   `requirements.txt`
-   `src/` (The entire folder)
-   `data/` (The entire folder)
-   `.streamlit/` (The config folder)

### Option B: Upload via Git (Recommended)
1.  Clone the repository shown in your Space:
    ```bash
    git clone https://huggingface.co/spaces/YOUR_USERNAME/travel-orchestrator
    ```
2.  Copy all your project files into that folder.
3.  Add, Commit, and Push:
    ```bash
    git add .
    git commit -m "Initial deploy"
    git push
    ```

## Step 4: Access Your App
Once pushed, the "Building" status will appear. It may take 3-5 minutes to install dependencies.
Once "Running", your app will be live at the URL provided by Hugging Face!
