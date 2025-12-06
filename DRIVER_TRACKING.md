# 👤 Driver Tracking Feature - Documentation

## Overview

The enhanced RAAG system now includes comprehensive driver tracking capabilities, allowing you to:
- Track individual driver performance
- Monitor per-driver statistics
- View driver evaluation history
- Create leaderboards
- Identify training needs

---

## 🎯 Key Features

### 1. Driver Identification
Every evaluation requires a Driver ID, enabling:
- Individual performance tracking
- Accountability and quality control
- Targeted training interventions
- Performance-based incentives

### 2. Per-Driver Statistics
Track for each driver:
- Total evaluations performed
- Average confidence scores
- OK vs NEEDS_FIX ratio (damage rate)
- Feedback contributions
- Recent evaluation history

### 3. System-Wide Analytics
- Overall system performance
- Driver leaderboards
- Comparative analysis
- Trend identification

---

## 📊 New API Endpoints

### 1. Upload Box with Driver Info
```bash
POST /upload_box
```

**Parameters:**
- `file`: Box image (required)
- `driver_id`: Driver identifier (required)
- `box_id`: Package/box identifier (optional)

**Example:**
```bash
curl -X POST http://localhost:7861/upload_box \
  -F "file=@box.jpg" \
  -F "driver_id=D12345" \
  -F "box_id=PKG-789456"
```

**Response:**
```json
{
  "condition": "OK",
  "confidence": 0.92,
  "reason": "Minor wear, structurally sound",
  "damage_types": [],
  "should_review": false,
  "image_id": "img_1234567890.jpg",
  "driver_id": "D12345",
  "box_id": "PKG-789456"
}
```

---

### 2. Get Driver Statistics
```bash
GET /driver_statistics?driver_id=D12345
```

**Response:**
```json
{
  "driver_id": "D12345",
  "statistics": {
    "total_evaluations": 47,
    "average_confidence": 0.89,
    "ok_count": 43,
    "needs_fix_count": 4,
    "feedback_count": 2,
    "damage_rate": 0.085
  }
}
```

---

### 3. Get Driver History
```bash
GET /driver_history?driver_id=D12345&limit=10
```

**Response:**
```json
{
  "driver_id": "D12345",
  "total": 47,
  "history": [
    {
      "image": "img_123.jpg",
      "driver_id": "D12345",
      "box_id": "PKG-789",
      "condition": "OK",
      "confidence": 0.92,
      "reason": "...",
      "timestamp": "2024-12-05T10:30:00"
    },
    ...
  ]
}
```

---

### 4. Get Leaderboard
```bash
GET /leaderboard?limit=10
```

**Response:**
```json
{
  "leaderboard": [
    {
      "driver_id": "D12345",
      "total_evaluations": 156,
      "average_confidence": 0.91,
      "feedback_contributions": 8
    },
    {
      "driver_id": "D67890",
      "total_evaluations": 143,
      "average_confidence": 0.88,
      "feedback_contributions": 5
    },
    ...
  ]
}
```

---

## 🖥️ Updated Gradio Interface

### New Input Fields

1. **Driver ID** (Required)
   - Text input for driver identifier
   - Examples: D12345, DRIVER-001, JohnD
   - Required for all evaluations

2. **Box ID** (Optional)
   - Text input for package/box tracking
   - Examples: PKG-789456, BOX-123
   - Helpful for tracing specific packages

### New UI Sections

1. **Driver Statistics Panel**
   - Shows individual driver performance
   - Updates after each evaluation
   - Displays:
     - Total evaluations
     - Average confidence
     - OK vs NEEDS_FIX counts
     - Feedback contributions

2. **History Viewer**
   - "Load My History" button
   - Shows last 10 evaluations for driver
   - Includes timestamps and results

---

## 💼 Use Cases

### 1. Driver Performance Management

