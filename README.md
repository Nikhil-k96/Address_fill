# Google Cloud Geocoding Scraper – Site & Billing Address Enrichment for Salesforce

## Overview
This project contains two Python scripts built to enrich missing **Site** and **Billing** addresses for Salesforce Accounts using the **Google Cloud Geocoding API**.

The primary goal was to overcome a Salesforce **validation rule** that required all Account records to have complete Site and Billing addresses before they could be updated or saved.  
Without this enrichment, many records could not be modified because of incomplete address data.

## Files in this Repository
- **`geocode_GCP_scraper(Site).py`** – Enriches missing Site addresses.
- **`geocode_GCP_scraper(Billing).py`** – Enriches missing Billing addresses.

## Features
- Automates address lookups using the **Google Cloud Geocoding API**.
- Retrieves accurate street, city, state, postal code, and country.
- Handles partial matches and returns the best possible results.
- Outputs enriched CSVs ready for Salesforce data loads.

## Requirements
Install Python dependencies with:
```bash
pip install -r requirements.txt
```

## Setup
1. Enable the **Google Cloud Geocoding API** in your Google Cloud project.
2. Obtain an API Key.
3. Create a `.env` file in the project directory and add:
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Place your input CSV file in the same folder as the script.
6. Run the script for Site addresses:
   ```bash
   python geocode_GCP_scraper(Site).py
   ```
   Or for Billing addresses:
   ```bash
   python geocode_GCP_scraper(Billing).py
   ```

## Output
A new CSV file containing enriched address fields for Salesforce uploads.

## Example `.env`
```
GOOGLE_API_KEY=AIzaSy...
```

## Notes
- Make sure `.env` is in `.gitignore` so the API key is never pushed to GitHub.
- The sample CSV in this repository contains only fake data for demonstration.
