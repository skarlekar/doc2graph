import pandas as pd
import streamlit as st
from typing import List

from schema import Relationship, RelationshipList, RelationshipLite, RelationshipLiteList

def convert_to_lite(relationships: List[Relationship]) -> List[RelationshipLite]:
    unique_results = []
    seen = set()
    for r in relationships:
        key = (r.head_type, r.relation, r.tail_type)
        if key not in seen:
            seen.add(key)
            # Create a RelationshipLite object with check=False
            lite_relationship = RelationshipLite(
                head_type=r.head_type,
                relation=r.relation,
                tail_type=r.tail_type,
                check=False
            )
            unique_results.append(lite_relationship)
    return unique_results

def get_dataframe(results: List[RelationshipLite]) -> pd.DataFrame:

    data = [{
        'From': item.head_type,
        'Relationship': item.relation,
        'To': item.tail_type
    } for item in results]

    # Convert to DataFrame
    df = pd.DataFrame(data)
    return df