from typing import Optional
from pydantic import BaseModel, Field, field_validator

class ExtractionResult(BaseModel):
    """Data model for shipping email extraction results."""
    id: str = Field(..., description="Unique email identifier")
    reasoning: Optional[str] = Field(None, description="AI's internal logic for extraction")
    product_line: Optional[str] = Field(None, pattern=r"^pl_sea_(import|export)_lcl$")
    origin_port_code: Optional[str] = Field(None, min_length=5, max_length=5)
    origin_port_name: Optional[str] = Field(None)
    destination_port_code: Optional[str] = Field(None, min_length=5, max_length=5)
    destination_port_name: Optional[str] = Field(None)
    incoterm: Optional[str] = Field("FOB")
    cargo_weight_kg: Optional[float] = Field(None, ge=0)
    cargo_cbm: Optional[float] = Field(None, ge=0)
    is_dangerous: bool = Field(False)

    @field_validator("incoterm")
    @classmethod
    def normalize_incoterm(cls, v: Optional[str]) -> str:
        if not v or not isinstance(v, str):
            return "FOB"
        valid_incoterms = {"FOB", "CIF", "CFR", "EXW", "DDP", "DAP", "FCA", "CPT", "CIP", "DPU"}
        upper_v = v.strip().upper()
        return upper_v if upper_v in valid_incoterms else "FOB"

    @field_validator("cargo_weight_kg", "cargo_cbm")
    @classmethod
    def round_numeric(cls, v: Optional[float]) -> Optional[float]:
        if v is not None:
            return round(float(v), 2)
        return v
