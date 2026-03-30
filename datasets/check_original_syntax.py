import pandas as pd
import requests
import json


def check_code_syntax(code: str):
    endpoint = 'http://localhost:8002/api/syntax_checker'
    # Ensure code is a string and not NaN
    if pd.isna(code) or str(code).strip() == "":
        return 'CODE_BLOCK_NOT_FOUND'

    payload = {'code': str(code)}

    try:
        response = requests.post(url=endpoint, json=payload)
        # Check if the request was successful before decoding
        response.raise_for_status()
        result = json.loads(response.content.decode("utf-8"))
        result_content = result['result']
        if result_content != 'OK':
            print(code)
            print("*" * 30)
        return result_content
    except Exception as e:
        return f'ERROR: {str(e)}'


# --- Main Execution ---

# 1. Read the dataset
df = pd.read_csv('old_datasets/dataset.csv')

# 2. Iterate through the 'modules' column and store results
print("Checking syntax... this may take a moment.")
df['syntax_result'] = df['modules'].apply(check_code_syntax)

# 3. Count the "OK" responses
ok_count = (df['syntax_result'] == 'OK').sum()

# 4. Output results
print("-" * 30)
print(f"Total rows processed: {len(df)}")
print(f"Number of 'OK' responses: {ok_count}")
print("-" * 30)

# Optional: Save the results to a new CSV
# df.to_csv('syntax_results.csv', index=False)