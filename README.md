# 🔍 EmailForge — Email Intelligence & Pattern Discovery Suite Pro

<p align="center">
  <img src="https://img.shields.io/badge/Version-9.0-blue?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Python-3.8%2B-yellow?style=for-the-badge&logo=python" />
  <img src="https://img.shields.io/badge/GUI-Tkinter-informational?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Use-Lab%20%2F%20Authorized%20Only-red?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=for-the-badge" />
</p>

<p align="center">
  An advanced email intelligence and pattern discovery tool with a dark-themed GUI dashboard. Generate, analyze, and verify email addresses using intelligent pattern learning, role detection, team clustering, and SMTP verification — built for authorized penetration testing and cybersecurity research labs.
</p>

---

## ✨ Features

| Feature | Description |
|---|---|
| 🎯 **Smart Mode** | Learns email naming conventions from a seed email and generates pattern-based addresses |
| ⚡ **Brute Mode** | Comprehensive enumeration across all name × pattern combinations for deep coverage |
| 📧 **Pattern Learning** | Automatically identifies formats like `first.last`, `f.last`, `lastfirst`, `flast`, and 8+ more |
| 🕵️ **Role Detection** | Classifies emails into 14 role categories (Admin, Executive, HR, IT, Sales, Legal, etc.) |
| 🏢 **Department Detection** | Maps emails to 10 departments (Engineering, Finance, Product, Operations, etc.) |
| 👥 **Team Clustering** | Groups discovered emails into role-based and department-based clusters |
| ✅ **SMTP Verification** | Verifies email existence via real MX record lookup and SMTP RCPT handshake |
| 🔗 **LinkedIn Hint Generator** | Generates probable LinkedIn profile URLs for discovered name-email pairs |
| 📊 **Confidence Scoring** | Ranks every generated email with a confidence percentage (configurable threshold) |
| 💾 **Report Export** | Saves full results to timestamped `.json` and `.txt` reports per scan |
| 📋 **Activity Log** | Real-time in-app log with timestamps for every operation step |
| 🔢 **Numerical Variations** | Extends base emails with numbered suffixes (e.g., `john.smith1@...`) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.8+ |
| GUI Framework | Tkinter + ttk |
| DNS Resolution | `dnspython` |
| HTTP Requests | `requests`, `BeautifulSoup4` |
| Concurrency | `concurrent.futures` (ThreadPoolExecutor) |
| Email Verification | `smtplib` (built-in) |
| Data Modeling | Python `dataclasses` |
| Output Formats | JSON, plain text |

---

## ⚙️ Requirements

- Python 3.8 or higher
- Windows / Linux / macOS
- Active internet connection (for DNS lookups and SMTP verification)

### Python Dependencies

```bash
pip install dnspython requests beautifulsoup4 urllib3
```

> Tkinter is included with most Python distributions. If missing on Linux:
> ```bash
> sudo apt install python3-tk
> ```

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/emailforge.git
cd emailforge
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
python EmailForge.py
```

The GUI window launches at **1400×850** resolution.

---

## 🖥️ How to Use

### Step 1 — Configure Input

| Field | Description |
|---|---|
| **Target Domain** | Enter the domain to analyze (e.g., `company.com`) |
| **Seed Email** *(optional)* | Provide a known email like `john.smith@company.com` to teach the pattern analyzer |
| **Max Results** | Slide to set the result cap (50–2000) |
| **Verify via SMTP** | Toggle to enable live email verification (slower but accurate) |

### Step 2 — Choose a Mode

| Mode | Behavior |
|---|---|
| 🎯 **Smart Mode** | Learns the domain's naming pattern from the seed and generates targeted combinations |
| ⚡ **Brute Mode** | Enumerates all first×last×format combinations for maximum coverage |

### Step 3 — Start Discovery

Click **🚀 START DISCOVERY**. The tool will:

1. Learn patterns from seed email (if provided)
2. Generate email addresses based on mode
3. Analyze each email for role and department
4. Optionally verify emails via SMTP
5. Display results across three result tabs
6. Save a JSON + TXT report to `email_intel_reports/`

---

## 📂 Output Files

All reports are saved in the `email_intel_reports/` directory:

```
email_intel_reports/
├── company.com_20250605_143022.json   ← Full structured data (people, patterns, teams)
├── company.com_20250605_143022.txt    ← Human-readable verified emails report
└── email_intel.log                    ← Persistent activity log
```

### Sample JSON Structure

```json
{
  "domain": "company.com",
  "timestamp": "20250605_143022",
  "mode": "smart",
  "total_discovered": 320,
  "valid_emails": 14,
  "people": [
    {
      "email": "john.smith@company.com",
      "first_name": "john",
      "last_name": "smith",
      "role": "management",
      "department": "Engineering",
      "confidence_score": 0.85,
      "linkedin_hint": "linkedin.com/in/john-smith",
      "is_verified": true
    }
  ],
  "teams": { "role_management": ["john.smith@company.com"] },
  "patterns": [{ "pattern_type": "first.last", "separator": ".", "confidence": 1.0 }]
}
```

---

## 🧩 Email Patterns Supported

| Pattern | Example |
|---|---|
| `first.last` | `john.smith@...` |
| `first_last` | `john_smith@...` |
| `first-last` | `john-smith@...` |
| `firstlast` | `johnsmith@...` |
| `f.last` | `j.smith@...` |
| `f_last` | `j_smith@...` |
| `flast` | `jsmith@...` |
| `first.l` | `john.s@...` |
| `firstl` | `johns@...` |
| `last.first` | `smith.john@...` |
| `lastfirst` | `smithjohn@...` |

---

## 🏢 Role & Department Detection

### Detected Roles (14)
`admin` · `executive` · `management` · `hr` · `it` · `sales` · `marketing` · `finance` · `legal` · `support` · `engineering` · `operations` · `research` · `product`

### Detected Departments (10)
`Engineering` · `Sales` · `Marketing` · `HR` · `Finance` · `Legal` · `Operations` · `Product` · `IT` · `Support`

---

## ⚠️ Legal & Ethical Disclaimer

> **This tool is strictly for authorized, educational, and lab use only.**
>
> - ✅ Use only on domains you **own** or have **explicit written permission** to test
> - ✅ Suitable for CTF challenges, security labs, and internal penetration testing
> - ❌ Do **not** use against real organizations without legal authorization
> - ❌ Email harvesting or unauthorized SMTP probing may violate laws such as the **CFAA (USA)**, **IT Act 2000 (India)**, **GDPR (EU)**, and similar legislation
>
> The author bears **no responsibility** for any misuse of this tool.

---

## 👤 Author

**Abhishek Rampariya**

- GitHub: [@AbhishekRampariya](https://github.com/AbhishekRampariya)

---

## 📄 License

This project is licensed for **educational and authorized lab use only**. Commercial redistribution is prohibited without permission.

---

<p align="center">Built with 🐍 Python · Dark Mode GUI · Smart Pattern Engine</p>
<p align="center">EmailForge v9.0 — Intelligence over Brute Force</p>
