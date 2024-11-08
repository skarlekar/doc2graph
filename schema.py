from pydantic import BaseModel, Field
from typing import List

class Relationship(BaseModel):
    head: str = Field(
        description="The text of the extracted entity"
    )
    head_type: str = Field(
        description="The type of the extracted head entity"
    )
    relation: str = Field(
        description="The type of relation between the head and tail"
    )
    tail: str = Field(
        description="The text of the entity representing the tail of the relation"
    )
    tail_type: str = Field(
        description="The type of the tail entity"
    )

class RelationshipList(BaseModel):
    relationships: List[Relationship]

    class Config:
        json_schema_extra = {
            "example": [
                {
                    "head": "John Smith",
                    "head_type": "Person",
                    "relation": "WORKS_AT",
                    "tail": "Acme Corporation",
                    "tail_type": "Organization"
                }
            ]
        } 

class RelationshipLite(BaseModel):
    head_type: str = Field(
        description="The type of the extracted head entity"
    )
    relation: str = Field(
        description="The type of relation between the head and tail"
    )
    tail_type: str = Field(
        description="The type of the tail entity"
    )
    check: bool = Field(
        description="Whether the relationship has been checked"
    )

class RelationshipLiteList(BaseModel):
    relationships: List[RelationshipLite]

    class Config:
        json_schema_extra = {
            "example": [
                {
                    "head_type": "Person",
                    "relation": "WORKS_AT",
                    "tail_type": "Organization",
                    "check": False
                }
            ]
        } 