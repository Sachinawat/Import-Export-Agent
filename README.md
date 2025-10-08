# Import-Export-Agent
🌍 Import/Export Intelligence Module
🚀 AI-Powered Trade Data Analysis & Insights Engine

An AI-driven FastAPI service designed to analyze import/export trade queries, generate actionable insights, and provide Excel exports of trade data — combining perception, decision, and action intelligence layers.

🧠 Overview

The Import/Export Intelligence Module intelligently processes natural language trade queries to:

Understand user intent (e.g., "Top exporters of coffee in India").

Decide optimal data-fetching strategies (e.g., based on product, HSN code, or country).

Act by fetching relevant trade data, generating insights, and exporting structured results into an Excel file.

This microservice integrates seamlessly into larger AI analytics ecosystems, automating trade research, market analysis, and competitive intelligence.

⚙️ Architecture

The system follows an Agent-based AI Architecture:

Agent	Responsibility	Description
🧩 Perceive Agent	Understands input	Parses user natural language queries into structured data (intent, entities, HSN codes, etc.)
🧭 Decide Agent	Plans next steps	Determines what data sources, APIs, or database queries should be used
⚙️ Act Agent	Executes tasks	Fetches trade data, generates analytics, and exports results into Excel
📁 Project Structure
import_export_intelligence/
│
├── main.py                     # FastAPI application entry point
├── config.py                   # Logging configuration & directory setup
├── models.py                   # Pydantic models for input/output schemas
├── services/
│   ├── perceive_agent.py       # Natural language query parser
│   ├── decide_agent.py         # Strategy planner based on parsed query
│   └── act_agent.py            # Data fetching, recommendation, and Excel export
│
├── logs/                       # Automatically created log and Excel storage directory
└── README.md                   # Project documentation (this file)

🧩 API Endpoints
1️⃣ Analyze Trade Query

POST /analyze-trade

Analyzes a natural language query related to trade (import/export).

🔹 Request Body Example
{
  "query": "Show me the top 10 exporters of tea from India in 2024"
}

🔹 Response Example
{
  "query": "Show me the top 10 exporters of tea from India in 2024",
  "parsed_query": {
    "intent": "export_analysis",
    "product_name": "tea",
    "country": "India",
    "year": 2024
  },
  "trade_data": [
    {
      "exporter_name": "ABC Traders Pvt Ltd",
      "country": "India",
      "export_value": 1200000,
      "hsn_code": "0902"
    }
  ],
  "recommendations": [
    "Consider analyzing price trends for tea exports in Q2 2024.",
    "Monitor competitor export volume from Sri Lanka for better market positioning."
  ],
  "download_link": "/download/trade_data_tea_export_analysis.xlsx"
}

🔹 Description

Input: Natural language query about import/export data.

Output: AI-analyzed trade insights + downloadable Excel file link.

Response Model: IntelligenceOutput

Response Type: JSON

2️⃣ Download Excel Report

GET /download/{filename}

Downloads the Excel report generated from a previous analysis.

🔹 Example
GET /download/trade_data_tea_export_analysis.xlsx

🔹 Response

Returns an Excel file containing structured trade data and insights.

3️⃣ Root Endpoint

GET /

A simple health check and API introduction message.

Response Example:

{
  "message": "Welcome to the Import/Export Intelligence Module! Use /docs for API documentation."
}

🧰 Setup Instructions
🔹 Prerequisites

Ensure you have the following installed:

Python 3.9+

pip / virtualenv

FastAPI and Uvicorn

OpenPyXL (for Excel exports)

🔹 Installation
# Clone the repository
git clone https://github.com/yourusername/import-export-intelligence.git
cd import-export-intelligence

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # (Linux/Mac)
venv\Scripts\activate           # (Windows)

# Install dependencies
pip install -r requirements.txt

🔹 Run the API
uvicorn main:app --reload


Access API Docs at:
📄 http://127.0.0.1:8000/docs

🧪 Example Usage (via cURL)
curl -X POST "http://127.0.0.1:8000/analyze-trade" \
-H "Content-Type: application/json" \
-d '{"query": "Top importers of crude oil in India"}'

🗂️ Logging & Data Storage

All logs and generated Excel files are saved inside the logs/ directory.

Each generated file is uniquely named based on:

trade_data_<product_or_hsn>_<intent>.xlsx


Example:

logs/trade_data_coffee_export_analysis.xlsx

🧩 Pydantic Models
QueryInput
class QueryInput(BaseModel):
    query: str

IntelligenceOutput
class IntelligenceOutput(BaseModel):
    query: str
    parsed_query: dict
    trade_data: list
    recommendations: list
    download_link: str

🧠 Agents Overview
Perceive Agent

NLP-based parser for understanding trade queries.

Extracts:

Product names

Countries

Trade direction (import/export)

Year, quantity, and intent

Decide Agent

Maps parsed queries to data-fetch strategies.

Handles different cases:

Product vs HSN search

Import vs Export context

Multi-country or regional analysis

Act Agent

Executes final trade intelligence tasks:

Fetches data from databases/APIs

Cleans and processes the results

Generates recommendations

Exports to Excel using OpenPyXL

🧱 Example Excel Export
Exporter Name	Country	Product	Year	Export Value (USD)	HSN Code
ABC Traders Pvt Ltd	India	Tea	2024	1,200,000	0902
Global Tea Exports	India	Tea	2024	950,000	0902
🧩 Error Handling
Error	Description	Example
400 Bad Request	Invalid query or missing intent	Could not determine import/export intent from query.
404 Not Found	Excel file not found	When download file is missing
500 Internal Server Error	Unexpected runtime errors	Logged in logs/ directory for debugging
🛡️ Logging

All activities are logged using the logger defined in config.py

Log levels:

INFO → Normal operations

ERROR → Recoverable issues

CRITICAL → Unhandled exceptions

Logs are saved in:

logs/app.log

🚀 Future Enhancements

✅ Integrate live trade APIs (UN Comtrade, DGFT, etc.)
✅ Add dashboard for visual analytics
✅ Enable multilingual query support
✅ Add time-series forecasting (imports/exports trends)
✅ Deploy via Docker for production scalability

🧑‍💻 Contributors

Author: Sachin Awati

GitHub: github.com/Sachinawat