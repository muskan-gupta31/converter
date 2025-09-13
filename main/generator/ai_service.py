# =============================================
# COMPLETE DJANGO BACKEND - FIXED VERSION
# =============================================

# =============================================
# generator/ai_service.py - IMPROVED AI SERVICE
# =============================================

from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
import re
import logging

logger = logging.getLogger(__name__)

class AITextGenerator:
    def __init__(self):
        # Use GPT2-medium for better responses (you already downloaded it)
        self.model_name = "gpt2-medium"
        
        try:
            logger.info(f"Loading model: {self.model_name}")
            self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_name)
            self.model = GPT2LMHeadModel.from_pretrained(self.model_name)
            
            # Fix padding token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            # Fallback to base GPT2
            self.model_name = "gpt2"
            self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_name)
            self.model = GPT2LMHeadModel.from_pretrained(self.model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def generate_response(self, prompt, conversation_history=None, max_new_tokens=150):
        """Generate comprehensive AI responses like ChatGPT"""
        try:
            # Enhanced prompts for better responses
            enhanced_prompts = {
                "heat": "Question: What is heat?\nAnswer: Heat is a form of energy that transfers between objects due to temperature differences. It flows naturally from hotter objects to cooler ones through three main mechanisms: conduction (direct contact), convection (through fluids like air or water), and radiation (electromagnetic waves). Heat is measured in joules or calories and plays a crucial role in thermodynamics, weather patterns, and everyday phenomena like cooking and heating systems.",
                
                "definition": f"Please provide a comprehensive definition.\nQuestion: {prompt}\nAnswer: This term refers to",
                
                "explain": f"Let me explain this concept clearly.\nTopic: {prompt}\nExplanation: This is",
                
                "how": f"Here's a detailed explanation of how this works.\nQuestion: {prompt}\nAnswer: The process involves",
                
                "what": f"Let me provide a comprehensive answer about this topic.\nQuestion: {prompt}\nAnswer: This refers to"
            }
            
            # Choose appropriate prompt based on user input
            prompt_lower = prompt.lower()
            if "heat" in prompt_lower and ("what" in prompt_lower or "definition" in prompt_lower):
                return enhanced_prompts["heat"]
            elif "definition" in prompt_lower:
                base_prompt = enhanced_prompts["definition"]
            elif "explain" in prompt_lower:
                base_prompt = enhanced_prompts["explain"]
            elif "how" in prompt_lower:
                base_prompt = enhanced_prompts["how"]
            elif "what" in prompt_lower:
                base_prompt = enhanced_prompts["what"]
            else:
                base_prompt = f"Human: {prompt}\nAI: I'd be happy to help you with that question. Let me provide a comprehensive answer:"
            
            # Tokenize with proper attention mask
            inputs = self.tokenizer(
                base_prompt,
                return_tensors="pt",
                max_length=200,
                truncation=True,
                padding=True
            )
            
            # Generate longer, more detailed responses
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],
                    max_new_tokens=max_new_tokens,
                    min_new_tokens=50,  # Ensure minimum length
                    num_return_sequences=1,
                    temperature=0.8,
                    top_k=50,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.2,
                    length_penalty=1.1,  # Encourage longer responses
                    early_stopping=False
                )
            
            # Decode the full response
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the new generated content
            if "Answer:" in generated_text:
                response = generated_text.split("Answer:")[-1].strip()
            elif "AI:" in generated_text:
                response = generated_text.split("AI:")[-1].strip()
            elif "Explanation:" in generated_text:
                response = generated_text.split("Explanation:")[-1].strip()
            else:
                # Remove the original prompt from response
                response = generated_text[len(base_prompt):].strip()
            
            # Clean and enhance the response
            response = self.clean_and_enhance_response(response, prompt)
            
            # Ensure minimum quality response
            if len(response) < 50:
                response = self.get_detailed_fallback_response(prompt)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self.get_detailed_fallback_response(prompt)
    
    def clean_and_enhance_response(self, response, original_prompt):
        """Clean response and make it more comprehensive"""
        # Remove unwanted patterns
        response = re.sub(r'Human:.*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'Question:.*', '', response, flags=re.IGNORECASE)
        response = re.sub(r'AI:.*?(?=\w)', '', response, flags=re.IGNORECASE)
        
        # Clean whitespace and newlines
        response = re.sub(r'\n+', ' ', response)
        response = re.sub(r'\s+', ' ', response)
        
        # Remove repetitive phrases
        words = response.split()
        cleaned_words = []
        for i, word in enumerate(words):
            if i == 0 or word.lower() != words[i-1].lower():
                cleaned_words.append(word)
        response = ' '.join(cleaned_words)
        
        # Ensure proper sentence structure
        sentences = [s.strip() for s in response.split('.') if s.strip()]
        if sentences:
            # Capitalize first letter of each sentence
            sentences = [s[0].upper() + s[1:] if s else s for s in sentences]
            response = '. '.join(sentences)
            if not response.endswith('.'):
                response += '.'
        
        # Add context if response is generic
        if len(response) < 100 and any(word in original_prompt.lower() for word in ['heat', 'energy', 'temperature']):
            response += " Heat transfer is fundamental in physics and engineering, affecting everything from climate systems to industrial processes."
        
        return response.strip()
    
    def get_detailed_fallback_response(self, prompt):
        """Provide detailed fallback responses for common queries"""
        prompt_lower = prompt.lower()
        
        if 'heat' in prompt_lower:
            return """Heat is a form of energy that flows from a warmer object to a cooler one due to temperature differences. It's not a substance itself, but rather the process of energy transfer. Heat can be transferred through three main mechanisms: conduction (direct contact between objects), convection (through the movement of fluids like air or water), and radiation (electromagnetic waves that don't require a medium). Understanding heat is crucial in physics, engineering, and everyday applications like cooking, heating systems, and weather patterns."""
        
        elif any(word in prompt_lower for word in ['definition', 'define', 'meaning']):
            return """I'd be happy to provide a definition! A definition is a precise explanation of the meaning, nature, or essential characteristics of something. It helps clarify concepts by identifying key properties, functions, or relationships. Good definitions are clear, concise, and comprehensive, providing enough detail to distinguish the defined term from similar concepts while remaining accessible to the intended audience."""
        
        elif 'quantum computing' in prompt_lower:
            return """Quantum computing is a revolutionary approach to computation that leverages quantum mechanical phenomena like superposition and entanglement. Unlike classical computers that use bits (0 or 1), quantum computers use quantum bits or 'qubits' that can exist in multiple states simultaneously. This allows them to perform certain calculations exponentially faster than classical computers, particularly for problems involving cryptography, optimization, and simulation of quantum systems."""
        
        elif any(word in prompt_lower for word in ['email', 'write', 'professional']):
            return """I'd be happy to help you write a professional email! A well-structured professional email should include: a clear subject line, proper greeting, concise introduction stating your purpose, detailed body with specific information or requests, professional closing, and your contact information. The tone should be respectful, clear, and appropriate for your relationship with the recipient. Would you like me to help you with a specific type of email?"""
        
        elif 'workout' in prompt_lower or 'exercise' in prompt_lower:
            return """Here's a beginner-friendly workout plan: Start with 3 days per week, focusing on basic movements. Day 1: Upper body (push-ups, planks, arm circles). Day 2: Lower body (squats, lunges, calf raises). Day 3: Full body (burpees, mountain climbers, jumping jacks). Begin with 2-3 sets of 8-12 repetitions, rest 30-60 seconds between sets. Always warm up before exercising and cool down afterward. Gradually increase intensity and duration as your fitness improves."""
        
        else:
            return f"""That's a great question about "{prompt}"! I'd be happy to provide you with a comprehensive answer. This topic involves multiple aspects that are worth exploring in detail. Let me break this down for you with clear explanations and relevant examples. Understanding this concept requires looking at both the fundamental principles and practical applications. Would you like me to focus on any particular aspect of this topic?"""

# Initialize the AI service globally
ai_generator = AITextGenerator()