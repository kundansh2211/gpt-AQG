import os
from openai import OpenAI
from fetchers import get_stex_content

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

def replace_placeholders(template_str, assignment):
    # Replace placeholders with actual values from the assignment dictionary
    final_prompt = template_str.replace("%%course%%", assignment.get("course", ""))
    
    # Correcting the section content replacement
    section_content = get_stex_content(
        assignment['section']['archive'], 
        assignment['section']['filepath']
    )
    final_prompt = final_prompt.replace("%%section%%", section_content)
    
    final_prompt = final_prompt.replace("%%num_questions%%", str(assignment.get("num_questions", "")))
    final_prompt = final_prompt.replace("%%sample_question%%", assignment.get("sample_question", ""))
    final_prompt = final_prompt.replace("%%concepts%%", ", ".join(assignment.get("concepts", [])))
    
    return final_prompt
