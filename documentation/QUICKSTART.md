# 🚀 Quick Start Guide - RAAG Box Condition Classifier

## What You Need
- Python 3.8+
- OpenAI API key
- 5 minutes

---

## Step 1: Install Dependencies (1 min)

```bash
pip install -r requirements_enhanced.txt
```

---

## Step 2: Set Your OpenAI API Key (30 sec)

```bash
# Linux/Mac
export OPENAI_API_KEY="sk-your-key-here"

# Windows
set OPENAI_API_KEY=sk-your-key-here
```

---

## Step 3: Test Everything Works (1 min)

```bash
python test_system.py
```

You should see:
```
✅ All packages imported successfully
✅ API key found
✅ Successfully connected to OpenAI
✅ RAAG initialized successfully
...
🎉 All tests passed! System is ready to use.
```

---

## Step 4: Start the System (1 min)

```bash
bash start_enhanced.sh
```

Or manually:
```bash
# Terminal 1 - Backend
python api_enhanced.py

# Terminal 2 - Frontend  
python gradio_app_enhanced.py
```

---

## Step 5: Open the UI (5 sec)

Open your browser to: **http://localhost:7860**

---

## Step 6: Upload a Box Image

1. Click "📸 Upload Box Image"
2. Select a box photo
3. Click "🔍 Check Condition"
4. Get instant result with confidence!

---

## 🎯 First Test

Try these test images:
- **OK Box**: Clean cardboard box, minor wear
- **NEEDS_FIX Box**: Torn, dented, or water damaged

The system will classify and show:
- ✅ Result (OK / NEEDS_FIX)
- 🎯 Confidence score
- 📝 Reasoning
- ⚠️ Whether it needs manual review

---

## 🧠 How It Learns

### Automatic (No Action Needed)
- High confidence predictions (>85%) → Auto-added to training
- Low confidence (<85%) → Flagged as edge cases
- System monitors drift automatically

### Optional Feedback
If the system makes a mistake:
1. Click "✅ Actually OK" or "🔧 Actually NEEDS_FIX"
2. System immediately learns from correction

---

## 📊 Monitor Performance

Check **System Statistics** section to see:
- Total evaluations
- Average confidence
- Training samples accumulated
- Drift alerts

---

## 🔄 When to Retrain

System will alert when:
- Training samples ≥ 50
- Drift score > 30%
- Confidence dropping

Then run:
```bash
curl -X POST http://localhost:7861/export_training_data
```

This exports `training_data.jsonl` for OpenAI fine-tuning.

---

## 🐛 Common Issues

### "OPENAI_API_KEY not set"
```bash
export OPENAI_API_KEY="sk-..."
```

### "Cannot connect to API"
Make sure FastAPI is running:
```bash
curl http://localhost:7861/
```

### "Port already in use"
Change ports in code:
- FastAPI: 7861 (in api_enhanced.py)
- Gradio: 7860 (in gradio_app_enhanced.py)

---

## 📁 Important Files

After running, you'll see:
```
memory.json          # RAAG memory (DO NOT DELETE)
db.json             # Classification logs
images/             # Uploaded box images
training_data.jsonl # Export for fine-tuning
```

---

## ⚡ Production Deployment

### Option 1: Hugging Face Spaces (Easiest)
1. Create Gradio Space
2. Upload all `*_enhanced.py` files + requirements
3. Add `OPENAI_API_KEY` to secrets
4. Done! Auto-deploys

### Option 2: AWS/GCP
```bash
# Docker deployment
docker build -t raag-classifier .
docker run -p 7860:7860 -p 7861:7861 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  raag-classifier
```

---

## 🎓 Next Steps

1. ✅ Run test images
2. 📊 Monitor statistics  
3. 🔄 Collect 50+ evaluations
4. 🎯 Export training data
5. 🚀 Fine-tune model
6. 🌐 Deploy to production

---

## 💡 Tips for Best Results

### For Drivers
- Take clear, well-lit photos
- Show all sides if damage suspected
- Photo entire box, not just one corner

### For System Performance
- Review low-confidence predictions periodically
- Provide feedback on obvious mistakes
- Export training data weekly
- Fine-tune model monthly

---

## 📞 Need Help?

Check:
1. This guide
2. README_COMPLETE.md (detailed docs)
3. Code comments
4. `/statistics` API endpoint

---

**You're ready to go! 🎉**

Start with: `bash start_enhanced.sh`