**Identify High Performers:**
```python
# Get leaderboard
response = requests.get("http://localhost:7861/leaderboard")
top_drivers = response.json()["leaderboard"][:5]

for driver in top_drivers:
    print(f"{driver['driver_id']}: {driver['total_evaluations']} evaluations")
```

**Identify Training Needs:**
```python
# Get driver with low confidence scores
driver_stats = requests.get(
    "http://localhost:7861/driver_statistics?driver_id=D12345"
).json()

if driver_stats["statistics"]["average_confidence"] < 0.8:
    print(f"Driver {driver_id} may need additional training")
```

---

### 2. Quality Control

**Monitor Damage Rates:**
```python
# Check if driver has unusually high damage rate
stats = get_driver_statistics("D12345")
damage_rate = stats["damage_rate"]

if damage_rate > 0.15:  # More than 15% damaged
    print(f"⚠️ High damage rate for driver {driver_id}")
    # Investigate routes, handling procedures, etc.
```

---

### 3. Incentive Programs

**Create Performance Metrics:**
```python
def calculate_driver_score(driver_id):
    stats = get_driver_statistics(driver_id)
    
    # Score based on:
    # - Number of evaluations (activity)
    # - Average confidence (quality)
    # - Feedback contributions (improvement)
    
    score = (
        stats["total_evaluations"] * 0.3 +
        stats["average_confidence"] * 100 * 0.5 +
        stats["feedback_count"] * 10 * 0.2
    )
    
    return score

# Rank drivers and reward top performers
```

---

### 4. Route Optimization

**Identify Problem Routes:**
```python
# Get all evaluations by driver
history = get_driver_history("D12345", limit=100)

# Analyze if certain areas have more damage
damage_locations = [
    eval for eval in history 
    if eval["condition"] == "NEEDS_FIX"
]

# Identify patterns (time of day, location, etc.)
```

---

## 📈 Analytics Examples

### Driver Performance Report

```python
def generate_driver_report(driver_id):
    stats = requests.get(
        f"http://localhost:7861/driver_statistics?driver_id={driver_id}"
    ).json()["statistics"]
    
    history = requests.get(
        f"http://localhost:7861/driver_history?driver_id={driver_id}&limit=100"
    ).json()["history"]
    
    report = f"""
    Driver Performance Report: {driver_id}
    =====================================
    
    Total Evaluations: {stats['total_evaluations']}
    Average Confidence: {stats['average_confidence']:.1%}
    
    Box Conditions:
    - OK: {stats['ok_count']} ({stats['ok_count']/stats['total_evaluations']:.1%})
    - NEEDS FIX: {stats['needs_fix_count']} ({stats['damage_rate']:.1%})
    
    Quality Score: {stats['average_confidence'] * 100:.0f}/100
    Feedback Contributions: {stats['feedback_count']}
    
    Recent Trend:
    """
    
    # Analyze last 10 evaluations
    recent = history[:10]
    recent_avg_conf = sum(r['confidence'] for r in recent) / len(recent)
    
    if recent_avg_conf > stats['average_confidence']:
        report += "📈 Improving"
    elif recent_avg_conf < stats['average_confidence']:
        report += "📉 Declining"
    else:
        report += "➡️ Stable"
    
    return report
```

---

### Fleet-Wide Analysis

```python
def analyze_fleet():
    leaderboard = requests.get(
        "http://localhost:7861/leaderboard?limit=100"
    ).json()["leaderboard"]
    
    total_drivers = len(leaderboard)
    total_evaluations = sum(d['total_evaluations'] for d in leaderboard)
    avg_confidence = sum(
        d['average_confidence'] * d['total_evaluations'] 
        for d in leaderboard
    ) / total_evaluations
    
    print(f"""
    Fleet Performance Summary
    =========================
    Total Drivers: {total_drivers}
    Total Evaluations: {total_evaluations}
    Fleet Average Confidence: {avg_confidence:.1%}
    
    Top Performer: {leaderboard[0]['driver_id']}
    Most Active: {max(leaderboard, key=lambda x: x['total_evaluations'])['driver_id']}
    """)
```

