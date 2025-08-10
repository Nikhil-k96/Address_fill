"""
geocode_gcp_scraper.py

This script reads a CSV file with missing address fields and uses the Google Geocoding API to fetch and fill in the missing parts
of each address. It supports US and US-territory locations and handles blanks, placeholders, and fallbacks gracefully.
"""

import time
import pandas as pd
import requests

API_KEY = "your_real_api_key_here"
INPUT_FILE = "Missing Site addresses 2.csv"
OUTPUT_FILE = "GCP_scraped_Site_Addresses 2.csv"
AUTOSAVE_FILE = "autosave_output_site.csv"

VALID_US_COUNTRIES = {
    "united states", "usa", "us",
    "puerto rico", "guam", "u.s. virgin islands",
    "american samoa", "northern mariana islands"
}


def is_missing(value):
    """Check if a value is missing or a known placeholder"""
    if pd.isna(value):
        return True
    value_str = str(value).replace('\xa0', '').strip().lower()
    return value_str in {"", "tbd", "null", "unknown"}


def get_geocoded_result(address_query):
    """Call the Google Geocoding API and return the first result or handle limits"""
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address_query, "key": API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data["status"] == "OVER_QUERY_LIMIT":
                return "LIMIT_REACHED"
            if data["status"] == "OK" and data["results"]:
                return data["results"][0]
    except requests.RequestException:
        return {}
    return {}


def extract_component(components_list, component_type):
    """Extract a specific type from address components"""
    for part in components_list:
        if component_type in part["types"]:
            return part["long_name"]
    return None


# Load the CSV
df = pd.read_csv(
    INPUT_FILE,
    keep_default_na=True,
    na_values=["", " ", "\xa0", "TBD", "tbd", "null", "unknown"]
)

# Ensure expected columns exist
if "ScrapedAddress" not in df.columns:
    df["ScrapedAddress"] = ""
if "UpdatedFields" not in df.columns:
    df["UpdatedFields"] = ""

# Enrichment loop
for index, record in df.iterrows():
    print(f"\n🟡 Row {index} raw values:")
    for field in ["ShippingStreet", "ShippingCity", "ShippingState", "ShippingPostalCode", "ShippingCountry"]:
        print(f"  {field}: '{record.get(field)}'")

    fields_missing = any(is_missing(record.get(field)) for field in [
        "ShippingStreet", "ShippingCity", "ShippingState", "ShippingPostalCode", "ShippingCountry"])

    if fields_missing and pd.notna(record.get("Name")):
        query_parts = [record["Name"]]
        for field in ["ShippingStreet", "ShippingCity", "ShippingState", "ShippingPostalCode", "ShippingCountry"]:
            value = record.get(field)
            if pd.notna(value) and not is_missing(value):
                query_parts.append(str(value))
        address_query = ", ".join(query_parts)

        print(f"🔍 Row {index}: Searching for '{address_query}'")
        geocode_result = get_geocoded_result(address_query)

        if geocode_result == "LIMIT_REACHED":
            print("🚫 Google API limit hit. Stopping to avoid failure.")
            break

        if geocode_result:
            components = geocode_result.get("address_components", [])
            formatted = geocode_result.get("formatted_address", "")
            print("📦 Full formatted address returned by API:", formatted)
            print("📌 Components extracted:")
            for part in components:
                print(f"  - {part['types']}: {part['long_name']}")

            country = extract_component(components, "country")
            if not country or country.strip().lower() not in VALID_US_COUNTRIES:
                print(
                    f"⛔ Row {index}: Skipped - non-US address returned: {country}")
                df.at[index,
                      "UpdatedFields"] = f"Skipped (non-US result: {country})"
                continue

            df.at[index, "ScrapedAddress"] = formatted
            street_number = extract_component(components, "street_number")
            route = extract_component(components, "route")
            if street_number and route:
                final_street = f"{street_number} {route}".strip()
            elif route:
                final_street = route
            else:
                final_street = ""

            updates = []
            changes = []

            if is_missing(record.get("ShippingStreet")) and final_street:
                df.at[index, "ShippingStreet"] = final_street
                updates.append("ShippingStreet")
                changes.append(f"    ShippingStreet = {final_street}")
            if is_missing(record.get("ShippingCity")):
                city = extract_component(components, "locality")
                if city:
                    df.at[index, "ShippingCity"] = city
                    updates.append("ShippingCity")
                    changes.append(f"    ShippingCity = {city}")
            if is_missing(record.get("ShippingState")):
                state = extract_component(
                    components, "administrative_area_level_1")
                if state:
                    df.at[index, "ShippingState"] = state
                    updates.append("ShippingState")
                    changes.append(f"    ShippingState = {state}")
            if is_missing(record.get("ShippingPostalCode")):
                postal = extract_component(components, "postal_code")
                if postal:
                    df.at[index, "ShippingPostalCode"] = postal
                    updates.append("ShippingPostalCode")
                    changes.append(f"    ShippingPostalCode = {postal}")
            if is_missing(record.get("ShippingCountry")):
                if country:
                    df.at[index, "ShippingCountry"] = country
                    updates.append("ShippingCountry")
                    changes.append(f"    ShippingCountry = {country}")

            if updates:
                df.at[index, "UpdatedFields"] = ", ".join(updates)
                print(
                    f"✅ Row {index}: Updated → {df.at[index, 'UpdatedFields']}")
                for change in changes:
                    print(change)
            else:
                df.at[index, "UpdatedFields"] = "None (already complete)"
                print(f"✅ Row {index}: Updated → None (already complete)")
        else:
            print(f"❌ Row {index}: No address found")
            df.at[index, "UpdatedFields"] = "Not found"

        if index % 10 == 0:
            df.to_csv(AUTOSAVE_FILE, index=False)
            print(f"💾 Auto-saved to '{AUTOSAVE_FILE}'")

        time.sleep(1)

print(f"\n✅ Done. Output saved to '{OUTPUT_FILE}'")
df.to_csv(OUTPUT_FILE, index=False)
