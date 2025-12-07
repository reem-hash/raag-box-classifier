import gradio as gr
import requests
import io
from typing import Tuple, Optional
from datetime import datetime
import numpy as np
from PIL import Image

# API Configuration
API_URL = "http://127.0.0.1:7861/upload_box"
FEEDBACK_URL = "http://127.0.0.1:7861/feedback"
STATS_URL = "http://127.0.0.1:7861/statistics"
DRIVER_STATS_URL = "http://127.0.0.1:7861/driver_statistics"

# Global state
current_image = None
current_result = None
current_driver_id = None

# Authentic Snoonu Brand Colors (from official brand identity)
SNOONU_RED = "#E31E24"  # Signature Snoonu red
SNOONU_RED_LIGHT = "#FF4444"  # Lighter red for gradients
SNOONU_SUCCESS = "#00C851"  # Green for success
SNOONU_DARK = "#1A1A1A"  # Dark text
SNOONU_GRAY = "#F5F5F5"  # Light background


def check_image_quality(image) -> Tuple[bool, str]:
    """Check if image meets quality requirements"""
    if image is None:
        return False, ""
    
    try:
        img_array = np.array(image)
        brightness = np.mean(img_array)
        
        if brightness < 50:
            return False, "📸 Too dark - Please use better lighting"
        
        if brightness > 240:
            return False, "📸 Too bright - Move away from direct light"
        
        gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array
        laplacian_var = np.var(gray[1:] - gray[:-1])
        
        if laplacian_var < 100:
            return False, "📸 Blurry - Hold camera steady"
        
        if image.size[0] < 300 or image.size[1] < 300:
            return False, "📸 Get closer to the box"
        
        return True, "✓ Photo looks good!"
        
    except Exception as e:
        return True, ""


def evaluate_box(image, driver_id: str) -> Tuple[str, str, str]:
    """Main evaluation function - simplified"""
    global current_image, current_result, current_driver_id
    
    if image is None:
        return "📸 Please take a photo first", "", ""
    
    if not driver_id or driver_id.strip() == "":
        return "👤 Please enter your Driver ID", "", ""
    
    # Check image quality
    is_quality_ok, quality_msg = check_image_quality(image)
    if not is_quality_ok:
        return f"⚠️ {quality_msg}\n\nPlease retake the photo", "", quality_msg
    
    # Store for feedback
    current_image = image
    current_driver_id = driver_id.strip()
    
    # Convert to bytes
    buf = io.BytesIO()
    image.save(buf, format="JPEG")
    img_bytes = buf.getvalue()
    buf.seek(0)
    
    # Send to API
    try:
        files = {"file": ("image.jpg", buf, "image/jpeg")}
        data = {"driver_id": current_driver_id, "box_id": ""}
        
        response = requests.post(API_URL, files=files, data=data, timeout=30)
        response.raise_for_status()
        
        result_data = response.json()
        current_result = result_data
        
        condition = result_data.get("condition", "UNKNOWN")
        confidence = result_data.get("confidence", 0.0)
        reason = result_data.get("reason", "")
        
        # Create simple, clear result with Snoonu branding
        if condition == "OK":
            result_html = f"""
<div style="text-align: center; padding: 40px 30px; background: linear-gradient(135deg, #00C851 0%, #00E45D 100%); border-radius: 20px; color: white; box-shadow: 0 4px 20px rgba(0,200,81,0.3);">
    <div style="font-size: 64px; margin-bottom: 10px;">✓</div>
    <h2 style="margin: 0 0 8px 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">All Good!</h2>
    <p style="margin: 0; font-size: 18px; opacity: 0.95;">Ready to deliver</p>
    <div style="margin-top: 25px; padding: 15px; background: rgba(255,255,255,0.2); border-radius: 12px; backdrop-filter: blur(10px);">
        <p style="margin: 0; font-size: 14px; opacity: 0.9;">{reason}</p>
    </div>
</div>
"""
        else:
            result_html = f"""
<div style="text-align: center; padding: 40px 30px; background: linear-gradient(135deg, #E31E24 0%, #FF4444 100%); border-radius: 20px; color: white; box-shadow: 0 4px 20px rgba(227,30,36,0.3);">
    <div style="font-size: 64px; margin-bottom: 10px;">⚠️</div>
    <h2 style="margin: 0 0 8px 0; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">Needs Check</h2>
    <p style="margin: 0; font-size: 18px; opacity: 0.95;">Contact operations team</p>
    <div style="margin-top: 25px; padding: 15px; background: rgba(255,255,255,0.2); border-radius: 12px; backdrop-filter: blur(10px);">
        <p style="margin: 0; font-size: 14px; opacity: 0.9;">{reason}</p>
    </div>
</div>
"""
        
        # Driver info card with Snoonu styling
        driver_info = f"""
<div style="background: white; padding: 20px; border-radius: 16px; margin-top: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 15px;">
        <div style="text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Driver</div>
            <div style="color: #1A1A1A; font-size: 16px; font-weight: 600;">{current_driver_id}</div>
        </div>
        <div style="text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Time</div>
            <div style="color: #1A1A1A; font-size: 16px; font-weight: 600;">{datetime.now().strftime('%I:%M %p')}</div>
        </div>
        <div style="text-align: center;">
            <div style="color: #666; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;">Confidence</div>
            <div style="color: #1A1A1A; font-size: 16px; font-weight: 600;">{confidence:.0%}</div>
        </div>
    </div>
    <div style="background: #F8F9FA; padding: 12px; border-radius: 10px; border-left: 3px solid #E31E24;">
        <p style="margin: 0; color: #666; font-size: 13px; line-height: 1.5;">
            💡 This check ensures your equipment is safe and ready
        </p>
    </div>
</div>
"""
        
        return result_html + driver_info, quality_msg, ""
        
    except Exception as e:
        return f"""
<div style="text-align: center; padding: 40px 30px; background: #FFF5F5; border-radius: 20px; border: 2px solid #FFEBEE;">
    <div style="font-size: 48px; margin-bottom: 15px; color: #E31E24;">⚠️</div>
    <h2 style="margin: 0 0 8px 0; color: #E31E24; font-size: 24px; font-weight: 700;">Connection Error</h2>
    <p style="margin: 0; color: #666; font-size: 14px;">Please check your internet connection</p>
    <p style="margin: 15px 0 0 0; color: #999; font-size: 12px;">or contact support team</p>
</div>
""", quality_msg, ""


