import openai
from dotenv import load_dotenv
import os
import json
from openai import OpenAI
from models import  Question
from datetime import datetime


load_dotenv()

# Initialize the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  
def generate_gptResponse(finalPrompt):
    # Create a chat completion request
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": finalPrompt}
        ]
    )
    
    # Extract the response message content
    message = response.choices[0].message.content
    
    return message

def process_questions(extractedJson, generation, modification_type):
    questions = []
    for question_data in extractedJson:
        complete_question = {
            "id": question_data.get('id'),
            "question": question_data.get('question'),
            "type": question_data.get('type'),
            "correctAnswer": question_data.get('correctAnswer', ''),
            "options": question_data.get('options', [])
        }
        question_id = question_data.get('id')
        question_text = json.dumps(complete_question)
        question_type = question_data.get('type')
        template_id = generation.templateId
        assignment = generation.assignment
        generation_id=generation.generationId

        if not question_text or not question_type or not question_id:
            continue
        try:
            existing_question = Question.query.filter_by(questionId=question_id, generationId=generation_id).order_by(Question.version.desc()).first()

        except Exception as e:
            print(f"Error querying existing question: {e}")
       
          
        new_version = existing_question.version + 1 if existing_question else 1
        question = Question(
            questionId=question_id,
            generationId=generation_id,
            questionType=question_type,
            questionText=question_text,
            version=new_version,
            modificationType=modification_type,
            templateId=template_id,
            assignment=assignment,
            updater="Abhishek",
            updateTime=datetime.now()
        )
        questions.append(question)
    
    return questions



def lastTextGenerationApi(section_content):
    return f'''. Add values from assignments for specific key in the whole prompt at the place of placeholders, and if no 
    placeholder for a specific key is available in the prompt, then use the information from the assignments and the prompt 
    to generate the question. If `SECTION_STEX` or `SECTION_TIDY_STEX` is available in assignments, use the content provided 
    by {section_content} and, according to the prompt, use this section_value to generate questions.

    Also, according to the value of gptResponseFormat:
    - If the value is JSON, then format the output as JSON.
    - If the value is LATEX_FORMAT, then format the output as LATEX with the following fields:
      - `id`: Unique identifier
      - `question`: The question text
      - `type`: The type of question (e.g., "single-correct")
      - `options`: A list of possible answers
      - `correctAnswer`: The correct answer

    Ensure the output is correctly formatted and do not include any other text or explanation. Even if you 
    require additional information or want to explain it better, do not return other texts than the prescribed format.

    You should, however, return an empty JSON if you do not understand anything at all from the prompt or assignments. 
    Return JSON output starting with ### and ending with ###. The output (whether JSON or LATEX) should always be inside an array, even if it is empty or contains only a single value.

    The generated question should be meaningful and not irrelevant. If there is no excess information, just return an empty JSON or LATEX.'''

def finalPromptAddReferences(currentProblem):
    return   f'''You have previously generated a set of problems. Now, I will provide a specific problem from that set, and your task is to focus only on this specific problem. Your task is to:
Add any relevant references or additional information to enhance the problem's clarity.
For example, if the problem mentions a function that hasn't been defined, include its definition within the problem.
Ensure that any referenced concepts, terms, or functions are clearly explained within the problem itself.
If no references or additional information are needed to clarify the problem, add a reference to where the problem or information is taken from (e.g., a book, paper, or source of information).
Important:

Do not modify any other parts of the problem or its format.
Do not add any extra text or new fields (such as "references"). Embed any additional information directly into the problem where appropriate.
Maintain the original structure of the problem as much as possible.
Return the problem in the JSON format with all keys and values enclosed in double quotes , and enclose the entire updated content within ### and ###.

The specific problem you need to update is: {currentProblem}.
'''

def finalPromptFixDistractors(currentProblem):
    return f'''You have previously generated a set of problems. Now, I will provide a specific problem from that set, and your task is to focus only on this specific problem. Your task is to:

    - Fix the distractors in the options list to ensure they are:
        - Similar in nature and closely related to the topic of the question.
        - Relevant and plausible enough to be considered as distractors.
        - Clear and non-ambiguous.
    - Ensure that the corrected options are still related to the topic of the question.

    Important:
    - Do not modify any other parts of the response aside from the provided problem.
    - Do not add any extra text, explanations, or new fields. Directly update the distractors within the problem where appropriate.
    -Maintain the original structure of the problem as much as possible.
Return the problem in the JSON format with all keys and values enclosed in double quotes , and enclose the entire updated content within ### and ###.

The specific problem you need to update is: {currentProblem}.
    '''

def finalPromptRemoveAmbiguity(currentProblem):
    return f'''You have previously generated a set of problems. Now, I will provide a specific problem from that set, and your task is to focus only on this specific problem. Your task is to:

    - Remove any ambiguity in the question and options list to ensure that:
        - The question is clear, concise, and unambiguous.
        - All options are distinct, clear, and don't overlap in meaning.
        - There is no confusion in the interpretation of any option.
        - Ensure all options are closely related to the question but differ in plausible ways.
    - Ensure that the corrected problem maintains its original intent and educational value.

    Important:
    - Do not modify any other parts of the response aside from the provided problem.
    - Ensure the response remains concise, avoiding unnecessary additions.
     -Maintain the original structure of the problem as much as possible.
Return the problem in the JSON format with all keys and values enclosed in double quotes , and enclose the entire updated content within ### and ###.

The specific problem you need to update is: {currentProblem}.
    '''

