import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# Load your data
input_file = 'file.xlsx'  # Replace with your file path
df = pd.read_excel(input_file)

# Replace with your actual column names
lat_col = 'latitude'
lon_col = 'longitude'

# Extract coordinates
coords = df[[lat_col, lon_col]].to_numpy()

# Normalize data
scaler = StandardScaler()
coords_scaled = scaler.fit_transform(coords)

# Initialize Isolation Forest
iso_forest = IsolationForest(n_estimators=300, contamination=0.05, random_state=42)

# Fit and predict
df['Anomaly_Score'] = iso_forest.fit_predict(coords_scaled)  # -1 for anomalies, 1 for normal

# Save results
output_file = 'isolation_forest_results.xlsx'
df.to_excel(output_file, index=False)
print(f"Results saved to {output_file}")

# Visualization
plt.figure(figsize=(10, 6))
normal_mask = df['Anomaly_Score'] == 1
plt.scatter(df.loc[normal_mask, lon_col], df.loc[normal_mask, lat_col], c='b', label='Normal', alpha=0.6)
anomaly_mask = df['Anomaly_Score'] == -1
plt.scatter(df.loc[anomaly_mask, lon_col], df.loc[anomaly_mask, lat_col], c='r', label='Anomaly', marker='x')

plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Isolation Forest Anomaly Detection')
plt.legend()
plt.show()

# To determine the n_estimators to use. At some point, when the n_estimators increase further, the number of anomalies detected stagnate.
n_estimators_list = [100, 200, 300, 400, 500]
results = []

for n in n_estimators_list:
    iso = IsolationForest(n_estimators=n, contamination=0.05, random_state=42)
    df['scores'] = iso.fit_predict(coords)
    # Count anomalies
    anomalies = df[df['scores'] == -1]
    results.append((n, len(anomalies)))

# Plotting
plt.plot([r[0] for r in results], [r[1] for r in results], marker='o')
plt.xlabel('Number of Trees')
plt.ylabel('Number of Detected Anomalies')
plt.title('Effect of n_estimators on Anomaly Detection')
plt.show()
