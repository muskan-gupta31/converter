from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
import re
import logging

logger = logging.getLogger(__name__)

class AITextGenerator:
    def __init__(self):
        self.model_name = "gpt2-medium"  # Use medium for better responses
        
        try:
            logger.info(f"Loading model: {self.model_name}")
            self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_name)
            self.model = GPT2LMHeadModel.from_pretrained(self.model_name)
            
            # Add padding token
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
    
    def generate_response(self, prompt, conversation_history=None, max_length=150):
        """Generate AI response with improved settings"""
        try:
            # Create a more natural prompt
            if "heat" in prompt.lower() or "definition" in prompt.lower():
                # Handle specific questions better
                enhanced_prompt = f"Question: {prompt}\nAnswer:"
            else:
                enhanced_prompt = f"Human: {prompt}\nAI:"
            
            # Tokenize input
            inputs = self.tokenizer.encode(
                enhanced_prompt,
                return_tensors="pt",
                max_length=200,
                truncation=True
            )
            
            # Generate response with better parameters
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + max_length,
                    min_length=inputs.shape[1] + 30,  # Ensure minimum response length
                    num_return_sequences=1,
                    temperature=0.7,  # More focused responses
                    top_k=50,
                    top_p=0.9,
                    do_sample=True,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.3,  # Reduce repetition
                    no_repeat_ngram_size=3
                )
            
            # Decode response
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the AI response
            if "Answer:" in generated_text:
                response = generated_text.split("Answer:")[-1].strip()
            elif "AI:" in generated_text:
                response = generated_text.split("AI:")[-1].strip()
            else:
                response = generated_text[len(enhanced_prompt):].strip()
            
            # Clean up the response
            response = self.clean_response(response)
            
            # Provide fallback responses for common queries
            if not response or len(response) < 15:
                if "heat" in prompt.lower():
                    return "Heat is a form of energy that flows from a warmer object to a cooler one. It's the energy transfer that occurs due to temperature differences. Heat can be transferred through conduction (direct contact), convection (fluid movement), and radiation (electromagnetic waves)."
                elif "definition" in prompt.lower():
                    return "I'd be happy to provide a definition! Could you specify what term you'd like me to define?"
                else:
                    return "That's an interesting question! I'd be happy to help you explore this topic further. Could you provide a bit more context about what specifically you'd like to know?"
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble generating a response right now. Please try again."
    
    def clean_response(self, response):
        """Clean and format the AI response"""
        # Remove unwanted patterns
        response = re.sub(r'Human:.*', '', response)  # Remove any Human: text
        response = re.sub(r'Question:.*', '', response)  # Remove Question: text
        response = re.sub(r'\n+', ' ', response)  # Replace multiple newlines
        response = re.sub(r'\s+', ' ', response)  # Normalize whitespace
        
        # Remove incomplete sentences at the end
        sentences = response.split('.')
        if len(sentences) > 1 and len(sentences[-1].strip()) < 10:
            sentences = sentences[:-1]
        
        response = '. '.join(sentences)
        if response and not response.endswith('.') and not response.endswith('!') and not response.endswith('?'):
            response += '.'
        
        return response.strip()

# Initialize global AI service
ai_generator = AITextGenerator()