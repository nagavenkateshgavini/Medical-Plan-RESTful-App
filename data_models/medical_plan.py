from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class PlanCostShares(BaseModel):
    deductible: int
    _org: str
    copay: int
    objectId: str
    objectType: str


class LinkedService(BaseModel):
    _org: str
    objectId: str
    objectType: str
    name: str


class PlanserviceCostShares(BaseModel):
    deductible: int
    _org: str
    copay: int
    objectId: str
    objectType: str


class LinkedPlanServiceItem(BaseModel):
    linkedService: LinkedService
    planserviceCostShares: PlanserviceCostShares
    _org: str
    objectId: str
    objectType: str


class PlanSchema(BaseModel):
    planCostShares: PlanCostShares
    linkedPlanServices: List[LinkedPlanServiceItem]
    _org: str
    objectId: str
    objectType: str
    planType: str
    # creationDate: Optional[datetime]

    class Config:
        title = "The Plan Schema"
        schema_extra = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "$id": "http://example.com/root.json"
        }

    @classmethod
    def validate_linkedPlanServices(cls, v):
        if len(v) < 1:
            raise ValueError('linkedPlanServices must contain at least one item')
        return v

    @classmethod
    def __get_validators__(cls):
        yield from super().__get_validators__()
        yield cls.validate_linkedPlanServices