---

## 🔒 Privacy Considerations

### Driver ID Recommendations

1. **Use Anonymized IDs**
   - D12345 instead of "John Smith"
   - Protect driver privacy while enabling tracking

2. **Secure Storage**
   - Keep driver ID mappings secure
   - Limit access to sensitive data

3. **Data Retention**
   - Define data retention policies
   - Archive old records appropriately

4. **Transparency**
   - Inform drivers about tracking
   - Explain how data is used
   - Provide drivers access to their own stats

---

## 🚀 Quick Start with Driver Tracking

### 1. Update Your Files

Replace the old files with driver-enabled versions:
```bash
# Use the new files
cp api_driver.py api.py
cp gradio_app_driver.py gradio_app.py
cp storage_driver.py storage.py
```

### 2. Restart System

```bash
# Stop old processes
pkill -f api.py
pkill -f gradio_app.py

# Start new system
bash start_enhanced.sh
```

### 3. Test Driver Tracking

```bash
# Upload with driver ID
curl -X POST http://localhost:7861/upload_box \
  -F "file=@test_box.jpg" \
  -F "driver_id=TEST_DRIVER_001"

# Check driver stats
curl http://localhost:7861/driver_statistics?driver_id=TEST_DRIVER_001

# View history
curl http://localhost:7861/driver_history?driver_id=TEST_DRIVER_001
```

---

## 📊 Dashboard Ideas

### Management Dashboard

```
┌─────────────────────────────────────────────┐
│  Fleet Overview                             │
├─────────────────────────────────────────────┤
│  Active Drivers: 47                         │
│  Today's Evaluations: 234                   │
│  Average Confidence: 87%                    │
│  System Health: 🟢 Good                     │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Top Performers This Week                   │
├─────────────────────────────────────────────┤
│  1. D12345 - 156 evaluations - 91% conf    │
│  2. D67890 - 143 evaluations - 88% conf    │
│  3. D11111 - 138 evaluations - 87% conf    │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Needs Attention                            │
├─────────────────────────────────────────────┤
│  ⚠️ D99999 - Low confidence (72%)          │
│  ⚠️ D88888 - High damage rate (18%)        │
└─────────────────────────────────────────────┘
```

### Driver Dashboard

```
┌─────────────────────────────────────────────┐
│  Your Performance - D12345                  │
├─────────────────────────────────────────────┤
│  Total Evaluations: 156                     │
│  Your Confidence: 91%                       │
│  Fleet Average: 87%                         │
│  Your Rank: #1 of 47                        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  This Week's Activity                       │
├─────────────────────────────────────────────┤
│  Mon: 28 evaluations                        │
│  Tue: 32 evaluations                        │
│  Wed: 31 evaluations                        │
│  Thu: 29 evaluations                        │
│  Fri: 30 evaluations                        │
└─────────────────────────────────────────────┘
```

---

## 🎯 Best Practices

### 1. Driver Onboarding
- Assign unique Driver IDs
- Train on system usage
- Explain performance tracking
- Show how to view their stats

### 2. Regular Reviews
- Weekly performance reports
- Monthly trend analysis
- Quarterly training sessions
- Annual performance reviews

### 3. Feedback Culture
- Encourage mistake corrections
- Reward feedback contributions
- Make feedback easy and quick
- Show impact of feedback

### 4. Fair Evaluation
- Consider route difficulty
- Account for weather conditions
- Look at trends, not single events
- Combine multiple metrics

---

## 📚 Additional Resources

### API Documentation
Full API reference: `http://localhost:7861/docs`

### Example Queries
See `DRIVER_TRACKING_EXAMPLES.py` for code samples

### Dashboard Templates
See `DASHBOARD_TEMPLATES.html` for UI examples

---

**Driver tracking transforms your RAAG system from a simple classifier into a comprehensive performance management tool!** 🚀
