from typing import Optional
from pydantic import BaseModel, Field

class ExtractionResult(BaseModel):
    id: str = Field(description="Unique identifier for the email")
    product_line: Optional[str] = Field(None, description="Product line (e.g., pl_sea_import_lcl, pl_sea_export_lcl)")
    origin_port_code: Optional[str] = Field(None, description="5-letter UN/LOCODE for origin port")
    origin_port_name: Optional[str] = Field(None, description="Canonical name of the origin port")
    destination_port_code: Optional[str] = Field(None, description="5-letter UN/LOCODE for destination port")
    destination_port_name: Optional[str] = Field(None, description="Canonical name of the destination port")
    incoterm: Optional[str] = Field("FOB", description="Incoterm (e.g., FOB, CIF). Defaults to FOB.")
    cargo_weight_kg: Optional[float] = Field(None, description="Total cargo weight in kg")
    cargo_cbm: Optional[float] = Field(None, description="Total cargo volume in CBM")
    is_dangerous: Optional[bool] = Field(False, description="Whether the shipment contains dangerous goods")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "EMAIL_001",
                "product_line": "pl_sea_import_lcl",
                "origin_port_code": "HKHKG",
                "origin_port_name": "Hong Kong",
                "destination_port_code": "INMAA",
                "destination_port_name": "Chennai",
                "incoterm": "FOB",
                "cargo_weight_kg": 100.50,
                "cargo_cbm": 5.0,
                "is_dangerous": False
            }
        }
