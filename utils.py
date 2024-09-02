import openai
from dotenv import load_dotenv
import os
from openai import OpenAI

load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  
def generate_gpt_response(final_prompt):
    # Create a chat completion request
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": final_prompt}
        ]
    )
    
    # Extract the response message content
    message = response.choices[0].message.content
    
    return message

