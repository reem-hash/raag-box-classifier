import gradio as gr
import requests
import io
from typing import Tuple, Optional

# API Configuration
API_URL = "http://127.0.0.1:7861/upload_box"
FEEDBACK_URL = "http://127.0.0.1:7861/feedback"
STATS_URL = "http://127.0.0.1:7861/statistics"

# Global state
current_image = None
current_result = None


def evaluate_box(image) -> Tuple[str, Optional[str], str]:
    """
    Evaluate box condition and return result with confidence
    
    Returns:
        (result_text, preview_image, statistics)
    """
    global current_image, current_result
    
    if image is None:
        return "⚠️ Please upload an image first.", None, ""
    
    print("📸 Evaluating box image...")
    
    # Store for feedback
    current_image = image
    
    # Convert PIL to bytes
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    img_bytes = buf.getvalue()
    
    # Send to API
    files = {"file": ("image.jpg", img_bytes, "image/jpeg")}
    
    try:
        response = requests.post(API_URL, files=files, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        current_result = data
        
        # Format result
        condition = data.get("condition", "UNKNOWN")
        confidence = data.get("confidence", 0.0)
        reason = data.get("reason", "No reason provided")
        should_review = data.get("should_review", False)
        damage_types = data.get("damage_types", [])
        
        # Create status message
        if condition == "OK":
            icon = "🟢"
            status_color = "green"
        else:
            icon = "🔴"
            status_color = "red"
        
        # Confidence indicator
        conf_emoji = "🟢" if confidence >= 0.85 else "🟡" if confidence >= 0.6 else "🔴"
        
        result_text = f"""# {icon} BOX CONDITION: {condition}

**Confidence:** {conf_emoji} {confidence:.1%}
**Reason:** {reason}
"""
        
        if damage_types:
            result_text += f"\n**Damage Types:** {', '.join(damage_types)}"
        
        if should_review:
            result_text += "\n\n⚠️ **Low confidence** - Consider manual review"
        
        # Get statistics
        stats_text = get_statistics_display()
        
        return result_text, image, stats_text
        
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ **Error connecting to API:** {str(e)}\n\nMake sure the backend is running on port 7861."
        return error_msg, None, ""
    except Exception as e:
        error_msg = f"❌ **Error:** {str(e)}"
        return error_msg, None, ""


def send_feedback(correct_label: str) -> str:
    """Send feedback to improve the model"""
    global current_image, current_result
    
    if current_image is None:
        return "⚠️ No image to provide feedback for. Upload and evaluate an image first."
    
    print(f"📝 Sending feedback: {correct_label}")
    
    # Convert PIL to bytes
    buf = io.BytesIO()
    current_image.save(buf, format="JPEG")
    img_bytes = buf.getvalue()
    
    files = {"image": ("image.jpg", img_bytes, "image/jpeg")}
    data = {"correct_label": correct_label}
    
    try:
        response = requests.post(FEEDBACK_URL, files=files, data=data, timeout=10)
        response.raise_for_status()
        
        return f"✅ **Feedback recorded!** The system will learn from this correction.\n\n**Correct label:** {correct_label}"
        
    except Exception as e:
        return f"❌ Error sending feedback: {str(e)}"


def get_statistics_display() -> str:
    """Fetch and format system statistics"""
    try:
        response = requests.get(STATS_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        stats = data.get("statistics", {})
        
        total = stats.get("total_evaluations", 0)
        low_conf_rate = stats.get("low_confidence_rate", 0)
        avg_conf = stats.get("average_confidence", 0)
        recent_conf = stats.get("recent_confidence_trend", 0)
        training_samples = stats.get("training_samples_available", 0)
        retrain = data.get("retraining_recommended", False)
        
        stats_text = f"""## 📊 System Statistics

**Total Evaluations:** {total}
**Average Confidence:** {avg_conf:.1%}
**Recent Trend:** {recent_conf:.1%}
**Low Confidence Rate:** {low_conf_rate:.1%}
**Training Samples:** {training_samples}
"""
        
        if retrain:
            stats_text += "\n🔄 **Retraining recommended** - Sufficient data accumulated"
        
        return stats_text
        
    except Exception as e:
        return f"Statistics unavailable: {str(e)}"


# Build Gradio Interface
with gr.Blocks(title="📦 RAAG Operations Equipment Checker", theme=gr.themes.Soft()) as interface:
    
    gr.Markdown("""
    # 📦 RAAG Operations Equipment Checker
    ### Self-Improving Box Condition Classifier with Reinforcement Learning
    
    Upload a box image to automatically evaluate its condition. The system learns from each evaluation and improves over time.
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 📸 Upload Box Image")
            img_input = gr.Image(type="pil", label="Box Image")
            
            submit_btn = gr.Button("🔍 Check Condition", variant="primary", size="lg")
            
            gr.Markdown("---")
            gr.Markdown("### 🎯 Provide Feedback (Optional)")
            gr.Markdown("Help improve the model by correcting mistakes:")
            
            with gr.Row():
                ok_btn = gr.Button("✅ Actually OK", size="sm")
                fix_btn = gr.Button("🔧 Actually NEEDS_FIX", size="sm")
            
            feedback_output = gr.Markdown(label="Feedback Status")
        
        with gr.Column(scale=1):
            gr.Markdown("### 📋 Results")
            result_output = gr.Markdown(label="Classification Result")
            
            preview_output = gr.Image(label="Preview", interactive=False)
    
    gr.Markdown("---")
    
    with gr.Row():
        stats_output = gr.Markdown(label="System Statistics")
    
    # Button actions
    submit_btn.click(
        fn=evaluate_box,
        inputs=img_input,
        outputs=[result_output, preview_output, stats_output]
    )
    
    ok_btn.click(
        fn=lambda: send_feedback("OK"),
        outputs=feedback_output
    )
    
    fix_btn.click(
        fn=lambda: send_feedback("NEEDS_FIX"),
        outputs=feedback_output
    )
    
    # Auto-load statistics on start
    interface.load(
        fn=get_statistics_display,
        outputs=stats_output
    )
    
    gr.Markdown("""
    ---
    ### 🤖 How It Works
    
    1. **Upload Image** - The system analyzes box condition using AI vision
    2. **Get Result** - Receive instant classification with confidence score
    3. **Provide Feedback** - Optionally correct mistakes to improve the model
    4. **Automatic Learning** - High-confidence predictions automatically train the system
    5. **Drift Detection** - System monitors performance and alerts when retraining is needed
    
    **Features:**
    - ✨ Self-improving through reinforcement learning
    - 🎯 Confidence-based auto-evaluation
    - 📈 Automatic drift detection
    - 🔄 Training data accumulation for fine-tuning
    - 📊 Real-time performance statistics
    """)


if __name__ == "__main__":
    print("🚀 Starting Gradio interface...")
    print("📍 Make sure the FastAPI backend is running on port 7861")
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
