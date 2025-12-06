import base64
import json
from openai import OpenAI
from typing import Dict, Tuple


class EnhancedClassifier:
    """
    Enhanced box condition classifier with:
    - Structured output
    - Confidence scoring
    - Detailed reasoning
    - RAAG context integration
    """
    
    def __init__(self, raag):
        self.raag = raag
        self.client = OpenAI()
        self.model = "gpt-4o-mini"  # Using correct model name
    
    def classify_box_condition(self, img_bytes: bytes) -> Dict:
        """
        Classify box condition with structured output
        
        Returns:
            {
                "status": "OK" | "NEEDS_FIX",
                "confidence": 0.0-1.0,
                "reason": "Detailed explanation",
                "damage_types": ["tear", "dent", etc.]
            }
        """
        # Retrieve context from RAAG memory
        context_examples = self.raag.retrieve_context("box_condition", n=5)
        context_prompt = self.raag.format_context_for_prompt(context_examples)
        
        # Get statistics for adaptive prompting
        stats = self.raag.get_statistics()
        
        # Convert image to base64
        img_b64 = base64.b64encode(img_bytes).decode()
        
        # Build adaptive prompt
        system_prompt = self._build_system_prompt(stats)
        user_prompt = self._build_user_prompt(context_prompt)
        
        try:
            # Call OpenAI with vision
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1  # Low temperature for consistency
            )
            
            # Parse response
            result_text = response.choices[0].message.content.strip()
            
            # Extract structured data
            structured_result = self._parse_response(result_text)
            
            # Update RAAG memory with result
            self.raag.update_memory("box_condition", structured_result)
            
            return structured_result
            
        except Exception as e:
            print(f"❌ Classification error: {e}")
            # Return safe default
            return {
                "status": "ERROR",
                "confidence": 0.0,
                "reason": f"Classification failed: {str(e)}",
                "damage_types": [],
                "result": "ERROR"
            }
    
    def _build_system_prompt(self, stats: Dict) -> str:
        """Build adaptive system prompt based on current statistics"""
        
        base_prompt = """You are an expert delivery box condition evaluator. Your job is to classify boxes as OK or NEEDS_FIX.

EVALUATION CRITERIA:

OK Conditions:
- Minor scuffs or dirt that don't affect structural integrity
- Light wear on edges
- Small cosmetic marks
- Box is fully intact and functional

NEEDS_FIX Conditions:
- Tears or holes (even small ones)
- Crushed or significantly dented areas
- Water damage or excessive staining
- Missing flaps or components
- Any damage that could compromise contents

IMPORTANT: Return your answer in this EXACT JSON format:
{
    "status": "OK" or "NEEDS_FIX",
    "confidence": 0.0 to 1.0,
    "reason": "Clear explanation of your decision",
    "damage_types": ["list", "of", "damage", "types"]
}"""

        # Add adaptive guidance based on drift
        if stats.get("drift_score", 0) > 0.3:
            base_prompt += "\n\n⚠️ ALERT: Recent predictions have shown lower confidence. Be extra thorough in your analysis."
        
        return base_prompt
    
    def _build_user_prompt(self, context: str) -> str:
        """Build user prompt with RAAG context"""
        
        prompt = f"""Analyze this box image and classify its condition.

{context}

Based on these previous examples and the current image, provide your classification in the JSON format specified."""
        
        return prompt
    
    def _parse_response(self, response_text: str) -> Dict:
        """
        Parse model response into structured format
        Handles both JSON and plain text responses
        """
        try:
            # Try to extract JSON from response
            # Handle markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
            else:
                json_str = response_text.strip()
            
            # Parse JSON
            result = json.loads(json_str)
            
            # Normalize status field
            status = result.get("status", "UNKNOWN").upper()
            if status not in ["OK", "NEEDS_FIX"]:
                # Try to infer from text
                if "ok" in status.lower() and "not" not in status.lower():
                    status = "OK"
                else:
                    status = "NEEDS_FIX"
            
            # Ensure all required fields
            structured = {
                "status": status,
                "result": status,  # Keep for backward compatibility
                "confidence": float(result.get("confidence", 0.5)),
                "reason": result.get("reason", "No reason provided"),
                "damage_types": result.get("damage_types", [])
            }
            
            return structured
            
        except json.JSONDecodeError:
            # Fallback: parse plain text response
            return self._parse_plain_text(response_text)
    
    def _parse_plain_text(self, text: str) -> Dict:
        """Fallback parser for plain text responses"""
        
        text_lower = text.lower()
        
        # Determine status
        if "ok" in text_lower and "not ok" not in text_lower and "needs fix" not in text_lower:
            status = "OK"
            confidence = 0.6
        elif "needs fix" in text_lower or "not ok" in text_lower or "damaged" in text_lower:
            status = "NEEDS_FIX"
            confidence = 0.6
        else:
            status = "NEEDS_FIX"  # Default to safer option
            confidence = 0.3
        
        return {
            "status": status,
            "result": status,
            "confidence": confidence,
            "reason": text[:200],  # First 200 chars
            "damage_types": []
        }
    
    def evaluate_with_confidence(self, img_bytes: bytes) -> Tuple[str, float, str]:
        """
        Simplified interface that returns (status, confidence, reason)
        """
        result = self.classify_box_condition(img_bytes)
        return (
            result["status"],
            result["confidence"],
            result["reason"]
        )
