from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from classifier_enhanced import EnhancedClassifier
from raag_enhanced import RAGMemory
from storage import Storage
from typing import Optional
from collections import defaultdict
import os

app = FastAPI(
    title="RAAG Box Condition Evaluator with Driver Tracking",
    description="Self-improving box condition classifier with driver performance tracking",
    version="2.1"
)

# Initialize components
raag = RAGMemory(
    memory_file="memory.json",
    confidence_threshold=0.85,
    drift_threshold=0.3
)
classifier = EnhancedClassifier(raag)
storage = Storage()


@app.get("/")
async def root():
    """API Health check"""
    stats = raag.get_statistics()
    return {
        "status": "online",
        "version": "2.1",
        "features": [
            "vision_classification",
            "reinforcement_learning",
            "drift_detection",
            "driver_tracking"
        ],
        "statistics": stats
    }


@app.post("/upload_box")
async def upload_box(
    file: UploadFile = File(...),
    driver_id: str = Form(...),
    box_id: Optional[str] = Form(None)
):
    """
    Classify uploaded box image with driver tracking
    
    Args:
        file: Box image
        driver_id: Driver identifier (required)
        box_id: Optional box/package identifier
        
    Returns:
        - condition: OK or NEEDS_FIX
        - confidence: 0.0-1.0
        - reason: Explanation
        - should_review: Whether confidence is low
        - image_id: Stored image identifier
    """
    try:
        # Validate driver_id
        if not driver_id or driver_id.strip() == "":
            return JSONResponse(
                status_code=400,
                content={"error": "driver_id is required"}
            )
        
        driver_id = driver_id.strip()
        
        # Read image
        img_bytes = await file.read()
        
        # Save image
        filename, filepath = storage.save_image(img_bytes, "jpg")
        
        print(f"📸 Processing image: {filename} for Driver: {driver_id}")
        
        # Classify with enhanced classifier
        result = classifier.classify_box_condition(img_bytes)
        
        # Add driver and box metadata
        result["driver_id"] = driver_id
        result["box_id"] = box_id if box_id else ""
        result["image_id"] = filename
        
        # Log to database
        storage.log_record({
            "image": filename,
            "driver_id": driver_id,
            "box_id": box_id if box_id else "",
            "condition": result["status"],
            "confidence": result["confidence"],
            "reason": result["reason"],
            "damage_types": result.get("damage_types", []),
            "timestamp": result.get("timestamp", "")
        })
        
        print(f"✅ Classification: {result['status']} (confidence: {result['confidence']:.2f}) - Driver: {driver_id}")
        
        # Determine if review is needed
        should_review = result["confidence"] < raag.confidence_threshold
        
        return {
            "condition": result["status"],
            "confidence": result["confidence"],
            "reason": result["reason"],
            "damage_types": result.get("damage_types", []),
            "should_review": should_review,
            "image_id": filename,
            "driver_id": driver_id,
            "box_id": box_id
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.post("/feedback")
async def submit_feedback(
    image: UploadFile = File(...),
    correct_label: str = Form(...),
    driver_id: Optional[str] = Form(None)
):
    """
    Submit feedback for a prediction
    Used for reinforcement learning when human correction is available
    
    Args:
        image: The box image
        correct_label: The correct classification (OK or NEEDS_FIX)
        driver_id: Driver who provided the feedback
    """
    try:
        img_bytes = await image.read()
        
        # Save feedback image
        filename, filepath = storage.save_image(img_bytes, "jpg")
        
        print(f"📝 Feedback received: {correct_label} from Driver: {driver_id or 'unknown'}")
        
        # Store feedback as high-confidence training data
        feedback_data = {
            "result": correct_label.upper(),
            "confidence": 1.0,  # Human feedback is 100% confident
            "reason": f"Human feedback from driver {driver_id or 'unknown'}",
            "damage_types": [],
            "feedback": True,
            "driver_id": driver_id or "unknown",
            "image_id": filename
        }
        
        # Update RAAG memory
        raag.update_memory("box_condition", feedback_data)
        
        # Log to storage
        storage.log_record({
            "image": filename,
            "driver_id": driver_id or "unknown",
            "box_id": "",
            "condition": correct_label.upper(),
            "confidence": 1.0,
            "reason": "Human feedback",
            "feedback": True
        })
        
        return {
            "status": "success",
            "message": "Feedback recorded for reinforcement learning",
            "driver_id": driver_id
        }
        
    except Exception as e:
        print(f"❌ Feedback error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/statistics")
async def get_statistics():
    """Get current system statistics and performance metrics"""
    stats = raag.get_statistics()
    
    # Check if retraining is recommended
    should_retrain = raag.should_trigger_retraining()
    
    # Get all records for additional stats
    all_records = storage.get_all_records()
    
    return {
        "statistics": stats,
        "retraining_recommended": should_retrain,
        "total_images": len(all_records)
    }


@app.get("/driver_statistics")
async def get_driver_statistics(driver_id: str):
    """
    Get statistics for a specific driver
    
    Args:
        driver_id: Driver identifier
        
    Returns:
        Driver-specific performance metrics
    """
    try:
        all_records = storage.get_all_records()
        
        # Filter records for this driver
        driver_records = [r for r in all_records if r.get("driver_id") == driver_id]
        
        if not driver_records:
            return {
                "driver_id": driver_id,
                "statistics": {
                    "total_evaluations": 0,
                    "average_confidence": 0.0,
                    "ok_count": 0,
                    "needs_fix_count": 0,
                    "feedback_count": 0
                }
            }
        
        # Calculate driver statistics
        total = len(driver_records)
        ok_count = len([r for r in driver_records if r.get("condition") == "OK"])
        needs_fix_count = len([r for r in driver_records if r.get("condition") == "NEEDS_FIX"])
        feedback_count = len([r for r in driver_records if r.get("feedback", False)])
        
        confidences = [r.get("confidence", 0) for r in driver_records if "confidence" in r]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        return {
            "driver_id": driver_id,
            "statistics": {
                "total_evaluations": total,
                "average_confidence": avg_confidence,
                "ok_count": ok_count,
                "needs_fix_count": needs_fix_count,
                "feedback_count": feedback_count,
                "damage_rate": needs_fix_count / total if total > 0 else 0.0
            }
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/driver_history")
async def get_driver_history(driver_id: str, limit: int = 10):
    """
    Get recent evaluation history for a specific driver
    
    Args:
        driver_id: Driver identifier
        limit: Maximum number of records to return
    """
    try:
        all_records = storage.get_all_records()
        
        # Filter and sort by most recent
        driver_records = [r for r in all_records if r.get("driver_id") == driver_id]
        driver_records = sorted(
            driver_records,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:limit]
        
        return {
            "driver_id": driver_id,
            "total": len([r for r in all_records if r.get("driver_id") == driver_id]),
            "history": driver_records
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/leaderboard")
async def get_leaderboard(limit: int = 10):
    """
    Get top drivers by various metrics
    
    Returns leaderboard of drivers by:
    - Most evaluations
    - Highest average confidence
    - Most feedback contributions
    """
    try:
        all_records = storage.get_all_records()
        
        # Group by driver
        driver_data = defaultdict(lambda: {
            "total": 0,
            "confidences": [],
            "feedback_count": 0
        })
        
        for record in all_records:
            driver_id = record.get("driver_id")
            if not driver_id:
                continue
            
            driver_data[driver_id]["total"] += 1
            
            if "confidence" in record:
                driver_data[driver_id]["confidences"].append(record["confidence"])
            
            if record.get("feedback", False):
                driver_data[driver_id]["feedback_count"] += 1
        
        # Calculate rankings
        leaderboard = []
        for driver_id, data in driver_data.items():
            avg_conf = sum(data["confidences"]) / len(data["confidences"]) if data["confidences"] else 0
            leaderboard.append({
                "driver_id": driver_id,
                "total_evaluations": data["total"],
                "average_confidence": avg_conf,
                "feedback_contributions": data["feedback_count"]
            })
        
        # Sort by total evaluations
        leaderboard.sort(key=lambda x: x["total_evaluations"], reverse=True)
        
        return {
            "leaderboard": leaderboard[:limit]
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/training_data")
async def get_training_data():
    """Get available training data for model fine-tuning"""
    training_data = raag.get_training_dataset()
    
    return {
        "available_samples": len(training_data),
        "ready_for_training": len(training_data) >= 50,
        "sample_preview": training_data[:3] if training_data else []
    }


@app.post("/export_training_data")
async def export_training_data():
    """Export training data in JSONL format for OpenAI fine-tuning"""
    try:
        output_file = "training_data.jsonl"
        exported_file = raag.export_for_finetuning(output_file)
        
        return {
            "status": "success",
            "file": exported_file,
            "samples": len(raag.get_training_dataset())
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


@app.get("/history")
async def get_history(limit: int = 10):
    """Get recent classification history"""
    records = storage.get_all_records()
    
    # Return most recent
    return {
        "total": len(records),
        "recent": records[-limit:] if len(records) > limit else records
    }


@app.post("/reset_memory")
async def reset_memory():
    """Reset RAAG memory (use with caution)"""
    if os.path.exists("memory.json"):
        os.remove("memory.json")
    
    global raag
    raag = RAGMemory()
    
    return {
        "status": "success",
        "message": "Memory reset complete"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7861)
