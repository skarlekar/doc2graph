import numpy as np
import pandas as pd
import streamlit as st
from typing import List

from json_data import sample_results
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

@st.cache_data
def get_profile_dataset() -> pd.DataFrame:
    # Wrap the list in a dictionary with 'relationships' key
    if isinstance(sample_results, list):
        validated_data = RelationshipList(relationships=sample_results)
    else:
        # If response is already in the expected format
        validated_data = RelationshipList(**sample_results)

    # Convert the relationships to a list of RelationshipLite
    lite_results = convert_to_lite(validated_data.relationships)
    data = [{
        'From': item.head_type,
        'Relationship': item.relation,
        'To': item.tail_type
    } for item in lite_results]

    # Convert to DataFrame
    df = pd.DataFrame(data)
    return df

# Configure columns
column_configuration = {
    "From": st.column_config.TextColumn("From", width=200),
    "Relationship": st.column_config.TextColumn("Relationship", width=200),
    "To": st.column_config.TextColumn("To", width=200)
}


tabs = st.tabs(["Select Relationships"])
select = tabs[0]  # Get the first tab

with select:
    st.header("All Relationships")

    df = get_profile_dataset()

    event = st.dataframe(
        df,
        column_config=column_configuration,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
    )

    st.header("Selected Relationships")
    selected_relationships = event.selection.rows
    filtered_df = df.iloc[selected_relationships]
    st.dataframe(
        filtered_df,
        column_config=column_configuration,
        use_container_width=True,
    )

