"""Script for comprehensive evaluation of the linguistic evasion labeler"""

import os
import json
import pandas as pd
import numpy as np
import time
from atproto import Client
from dotenv import load_dotenv
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
)

# Import your labeler
from pylabel.policy_proposal_labeler import LinguisticEvasionLabeler

load_dotenv(override=True)
USERNAME = os.getenv("USERNAME")
PW = os.getenv("PW")

# Define the labels we're testing
GENERAL_LABEL = "linguistic-evasion"
SPECIFIC_LABELS = ["character-substitution", "homophone", "spoonerism"]
ALL_LABELS = [GENERAL_LABEL] + SPECIFIC_LABELS


def evaluate_general_label(y_true, y_pred):
    """Evaluate performance for the general linguistic-evasion label"""
    print("\n===== EVALUATION: GENERAL LABEL (linguistic-evasion) =====")

    if sum(y_true) > 0 and sum(y_pred) > 0:
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred)
        recall = recall_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)

        # Create confusion matrix
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

        print(f"Accuracy:  {accuracy:.4f}")
        print(f"Precision: {precision:.4f}")
        print(f"Recall:    {recall:.4f}")
        print(f"F1 Score:  {f1:.4f}")
        print("\nConfusion Matrix:")
        print(f"True Positives:  {tp} (correctly identified evasion)")
        print(f"False Positives: {fp} (normal posts incorrectly labeled as evasion)")
        print(f"True Negatives:  {tn} (correctly identified normal posts)")
        print(f"False Negatives: {fn} (missed evasion)")

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }
    else:
        print("Unable to calculate metrics - insufficient prediction data")
        return {}


def evaluate_specific_labels(test_data, predictions):
    """Evaluate performance for specific evasion technique labels"""
    print("\n===== EVALUATION: SPECIFIC LABELS =====")

    results = {}

    for label in SPECIFIC_LABELS:
        y_true = []
        y_pred = []

        for i, row in enumerate(test_data.iterrows()):
            expected_labels = json.loads(row[1]["Labels"])
            predicted_labels = predictions[i]

            # Binary classification: 1 if the specific label is present, 0 otherwise
            expected = 1 if label in expected_labels else 0
            predicted = 1 if label in predicted_labels else 0

            y_true.append(expected)
            y_pred.append(predicted)

        print(f"\n----- Label: {label} -----")
        if sum(y_true) > 0 and sum(y_pred) > 0:
            accuracy = accuracy_score(y_true, y_pred)
            precision = precision_score(y_true, y_pred)
            recall = recall_score(y_true, y_pred)
            f1 = f1_score(y_true, y_pred)

            # Create confusion matrix
            tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

            print(f"Accuracy:  {accuracy:.4f}")
            print(f"Precision: {precision:.4f}")
            print(f"Recall:    {recall:.4f}")
            print(f"F1 Score:  {f1:.4f}")
            print("\nConfusion Matrix:")
            print(f"True Positives:  {tp} (correctly identified {label})")
            print(f"False Positives: {fp} (incorrectly labeled as {label})")
            print(f"True Negatives:  {tn} (correctly identified not {label})")
            print(f"False Negatives: {fn} (missed {label})")

            results[label] = {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1": f1,
            }
        else:
            print(
                f"Unable to calculate metrics for {label} - insufficient prediction data"
            )
            results[label] = {}

    return results


def comprehensive_evaluation(client, labeler, test_data_file):
    """
    Perform comprehensive evaluation of the linguistic evasion labeler

    Args:
        client: ATProto client
        labeler: Initialized linguistic evasion labeler
        test_data_file: Path to CSV file with test data
    """
    print(f"Loading test data from {test_data_file}")
    test_data = pd.read_csv(test_data_file)

    # Count how many positive and negative examples
    total = len(test_data)
    positive_examples = sum(
        len(json.loads(labels)) > 0 for labels in test_data["Labels"]
    )
    negative_examples = total - positive_examples

    print(f"Test dataset contains {total} posts:")
    print(f"  - {positive_examples} positive examples (with linguistic evasion)")
    print(f"  - {negative_examples} negative examples (normal posts)")

    # Track general label metrics
    general_y_true = []  # Ground truth for linguistic-evasion label
    general_y_pred = []  # Predictions for linguistic-evasion label

    # Track all predictions for specific label evaluation
    all_predictions = []
    processing_times = []
    errors = 0

    print("\nEvaluating labeler on test data...")
    for i, row in enumerate(test_data.iterrows()):
        url = row[1]["URL"]
        expected_labels = json.loads(row[1]["Labels"])

        # Add to general true labels list
        has_general_label = GENERAL_LABEL in expected_labels or any(
            label in SPECIFIC_LABELS for label in expected_labels
        )
        general_y_true.append(1 if has_general_label else 0)

        try:
            # Measure processing time
            start_time = time.time()
            predicted_labels = labeler.moderate_post(url)
            processing_time = time.time() - start_time
            processing_times.append(processing_time)

            # Store all predictions for later specific label evaluation
            all_predictions.append(predicted_labels)

            # Track general label prediction
            has_predicted_general = GENERAL_LABEL in predicted_labels
            general_y_pred.append(1 if has_predicted_general else 0)

            # Print progress
            result = (
                "✓"
                if (has_general_label and has_predicted_general)
                or (not has_general_label and not has_predicted_general)
                else "✗"
            )
            print(f"[{i+1}/{total}] {result} URL: {url}")
            print(f"    Expected: {expected_labels}")
            print(f"    Predicted: {predicted_labels}")
            print(f"    Time: {processing_time:.3f}s")

        except Exception as e:
            errors += 1
            all_predictions.append([])  # Empty prediction on error
            general_y_pred.append(0)  # Default to no detection on error
            print(f"[{i+1}/{total}] Error processing {url}: {e}")

    # Evaluate general label performance
    general_metrics = evaluate_general_label(general_y_true, general_y_pred)

    # Evaluate specific label performance
    specific_metrics = evaluate_specific_labels(test_data, all_predictions)

    # Performance metrics
    if processing_times:
        avg_time = np.mean(processing_times)
        max_time = np.max(processing_times)
        min_time = np.min(processing_times)
        print("\n===== PERFORMANCE METRICS =====")
        print(f"Average processing time: {avg_time:.3f} seconds per post")
        print(f"Fastest processing time: {min_time:.3f} seconds")
        print(f"Slowest processing time: {max_time:.3f} seconds")

    print(f"Errors encountered: {errors} ({errors/total:.1%} of test data)")
    print("============================")

    # Return all metrics for potential further use
    return {
        "general": general_metrics,
        "specific": specific_metrics,
        "performance": {
            "avg_time": avg_time if processing_times else None,
            "errors": errors,
            "total": total,
        },
    }


def main():
    """Main function to run the comprehensive evaluation"""
    client = Client()
    client.login(USERNAME, PW)

    # Initialize labeler
    labeler = LinguisticEvasionLabeler(client, "src/labeler-inputs")

    # Path to test data
    test_data_file = "src/test-data/linguistic_evasion_test_posts.csv"

    # Run comprehensive evaluation without storing the return value
    comprehensive_evaluation(client, labeler, test_data_file)


if __name__ == "__main__":
    main()