def send_feedback(correct_label: str) -> str:
    """Send feedback - simplified"""
    global current_image, current_driver_id
    
    if current_image is None or current_driver_id is None:
        return "⚠️ Please complete a check first"
    
    try:
        buf = io.BytesIO()
        current_image.save(buf, format="JPEG")
        buf.seek(0)
        
        files = {"image": ("image.jpg", buf, "image/jpeg")}
        data = {"correct_label": correct_label, "driver_id": current_driver_id}
        
        response = requests.post(FEEDBACK_URL, files=files, data=data, timeout=10)
        response.raise_for_status()
        
        return f"""
<div style="background: #E8F5E9; padding: 16px; border-radius: 12px; border-left: 4px solid #00C851;">
    <p style="margin: 0; color: #2E7D32; font-size: 14px; font-weight: 500;">
        ✓ Thanks! Your feedback helps improve the system
    </p>
</div>
"""
    except Exception as e:
        return "⚠️ Could not save feedback. Please try again."


def get_my_stats(driver_id: str) -> str:
    """Get driver stats - simplified display with Snoonu styling"""
    if not driver_id or driver_id.strip() == "":
        return ""
    
    try:
        response = requests.get(f"{DRIVER_STATS_URL}?driver_id={driver_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            stats = data.get("statistics", {})
            
            total = stats.get('total_evaluations', 0)
            ok = stats.get('ok_count', 0)
            needs_fix = stats.get('needs_fix_count', 0)
            
            return f"""
<div style="background: white; padding: 25px; border-radius: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
    <h3 style="margin: 0 0 20px 0; color: #1A1A1A; font-size: 18px; font-weight: 700;">📊 Your Activity</h3>
    <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px;">
        <div style="text-align: center; padding: 20px 15px; background: linear-gradient(135deg, #F5F5F5 0%, #FAFAFA 100%); border-radius: 12px; border: 1px solid #E0E0E0;">
            <div style="font-size: 32px; font-weight: 700; color: #1A1A1A; margin-bottom: 5px;">{total}</div>
            <div style="font-size: 11px; color: #666; text-transform: uppercase; letter-spacing: 0.5px;">Total</div>
        </div>
        <div style="text-align: center; padding: 20px 15px; background: linear-gradient(135deg, #E8F5E9 0%, #F1F8F2 100%); border-radius: 12px; border: 1px solid #C8E6C9;">
            <div style="font-size: 32px; font-weight: 700; color: #00C851; margin-bottom: 5px;">{ok}</div>
            <div style="font-size: 11px; color: #2E7D32; text-transform: uppercase; letter-spacing: 0.5px;">Good</div>
        </div>
        <div style="text-align: center; padding: 20px 15px; background: linear-gradient(135deg, #FFEBEE 0%, #FFF5F5 100%); border-radius: 12px; border: 1px solid #FFCDD2;">
            <div style="font-size: 32px; font-weight: 700; color: #E31E24; margin-bottom: 5px;">{needs_fix}</div>
            <div style="font-size: 11px; color: #C62828; text-transform: uppercase; letter-spacing: 0.5px;">Check</div>
        </div>
    </div>
</div>
"""
        return ""
    except:
        return ""


# Custom CSS for authentic Snoonu branding
custom_css = """
/* Snoonu Brand Styling - Official Colors */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.gradio-container {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
    background: #FAFAFA !important;
}

/* Remove default gradio styling */
.contain { gap: 20px !important; }

/* Header styling with Snoonu red */
.snoonu-header {
    background: linear-gradient(135deg, #E31E24 0%, #FF4444 100%);
    padding: 30px;
    border-radius: 20px;
    margin-bottom: 30px;
    text-align: center;
    color: white;
    box-shadow: 0 4px 20px rgba(227, 30, 36, 0.25);
}

.snoonu-logo {
    font-size: 42px;
    font-weight: 800;
    letter-spacing: -1px;
    margin: 0;
    text-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

/* Primary button - Snoonu red */
.primary-btn button {
    background: linear-gradient(135deg, #E31E24 0%, #FF4444 100%) !important;
    border: none !important;
    color: white !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    padding: 22px !important;
    border-radius: 14px !important;
    box-shadow: 0 4px 16px rgba(227, 30, 36, 0.3) !important;
    transition: all 0.3s ease !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

.primary-btn button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(227, 30, 36, 0.4) !important;
}

.primary-btn button:active {
    transform: translateY(0) !important;
}

/* Feedback buttons */
.feedback-btn button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 12px 20px !important;
    font-size: 14px !important;
    transition: all 0.2s ease !important;
}

/* Input fields - Modern styling */
input[type="text"] {
    border-radius: 12px !important;
    border: 2px solid #E0E0E0 !important;
    padding: 14px 16px !important;
    font-size: 16px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
    background: white !important;
}

input[type="text"]:focus {
    border-color: #E31E24 !important;
    box-shadow: 0 0 0 4px rgba(227, 30, 36, 0.1) !important;
    outline: none !important;
}

/* Image upload area */
.image-container {
    border: 3px dashed #E0E0E0 !important;
    border-radius: 16px !important;
    background: white !important;
    transition: all 0.3s ease !important;
    padding: 20px !important;
}

.image-container:hover {
    border-color: #E31E24 !important;
    background: #FFF5F5 !important;
}

/* Labels */
label {
    font-weight: 600 !important;
    color: #1A1A1A !important;
    font-size: 14px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}

/* Cards and sections */
.info-card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    margin: 15px 0;
}

/* Section titles */
h3 {
    color: #1A1A1A !important;
    font-weight: 700 !important;
    font-size: 18px !important;
}

/* Markdown styling */
.markdown {
    color: #1A1A1A !important;
}

/* Remove extra padding */
.block { padding: 0 !important; }
"""

# Build the authentic Snoonu-branded interface
with gr.Blocks(css=custom_css, theme=gr.themes.Soft(), title="Snoonu Box Check") as interface:
    
    # Header with Snoonu branding
    gr.HTML("""
    <div class="snoonu-header">
        <div class="snoonu-logo">📦 Snoonu</div>
        <p style="margin: 12px 0 0 0; font-size: 18px; opacity: 0.95; font-weight: 500;">
            Box Safety Check
        </p>
        <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.85; font-weight: 400;">
            Quick equipment check for drivers
        </p>
    </div>
    """)
    
    with gr.Row():
        # Left column - Input
        with gr.Column(scale=1):
            # Driver ID section
            gr.HTML("""
            <div style="background: white; padding: 20px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
                <h3 style="margin: 0 0 12px 0; color: #1A1A1A; font-size: 16px; font-weight: 700;">👤 Driver ID</h3>
            """)
            
            driver_id_input = gr.Textbox(
                label="",
                placeholder="Enter your Driver ID (e.g., D12345)",
                show_label=False,
                container=False
            )
            
            gr.HTML("</div>")
            
            # Photo section
            gr.HTML("""
            <div style="background: white; padding: 20px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
                <h3 style="margin: 0 0 15px 0; color: #1A1A1A; font-size: 16px; font-weight: 700;">📸 Take Photo</h3>
                <div style="background: #FFF9F0; padding: 16px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #FFC107;">
                    <p style="margin: 0; color: #F57C00; font-size: 13px; line-height: 1.6; font-weight: 500;">
                        <strong style="display: block; margin-bottom: 8px;">Quick Tips:</strong>
                        ✓ Use good lighting<br>
                        ✓ Hold camera steady<br>
                        ✓ Show full box side
                    </p>
                </div>
            </div>
            """)
            
            # Image input
            try:
                img_input = gr.Image(
                    sources=["webcam", "upload"],
                    type="pil",
                    label="",
                    show_label=False,
                    container=False,
                    elem_classes=["image-container"]
                )
            except TypeError:
                img_input = gr.Image(
                    source="webcam",
                    type="pil",
                    label="",
                    show_label=False,
                    container=False,
                    elem_classes=["image-container"]
                )
            
            # Photo quality feedback
            quality_status = gr.Markdown("", visible=True)
            
            gr.HTML("<div style='height: 20px;'></div>")
            
            # Main check button
            with gr.Row(elem_classes=["primary-btn"]):
                submit_btn = gr.Button("✓ Check Box", variant="primary", size="lg")
            
            gr.HTML("<div style='height: 30px;'></div>")
            
            # Feedback section
            gr.HTML("""
            <div style="background: white; padding: 20px; border-radius: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
                <h3 style="margin: 0 0 8px 0; color: #1A1A1A; font-size: 16px; font-weight: 700;">💬 Wrong Result?</h3>
                <p style="color: #666; font-size: 13px; margin: 0 0 15px 0; line-height: 1.5;">
                    Help us improve - only if the result was incorrect
                </p>
            """)
            
            with gr.Row(elem_classes=["feedback-btn"]):
                ok_btn = gr.Button("✓ Actually OK", size="sm", variant="secondary")
                fix_btn = gr.Button("⚠️ Needs Check", size="sm", variant="secondary")
            
            gr.HTML("</div>")
            
            feedback_output = gr.HTML()
        
        # Right column - Results
        with gr.Column(scale=1):
            gr.HTML("""
            <div style="background: white; padding: 20px; border-radius: 16px; margin-bottom: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
                <h3 style="margin: 0 0 15px 0; color: #1A1A1A; font-size: 16px; font-weight: 700;">📋 Result</h3>
            </div>
            """)
            
            result_output = gr.HTML()
            
            gr.HTML("<div style='height: 25px;'></div>")
            
            stats_output = gr.HTML()
    
    # Footer with Snoonu branding
    gr.HTML("""
    <div style="text-align: center; padding: 30px; margin-top: 40px; background: white; border-radius: 16px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);">
        <div style="display: inline-flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <div style="width: 40px; height: 40px; background: linear-gradient(135deg, #E31E24 0%, #FF4444 100%); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 20px;">
                📦
            </div>
            <div style="font-size: 24px; font-weight: 700; color: #1A1A1A;">Snoonu</div>
        </div>
        <p style="margin: 0; color: #666; font-size: 14px; font-weight: 500;">
            Equipment safety check • Built in Qatar, for Qatar
        </p>
        <p style="margin: 12px 0 0 0; color: #999; font-size: 12px;">
            This tool tracks equipment condition, not driver performance
        </p>
    </div>
    """)
    
    # Button actions
    submit_btn.click(
        fn=evaluate_box,
        inputs=[img_input, driver_id_input],
        outputs=[result_output, quality_status, feedback_output]
    ).then(
        fn=get_my_stats,
        inputs=[driver_id_input],
        outputs=[stats_output]
    )
    
    ok_btn.click(
        fn=lambda: send_feedback("OK"),
        outputs=feedback_output
    )
    
    fix_btn.click(
        fn=lambda: send_feedback("NEEDS_FIX"),
        outputs=feedback_output
    )
    
    # Auto-load stats on driver ID change
    driver_id_input.change(
        fn=get_my_stats,
        inputs=[driver_id_input],
        outputs=[stats_output]
    )


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🚀 Snoonu Box Safety Checker")
    print("  Authentic Snoonu Brand Identity")
    print("="*60)
    print(f"\n📦 Gradio version: {gr.__version__}")
    print("🎨 Snoonu signature red: #E31E24")
    print("📸 Camera input: Enabled")
    print("✨ Qatar's first super app branding")
    print("\n💡 Opening at: http://localhost:7860")
    print("\n⚠️  Make sure backend is running on port 7861")
    print("   Start with: python main.py\n")
    print("="*60 + "\n")
    
    interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )