# 🚀 Deployment & Troubleshooting Guide

## Production Deployment Options

### Option 1: Hugging Face Spaces (Recommended - Easiest)

**Why:** Free hosting, auto-scaling, built for Gradio apps

**Steps:**

1. **Create Space**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Name: `raag-box-classifier`
   - SDK: **Gradio**
   - Hardware: **Free (CPU)** or **Upgraded (GPU)** for faster processing

2. **Upload Files**
   ```bash
   # Clone your space
   git clone https://huggingface.co/spaces/YOUR_USERNAME/raag-box-classifier
   cd raag-box-classifier
   
   # Copy all enhanced files
   cp api_enhanced.py app.py  # HF expects app.py
   cp classifier_enhanced.py .
   cp raag_enhanced.py .
   cp storage.py .
   cp requirements_enhanced.txt requirements.txt
   
   # Create README
   cp README_COMPLETE.md README.md
   ```

3. **Set Secrets**
   - Go to Space settings → Repository secrets
   - Add: `OPENAI_API_KEY` = `sk-your-key`

4. **Create app.py for HF**
   ```python
   # app.py (Hugging Face entry point)
   import os
   import subprocess
   import threading
   import time
   
   # Start FastAPI backend in background
   def start_backend():
       subprocess.Popen([
           "uvicorn", 
           "api_enhanced:app", 
           "--host", "0.0.0.0", 
           "--port", "7861"
       ])
   
   # Start backend thread
   backend_thread = threading.Thread(target=start_backend, daemon=True)
   backend_thread.start()
   
   # Wait for backend to start
   time.sleep(5)
   
   # Import and launch Gradio
   from gradio_app_enhanced import interface
   interface.launch()
   ```

5. **Push to HF**
   ```bash
   git add .
   git commit -m "Deploy RAAG classifier"
   git push
   ```

6. **Done!** Space will auto-deploy at:
   `https://huggingface.co/spaces/YOUR_USERNAME/raag-box-classifier`

---

### Option 2: AWS EC2

**Why:** Full control, can handle high traffic

**Steps:**

1. **Launch EC2 Instance**
   - Ubuntu 22.04 LTS
   - t2.medium or larger
   - Open ports: 7860, 7861

2. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv -y
   
   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate
   
   # Install requirements
   pip install -r requirements_enhanced.txt
   ```

3. **Set Environment Variable**
   ```bash
   echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
   source ~/.bashrc
   ```

4. **Run with systemd (auto-restart)**
   
   Create `/etc/systemd/system/raag-backend.service`:
   ```ini
   [Unit]
   Description=RAAG FastAPI Backend
   After=network.target
   
   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/raag
   Environment="OPENAI_API_KEY=sk-..."
   ExecStart=/home/ubuntu/raag/venv/bin/uvicorn api_enhanced:app --host 0.0.0.0 --port 7861
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Create `/etc/systemd/system/raag-frontend.service`:
   ```ini
   [Unit]
   Description=RAAG Gradio Frontend
   After=network.target raag-backend.service
   
   [Service]
   Type=simple
   User=ubuntu
   WorkingDirectory=/home/ubuntu/raag
   Environment="OPENAI_API_KEY=sk-..."
   ExecStart=/home/ubuntu/raag/venv/bin/python gradio_app_enhanced.py
   Restart=always
   
   [Install]
   WantedBy=multi-user.target
   ```
   
   Enable and start:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable raag-backend raag-frontend
   sudo systemctl start raag-backend raag-frontend
   ```

5. **Setup Nginx (optional, for HTTPS)**
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://localhost:7860;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
       }
   }
   ```

---

### Option 3: Docker Deployment

