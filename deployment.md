# Deploying Acoustica to Microsoft Azure

Because I have already containerized your entire architecture into `docker-compose`, deploying to Azure is incredibly straightforward! Your components are completely self-contained. 

However, because the `Demucs` AI model requires heavy matrix computation to separate audio stems, **you must ensure whatever Azure cloud tier you select has a minimum of 8GB of RAM**. If you choose a server with 1GB or 2GB of RAM, the backend container will immediately crash with an "OOM" (Out Of Memory) error when it attempts to process a song.

Here are the two best pathways for deployment:

---

## Path 1: Azure Virtual Machine (Recommended & Easiest)
Because you already have a `docker-compose.yml` file, creating a Linux Virtual Machine is the fastest way to get online because it behaves *exactly* like your local computer.

### Step 1: Create the Server
1. Go to the Azure Portal.
2. Search for **Virtual Machines** and click **Create**.
3. **Image**: Select **Ubuntu Server 22.04 LTS**.
4. **Size**: Select a **B2ms** or **D2s_v3** instance. (Do *not* pick the free tier 'B1s', Demucs will crash it).
5. **Inbound Port Rules**: Open **SSH (22)** to connect to it, and **HTTP (80)** / **Custom (3000)** so you can access the frontend.

### Step 2: Configure the Machine
Once the VM starts, SSH into it via your terminal:
```bash
ssh azureuser@<your-azure-ip>
```
Install Docker engine natively:
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose -y
sudo usermod -aG docker $USER
```
*(You will need to disconnect and reconnect via SSH for the docker permissions to apply).*

### Step 3: Launch!
1. Get your code onto the server (You can push it to a private GitHub repo and `git clone` it on the server, or use `scp` / SFTP to copy your folder directly).
2. Navigate into the folder and unleash the magic:
```bash
docker-compose up -d --build
```
Your UI is now globally live!

---

## Path 2: Azure Web App for Containers (PaaS)
If you prefer "Serverless" architecture and don't want to manage an Ubuntu operating system, you can give your Docker images directly to Azure App Service.

### Step 1: Push Images to Cloud Hub
You first need to upload the image blueprints to Azure's internal storage hub so the App Service can download them.
1. Create an **Azure Container Registry (ACR)** in the portal.
2. Login to your registry locally using the Azure CLI:
   ```bash
   az acr login --name <YourRegistryName>
   ```
3. Build and tag both of your environments:
   ```bash
   docker build -t <YourRegistryName>.azurecr.io/acoustica-backend -f Dockerfile .
   docker build -t <YourRegistryName>.azurecr.io/acoustica-frontend -f frontend/Dockerfile .
   ```
4. Push them into the cloud vault:
   ```bash
   docker push <YourRegistryName>.azurecr.io/acoustica-backend
   docker push <YourRegistryName>.azurecr.io/acoustica-frontend
   ```

### Step 2: Boot the Containers
1. Go to the Azure Portal -> **App Services** -> **Create**.
2. **Publish Strategy**: Select **Docker Container**.
3. **Operating System**: Linux.
4. **Pricing Plan**: Ensure you pick a **Premium (P1v3)** or **Standard (S2)**. 
5. In the **Docker** tab, select **Docker Compose (Preview)**.
6. Upload your `docker-compose.yml` file! Azure will automatically grab those images from your registry and map them exactly how they are mapped locally.

> [!WARNING] 
> **Storage Volatility:** Because Demucs writes large audio files to the `/separated` output folder, you need to understand that App Service containers are ephemeral. If Azure restarts your app for maintenance, those local `.wav` files will vanish. If permanent history is required, you must link an **Azure Files (Storage Account)** volume mapping directly into your container!
