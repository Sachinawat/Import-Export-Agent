
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict

class QueryInput(BaseModel):
    """
    Input model for the user's natural language query.
    """
    query: str = Field(..., example="What countries are importing HSN 8419 in high volume?")

class ParsedQuery(BaseModel):
    """
    Model for the query parsed by the Perceive Agent.
    """
    hsn_code: Optional[str] = Field(None, description="Extracted HSN code.")
    product_name: Optional[str] = Field(None, description="Extracted product name.")
    country: Optional[str] = Field(None, description="Extracted country name.")
    intent: Optional[str] = Field(None, description="'import' or 'export' intent.")
    keywords: List[str] = Field([], description="Additional relevant keywords.")

class TradeDataRecord(BaseModel):
    """
    Model for a single trade data record, expanded with shipment details.
    All fields are Optional as data availability will vary.
    """
    # Core Trade Data
    country: Optional[str] = None # Partner country (import from/export to)
    volume_usd: Optional[float] = None
    volume_unit: Optional[float] = None
    unit: Optional[str] = None
    year: Optional[int] = None
    source: Optional[str] = None

    # New fields for detailed shipment data
    hscode: Optional[str] = Field(None, alias="HS Code", description="Harmonized System Code")
    product_description: Optional[str] = Field(None, alias="Product Description")
    hs_product_description: Optional[str] = Field(None, alias="HS Product Description")
    shipper_name: Optional[str] = Field(None, alias="Shipper Name")
    consignee_name: Optional[str] = Field(None, alias="Consignee Name")
    std_quantity: Optional[float] = Field(None, alias="Standard Quantity")
    std_unit: Optional[str] = Field(None, alias="Standard Unit")
    country_of_destination: Optional[str] = Field(None, alias="Country of Destination")
    package_type: Optional[str] = Field(None, alias="Package Type")
    country_of_origin: Optional[str] = Field(None, alias="Country of Origin")
    quantity: Optional[float] = Field(None, alias="Quantity")
    bill_of_lading_no: Optional[str] = Field(None, alias="Bill of Lading No")
    consignee_address: Optional[str] = Field(None, alias="Consignee Address")
    supplier_address: Optional[str] = Field(None, alias="Supplier Address")
    container_teu: Optional[float] = Field(None, alias="Container TEU")
    port_of_origin: Optional[str] = Field(None, alias="Port of Origin")
    port_of_destination: Optional[str] = Field(None, alias="Port of Destination")
    port_of_delivery: Optional[str] = Field(None, alias="Port of Delivery")
    gross_weight: Optional[float] = Field(None, alias="Gross Weight")
    measurement: Optional[str] = Field(None, alias="Measurement") # e.g., "10 CBM"
    freight_term: Optional[str] = Field(None, alias="Freight Term") # e.g., "FOB", "CIF"
    forwarder_name: Optional[str] = Field(None, alias="Forwarder Name")
    declarant_name: Optional[str] = Field(None, alias="Declarant Name")
    notify_party_address: Optional[str] = Field(None, alias="Notify Party Address")
    declarant_name_2: Optional[str] = Field(None, alias="Declarant Name 2")
    marks_number: Optional[str] = Field(None, alias="Marks Number")
    contact_number_booking: Optional[str] = Field(None, alias="Contact Number Booking")
    contact_email_booking: Optional[str] = Field(None, alias="Contact Email Booking")

    # Pydantic configuration for alias and extra fields
    class Config:
        populate_by_name = True # Allow fields to be populated by their alias
        json_encoders = {
            HttpUrl: str # Ensure HttpUrl is serialized as string
        }


class Recommendation(BaseModel):
    """
    Model for a single recommendation.
    """
    title: str
    description: str

class IntelligenceOutput(BaseModel):
    """
    Final output model for the intelligence module.
    """
    query: str
    parsed_query: ParsedQuery
    trade_data: List[TradeDataRecord]
    recommendations: List[Recommendation]
    download_link: Optional[str] = Field(None, description="Placeholder for Excel download link.")

    # No need for custom json_encoders here if HttpUrl is already handled in TradeDataRecord
    # Pydantic's default behavior with exclude_none will work in main.py