# src/dataset_manager.py
#  This uniquely identifies a dataset structure
import json

def get_dataset_signature(df):
    return json.dumps({
        "columns": sorted(df.columns.tolist()),
        "dtypes": [str(t) for t in df.dtypes]
    })
