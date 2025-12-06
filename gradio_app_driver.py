import gradio as gr
import requests
import io
from typing import Tuple, Optional
from datetime import datetime

# API Configuration
API_URL = "http://127.0.0.1:7861/upload_box"
FEEDBACK_URL = "http://127.0.0.1:7861/feedback"
STATS_URL = "http://127.0.0.1:7861/statistics"
DRIVER_STATS_URL = "http://127.0.0.1:7861/driver_statistics"

# Global state
current_image = None
current_result = None
current_driver_id = None


def evaluate_box(image, driver_id: str, box_id: str = "") -> Tuple[str, Optional[str], str]:
    """
    Evaluate box condition and return result with confidence
    
    Args:
        image: PIL Image of the box
        driver_id: Driver identifier
        box_id: Optional box/package identifier
        
    Returns:
        (result_text, preview_image, statistics)
    """
    global current_image, current_result, current_driver_id
    
    if image is None:
        return "⚠️ Please upload an image first.", None, ""
    
    if not driver_id or driver_id.strip() == "":
        return "⚠️ Please enter your Driver ID.", None, ""
    
    print(f"📸 Evaluating box image for Driver: {driver_id}")
    
    # Store for feedback
    current_image = image
    current_driver_id = driver_id.strip()
    
    # Convert PIL to bytes
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    img_bytes = buf.getvalue()
    
    # Prepare form data
    files = {"file": ("image.jpg", img_bytes, "image/jpeg")}
    data = {
        "driver_id": current_driver_id,
        "box_id": box_id.strip() if box_id else ""
    }
    
    # Send to API
    try:
        response = requests.post(API_URL, files=files, data=data, timeout=30)
        response.raise_for_status()
        
        result_data = response.json()
        current_result = result_data
        
        # Format result
        condition = result_data.get("condition", "UNKNOWN")
        confidence = result_data.get("confidence", 0.0)
        reason = result_data.get("reason", "No reason provided")
        should_review = result_data.get("should_review", False)
        damage_types = result_data.get("damage_types", [])
        image_id = result_data.get("image_id", "")
        
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

**Driver ID:** {current_driver_id}
**Box ID:** {box_id if box_id else "Not specified"}
**Image ID:** {image_id}
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

**Confidence:** {conf_emoji} {confidence:.1%}
**Reason:** {reason}
"""
        
        if damage_types:
            result_text += f"\n**Damage Types:** {', '.join(damage_types)}"
        
        if should_review:
            result_text += "\n\n⚠️ **Low confidence** - Consider manual review"
        
        # Get statistics
        stats_text = get_statistics_display(current_driver_id)
        
        return result_text, image, stats_text
        
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ **Error connecting to API:** {str(e)}\n\nMake sure the backend is running on port 7861."
        return error_msg, None, ""
    except Exception as e:
        error_msg = f"❌ **Error:** {str(e)}"
        return error_msg, None, ""


def send_feedback(correct_label: str) -> str:
    """Send feedback to improve the model"""
    global current_image, current_result, current_driver_id
    
    if current_image is None:
        return "⚠️ No image to provide feedback for. Upload and evaluate an image first."
    
    if not current_driver_id:
        return "⚠️ Driver ID not found. Please evaluate an image first."
    
    print(f"📝 Sending feedback: {correct_label} from Driver: {current_driver_id}")
    
    # Convert PIL to bytes
    buf = io.BytesIO()
    current_image.save(buf, format="JPEG")
    img_bytes = buf.getvalue()
    
    files = {"image": ("image.jpg", img_bytes, "image/jpeg")}
    data = {
        "correct_label": correct_label,
        "driver_id": current_driver_id
    }
    
    try:
        response = requests.post(FEEDBACK_URL, files=files, data=data, timeout=10)
        response.raise_for_status()
        
        return f"✅ **Feedback recorded!** The system will learn from this correction.\n\n**Driver:** {current_driver_id}\n**Correct label:** {correct_label}\n\nThank you for helping improve the system!"
        
    except Exception as e:
        return f"❌ Error sending feedback: {str(e)}"


def get_statistics_display(driver_id: str = None) -> str:
    """Fetch and format system statistics"""
    try:
        # Get overall statistics
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
        
        # Get driver-specific statistics if driver_id provided
        if driver_id and driver_id.strip():
            try:
                driver_response = requests.get(
                    f"{DRIVER_STATS_URL}?driver_id={driver_id}",
                    timeout=5
                )
                if driver_response.status_code == 200:
                    driver_data = driver_response.json()
                    driver_stats = driver_data.get("statistics", {})
                    
                    stats_text += f"""

