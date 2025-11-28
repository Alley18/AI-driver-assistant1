# ------------------------
# evaluate_model.py
# ------------------------
import pandas as pd
import joblib
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)

# ------------------------
# Load model and datasets
# ------------------------
print("Loading model and datasets...")
model = joblib.load('driver_random_forest_model_tuned.joblib')

X_val = pd.read_csv('driver_val_features.csv')
y_val = pd.read_csv('driver_val_labels.csv').squeeze()  # convert DataFrame to Series
X_test = pd.read_csv('driver_test_features.csv')
y_test = pd.read_csv('driver_test_labels.csv').squeeze()

# Class labels for readability
classes = ['normal', 'drowsy', 'distracted']

# ------------------------
# Evaluate on validation set
# ------------------------
print("\n" + "="*60)
print("VALIDATION RESULTS")
print("="*60)

val_preds = model.predict(X_val)

print(f"Accuracy : {accuracy_score(y_val, val_preds):.4f}")
print(f"Precision: {precision_score(y_val, val_preds, average='weighted'):.4f}")
print(f"Recall   : {recall_score(y_val, val_preds, average='weighted'):.4f}")
print(f"F1-Score : {f1_score(y_val, val_preds, average='weighted'):.4f}")

# Confusion Matrix (with labels)
cm_val = confusion_matrix(y_val, val_preds)
print("\nConfusion Matrix (Validation):")
print(pd.DataFrame(cm_val, index=classes, columns=classes))

# Detailed classification report
print("\nClassification Report (Validation):")
print(classification_report(y_val, val_preds, target_names=classes))

# ------------------------
# Evaluate on test set
# ------------------------
print("\n" + "="*60)
print("TEST RESULTS")
print("="*60)

test_preds = model.predict(X_test)

print(f"Accuracy : {accuracy_score(y_test, test_preds):.4f}")
print(f"Precision: {precision_score(y_test, test_preds, average='weighted'):.4f}")
print(f"Recall   : {recall_score(y_test, test_preds, average='weighted'):.4f}")
print(f"F1-Score : {f1_score(y_test, test_preds, average='weighted'):.4f}")

cm_test = confusion_matrix(y_test, test_preds)
print("\nConfusion Matrix (Test):")
print(pd.DataFrame(cm_test, index=classes, columns=classes))

print("\nClassification Report (Test):")
print(classification_report(y_test, test_preds, target_names=classes))

print("\nEvaluation complete.")