**Why:** Portable, consistent across environments

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.10-slim
   
   WORKDIR /app
   
   # Install dependencies
   COPY requirements_enhanced.txt .
   RUN pip install --no-cache-dir -r requirements_enhanced.txt
   
   # Copy application
   COPY *.py .
   
   # Create directories
   RUN mkdir -p images
   
   # Expose ports
   EXPOSE 7860 7861
   
   # Set environment variable
   ENV OPENAI_API_KEY=""
   
   # Start script
   COPY start_enhanced.sh .
   RUN chmod +x start_enhanced.sh
   
   CMD ["./start_enhanced.sh"]
   ```

2. **Create docker-compose.yml**
   ```yaml
   version: '3.8'
   
   services:
     raag-classifier:
       build: .
       ports:
         - "7860:7860"
         - "7861:7861"
       environment:
         - OPENAI_API_KEY=${OPENAI_API_KEY}
       volumes:
         - ./images:/app/images
         - ./memory.json:/app/memory.json
         - ./db.json:/app/db.json
       restart: unless-stopped
   ```

3. **Deploy**
   ```bash
   # Build
   docker-compose build
   
   # Run
   docker-compose up -d
   
   # Check logs
   docker-compose logs -f
   ```

---

### Option 4: Google Cloud Run

**Why:** Serverless, auto-scaling, pay-per-use

1. **Create cloudbuild.yaml**
   ```yaml
   steps:
     - name: 'gcr.io/cloud-builders/docker'
       args: ['build', '-t', 'gcr.io/$PROJECT_ID/raag-classifier', '.']
     - name: 'gcr.io/cloud-builders/docker'
       args: ['push', 'gcr.io/$PROJECT_ID/raag-classifier']
   images:
     - 'gcr.io/$PROJECT_ID/raag-classifier'
   ```

2. **Deploy**
   ```bash
   gcloud run deploy raag-classifier \
     --image gcr.io/PROJECT_ID/raag-classifier \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars OPENAI_API_KEY=sk-...
   ```

---

## 🐛 Troubleshooting Guide

### Problem: "OpenAI API Error: Invalid API Key"

**Symptoms:**
```
❌ OpenAI connection failed: Error code: 401
Unauthorized
```

**Solutions:**

1. **Check key is set:**
   ```bash
   echo $OPENAI_API_KEY
   ```

2. **Verify key format:**
   ```bash
   # Should start with 'sk-' or 'sk-proj-'
   # Should be ~50+ characters long
   ```

3. **Test key directly:**
   ```python
   from openai import OpenAI
   client = OpenAI(api_key="sk-...")
   print(client.models.list())
   ```

4. **Check key permissions:**
   - Go to https://platform.openai.com/api-keys
   - Verify key has permissions for Chat Completions
   - Check usage limits aren't exceeded

---

### Problem: "Cannot connect to backend"

**Symptoms:**
```
❌ Error connecting to API: Connection refused
```

**Solutions:**

1. **Check backend is running:**
   ```bash
   curl http://localhost:7861/
   # Should return: {"status":"online",...}
   ```

2. **Check port availability:**
   ```bash
   netstat -tuln | grep 7861
   # Should show LISTEN on port 7861
   ```

3. **Check for port conflicts:**
   ```bash
   # Kill process using port
   lsof -ti:7861 | xargs kill -9
   ```

4. **Check firewall:**
   ```bash
   # Allow ports
   sudo ufw allow 7860
   sudo ufw allow 7861
   ```

5. **Check logs:**
   ```bash
   # Backend logs
   tail -f /var/log/raag-backend.log
   ```

---

### Problem: "Low confidence predictions"

**Symptoms:**
```
⚠️ Average confidence: 65%
⚠️ Low confidence rate: 45%
```

**Root Causes:**
1. Model seeing unusual box types
2. Poor image quality
3. Ambiguous damage cases
4. Need for fine-tuning

**Solutions:**

1. **Check image quality:**
   - Ensure good lighting
   - Clear, focused images
   - Show entire box

2. **Review recent predictions:**
   ```bash
   curl http://localhost:7861/history?limit=20
   ```

3. **Add specific examples to prompt:**
   ```python
   # In classifier_enhanced.py, add to system prompt:
   ADDITIONAL_GUIDANCE = """
   Special cases:
   - Cardboard discoloration is OK if no structural damage
   - Small tears (<1 inch) are OK
   - Water stains without soggy material are OK
   """
   ```

4. **Collect feedback:**
   - Ask drivers to correct obvious mistakes
   - Use feedback to improve

5. **Fine-tune model:**
   ```bash
   # Export training data
   curl -X POST http://localhost:7861/export_training_data
   
   # Use training_data.jsonl to fine-tune
   ```

---

### Problem: "Memory not persisting"

**Symptoms:**
```
Statistics reset to 0 after restart
Previous predictions lost
```

**Solutions:**

1. **Check file permissions:**
   ```bash
   ls -l memory.json db.json
   # Should be readable/writable
   chmod 644 memory.json db.json
   ```

2. **Verify file location:**
   ```bash
   # Memory should be in working directory
   pwd
   ls -la *.json
   ```

3. **Check disk space:**
   ```bash
   df -h
   # Ensure enough space
   ```

4. **Use absolute paths:**
   ```python
   # In api_enhanced.py
   import os
   MEMORY_PATH = os.path.join(os.getcwd(), "memory.json")
   raag = RAGMemory(memory_file=MEMORY_PATH)
   ```

---

### Problem: "High drift score"

**Symptoms:**
```
⚠️ DRIFT DETECTED
Drift score: 0.42
```

**What it means:**
- Model performance degrading
- More low-confidence predictions than usual
- May need retraining

**Solutions:**

1. **Review recent changes:**
   - New box types introduced?
   - Different lighting conditions?
   - Camera changes?

2. **Check training data:**
   ```bash
   curl http://localhost:7861/training_data
   ```

3. **Export and fine-tune:**
   ```bash
   # If you have 50+ samples
   curl -X POST http://localhost:7861/export_training_data
   # Then fine-tune model with training_data.jsonl
   ```

4. **Adjust confidence threshold temporarily:**
   ```python
   # In api_enhanced.py (temporary fix)
   raag = RAGMemory(
       confidence_threshold=0.75,  # Lower threshold
       drift_threshold=0.4         # Higher tolerance
   )
   ```

---

### Problem: "Gradio UI not loading"

**Symptoms:**
```
Cannot access http://localhost:7860
ERR_CONNECTION_REFUSED
```

**Solutions:**

1. **Check Gradio is running:**
   ```bash
   ps aux | grep gradio
   ```

2. **Check logs:**
   ```bash
   python gradio_app_enhanced.py
   # Watch for errors
   ```

3. **Try different port:**
   ```python
   # In gradio_app_enhanced.py
   interface.launch(
       server_port=8080,  # Try different port
       share=True         # Create public link
   )
   ```

4. **Check firewall/network:**
   ```bash
   # Allow port
   sudo ufw allow 7860
   
   # Or use ngrok for testing
   ngrok http 7860
   ```

---

### Problem: "Out of memory errors"

**Symptoms:**
```
MemoryError: Unable to allocate array
Killed (OOM)
```

**Solutions:**

1. **Limit memory size:**
   ```python
   # In raag_enhanced.py
   # Keep only last 100 items
   if len(self.memory["box_condition"]) > 100:
       self.memory["box_condition"] = \
           self.memory["box_condition"][-100:]
   ```

2. **Use database instead of JSON:**
   ```python
   # Replace json storage with SQLite
   import sqlite3
   ```

3. **Increase system resources:**
   ```bash
   # For Docker
   docker run --memory=4g ...
   
   # For EC2
   # Upgrade to larger instance
   ```

---

## 🔍 Monitoring & Health Checks

### Health Check Endpoint

```bash
# Check system health
curl http://localhost:7861/ | jq

