import pandas as pd
import sys

file_path = sys.argv[1]

def analyze_dataset(file_path):
    if file_path.endswith(".csv"):
        df = pd.read_csv(file_path)
    elif file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)
    else:
        return {"error": "Unsupported file format"}

    result = {
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "missing_values": df.isnull().sum().to_dict(),
        "summary_statistics": df.describe().to_dict()
    }

    return result

print(analyze_dataset(file_path))