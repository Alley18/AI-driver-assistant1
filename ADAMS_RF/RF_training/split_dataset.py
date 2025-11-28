# ------------------------
# split_dataset.py
# ------------------------
import pandas as pd
from sklearn.model_selection import train_test_split

# Load your full dataset CSV
df = pd.read_csv('driver_dataset.csv')

# Optional: clean dataset
df = df.dropna()

# Encode labels
label_mapping = {'normal': 0, 'drowsy': 1, 'distracted': 2}
df['label'] = df['label'].map(label_mapping)

# Select feature columns and target
features = ['ear', 'mar', 'perclos', 'pitch', 'yaw', 'roll']
X = df[features]
y = df['label']

# Split dataset into train (70%), validation (15%), and test (15%)
X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, stratify=y, random_state=42)
val_size = 0.15 / (1 - 0.15)
X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=val_size, stratify=y_temp, random_state=42)

X_train.to_csv('driver_train_features.csv', index=False)
y_train.to_csv('driver_train_labels.csv', index=False)
X_val.to_csv('driver_val_features.csv', index=False)
y_val.to_csv('driver_val_labels.csv', index=False)
X_test.to_csv('driver_test_features.csv', index=False)
y_test.to_csv('driver_test_labels.csv', index=False)