from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
from classifier_enhanced import EnhancedClassifier
from raag_enhanced import RAGMemory
from storage import Storage
from typing import Optional
import os

app = FastAPI(
    title="RAAG Box Condition Evaluator",
    description="Self-improving box condition classifier with reinforcement learning",
    version="2.0"
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
        "version": "2.0",
        "features": ["vision_classification", "reinforcement_learning", "drift_detection"],
        "statistics": stats
    }


@app.post("/upload_box")
async def upload_box(file: UploadFile = File(...)):
    """
    Classify uploaded box image
    
    Returns:
        - condition: OK or NEEDS_FIX
        - confidence: 0.0-1.0
        - reason: Explanation
        - should_review: Whether confidence is low
    """
    try:
        # Read image
        img_bytes = await file.read()
        
        # Save image
        filename, filepath = storage.save_image(img_bytes, "jpg")
        
        print(f"📸 Processing image: {filename}")
        
        # Classify with enhanced classifier
        result = classifier.classify_box_condition(img_bytes)
        
        # Log to database
        storage.log_record({
            "image": filename,
            "condition": result["status"],
            "confidence": result["confidence"],
            "reason": result["reason"],
            "damage_types": result.get("damage_types", [])
        })
        
        print(f"✅ Classification: {result['status']} (confidence: {result['confidence']:.2f})")
        
        # Determine if review is needed
        should_review = result["confidence"] < raag.confidence_threshold
        
        return {
            "condition": result["status"],
            "confidence": result["confidence"],
            "reason": result["reason"],
            "damage_types": result.get("damage_types", []),
            "should_review": should_review,
            "image_id": filename
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
        driver_id: Optional driver identifier
    """
    try:
        img_bytes = await image.read()
        
        # Save feedback image
        filename, filepath = storage.save_image(img_bytes, "jpg")
        
        print(f"📝 Feedback received: {correct_label}")
        
        # Store feedback as high-confidence training data
        feedback_data = {
            "result": correct_label.upper(),
            "confidence": 1.0,  # Human feedback is 100% confident
            "reason": f"Human feedback from driver {driver_id or 'unknown'}",
            "damage_types": [],
            "feedback": True,
            "image_id": filename
        }
        
        # Update RAAG memory
        raag.update_memory("box_condition", feedback_data)
        
        # Log to storage
        storage.log_record({
            "image": filename,
            "condition": correct_label.upper(),
            "confidence": 1.0,
            "reason": "Human feedback",
            "feedback": True,
            "driver_id": driver_id
        })
        
        return {
            "status": "success",
            "message": "Feedback recorded for reinforcement learning"
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
    
    return {
        "statistics": stats,
        "retraining_recommended": should_retrain,
        "total_images": len(storage.get_all_records())
    }


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
