# 📦 RAAG Box Condition Classifier

> Self-improving AI system for delivery box quality control with reinforcement learning and driver tracking

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-green.svg)](https://openai.com/)

## 🎯 What It Does

Automatically evaluates delivery box conditions and **learns over time without manual labeling**:

- 📸 Drivers upload box photos
- 🤖 AI classifies: **OK** or **NEEDS_FIX**
- 📊 Tracks confidence scores
- 🔄 **Self-improves** from high-confidence predictions
- 👤 Optional driver performance tracking
- 📈 Automatic drift detection

## ✨ Key Features

### Core System
- ✅ **OpenAI Vision API** integration (GPT-4o-mini)
- ✅ **Reinforcement Learning** - learns from confident predictions
- ✅ **RAG Pattern** - retrieves similar past examples
- ✅ **Drift Detection** - monitors performance degradation
- ✅ **Auto Training Data** - generates datasets for fine-tuning
- ✅ **Gradio UI** - easy-to-use web interface

### Driver Tracking (Optional)
- 👤 Per-driver statistics
- 📊 Performance leaderboards
- 📜 Individual evaluation history
- 🎯 Training needs identification

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.8+
python --version

# OpenAI API key
# Get one from: https://platform.openai.com/api-keys
```

### Installation

```bash
# 1. Clone repository
git clone https://github.com/YOUR_USERNAME/raag-box-classifier.git
cd raag-box-classifier

# 2. Install dependencies
pip install -r requirements_enhanced.txt

# 3. Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# 4. Test the system
python test_system.py

# 5. Start the application
bash start_enhanced.sh
```

Visit `http://localhost:7860` to use the interface!

## 📁 Project Structure

```
raag-box-classifier/
├── api_enhanced.py              # FastAPI backend
├── api_driver.py                # Backend with driver tracking
├── classifier_enhanced.py       # AI vision classifier
├── raag_enhanced.py            # RAAG memory + RL logic
├── gradio_app_enhanced.py      # Basic Gradio UI
├── gradio_app_driver.py        # UI with driver tracking
├── storage.py                  # Data storage
├── storage_driver.py           # Storage with driver queries
├── requirements_enhanced.txt   # Python dependencies
├── start_enhanced.sh           # Startup script
├── test_system.py              # System verification
└── docs/
    ├── README_COMPLETE.md      # Comprehensive documentation
    ├── START_HERE.md           # Getting started guide
    └── DRIVER_FEATURE_SUMMARY.md
```

## 🎮 Usage

### Basic Usage (No Driver Tracking)

```bash
# Terminal 1: Start backend
python api_enhanced.py

# Terminal 2: Start UI
python gradio_app_enhanced.py
```

### With Driver Tracking

```bash
# Terminal 1: Start backend
python api_driver.py

# Terminal 2: Start UI
python gradio_app_driver.py
```

### API Usage

```bash
# Classify a box
curl -X POST http://localhost:7861/upload_box \
  -F "file=@box_image.jpg" \
  -F "driver_id=D12345"

# Get statistics
curl http://localhost:7861/statistics

# Get driver stats
curl http://localhost:7861/driver_statistics?driver_id=D12345
```

## 🧠 How It Works

### The RL Innovation

Traditional approach requires manually labeling thousands of images. RAAG instead:

1. **High Confidence (≥85%)** → Trusts prediction → Adds to training data
2. **Low Confidence (<85%)** → Flags for review → Doesn't corrupt data
3. **Retrieves Context** → Uses past similar cases as examples
4. **Detects Drift** → Monitors when performance degrades
5. **Auto Fine-tune** → Exports training data when ready

### Example Flow

```
Day 1: Upload box → AI: "OK (92% confident)" → Auto-save as training data
Day 2: Upload similar → AI retrieves Day 1 example → "OK (94% confident)"
Day 10: Weird box → AI: "NEEDS_FIX (67% confident)" → Flag for review
Week 4: Export 75 examples → Fine-tune model → Deploy improved version
```

## 📊 Performance Metrics

The system tracks:
- **Total Evaluations**: Number of boxes processed
- **Average Confidence**: How certain the AI is
- **Low Confidence Rate**: % needing review
- **Drift Score**: Performance degradation indicator
- **Training Samples**: Available for fine-tuning

## 🔧 Configuration

### Adjust Confidence Threshold

```python
# In api_enhanced.py or api_driver.py
raag = RAGMemory(
    confidence_threshold=0.85,  # Lower = more training data, less quality
    drift_threshold=0.3         # Lower = more sensitive to drift
)
```

### Change AI Model

```python
# In classifier_enhanced.py
self.model = "gpt-4o"  # For better accuracy (more expensive)
# or
self.model = "gpt-4o-mini"  # Faster and cheaper (default)
```

## 📚 Documentation

- **[START_HERE.md](docs/START_HERE.md)** - Complete package overview
- **[README_COMPLETE.md](docs/README_COMPLETE.md)** - Detailed technical documentation
- **[DRIVER_FEATURE_SUMMARY.md](docs/DRIVER_FEATURE_SUMMARY.md)** - Driver tracking guide

## 🛠️ Development

### Run Tests

```bash
python test_system.py
```

### Export Training Data

```bash
curl -X POST http://localhost:7861/export_training_data
# Creates training_data.jsonl for fine-tuning
```

### Reset Memory

```bash
curl -X POST http://localhost:7861/reset_memory
```

## 🚢 Deployment

### Local Deployment
```bash
bash start_enhanced.sh
```

### Docker (Coming Soon)
```bash
docker-compose up
```

### Hugging Face Spaces
1. Create new Space with Gradio SDK
2. Upload all files
3. Add `OPENAI_API_KEY` to secrets
4. Auto-deploys!

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [OpenAI GPT-4o](https://openai.com/)
- UI powered by [Gradio](https://gradio.app/)
- Backend using [FastAPI](https://fastapi.tiangolo.com/)

## 📧 Support

- 📖 Check [documentation](docs/)
- 🐛 Report bugs via [Issues](https://github.com/YOUR_USERNAME/raag-box-classifier/issues)
- 💬 Ask questions in [Discussions](https://github.com/YOUR_USERNAME/raag-box-classifier/discussions)

## 🗺️ Roadmap

- [ ] WhatsApp bot integration
- [ ] Multi-label damage classification
- [ ] Docker containerization
- [ ] Web dashboard for managers
- [ ] Mobile app
- [ ] Integration with logistics systems

---

**Built with ❤️ for efficient operations management**