---

## 👤 Your Statistics (Driver: {driver_id})

**Your Evaluations:** {driver_stats.get('total_evaluations', 0)}
**Your Average Confidence:** {driver_stats.get('average_confidence', 0):.1%}
**OK Boxes:** {driver_stats.get('ok_count', 0)}
**Needs Fix:** {driver_stats.get('needs_fix_count', 0)}
**Feedback Given:** {driver_stats.get('feedback_count', 0)}
"""
            except:
                pass  # Driver stats not available
        
        return stats_text
        
    except Exception as e:
        return f"Statistics unavailable: {str(e)}"


def get_driver_history(driver_id: str) -> str:
    """Get history for a specific driver"""
    if not driver_id or driver_id.strip() == "":
        return "⚠️ Please enter a Driver ID to view history."
    
    try:
        response = requests.get(
            f"http://127.0.0.1:7861/driver_history?driver_id={driver_id}&limit=10",
            timeout=5
        )
        response.raise_for_status()
        data = response.json()
        
        history = data.get("history", [])
        
        if not history:
            return f"No history found for Driver: {driver_id}"
        
        history_text = f"## 📋 Recent History for Driver: {driver_id}\n\n"
        
        for i, record in enumerate(history, 1):
            timestamp = record.get("timestamp", "Unknown")
            condition = record.get("condition", "Unknown")
            confidence = record.get("confidence", 0)
            box_id = record.get("box_id", "N/A")
            
            icon = "🟢" if condition == "OK" else "🔴"
            conf_emoji = "🟢" if confidence >= 0.85 else "🟡" if confidence >= 0.6 else "🔴"
            
            history_text += f"{i}. {icon} **{condition}** {conf_emoji} ({confidence:.1%})\n"
            history_text += f"   Box: {box_id} | Time: {timestamp}\n\n"
        
        return history_text
        
    except Exception as e:
        return f"❌ Error fetching history: {str(e)}"


# Build Gradio Interface
with gr.Blocks(title="📦 RAAG Driver Box Checker", theme=gr.themes.Soft()) as interface:
    
    gr.Markdown("""
    # 📦 RAAG Driver Box Condition Checker
    ### Self-Improving AI System with Driver Tracking
    
    Upload a box image to automatically evaluate its condition. The system tracks your performance and learns over time.
    """)
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 👤 Driver Information")
            driver_id_input = gr.Textbox(
                label="Driver ID *",
                placeholder="Enter your Driver ID (e.g., D12345)",
                info="Required for tracking your evaluations"
            )
            box_id_input = gr.Textbox(
                label="Box/Package ID (Optional)",
                placeholder="e.g., PKG-789456",
                info="Optional tracking number"
            )
            
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
        with gr.Column(scale=1):
            stats_output = gr.Markdown(label="Statistics")
        
        with gr.Column(scale=1):
            gr.Markdown("### 📜 Your Recent History")
            history_btn = gr.Button("🔄 Load My History", size="sm")
            history_output = gr.Markdown(label="History")
    
    # Button actions
    submit_btn.click(
        fn=evaluate_box,
        inputs=[img_input, driver_id_input, box_id_input],
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
    
    history_btn.click(
        fn=get_driver_history,
        inputs=driver_id_input,
        outputs=history_output
    )
    
    # Auto-load statistics on start
    interface.load(
        fn=get_statistics_display,
        outputs=stats_output
    )
    
    gr.Markdown("""
    ---
    ### 🤖 How It Works
    
    1. **Enter Driver ID** - Your unique identifier for tracking
    2. **Upload Image** - The system analyzes box condition using AI vision
    3. **Get Result** - Receive instant classification with confidence score
    4. **Provide Feedback** - Optionally correct mistakes to improve the model
    5. **Track Progress** - View your statistics and history
    
    **Features:**
    - ✨ Self-improving through reinforcement learning
    - 🎯 Driver performance tracking
    - 📈 Automatic drift detection
    - 🔄 Training data accumulation for fine-tuning
    - 📊 Real-time performance statistics
    
    **Privacy:** Your Driver ID is used only for performance tracking and system improvement.
    """)


if __name__ == "__main__":
    print("🚀 Starting Gradio interface with driver tracking...")
    print("📍 Make sure the FastAPI backend is running on port 7861")
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
