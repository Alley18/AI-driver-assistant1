# ------------------------
# train_random_forest_tuned.py
# ------------------------
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib

# Load datasets
X_train = pd.read_csv('driver_train_features.csv')
y_train = pd.read_csv('driver_train_labels.csv').squeeze()
X_val = pd.read_csv('driver_val_features.csv')
y_val = pd.read_csv('driver_val_labels.csv').squeeze()

best_params = {}
best_acc = 0
results = []

# Search combinations
for n_estimators in [50, 100, 200]:
    for max_depth in [5, 10, 15, None]:
        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=5,
            random_state=42
        )
        model.fit(X_train, y_train)
        val_acc = accuracy_score(y_val, model.predict(X_val))
        results.append((n_estimators, max_depth, val_acc))

        if val_acc > best_acc:
            best_acc = val_acc
            best_params = {'n_estimators': n_estimators, 'max_depth': max_depth}

print("Best parameters:", best_params)
print("Validation Accuracy:", best_acc)

# Retrain final Random Forest using best params
final_model = RandomForestClassifier(
    **best_params,
    min_samples_split=5,
    random_state=42
)
final_model.fit(X_train, y_train)

# Save final tuned model
joblib.dump(final_model, 'driver_random_forest_model_tuned.joblib')
print("Tuned Random Forest model saved.")