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
    print("eJson",extractedJson)
    print("genera",generation)
    print("modification_type",modification_type)
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
        print("question_text",question_text)
        print("question_type",question_type)
        print("question_id",question_id)
        if not question_text or not question_type or not question_id:
            print("continueing")
            continue
        try:
            existing_question = Question.query.filter_by(questionId=question_id, generationId=generation_id).order_by(Question.version.desc()).first()

        except Exception as e:
            print(f"Error querying existing question: {e}")
       
        print("exisQue",existing_question)

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
    print("questionz",questions)
    return questions