# Expected response:
{
  "status": "online",
  "version": "2.0",
  "features": [...],
  "statistics": {...}
}
```

### Monitoring Script

```bash
#!/bin/bash
# monitor.sh - Run every 5 minutes via cron

STATS=$(curl -s http://localhost:7861/statistics)

AVG_CONF=$(echo $STATS | jq '.statistics.average_confidence')
DRIFT=$(echo $STATS | jq '.statistics.drift_score')

if (( $(echo "$AVG_CONF < 0.75" | bc -l) )); then
    echo "⚠️ Low confidence: $AVG_CONF" | mail -s "RAAG Alert" admin@company.com
fi

if (( $(echo "$DRIFT > 0.4" | bc -l) )); then
    echo "⚠️ High drift: $DRIFT" | mail -s "RAAG Alert" admin@company.com
fi
```

### Performance Metrics

```bash
# Response time
time curl -X POST http://localhost:7861/upload_box -F "file=@test.jpg"

# Memory usage
ps aux | grep "api_enhanced\|gradio_app" | awk '{sum+=$6} END {print sum/1024 " MB"}'

# Disk usage
du -sh images/ memory.json db.json
```

---

## 📊 Production Best Practices

### 1. Backup Strategy

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
tar -czf backup_$DATE.tar.gz memory.json db.json images/

# Keep last 7 days
find backup_*.tar.gz -mtime +7 -delete
```

### 2. Log Rotation

```bash
# /etc/logrotate.d/raag
/var/log/raag/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 ubuntu ubuntu
}
```

### 3. Rate Limiting

```python
# In api_enhanced.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/upload_box")
@limiter.limit("10/minute")  # Max 10 uploads per minute
async def upload_box(...):
    ...
```

### 4. Error Alerting

```python
# In api_enhanced.py
import sentry_sdk

sentry_sdk.init(
    dsn="https://...",
    traces_sample_rate=1.0
)
```

### 5. Database Migration

When memory.json gets too large:

```python
# migrate_to_postgres.py
import json
import psycopg2

# Read memory.json
with open('memory.json') as f:
    data = json.load(f)

# Write to PostgreSQL
conn = psycopg2.connect(...)
cur = conn.cursor()

for item in data['box_condition']:
    cur.execute("""
        INSERT INTO predictions 
        (result, confidence, reason, timestamp)
        VALUES (%s, %s, %s, %s)
    """, (item['result'], item['confidence'], ...))

conn.commit()
```

---

## 🎯 Performance Optimization

### 1. Caching

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_context_cached(category: str):
    return raag.retrieve_context(category)
```

### 2. Async Processing

```python
import asyncio

async def classify_batch(images: List[bytes]):
    tasks = [classifier.classify_box_condition(img) for img in images]
    return await asyncio.gather(*tasks)
```

### 3. Image Optimization

```python
from PIL import Image

def optimize_image(img_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(img_bytes))
    # Resize if too large
    if img.width > 1024:
        img.thumbnail((1024, 1024))
    # Convert to JPEG
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    return buffer.getvalue()
```

---

## 🔐 Security Considerations

1. **API Key Protection**
   - Never commit API keys to git
   - Use environment variables
   - Rotate keys regularly

2. **Input Validation**
   ```python
   MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
   ALLOWED_TYPES = ['image/jpeg', 'image/png']
   ```

3. **Rate Limiting**
   - Prevent abuse
   - Protect OpenAI costs

4. **Authentication** (if needed)
   ```python
   from fastapi.security import HTTPBearer
   
   security = HTTPBearer()
   
   @app.post("/upload_box")
   async def upload_box(
       file: UploadFile,
       token: str = Depends(security)
   ):
       verify_token(token)
       ...
   ```

---

## 📞 Support Checklist

Before asking for help, check:

- [ ] Ran `python test_system.py` - all tests pass?
- [ ] OpenAI API key is valid and has credits
- [ ] Backend running on port 7861
- [ ] Frontend running on port 7860
- [ ] Can access http://localhost:7861/ 
- [ ] Checked logs for error messages
- [ ] Tried with a simple test image
- [ ] Read relevant sections in README_COMPLETE.md

---

**Happy deploying! 🚀**
