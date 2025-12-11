# Unresolved Tickets Flagging – Automation Pipeline

A lightweight automation pipeline to fetch **flagged unresolved incidents** from ServiceNow, preprocess them, compute aging/SLA metrics, and generate daily summary reports.  
This project is designed for Azure/AWS or local execution.

---

## 📌 Overview
ServiceNow automatically flags tickets older than **48+ hours** using:
```
u_unresolved_2d = true
```

This pipeline:

- Fetches flagged incidents via ServiceNow API  
- Cleans + preprocesses raw data  
- Computes age_days, total_hours, SLA breach  
- Generates daily summary  
- Sends email digest to DL (SMTP / MS Graph)  
- Stores CSV snapshots for audit

---

## 📁 Folder Structure
```
Unresolved-Tickets-Flagging-3/
│
├── fetch_raw_incidents.py         # Fetch flagged incidents (SNOW API)
├── process_incidents.py           # Clean + preprocess raw data
├── generate_and_send_summary.py   # Daily summary + email sender
├── onedrive.py                    # Optional OneDrive upload
│
├── raw_incidents.json             # Raw API response
├── raw_incidents.csv              # Flattened raw CSV
├── processed_incidents.csv        # Final cleaned data
│
├── requirements.txt               # Python deps
└── README.md                      # Documentation
```

---

## ⚙️ Setup

### 1. Create virtual environment
```bash
conda create -n wood python=3.10
conda activate wood
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Create `.env` file
```
SN_INSTANCE=https://yourinstance.service-now.com
SN_USER=your_bot_user
SN_PASS=your_password

CSV_OUTPUT=processed_incidents.csv

SMTP_HOST=mailrelay.woodplc.net
SMTP_PORT=25
SENDER=email.ai_automation@wisseninfotech.com
RECIPIENT=email.ai_automation@wisseninfotech.com
```

---

## 🚀 Running the Pipeline

### 1️⃣ Fetch raw flagged incidents
```bash
python fetch_raw_incidents.py
```
Outputs: `raw_incidents.json`, `raw_incidents.csv`

### 2️⃣ Process incidents
```bash
python process_incidents.py
```
Outputs: `processed_incidents.csv`

### 3️⃣ Generate daily summary email
```bash
python generate_and_send_summary.py
```

---

## 📊 Sample Summary Output
```
Ticket Aging Summary

Total tickets: 19
Aging:
- >=2 days: 17
- >5 days: 13
- >7 days: 2

Priority Distribution:
- 3 - Moderate: 8
- 4 - Low: 11

Region Distribution:
- Americas: 12
- Europe: 6
- APAC: 1

Oldest Ticket:
INC0027627 — 10 days old (242 hours)

Observations:
- Most aging tickets are Low priority.
- Majority come from Americas region.
```

---

## ☁️ Deployment (Optional)
Works on:

### Azure  
- Azure VM (script execution)  
- Azure Key Vault  
- Azure Logic App (7AM trigger)  
- Azure Blob Storage (audit history)  
- MS Graph API (email DL)

### AWS  
- Lambda  
- EventBridge  
- S3  
- Secrets Manager  
- SES (email digest)

---

## ✨ Future Enhancements
- Ticket anomaly detection  
- Volume spike alerts  
- Auto-escalation workflow  
- Power BI dashboards  
- OneDrive upload via MS Graph

---

## 👨‍💻 Author
**Parth Gajmal**  
AI Technical Lead, Wissen Infotech

