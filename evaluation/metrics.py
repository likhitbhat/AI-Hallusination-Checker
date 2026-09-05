from typing import List, Dict, Any


def calculate_evaluation_metrics(y_true: List[str], y_pred: List[str], latencies: List[float]) -> Dict[str, Any]:
    """
    Computes classification evaluation metrics:
    - Accuracy
    - Precision (for Hallucination detection)
    - Recall (for Hallucination detection)
    - F1-Score
    - False Positive Rate (FPR)
    - False Negative Rate (FNR)
    - Average Latency
    """
    total = len(y_true)
    if total == 0:
        return {}

    # Binary framing: Positive = LIKELY_HALLUCINATED, Negative = VERIFIED / OTHER
    tp = 0 # Predicted hallucination, actually hallucination
    fp = 0 # Predicted hallucination, actually verified
    tn = 0 # Predicted verified, actually verified
    fn = 0 # Predicted verified, actually hallucination
    correct = 0

    for yt, yp in zip(y_true, y_pred):
        if yt == yp:
            correct += 1

        is_true_hallucination = (yt == "LIKELY_HALLUCINATED")
        is_pred_hallucination = (yp == "LIKELY_HALLUCINATED")

        if is_true_hallucination and is_pred_hallucination:
            tp += 1
        elif not is_true_hallucination and is_pred_hallucination:
            fp += 1
        elif not is_true_hallucination and not is_pred_hallucination:
            tn += 1
        elif is_true_hallucination and not is_pred_hallucination:
            fn += 1

    accuracy = correct / total
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    return {
        "total_evaluated": total,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "average_latency_seconds": round(avg_latency, 4)
    }
