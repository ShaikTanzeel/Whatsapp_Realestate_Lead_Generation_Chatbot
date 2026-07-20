# Local Environment Setup Guide

This guide provides instructions to replicate and configure the Bilingual WhatsApp Real Estate Lead Generation System in a local development environment.

---

## 🛠️ Prerequisites

Before starting, ensure you have the following installed and configured on your host machine:

1. **Docker & Docker Compose:** For running PostgreSQL, n8n, and PgAdmin containers.
2. **PowerShell (Windows) or Bash (Linux/macOS):** To execute automation scripts.
3. **ngrok (or any localhost tunnel):** To expose your local n8n webhook port (`5678`) to the internet so Meta can deliver WhatsApp events.
4. **Accounts & API Credentials:**
   * **OpenAI API Key:** (gpt-4o-mini access enabled).
   * **Meta Developer Account:** (WhatsApp Cloud API sandbox access).
   * **Google Cloud Console Service Account:** (with Google Sheets API enabled).

---

## 📂 Project Structure

```text
├── .agents/                    # Workspace rules and guidelines
├── prompts/                    # System and agent prompts
│   ├── system_prompt.md        # Yara persona & mandatory fields
│   ├── cleanup_agent_prompt.md # Whisper transcription cleanup
│   ├── language_classifier_prompt.md
│   ├── extraction_prompt.md    # Structured JSON extraction rules
│   └── security_patterns.json  # Regex prompt injection list
├── scripts/                    # Environment management scripts
│   ├── start.ps1               # Automated local startup (Windows)
│   ├── stop.ps1                # Automated cleanup (Windows)
│   └── start.sh                # Automated startup (Linux/macOS)
├── docs/                       # Technical blueprints (Setup, VPS, Architecture)
├── init.sql                    # Postgres schema initialization script
├── docker-compose.yml          # Container configuration blueprint
└── main_whatsapp_flow.json     # n8n workflow template
```

---

## 🚀 Step-by-Step Installation

### Step 1: Clone the Repository & Configure Variables
1. Clone the project to your local machine.
2. Copy the `.env.example` file to create your active `.env` file:
   ```powershell
   copy .env.example .env
   ```
3. Open `.env` and fill in your credentials:
   * `OPENAI_API_KEY`: Your OpenAI API key.
   * `META_ACCESS_TOKEN`: Your Meta temporary or system user token.
   * `META_PHONE_NUMBER_ID`: The ID of your Meta WhatsApp sandbox phone number.
   * `META_VERIFY_TOKEN`: A custom password string (e.g., `RealEstateVerifyToken2026`) that you will register on the Meta Portal.
   * `GOOGLE_SHEETS_ID`: The ID of your target Google Spreadsheet.

---

### Step 2: Configure the CRM Google Sheet
1. Create a Google Sheet and add four tabs with these exact column headers:
   * **`Lead Pipeline` tab:**
     `Timestamp`, `Lead ID`, `Phone`, `Name`, `Budget`, `Intent`, `Property Type`, `Location`, `Timeline`, `Financing`, `Visa Interest`, `Language`, `Lead Score`, `Lead Points`, `Status`, `Agent Notes`, `row_number`
   * **`Handoff Queue` tab:**
     `Timestamp`, `Phone`, `Name`, `Collected So Far`, `Language`, `Handoff Reason`, `Status`, `row_number`
   * **`Security Events` tab:**
     `Timestamp`, `Phone (Hashed)`, `Violating Input`, `Violation Type`
2. Share the Google Sheet with your **Google Service Account Email** (found in your Service Account JSON file) as an **Editor**.

---

### Step 3: Boot the Containers
Run the automated powershell startup script to verify Docker, create shared volumes, spin up containers, configure ngrok, and launch your browser:
```powershell
.\scripts\start.ps1
```

*(Alternatively, run `docker-compose up -d` manually in the root directory).*

---

### Step 4: Import the n8n Workflow
1. Open your local n8n interface at `http://localhost:5678`.
2. Click **Add Workflow** ➔ Click the three dots in the top right ➔ Select **Import from File**.
3. Choose the [main_whatsapp_flow.json](file:///c:/Projects/Projects/Biligual%20Whatsapp%20Lead%20Generation-System/main_whatsapp_flow.json) file.
4. Set up your node credentials in n8n:
   * **Postgres node:** Configure host as `postgres`, database as `whatsapp_lead_db`, user as `postgres_admin`, and password as defined in your `.env`.
   * **OpenAI node:** Bind your OpenAI API Key credential.
   * **Google Sheets node:** Upload your Service Account JSON file.
   * **HTTP Request nodes (WhatsApp):** Bind your Meta Access Token as headers.

---

### Step 5: Configure the Meta Webhook
1. Go to the [Meta Developer Portal](https://developers.facebook.com) ➔ Your WhatsApp App ➔ **Configuration**.
2. Set the **Callback URL** to your active ngrok tunnel URL with the webhook path:
   `https://YOUR_NGROK_SUBDOMAIN.ngrok-free.dev/rest/webhooks/whatsapp`
3. Set the **Verify Token** to the exact `META_VERIFY_TOKEN` string defined in your `.env`.
4. Click **Verify and Save**.
5. Under Webhook Fields, click **Subscribe** to `messages`.

---

## 🧼 Resetting the Test Environment
To test the flow as a completely new user, run this command in your terminal to purge database history and clear n8n's RAM memory:
```powershell
docker exec -i whatsapp_postgres psql -U postgres_admin -d whatsapp_lead_db -c "DELETE FROM user_states WHERE phone_number = 'YOUR_TEST_NUMBER'; DELETE FROM ai_responses WHERE phone_number = 'YOUR_TEST_NUMBER'; DELETE FROM lead_qualification WHERE phone_number = 'YOUR_TEST_NUMBER';"
docker restart whatsapp_n8n
```
