import os
import pandas as pd
import requests
import openpyxl
import json

from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

Authorization = 'xx'

payload = { "grant_type": "client_credentials" }
headers_token = {
    "authorization": Authorization,
    "accept": "application/json",
    "content-type": "application/x-www-form-urlencoded"
}

apikey='yy'
URL_Token = 'https://...'
URL = "https://a..."

# After having inserted the authorization header in headers_token, we use it to obtain token response
token_response = requests.post(URL_Token, data=payload, headers=headers_token)

# From token response we obtain bearer token which we use in headers_bearer. The latter is necessary to retrieve the data from a given endpoint.
Bearer_token = token_response.json().get("access_token")
print(f"Your Bearer_token is: {Bearer_token}\n")

headers_bearer = {
   "authorization": f"Bearer {Bearer_token}",
    "x-api-key": apikey  # if required
}
limit = 250  # Your API limit per request
offset = 0
endpoint='...?limit='+str(limit)+'&offset='+str(offset)
print(endpoint)

# The below code (between triple double inverted commas) works but takes too much time to retrieve all data.
# The limit of 250 does not help because each time only 250 IDs will be fetched out of more 100k IDs with other data associated.
# This method which is executed sequentially could take at least 30 minutes to complete.
  
"""all_data = []
while True:
    #params = {'offset': offset, 'limit': limit}
    response = requests.get(URL+endpoint, headers=headers_bearer)
    data = response.json()
    print(response.status_code)
    if not data or len(data) == 0:
        break  # no more data
    all_data.extend(data)
    offset += limit  # move to next batch

print(f"Total records fetched: {len(all_data)}")"""

# However with the method below, that is concurrent programming, the concurrent.futures module is used to run multiple tasks concurrently using threads.
# Instead of waiting for one task to finish before starting the next, ThreadPoolExecutor allows several tasks to be in progress at the same time.
# ThreadPoolExecutor is one of the easiest ways to send multiple API requests concurrently, instead of waiting for each request to finish before sending the next.
# The time taken to fetch all data would be around 15 minutes.
# The data are stored in Parquet which is a file format designed for efficient storage and fast analytics on large datasets.
# It is a columnar storage format, meaning it stores data column by column instead of row by row and also supports efficient compression.

OUTPUT_DIR = "parquet_data"
os.makedirs(OUTPUT_DIR, exist_ok=True)

session = requests.Session()
session.headers.update(headers_bearer)

LIMIT = 250
MAX_WORKERS = 15 # It can be more or less. We can increase it to try to speed things up but some batches will fail to download. It depends on the capacity of the machine that we use.

os.makedirs(OUTPUT_DIR, exist_ok=True)

# FETCH ONE PAGE
def fetch_and_save(offset):
    endpoint = f"...?limit={LIMIT}&offset={offset}"
    url = URL.rstrip("/") + endpoint

    try:
        print(f"Fetching offset={offset}")
        r = session.get(url, timeout=(10, 300))
        r.raise_for_status()
        data = r.json()

        # normalize response
        if isinstance(data, list):
            records = data
        else:
            records = (
                data.get("description")
                or data.get("items")
                or data.get("content")
                or []
            )

        if not records:
            print(f"No records returned for offset={offset}")
            return 0

        df = pd.json_normalize(records)

        file_path = os.path.join(
            OUTPUT_DIR,
            f"data_{offset}.parquet"
        )

        df.to_parquet(file_path, index=False)
        #print(
        #    f"Saved offset={offset}, "
        #    f"rows={len(records)}, "
        #    f"file={file_path}"
        #)
        return len(records)

    except Exception as e:
        print(f"Offset {offset} failed: {e}")
        return 0

offsets = list(range(0, 100_000, LIMIT))
# RUN IN PARALLEL
total = 0

with concurrent.futures.ThreadPoolExecutor(
    max_workers=MAX_WORKERS
) as executor:
    future_to_offset = {
        executor.submit(fetch_and_save, offset): offset
        for offset in offsets
    }

    for future in concurrent.futures.as_completed(future_to_offset):
        offset = future_to_offset[future]
        try:
            count = future.result()
            total += count
            print(
                f"Completed offset={offset}, "
                f"records={count}, "
                f"running_total={total}"
            )
        except Exception as e:
            print(f"Offset {offset} crashed: {e}")

print(f"\nFinished. Total records processed: {total}")
