import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import collections
import model
from database import get_holdout_data_generator

class StreamController:
    def __init__(self):
        self.status = "STOPPED"  # STOPPED, RUNNING, PAUSED
        self._data_gen = None
        # Counters
        self.scanned = 0
        self.high_risk = 0
        self.normal = 0
        # Store recent predictions (newest first), keep last 100
        self.predictions = collections.deque(maxlen=100)

    def start(self):
        """Start the transaction replay from the beginning or resume from pause."""
        if self.status == "STOPPED":
            self._data_gen = get_holdout_data_generator()
            self.status = "RUNNING"
            # Reset counters
            self.scanned = 0
            self.high_risk = 0
            self.normal = 0
            self.predictions.clear()
        elif self.status == "PAUSED":
            self.status = "RUNNING"
        # If already RUNNING, do nothing

    def pause(self):
        """Pause the transaction replay."""
        if self.status == "RUNNING":
            self.status = "PAUSED"

    def reset(self):
        """Reset the replay to the beginning and stop."""
        self.status = "STOPPED"
        self._data_gen = None
        self.scanned = 0
        self.high_risk = 0
        self.normal = 0
        self.predictions.clear()

    def advance(self):
        """
        Advance the stream by one transaction if RUNNING.
        Returns True if a transaction was processed, False if not running or no more data.
        """
        if self.status != "RUNNING":
            return False
        try:
            tx = next(self._data_gen)
        except StopIteration:
            self.status = "STOPPED"
            return False
        # Compute prediction
        probability = model.predict_proba(tx['features'])
        threshold = model.get_optimal_threshold()
        risk_level = "HIGH" if probability >= threshold else "NORMAL"
        # Update counters
        self.scanned += 1
        if risk_level == "HIGH":
            self.high_risk += 1
        else:
            self.normal += 1
        # Store prediction (newest first)
        prediction_record = {
            'tx_hash': tx['tx_hash'],
            'block_number': tx['block_number'],
            'transaction_index': tx['transaction_index'],
            'risk_score': probability,
            'risk_level': risk_level,
            'features': tx['features']   # Include features for details
        }
        self.predictions.appendleft(prediction_record)
        return True

    def get_status(self):
        """Return the current status and counters."""
        return {
            "status": self.status,
            "scanned": self.scanned,
            "high_risk": self.high_risk,
            "normal": self.normal
        }

    def get_predictions(self):
        """Return a list of recent predictions (newest first)."""
        return list(self.predictions)

    def get_statistics(self):
        """Return statistics including attack rate."""
        total = self.scanned
        attack_rate = (self.high_risk / total * 100) if total > 0 else 0.0
        return {
            "total_scanned": total,
            "high_risk": self.high_risk,
            "normal": self.normal,
            "attack_rate": round(attack_rate, 2)
        }

# Singleton instance for use in the API
stream_controller = StreamController()