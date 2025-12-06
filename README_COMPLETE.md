# RAAG Operations Equipment Checker 📦

## Self-Improving Box Condition Classifier with Reinforcement Learning

This system uses AI vision to automatically evaluate delivery box conditions and improves over time without manual labeling.

---

## 🎯 System Overview

### What It Does
- Evaluates box images uploaded by drivers
- Returns: **OK** or **NEEDS_FIX** with confidence score
- **Automatically learns** from high-confidence predictions
- Detects when performance is drifting
- Accumulates training data for model fine-tuning

### Key Innovation: No Manual Labeling Required
Instead of requiring humans to label thousands of images, the system:
1. ✅ **Trusts high-confidence predictions** (≥85%) as ground truth
2. ⚠️ **Flags low-confidence cases** (<85%) as edge cases
3. 📊 **Monitors drift** - alerts when accuracy drops
4. 🔄 **Auto-generates training data** from confident predictions
5. 📈 **Triggers retraining** when enough data accumulates

---

## 🏗️ Architecture

```
┌─────────────────┐
│   Driver UI     │ (Gradio / WhatsApp)
│  Uploads Image  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   FastAPI       │
│   Backend       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Classifier     │ ◄──────┐
│  (OpenAI GPT-4) │        │ Retrieves
└────────┬────────┘        │ Context
         │                 │
         ▼                 │
┌─────────────────┐       │
│  RAAG Memory    │───────┘
│  (RL System)    │
└─────────────────┘
         │
         ▼
┌─────────────────┐
│   Storage       │
│ (Images + DB)   │
└─────────────────┘
```

---

## 🧠 Reinforcement Learning Logic

### 1. Confidence-Based Auto-Evaluation

```python
if confidence >= 0.85:
    # HIGH CONFIDENCE
    - Trust prediction as correct
    - Add to training dataset
    - Use for future context
    
elif confidence < 0.85:
    # LOW CONFIDENCE  
    - Flag as edge case
    - Don't use for training (yet)
    - Increase drift score
```

### 2. Context Retrieval (RAG Pattern)

Before classifying a new image:
1. Retrieve 5 most recent **high-confidence** examples
2. Include in prompt as reference
3. Model learns patterns from past decisions

Example context:
```
Previous decisions (most confident first):
1. Result: OK (Confidence: 0.95)
   Reason: Minor scuff on corner, structure intact
2. Result: NEEDS_FIX (Confidence: 0.91)
   Reason: Visible tear on side panel
...
```

### 3. Drift Detection

System monitors:
- **Low confidence rate** - If >30% predictions are low confidence
- **Confidence trend** - Moving average of last 100 predictions
- **Performance changes** - Sudden shifts in behavior

When drift detected:
```
⚠️ DRIFT ALERT: Low confidence rate at 35%
→ Recommend model retraining or prompt adjustment
```

### 4. Training Data Accumulation

```python
if training_samples >= 50 and drift_score > 0.3:
    # Trigger automatic retraining
    export_training_data()
    fine_tune_model()  # Can be automated weekly
```

---

## 🚀 How to Run

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY="sk-..."
```

### Option 1: Run Locally

```bash
# Terminal 1: Start FastAPI backend
python api_enhanced.py

# Terminal 2: Start Gradio UI
python gradio_app_enhanced.py
```

Then open: `http://localhost:7860`

### Option 2: Production Deployment

Deploy to **Hugging Face Spaces** (recommended):
1. Create new Space with **Gradio SDK**
2. Upload all files
3. Add `OPENAI_API_KEY` to Space secrets
4. It will auto-start both backend and frontend

---

## 📁 File Structure

```
project/
├── api_enhanced.py              # FastAPI backend with RL
├── classifier_enhanced.py       # AI vision classifier
├── raag_enhanced.py            # RAAG memory + RL logic
├── gradio_app_enhanced.py      # Gradio UI
├── storage.py                  # Image & DB storage
├── requirements.txt            # Dependencies
├── memory.json                 # RAAG memory (auto-created)
├── db.json                     # Classification logs
└── images/                     # Uploaded box images
```

---

## 🔧 Configuration

### Adjust Confidence Threshold

```python
# In api_enhanced.py
raag = RAGMemory(
    confidence_threshold=0.85,  # Lower = more training data, less quality
    drift_threshold=0.3         # Lower = more sensitive to drift
)
```

### Tune Model Behavior

```python
# In classifier_enhanced.py
response = self.client.chat.completions.create(
    model="gpt-4o-mini",      # or "gpt-4o" for better accuracy
    temperature=0.1,          # Lower = more consistent
    max_tokens=500
)
```

---

## 📊 API Endpoints

### POST `/upload_box`
Upload box image for classification
```json
Response:
{
    "condition": "OK",
    "confidence": 0.92,
    "reason": "Minor wear, structurally sound",
    "damage_types": [],
    "should_review": false
}
```

### POST `/feedback`
Submit human correction
```json
Request:
{
    "image": <file>,
    "correct_label": "NEEDS_FIX",
    "driver_id": "D123"
}
```

