import openai
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from urllib.parse import urlparse
import random # For simulating varying data availability

from config import settings, logger, LOGS_DIR
from models import QueryInput, ParsedQuery, TradeDataRecord, Recommendation
from utils import perform_google_search, simple_web_scraper, normalize_country_name

# Initialize OpenAI client
client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

class PerceiveAgent:
    # ... (no changes to PerceiveAgent)
    """
    Perceives the user's natural language query and extracts key entities.
    Uses an LLM for parsing.
    """
    def parse_query(self, query: str) -> ParsedQuery:
        logger.info(f"Perceive Agent: Parsing query - '{query}'")
        prompt = f"""
        Analyze the following user query and extract the HSN code, product name, country, and the user's intent (import or export).
        If an entity is not explicitly mentioned, return null for that field.
        Return the output as a JSON object with the following keys: hsn_code, product_name, country, intent, keywords.
        Keywords should be a list of additional relevant terms that could be used for searching.

        Examples:
        "What countries are importing HSN 8419 in high volume?"
        {{
            "hsn_code": "8419",
            "product_name": null,
            "country": null,
            "intent": "import",
            "keywords": ["high volume"]
        }}

        "Where can we export gas compressors from India?"
        {{
            "hsn_code": null,
            "product_name": "gas compressors",
            "country": "India",
            "intent": "export",
            "keywords": []
        }}

        "HSN 9021 imports to Germany, trends?"
        {{
            "hsn_code": "9021",
            "product_name": null,
            "country": "Germany",
            "intent": "import",
            "keywords": ["trends"]
        }}

        User query: "{query}"
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o", # Or "gpt-3.5-turbo" for cost-effectiveness
                messages=[
                    {"role": "system", "content": "You are a helpful assistant designed to extract structured information from user queries."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.0
            )
            parsed_data = json.loads(response.choices[0].message.content)
            logger.info(f"Perceive Agent: Parsed query: {parsed_data}")
            return ParsedQuery(**parsed_data)
        except json.JSONDecodeError as e:
            logger.error(f"Perceive Agent: Failed to decode JSON from LLM response: {e}. Raw response: {response.choices[0].message.content}")
            return ParsedQuery() # Return empty or default
        except Exception as e:
            logger.error(f"Perceive Agent: Error during query parsing: {e}")
            return ParsedQuery() # Return empty or default


class DecideAgent:
    # ... (no changes to DecideAgent)
    """
    Decides the best strategy and data sources based on the parsed query.
    """
    def decide_strategy(self, parsed_query: ParsedQuery) -> List[str]:
        logger.info(f"Decide Agent: Deciding strategy for parsed query: {parsed_query.model_dump_json()}")
        search_queries = []

        base_query = ""
        if parsed_query.hsn_code:
            base_query += f"HSN {parsed_query.hsn_code} "
        if parsed_query.product_name:
            base_query += f"{parsed_query.product_name} "

        if parsed_query.intent == "import":
            base_query += "import data "
        elif parsed_query.intent == "export":
            base_query += "export data "
        else:
            base_query += "trade data "

        if parsed_query.country:
            base_query += f"from {parsed_query.country} " if parsed_query.intent == "export" else f"to {parsed_query.country} "

        base_query += "open source statistics"
        search_queries.append(base_query.strip())

        # Add more specific search queries
        if parsed_query.hsn_code:
            search_queries.append(f"UN Comtrade HSN {parsed_query.hsn_code}")
            search_queries.append(f"EU Eurostat HSN {parsed_query.hsn_code} {parsed_query.intent} data")
            search_queries.append(f"US Census Bureau HSN {parsed_query.hsn_code} {parsed_query.intent} statistics")
            if parsed_query.country and normalize_country_name(parsed_query.country) == "India":
                search_queries.append(f"DGFT India HSN {parsed_query.hsn_code} {parsed_query.intent} data")

        logger.info(f"Decide Agent: Generated search queries: {search_queries}")
        return search_queries

class ActAgent:
    """
    Executes the data fetching, processing, and recommendation generation.
    """
    def __init__(self):
        self.scraped_data_cache = {}

    def fetch_data(self, search_queries: List[str], parsed_query: ParsedQuery) -> List[TradeDataRecord]:
        logger.info(f"Act Agent: Starting data fetching for {len(search_queries)} queries.")
        raw_trade_data: List[TradeDataRecord] = []

        for query in search_queries:
            google_results = perform_google_search(query)
            for result in google_results:
                link = result.get('link')
                title = result.get('title')
                if link and "pdf" not in link.lower() and "excel" not in link.lower():
                    if link in self.scraped_data_cache:
                        logger.info(f"Act Agent: Skipping already scraped URL: {link}")
                        continue

                    logger.info(f"Act Agent: Attempting to process search result: {title} ({link})")
                    simulated_scrape = self._simulate_scrape_from_url(link, query, parsed_query)
                    if simulated_scrape:
                        raw_trade_data.extend(simulated_scrape)
                        self.scraped_data_cache[link] = True
                    else:
                        logger.warning(f"Act Agent: No data simulated from {link}. Scraping might fail for this URL.")
        return raw_trade_data

    def _simulate_scrape_from_url(self, url: str, query: str, parsed_query: ParsedQuery) -> List[TradeDataRecord]:
        """
        Simulates data extraction for various trade fields.
        Intentionally leaves some fields as None to demonstrate 'show only available'.
        """
        logger.info(f"Simulating data extraction for URL: {url} based on query: {query}")

        hscode_val = parsed_query.hsn_code
        product_desc_val = parsed_query.product_name
        intent = parsed_query.intent

        dummy_data = []
        # These will be the *partner* countries in the trade record
        possible_partner_countries = ["USA", "Germany", "China", "Japan", "Brazil", "Canada", "Mexico", "France", "UK"]

        # If a specific country was queried (e.g., "export from India"),
        # then India is the reporting country, and the data records are about its partners.
        # So, the queried country itself should not appear in the `country` field of TradeDataRecord
        # because that field is for the *partner* in the trade.
        target_reporting_country_normalized = normalize_country_name(parsed_query.country) if parsed_query.country else None

        for partner_country_name in possible_partner_countries:
            # Skip if this partner country is the same as the reporting country from the query
            if target_reporting_country_normalized and normalize_country_name(partner_country_name) == target_reporting_country_normalized:
                continue

            # Simulate base trade data (volume, etc.)
            volume = 100000 + (abs(hash(partner_country_name + query)) % 100000)
            if intent == "import":
                volume *= 1.2
            elif intent == "export":
                volume *= 0.8

            # Simulate new detailed fields with varying availability
            # Use random.choice([value, None]) to make some fields optional
            record_data = {
                "country": partner_country_name,
                "volume_usd": float(volume),
                "volume_unit": volume / 100,
                "unit": random.choice(["kg", "units", "tons", None]),
                "year": 2023,
                "source": urlparse(url).netloc or "Simulated Data Source",

                # New detailed fields - simulate availability
                "hscode": hscode_val if random.random() > 0.1 else None, # 90% chance of being present
                "product_description": product_desc_val if random.random() > 0.05 else f"Generic {hscode_val or 'Product'}", # Always has something if HSN/Product exists
                "hs_product_description": random.choice([f"Description for HSN {hscode_val or 'unknown'}", None]),
                "shipper_name": random.choice([f"Shipper_{random.randint(100, 999)} Inc.", None]),
                "consignee_name": random.choice([f"Consignee_{random.randint(100, 999)} Co.", None]),
                "std_quantity": random.choice([round(volume / 5000, 2), None]),
                "std_unit": random.choice(["Pieces", "Pallets", None]),
                "country_of_destination": partner_country_name if intent == "export" else target_reporting_country_normalized, # Assuming this is the trade direction
                "package_type": random.choice(["Cartons", "Pallets", "Boxes", None]),
                "country_of_origin": target_reporting_country_normalized if intent == "export" else partner_country_name, # Assuming this is the trade direction
                "quantity": random.choice([round(volume / 1000, 2), None]),
                "bill_of_lading_no": random.choice([f"BL-{random.randint(10000, 99999)}", None]),
                "consignee_address": random.choice([f"123 Main St, {partner_country_name}", None]),
                "supplier_address": random.choice([f"456 Trade Rd, {target_reporting_country_normalized or 'Global'}", None]),
                "container_teu": random.choice([1.0, 2.0, 0.5, None]),
                "port_of_origin": random.choice([f"Port {random.choice(['A', 'B', 'C'])}", None]),
                "port_of_destination": random.choice([f"Port {random.choice(['X', 'Y', 'Z'])}", None]),
                "port_of_delivery": random.choice([f"Port {random.choice(['P', 'Q', 'R'])}", None]),
                "gross_weight": random.choice([round(volume / 100, 2), None]),
                "measurement": random.choice([f"{random.randint(10, 50)} CBM", None]),
                "freight_term": random.choice(["FOB", "CIF", "EXW", None]),
                "forwarder_name": random.choice([f"Forwarder {random.choice(['Logistics', 'Global'])}", None]),
                "declarant_name": random.choice([f"Declarant {random.randint(1, 5)}", None]),
                "notify_party_address": random.choice([f"789 Recv Blvd, {partner_country_name}", None]),
                "declarant_name_2": random.choice([f"Declarant {random.randint(6, 10)}", None]),
                "marks_number": random.choice([f"MN-{random.randint(1000, 9999)}", None]),
                "contact_number_booking": random.choice([f"+1{random.randint(1000000000, 9999999999)}", None]),
                "contact_email_booking": random.choice([f"booking{random.randint(1, 10)}@example.com", None])
            }
            
            dummy_data.append(TradeDataRecord(**record_data))
        return dummy_data


    def generate_recommendations(self, trade_data: List[TradeDataRecord], parsed_query: ParsedQuery) -> List[Recommendation]:
        logger.info(f"Act Agent: Generating recommendations for {len(trade_data)} records.")
        if not trade_data:
            return [Recommendation(title="No Data", description="No sufficient trade data found to generate specific recommendations.")]

        # Use model_dump(exclude_none=True) to ensure only present fields go to DF for analysis
        df = pd.DataFrame([td.model_dump(exclude_none=True) for td in trade_data])

        recommendations_list = []

        # Example 1: Top countries by volume (still relevant)
        if not df.empty and 'volume_usd' in df.columns:
            df['volume_usd'] = pd.to_numeric(df['volume_usd'], errors='coerce').fillna(0)
            
            top_countries = df.groupby('country')['volume_usd'].sum().nlargest(3)
            
            if not top_countries.empty:
                intent_phrase = parsed_query.intent + ("ing" if parsed_query.intent else "")
                title = f"Top 3 {intent_phrase} Markets by Volume"
                description_parts = []
                for country, volume in top_countries.items():
                    description_parts.append(f"{country}: ${volume:,.2f}")
                recommendations_list.append(Recommendation(title=title, description=", ".join(description_parts)))
        
        # Add new recommendation types based on new data fields (if they exist in the simulated data)
        if 'freight_term' in df.columns and not df['freight_term'].isnull().all():
            common_terms = df['freight_term'].mode()
            if not common_terms.empty:
                recommendations_list.append(Recommendation(
                    title="Common Freight Terms",
                    description=f"Most frequently observed freight term: {common_terms.iloc[0]}."
                ))
        
        if 'package_type' in df.columns and not df['package_type'].isnull().all():
            common_packages = df['package_type'].mode()
            if not common_packages.empty:
                recommendations_list.append(Recommendation(
                    title="Typical Packaging",
                    description=f"Common packaging type: {common_packages.iloc[0]}."
                ))

        # Use LLM for more sophisticated recommendations
        try:
            # Pass only the relevant columns for LLM context to avoid overwhelming it
            llm_df_for_prompt = df[['country', 'volume_usd', 'product_description', 'freight_term', 'package_type', 'shipper_name', 'consignee_name']].head(5).to_string() # Limiting to 5 rows for brevity
            
            llm_recommendation_prompt = f"""
            Based on the following sample trade data (showing first 5 rows and selected columns):
            {llm_df_for_prompt}

            And the parsed user query:
            {parsed_query.model_dump_json()}

            Considering the intent '{parsed_query.intent}' and specific product/HSN '{parsed_query.product_name or parsed_query.hsn_code}' (if available)
            and country '{parsed_query.country}' (if available),
            Provide 1-2 concise, actionable recommendations for import/export strategy specific to this context.
            Focus on insights derived from the provided data or common trade strategies.
            For example, if freight terms are mostly FOB, suggest exploring CIF for more control.
            Format as a JSON list of objects, each with 'title' and 'description' keys.
            """
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert trade analyst providing concise, actionable recommendations based on provided data and user query context. Do not make up data, focus on strategic advice."},
                    {"role": "user", "content": llm_recommendation_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7
            )
            llm_recs_raw = response.choices[0].message.content
            
            parsed_llm_recs = json.loads(llm_recs_raw)
            
            if isinstance(parsed_llm_recs, list):
                for rec_data in parsed_llm_recs:
                    if 'title' in rec_data and 'description' in rec_data:
                        recommendations_list.append(Recommendation(**rec_data))
            elif isinstance(parsed_llm_recs, dict) and 'recommendations' in parsed_llm_recs and isinstance(parsed_llm_recs['recommendations'], list):
                for rec_data in parsed_llm_recs['recommendations']:
                    if 'title' in rec_data and 'description' in rec_data:
                        recommendations_list.append(Recommendation(**rec_data))
            else:
                 logger.warning(f"Act Agent: LLM returned unexpected format for recommendations: {llm_recs_raw}")

        except json.JSONDecodeError as e:
            logger.warning(f"Act Agent: Failed to decode JSON from LLM recommendations: {e}. Raw response: {llm_recs_raw}")
        except Exception as e:
            logger.warning(f"Act Agent: Failed to generate LLM recommendations: {e}", exc_info=True)


        if not recommendations_list:
            recommendations_list.append(Recommendation(
                title="General Advice",
                description="Further detailed analysis is required for specific recommendations."
            ))

        return recommendations_list

    def export_to_excel(self, trade_data: List[TradeDataRecord], filename: str = "trade_data.xlsx") -> Path:
        """
        Exports the trade data to an Excel file.
        """
        output_path = LOGS_DIR / filename
        logger.debug(f"Attempting to save Excel to: {output_path.resolve()}")

        if not trade_data:
            logger.warning("No trade data to export to Excel. Creating an empty file.")
            pd.DataFrame().to_excel(output_path, index=False)
            logger.debug(f"Created empty Excel file at: {output_path.resolve()}")
            return output_path

        # Use model_dump(exclude_none=True) here too, so Excel only gets populated fields
        # This will remove columns that are entirely None, but keep columns where some values are None.
        # If you want ALL columns in the Excel, even if all values are None for a field, remove exclude_none=True.
        # However, it's generally better to show only relevant columns in Excel.
        # To show ALL columns (even if empty):
        # df = pd.DataFrame([td.model_dump(by_alias=True) for td in trade_data])
        # To show only columns that have at least one non-None value:
        df = pd.DataFrame([td.model_dump(by_alias=True, exclude_none=True) for td in trade_data])

        # If after excluding none, the DataFrame is empty, ensure at least all headers are present
        if df.empty and trade_data:
             # Create an empty DataFrame with all possible headers from the model, for consistency
             all_fields = TradeDataRecord.model_fields.keys()
             df = pd.DataFrame(columns=[TradeDataRecord.model_fields[field].alias or field for field in all_fields])
             logger.info("Created empty DataFrame for Excel with all headers as no data with values was found.")


        df.to_excel(output_path, index=False)
        logger.info(f"Act Agent: Data exported to Excel: {output_path}")
        logger.debug(f"Successfully created Excel file at: {output_path.resolve()}")
        return output_path

# Instantiate agents
perceive_agent = PerceiveAgent()
decide_agent = DecideAgent()
act_agent = ActAgent()