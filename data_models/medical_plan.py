from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, validator, Field


class PlanCostShares(BaseModel):
    deductible: int
    org: str
    copay: int
    objectId: str
    objectType: str


class LinkedService(BaseModel):
    org: str
    objectId: str
    objectType: str
    name: str


class PlanserviceCostShares(BaseModel):
    deductible: int
    org: str
    copay: int
    objectId: str
    objectType: str


class LinkedPlanServiceItem(BaseModel):
    linkedService: LinkedService
    planserviceCostShares: PlanserviceCostShares
    org: str
    objectId: str
    objectType: str


class PlanSchema(BaseModel):
    planCostShares: PlanCostShares
    linkedPlanServices: List[LinkedPlanServiceItem]
    org: str
    objectId: str
    objectType: str
    planType: str
    creationDate: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

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

# TODO: Better way to create partial models
# def create_partial_model(name: str, model: BaseModel) -> BaseModel:
#     fields = {}
#     for field_name, field_type in model.__annotations__.items():
#         if hasattr(field_type, '__origin__') and issubclass(field_type.__origin__, list):
#             # Handle lists of nested models
#             sub_model = field_type.__args__[0]
#             if issubclass(sub_model, BaseModel):
#                 fields[field_name] = (Optional[List[create_partial_model(field_name, sub_model)]], None)
#             else:
#                 fields[field_name] = (Optional[field_type], None)
#         elif issubclass(field_type, BaseModel):
#             # Handle nested models
#             fields[field_name] = (Optional[create_partial_model(field_name, field_type)], None)
#         else:
#             # Handle standard fields
#             fields[field_name] = (Optional[field_type], None)
#     return create_model(name, **fields)
#
# # Create the partial model for PlanSchema
# PartialPlanSchema = create_partial_model('PartialPlanSchema', PlanSchema)


class PatchPlanCostShares(BaseModel):
    deductible: Optional[int] = None
    org: Optional[str] = None
    copay: Optional[int] = None
    objectId: str
    objectType: Optional[str] = None


class PatchLinkedService(BaseModel):
    org: Optional[str] = None
    objectId: str
    objectType: Optional[str] = None
    name: Optional[str] = None


class PatchPlanserviceCostShares(BaseModel):
    deductible: Optional[int] = None
    org: Optional[str] = None
    copay: Optional[int] = None
    objectId: str
    objectType: Optional[str] = None


class PatchLinkedPlanServiceItem(BaseModel):
    linkedService: Optional[PatchLinkedService] = None
    planserviceCostShares: Optional[PatchPlanserviceCostShares] = None
    org: Optional[str] = None
    objectId: Optional[str] = None
    objectType: Optional[str] = None


class PatchPlanSchema(BaseModel):
    planCostShares: Optional[PatchPlanCostShares] = None
    linkedPlanServices: Optional[List[PatchLinkedPlanServiceItem]] = None
    org: Optional[str] = None
    objectId: str
    objectType: Optional[str] = None
    planType: Optional[str] = None
    creationDate: Optional[datetime] = None

    @classmethod
    def validate_linkedPlanServices(cls, v):
        if v is not None and len(v) < 1:
            raise ValueError('linkedPlanServices must contain at least one item')
        return v

    @classmethod
    def __get_validators__(cls):
        yield from super().__get_validators__()
        yield cls.validate_linkedPlanServices