### GET `/statistics`
Get system performance metrics
```json
Response:
{
    "statistics": {
        "total_evaluations": 150,
        "average_confidence": 0.87,
        "low_confidence_rate": 0.12,
        "training_samples_available": 75
    },
    "retraining_recommended": false
}
```

### POST `/export_training_data`
Export accumulated training data for fine-tuning
```json
Response:
{
    "status": "success",
    "file": "training_data.jsonl",
    "samples": 75
}
```

---

## 🎓 Understanding the Code

### Key Components

#### 1. **RAGMemory** (`raag_enhanced.py`)
- Stores classification history
- Retrieves relevant context
- Implements RL logic
- Detects performance drift
- Manages training data

Core methods:
```python
retrieve_context(n=5)           # Get best examples
update_memory(data)             # Add new prediction + apply RL
get_statistics()                # Performance metrics
should_trigger_retraining()     # Check if retraining needed
export_for_finetuning()         # Export training JSONL
```

#### 2. **EnhancedClassifier** (`classifier_enhanced.py`)
- Calls OpenAI Vision API
- Includes RAAG context in prompt
- Parses structured output
- Updates RAAG memory

Core flow:
```python
1. Retrieve context from RAAG
2. Build prompt with examples
3. Call OpenAI with image
4. Parse structured response
5. Update RAAG memory
```

#### 3. **FastAPI Backend** (`api_enhanced.py`)
- REST API endpoints
- Image storage
- Database logging
- Statistics tracking

---

## 🚀 Advanced: Automatic Fine-Tuning

### Step 1: Accumulate Data
System automatically collects high-confidence predictions as training data.

### Step 2: Export Training Data
```bash
curl -X POST http://localhost:7861/export_training_data
```
Creates `training_data.jsonl` in OpenAI fine-tuning format.

### Step 3: Fine-Tune Model
```python
from openai import OpenAI
client = OpenAI()

# Upload training file
file = client.files.create(
    file=open("training_data.jsonl", "rb"),
    purpose="fine-tune"
)

# Create fine-tuning job
job = client.fine_tuning.jobs.create(
    training_file=file.id,
    model="gpt-4o-mini-2024-07-18"
)

# Wait for completion...
```

### Step 4: Use Fine-Tuned Model
```python
# In classifier_enhanced.py
self.model = "ft:gpt-4o-mini-2024-07-18:your-org::abc123"
```

### Automation Schedule
Set up weekly cron job:
```bash
# crontab -e
0 0 * * 0 /path/to/auto_finetune.sh  # Every Sunday midnight
```

---

## 📈 Monitoring & Improvement

### Key Metrics to Watch

1. **Average Confidence**: Should be >0.85
   - If dropping → model is uncertain → drift likely

2. **Low Confidence Rate**: Should be <20%
   - If rising → need retraining

3. **Training Samples**: Accumulating over time
   - Once >50 → ready for fine-tuning

4. **Drift Score**: Should be <0.3
   - If >0.3 → performance degrading

### When to Intervene

❌ **Manual Review Needed:**
- Drift score >0.4
- Confidence dropping for 2+ days
- Repeated errors in same damage type

✅ **System is Learning:**
- Confidence stable or improving
- Training data growing
- Low confidence rate <20%

---

## 🔮 Future Enhancements

### 1. WhatsApp Integration
Replace Gradio with WhatsApp bot:
```python
from twilio import WhatsApp

@app.post("/whatsapp/message")
async def whatsapp_message(message: Message):
    if message.has_image():
        result = classifier.classify(message.image)
        return f"📦 {result['condition']}"
```

### 2. Multi-Label Classification
Extend to classify damage types:
- Tears
- Dents
- Water damage
- Missing components

### 3. Driver Performance Tracking
```python
stats_by_driver = {
    "driver_123": {
        "total_boxes": 45,
        "damaged_rate": 0.12,
        "avg_confidence": 0.89
    }
}
```

### 4. Active Learning
When confidence <0.7:
- Send image to supervisor
- Get immediate feedback
- Retrain model instantly

---

## 🐛 Troubleshooting

### "OpenAI API Error"
```bash
# Check API key
echo $OPENAI_API_KEY

# Test connection
python test_openai.py
```

### "Cannot connect to API"
```bash
# Check FastAPI is running
curl http://localhost:7861/

# Check logs
tail -f api_logs.txt
```

### "Low accuracy"
1. Check confidence threshold (might be too low)
2. Review recent classifications in `/history`
3. Export and inspect training data
4. Consider fine-tuning with accumulated data

### "Memory not persisting"
```bash
# Check memory file exists
ls -l memory.json

# Check permissions
chmod 644 memory.json
```

---

## 📚 Additional Resources

- [OpenAI Vision API](https://platform.openai.com/docs/guides/vision)
- [OpenAI Fine-Tuning](https://platform.openai.com/docs/guides/fine-tuning)
- [RAG Pattern](https://arxiv.org/abs/2005.11401)
- [Active Learning](https://en.wikipedia.org/wiki/Active_learning)

---

## 🤝 Support

For questions or issues:
1. Check this README
2. Review code comments
3. Inspect `/statistics` endpoint
4. Check system logs

---

## 📄 License

MIT License - Feel free to adapt for your operations!

---

**Built with ❤️ for efficient operations management**
