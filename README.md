# 🚀 Breezy HR ATS Integration Microservice

A Python-based serverless microservice that integrates with **Breezy HR** to expose a unified REST API for managing jobs, candidates, and applications. Built with the **Serverless Framework** and designed to run locally using `serverless-offline`.

---

## 📋 Table of Contents
1. [Project Structure](#project-structure)
2. [Setup Breezy HR](#setup-breezy-hr)
3. [Installation & Local Setup](#installation--local-setup)
4. [Running Locally](#running-locally)
5. [API Endpoints & curl Examples](#api-endpoints--curl-examples)
6. [Environment Variables](#environment-variables)

---

## 📁 Project Structure

```
TASK2/
├── handler.py              # Lambda entry points for each API endpoint
├── breezy_client.py        # Core Breezy HR API wrapper (all business logic)
├── serverless.yml          # Serverless Framework config (routes, env vars)
├── requirements.txt        # Python dependencies
├── package.json            # npm/serverless plugin dependencies
├── .env                    # Your secrets — DO NOT commit this!
├── .env.template           # Safe-to-commit secrets template
├── .gitignore              # Excludes .env, node_modules, cache
└── README.md               # This file
```

---

## 🔐 Setup Breezy HR

### Step 1: Create a Free Trial Account
1. Go to **[https://breezy.hr/](https://breezy.hr/)**
2. Click **"Try it free"** and sign up.
3. Complete the onboarding — create a company if prompted.

### Step 2: Create a Job Posting (to test with)
1. Inside the Breezy dashboard, click **"New Position"**.
2. Fill in a job title (e.g., "Software Engineer"), location, and publish it.
3. Note the **Position ID** from the URL when viewing the position:
   - URL looks like: `https://app.breezy.hr/p/XXXXXXXXX-software-engineer`
   - The `XXXXXXXXX` part is your **`job_id`**.

### Step 3: Generate Your API Key
1. Click your **profile picture** (top right) → **"Company Settings"**.
2. Go to **Settings → Integrations** (or look for **"API"** section).
3. Generate a **Personal Access Token**.
4. Copy the token — this is your `BREEZY_API_KEY`.

### Step 4: Find Your Company ID
1. Go to **Company Settings** in Breezy HR.
2. Your **Company ID** is visible in the URL:
   - URL looks like: `https://app.breezy.hr/company/YOUR_COMPANY_ID/settings`
3. Copy the company ID segment — this is your `BREEZY_COMPANY_ID`.

---

## ⚙️ Installation & Local Setup

### Prerequisites
- Python 3.9+
- Node.js 16+ & npm

### 1. Install npm dependencies (Serverless plugins)
```bash
npm install
```

### 2. Install Python dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy the template and fill in your actual values:
```bash
# Windows
copy .env.template .env

# Mac/Linux
cp .env.template .env
```

Now open `.env` and fill in:
```env
BREEZY_API_KEY=your_personal_access_token_here
BREEZY_COMPANY_ID=your_company_id_here
BREEZY_BASE_URL=https://api.breezy.hr/v3
```

---

## ▶️ Running Locally

Start the local serverless server (no AWS account needed):
```bash
npx serverless offline
```

You should see output like:
```
   ┌────────────────────────────────────────────────────────────┐
   │                                                            │
   │   GET | http://localhost:3000/dev/jobs                     │
   │   POST | http://localhost:3000/dev/candidates              │
   │   GET | http://localhost:3000/dev/applications             │
   │                                                            │
   └────────────────────────────────────────────────────────────┘
```

The local server runs at: **`http://localhost:3000`**

---

## 🌐 API Endpoints & curl Examples

### 1. `GET /jobs` — List Open Jobs

Fetches all open positions from Breezy HR.

**curl:**
```bash
curl http://localhost:3000/dev/jobs
```

**With pagination:**
```bash
curl "http://localhost:3000/dev/jobs?page=2"
```

**Example Response:**
```json
[
  {
    "id": "abc12345def67890",
    "title": "Software Engineer",
    "location": "San Francisco, CA",
    "status": "OPEN",
    "external_url": "https://yourcompany.breezy.hr/p/abc12345-software-engineer"
  }
]
```

---

### 2. `POST /candidates` — Submit a Candidate Application

Creates a candidate in Breezy HR and attaches them to a specific job.

**curl:**
```bash
curl -X POST http://localhost:3000/dev/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane.smith@example.com",
    "phone": "+919876543210",
    "resume_url": "https://example.com/jane-smith-resume.pdf",
    "job_id": "abc12345def67890"
  }'
```

**Example Response (201 Created):**
```json
{
  "message": "Candidate created and application submitted successfully",
  "candidate_id": "xyz99887766",
  "name": "Jane Smith",
  "email": "jane.smith@example.com",
  "job_id": "abc12345def67890"
}
```

---

### 3. `GET /applications` — List Applications for a Job

Returns all candidates who applied to a specific position.

**curl:**
```bash
curl "http://localhost:3000/dev/applications?job_id=abc12345def67890"
```

**With pagination:**
```bash
curl "http://localhost:3000/dev/applications?job_id=abc12345def67890&page=2"
```

**Example Response:**
```json
[
  {
    "id": "xyz99887766",
    "candidate_name": "Jane Smith",
    "email": "jane.smith@example.com",
    "status": "APPLIED"
  },
  {
    "id": "zzz55544433",
    "candidate_name": "John Doe",
    "email": "john.doe@example.com",
    "status": "SCREENING"
  }
]
```

---

## 🔒 Environment Variables

| Variable | Description | Required |
|---|---|---|
| `BREEZY_API_KEY` | Personal Access Token from Breezy HR | ✅ Yes |
| `BREEZY_COMPANY_ID` | Your Breezy HR Company ID | ✅ Yes |
| `BREEZY_BASE_URL` | Breezy HR API base URL (default: `https://api.breezy.hr/v3`) | Optional |

> ⚠️ **Never commit your `.env` file to git.** It contains sensitive secrets.

---

## 🏗️ How It Works

```
Client (curl/Postman)
        │
        ▼
serverless-offline (local)  ──OR──  AWS API Gateway (deployed)
        │
        ▼
    handler.py  (parses request, validates inputs)
        │
        ▼
breezy_client.py  (calls Breezy HR API, maps fields, handles errors)
        │
        ▼
    Breezy HR API  (https://api.breezy.hr/v3)
```
