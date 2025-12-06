import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
from collections import defaultdict


class RAGMemory:
    """
    Enhanced RAAG (Retrieval-Augmented Agent Generation) Memory System
    with Reinforcement Learning capabilities
    """
    
    def __init__(self, memory_file: str = "memory.json", 
                 confidence_threshold: float = 0.85,
                 drift_threshold: float = 0.3):
        self.memory_file = memory_file
        self.confidence_threshold = confidence_threshold
        self.drift_threshold = drift_threshold
        
        # Initialize memory structure
        if not os.path.exists(self.memory_file):
            self._initialize_memory()
        
        self.memory = self._load_memory()
        
    def _initialize_memory(self):
        """Initialize empty memory structure"""
        initial_memory = {
            "box_condition": [],
            "statistics": {
                "total_evaluations": 0,
                "correct_predictions": 0,
                "low_confidence_cases": 0,
                "last_accuracy": 1.0,
                "drift_score": 0.0
            },
            "patterns": {
                "common_damages": defaultdict(int),
                "edge_cases": [],
                "confidence_history": []
            },
            "reinforcement_data": {
                "high_confidence_correct": [],
                "low_confidence_cases": [],
                "model_improvements": []
            }
        }
        
        with open(self.memory_file, "w") as f:
            json.dump(initial_memory, f, indent=4)
    
    def _load_memory(self) -> Dict:
        """Load memory from file"""
        with open(self.memory_file, "r") as f:
            return json.load(f)
    
    def _save_memory(self):
        """Save memory to file"""
        with open(self.memory_file, "w") as f:
            json.dump(self.memory, f, indent=4, default=str)
    
    def retrieve_context(self, category: str = "box_condition", n: int = 5) -> List[Dict]:
        """
        Retrieve the most relevant examples for context
        Prioritizes high-confidence correct predictions
        """
        if category not in self.memory:
            return []
        
        examples = self.memory[category]
        
        # Sort by confidence and recency
        sorted_examples = sorted(
            examples[-20:],  # Look at last 20 examples
            key=lambda x: (x.get("confidence", 0.5), x.get("timestamp", "")),
            reverse=True
        )
        
        return sorted_examples[:n]
    
    def format_context_for_prompt(self, examples: List[Dict]) -> str:
        """Format retrieved examples for model prompt"""
        if not examples:
            return "No previous examples available."
        
        context_lines = ["Previous decisions (most confident first):"]
        
        for i, ex in enumerate(examples, 1):
            result = ex.get("result", "UNKNOWN")
            confidence = ex.get("confidence", 0.0)
            reason = ex.get("reason", "No reason provided")
            
            context_lines.append(
                f"{i}. Result: {result} (Confidence: {confidence:.2f})"
            )
            if reason and reason != "No reason provided":
                context_lines.append(f"   Reason: {reason}")
        
        return "\n".join(context_lines)
    
    def update_memory(self, category: str, prediction_data: Dict):
        """
        Add new prediction to memory with RL-based evaluation
        """
        # Add timestamp
        prediction_data["timestamp"] = datetime.utcnow().isoformat()
        
        # Extract key metrics
        confidence = prediction_data.get("confidence", 0.5)
        result = prediction_data.get("result")
        
        # Add to main memory
        if category not in self.memory:
            self.memory[category] = []
        
        self.memory[category].append(prediction_data)
        
        # Update statistics
        self._update_statistics(confidence)
        
        # Reinforcement learning logic
        self._apply_reinforcement_learning(prediction_data, confidence)
        
        # Check for drift
        self._detect_drift()
        
        # Save updated memory
        self._save_memory()
    
    def _update_statistics(self, confidence: float):
        """Update running statistics"""
        stats = self.memory["statistics"]
        stats["total_evaluations"] += 1
        
        # Track confidence distribution
        if "patterns" not in self.memory:
            self.memory["patterns"] = {"confidence_history": []}
        
        self.memory["patterns"]["confidence_history"].append(confidence)
        
        # Keep only last 100 confidence scores
        if len(self.memory["patterns"]["confidence_history"]) > 100:
            self.memory["patterns"]["confidence_history"] = \
                self.memory["patterns"]["confidence_history"][-100:]
        
        # Track low confidence cases
        if confidence < self.confidence_threshold:
            stats["low_confidence_cases"] += 1
    
    def _apply_reinforcement_learning(self, prediction_data: Dict, confidence: float):
        """
        Apply reinforcement learning logic:
        - High confidence predictions are trusted and used for training
        - Low confidence cases are flagged for review and edge case detection
        """
        rl_data = self.memory.get("reinforcement_data", {
            "high_confidence_correct": [],
            "low_confidence_cases": [],
            "model_improvements": []
        })
        
        if confidence >= self.confidence_threshold:
            # High confidence - assume correct and use for future training
            rl_data["high_confidence_correct"].append({
                "prediction": prediction_data,
                "timestamp": prediction_data["timestamp"],
                "used_for_training": False
            })
            
            # Keep only last 100 high confidence cases
            if len(rl_data["high_confidence_correct"]) > 100:
                rl_data["high_confidence_correct"] = \
                    rl_data["high_confidence_correct"][-100:]
        else:
            # Low confidence - flag as potential edge case
            rl_data["low_confidence_cases"].append({
                "prediction": prediction_data,
                "timestamp": prediction_data["timestamp"],
                "needs_review": True
            })
            
            # Keep only last 50 low confidence cases
            if len(rl_data["low_confidence_cases"]) > 50:
                rl_data["low_confidence_cases"] = \
                    rl_data["low_confidence_cases"][-50:]
        
        self.memory["reinforcement_data"] = rl_data
    
    def _detect_drift(self):
        """
        Detect if model performance is drifting
        Based on increase in low-confidence predictions
        """
        stats = self.memory["statistics"]
        total = stats["total_evaluations"]
        
        if total < 10:  # Need minimum samples
            return
        
        # Calculate drift score
        low_conf_rate = stats["low_confidence_cases"] / total
        
        # Update drift score
        stats["drift_score"] = low_conf_rate
        
        # Alert if drift detected
        if low_conf_rate > self.drift_threshold:
            self._log_drift_alert(low_conf_rate)
    
    def _log_drift_alert(self, drift_score: float):
        """Log drift detection event"""
        rl_data = self.memory.get("reinforcement_data", {})
        
        if "model_improvements" not in rl_data:
            rl_data["model_improvements"] = []
        
        rl_data["model_improvements"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "event": "DRIFT_DETECTED",
            "drift_score": drift_score,
            "action": "Recommend model retraining or prompt adjustment"
        })
        
        self.memory["reinforcement_data"] = rl_data
        
        print(f"⚠️  DRIFT ALERT: Low confidence rate at {drift_score:.1%}")
    
    def get_training_dataset(self) -> List[Dict]:
        """
        Generate training dataset from high-confidence predictions
        for potential fine-tuning
        """
        rl_data = self.memory.get("reinforcement_data", {})
        high_conf = rl_data.get("high_confidence_correct", [])
        
        # Filter unused training data
        training_data = [
            item["prediction"] for item in high_conf 
            if not item.get("used_for_training", False)
        ]
        
        return training_data
    
    def mark_as_used_for_training(self, n_samples: int):
        """Mark samples as used after fine-tuning"""
        rl_data = self.memory.get("reinforcement_data", {})
        high_conf = rl_data.get("high_confidence_correct", [])
        
        for i, item in enumerate(high_conf[:n_samples]):
            item["used_for_training"] = True
        
        self.memory["reinforcement_data"] = rl_data
        self._save_memory()
    
    def get_statistics(self) -> Dict:
        """Get current memory statistics"""
        stats = self.memory.get("statistics", {})
        
        # Calculate additional metrics
        conf_history = self.memory.get("patterns", {}).get("confidence_history", [])
        
        if conf_history:
            avg_confidence = np.mean(conf_history)
            recent_trend = np.mean(conf_history[-10:]) if len(conf_history) >= 10 else avg_confidence
        else:
            avg_confidence = 0.0
            recent_trend = 0.0
        
        return {
            "total_evaluations": stats.get("total_evaluations", 0),
            "low_confidence_cases": stats.get("low_confidence_cases", 0),
            "low_confidence_rate": stats.get("low_confidence_cases", 0) / max(stats.get("total_evaluations", 1), 1),
            "drift_score": stats.get("drift_score", 0.0),
            "average_confidence": avg_confidence,
            "recent_confidence_trend": recent_trend,
            "training_samples_available": len(self.get_training_dataset())
        }
    
    def should_trigger_retraining(self) -> bool:
        """
        Determine if model should be retrained based on:
        - Available training samples
        - Drift detection
        - Time since last training
        """
        training_samples = len(self.get_training_dataset())
        drift_score = self.memory["statistics"].get("drift_score", 0.0)
        
        # Trigger if we have enough samples and drift is high
        return training_samples >= 50 and drift_score > self.drift_threshold
    
    def export_for_finetuning(self, output_file: str = "training_data.jsonl"):
        """
        Export training data in JSONL format for OpenAI fine-tuning
        """
        training_data = self.get_training_dataset()
        
        with open(output_file, "w") as f:
            for item in training_data:
                # Format for OpenAI fine-tuning
                training_example = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert at evaluating delivery box conditions."
                        },
                        {
                            "role": "user",
                            "content": f"Classify this box condition. Previous result: {item.get('result')}"
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps({
                                "status": item.get("result"),
                                "reason": item.get("reason", ""),
                                "confidence": item.get("confidence", 0.5)
                            })
                        }
                    ]
                }
                f.write(json.dumps(training_example) + "\n")
        
        print(f"✅ Exported {len(training_data)} training examples to {output_file}")
        return output_file
