import json
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class BuildingAgent:
    def __init__(self):
        # We use the OpenAI client which is universally compatible with local LLMs (Ollama, LM Studio)
        # or hosted OSS models (Groq, Together). 
        # For local Ollama, base_url="http://localhost:11434/v1", api_key="ollama"
        self.client = OpenAI(
            base_url=os.getenv("LLM_BASE_URL", "http://localhost:11434/v1"),
            api_key=os.getenv("LLM_API_KEY", "ollama")
        )
        self.model = os.getenv("LLM_MODEL", "llama3")

    def evaluate_and_act(self, temp, pmv, energy):
        """
        Takes sensor data, queries the LLM, and returns optimal setpoints.
        """
        system_prompt = """
        You are an autonomous Eco-Loop Building Agent. Your goal is to minimize energy consumption (kWh) 
        while maintaining thermal comfort (PMV between -0.5 and +0.5).
        
        You will receive current zone metrics. You must return a JSON object with your control actions:
        {
            "heating_setpoint": float,
            "cooling_setpoint": float,
            "reasoning": "string explaining your choice"
        }
        """
        
        user_prompt = f"Current State - Temp: {temp}C, PMV: {pmv}, Energy: {energy}kWh. What are the optimal setpoints?"
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={ "type": "json_object" },
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            return json.loads(result)
        except Exception as e:
            print(f"Agent Error: {e}")
            # Fallback safe setpoints
            return {"heating_setpoint": 20.0, "cooling_setpoint": 24.0, "reasoning": "Fallback due to error"}
