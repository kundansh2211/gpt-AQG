from flask import Flask, request, jsonify
from fetchers import get_stex_content , get_recursive_stex 
from flask_cors import CORS
from db import db
from config import Config
from flask_migrate import Migrate
from models import Template, Generation, Question
from dotenv import load_dotenv
from datetime import datetime
from utils import generate_gptResponse
import json
import os
import re

app = Flask(__name__)
CORS(app)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
load_dotenv()


@app.route('/api/templates', methods=['POST'])
def create_template():
    data = request.json
    template = Template(
        templateType=data.get('templateType'),
        templateName=data.get('templateName'),
        templateVersion=data.get('templateVersion', 1),
        defaultAssignments=data.get('formData'),
        templateStr=data.get('templateStr'),
        updateMessage=data.get('updateMessage'),
        updater=data.get('updater'),
        gptResponseFormat=data.get('selectedFormat')
    )
    
    db.session.add(template)
    db.session.commit()

    return jsonify({"message": "Template created successfully", "templateId": template.templateId}), 201



@app.route('/api/templates/<int:templateId>', methods=['GET'])
def get_template(templateId):
    template = Template.query.get_or_404(templateId)
    return jsonify({
        "templateId": template.templateId,
        "templateType": template.templateType,
        "templateName": template.templateName,
        "templateVersion": template.templateVersion,
        "defaultAssignments": template.defaultAssignments,
        "templateStr": template.templateStr,
        "updateMessage": template.updateMessage,
        "updater": template.updater,
        "updated_time": template.updateTime,
        "gptResponseFormat":template.gptResponseFormat
    }), 200



@app.route('/api/templates/<int:templateId>', methods=['PUT'])
def update_template(templateId):
    template = Template.query.get_or_404(templateId)
    data = request.json
    template.templateType = data.get('templateType', template.templateType)
    template.templateName = data.get('templateName', template.templateName)
    template.templateVersion = data.get('templateVersion', template.templateVersion)
    template.defaultAssignments = data.get('defaultAssignments', template.defaultAssignments)
    template.templateStr = data.get('templateStr', template.templateStr)
    template.updateMessage = data.get('updateMessage', template.updateMessage)
    template.updater = data.get('updater', template.updater)
    
    db.session.commit()

    return jsonify({"message": "Template updated successfully"}), 200



@app.route('/api/templates/<int:templateId>', methods=['DELETE'])
def delete_template(templateId):
    template = Template.query.get_or_404(templateId)

    db.session.delete(template)
    db.session.commit()
    
    return jsonify({"message": "Template deleted successfully"}), 200



@app.route('/api/templates', methods=['GET'])
def list_templates():
    templates = Template.query.all()
    templates_list = []
    
    for template in templates:
        templates_list.append({
            "templateId": template.templateId,
            "templateType": template.templateType,
            "templateName": template.templateName,
            "templateVersion": template.templateVersion,
            "defaultAssignments": template.defaultAssignments,
            "templateStr": template.templateStr,
            "updateMessage": template.updateMessage,
            "updater": template.updater,
            "updated_time": template.updateTime,
            "gptResponseFormat":template.gptResponseFormat
        })
    
    return jsonify(templates_list), 200





@app.route('/api/generation_api', methods=['POST'])
def generation_api():
    data = request.json    
    templateId = data.get('templateId')
    template = Template.query.get_or_404(templateId)
    promptTexts = data.get('templateStr', []) 
    mergedPromptText = ' '.join(promptTexts)
    gptResponseFormat= template.gptResponseFormat    
    assignment = data.get('assignments')
    last=f'''. Add values from assignments for specific key in whole prompt at place of placeholders and if no
    placeholder for specific key is availale in prompt then use informations used in prompts and assignments
    to generate question and also accordin to value of gptResponseFormat i.e. if JSON then Format the output as JSON , if value is LATEX_FORMAT then format the output as LATEX with
    the following fields:
    - `id`: Unique identifier
    - `question`: The question text
    - `type`: The type of question (e.g., "single-correct")
    - `options`: A list of possible answers
    - `correctAnswer`: The correct answer
    Ensure that output is correctly formatted and Do not include any other text or explanation.Even if you 
    require any other information or want to explain in better ways still donot return other texts than the prescribed
    format. You should however return empty json if you donot understand anything at all from prompt or assignments  . 
    Return json output starting with ### and ending with ###. Everytime json or latex output should be inside an array even 
    if it is empty or only value inside it.Question should be somewhat like having meaning not irrelevant and if no excess
    information then just return empty json or latex '''

    
    finalPrompt=mergedPromptText+". assignment: "+str(assignment)+", gptResponseFormat: "+gptResponseFormat +last
    gptResponse = generate_gptResponse(finalPrompt)
    generation = Generation(
        templateId=templateId,
        promptText=finalPrompt,
        assignment=assignment, 
        gptResponse=gptResponse,
        createdAt=datetime.now()
    )

    db.session.add(generation)
    db.session.commit()

    generationId = generation.generationId
    createdAt = generation.createdAt
    
    generationObj = {
        "generationId": generationId,
        "templateId": templateId,
        "gptResponse": gptResponse,
        "createdAt": createdAt,
        "promptText": finalPrompt,
        "assignment": assignment,
        
    }

    return jsonify({
        "message": "Generation created successfully",
        "gptResponse": gptResponse,
        "generationId":generationId,
        "createdAt":createdAt,
        "generationObj":generationObj
    }), 201




@app.route('/api/generations_history', methods=['GET'])
def get_generations_by_templateType():
    templateType = request.args.get('templateType')
    if not templateType:
        return jsonify({"error": "templateType is required"}), 400

    generations = db.session.query(Generation).join(Template).filter(Template.templateType == templateType).all()

    if not generations:
        return jsonify({"message": "No generations found for the given templateType","generationList":[]}), 404

    generationList = [
        {   
            "generationId": generation.generationId,
            "templateId": generation.templateId,
            "gptResponse": generation.gptResponse,
            "createdAt": generation.createdAt,
            "promptStr":generation.promptText,
            "assignments":generation.assignment,            
        } 
        for generation in generations
    ]

    return jsonify({"generationList":generationList}), 200




@app.route('/api/question_extraction', methods=['POST'])
def question_extraction_api():
    try:
        data = request.json
        generationObj = data.get('generationObj')

        if isinstance(generationObj, str):
            generationObj = json.loads(generationObj)
        generationId = generationObj.get('generationId')
        modificationType = generationObj.get('modificationType', None)
        
        generation = Generation.query.get(generationId)
        if not generation:
            return jsonify({
                "message": f"Generation record with ID {generationId} not found."
            }), 404

        extractedJson = data.get('extractedJson', [])
        if not isinstance(extractedJson, list):
            extractedJson = [extractedJson]        
        if not isinstance(extractedJson, list):
            return jsonify({
                "message": "Invalid extractedJson format. Expected a list of questions."
            }), 400
        
        questions = []
        for questionData in extractedJson:
            complete_question = {
                "id": questionData.get('id'),
                "question": questionData.get('question'),
                "type": questionData.get('type'),
                "correctAnswer": questionData.get('correctAnswer', ''),
                "options": questionData.get('options', [])
            }
            questionId = questionData.get('id')
            questionText = json.dumps(complete_question)
            questionType = questionData.get('type')
            templateId = generation.templateId
            assignment = generation.assignment
            existing_question = Question.query.filter_by(questionId=questionId, generationId=generationId).order_by(Question.version.desc()).first()

            if existing_question:
                newVersion = existing_question.version + 1
            else:
                newVersion = 1
            
            if not questionText or not questionType or not questionId:
                continue
            
            question = Question(
                questionId=questionId,
                generationId=generationId,
                questionType=questionType,
                questionText=questionText,
                version=newVersion,
                modificationType=modificationType,
                templateId=templateId,
                assignment=assignment,
                updater="Abhishek",
                updateTime=datetime.now()
            )
            questions.append(question)
        
        if not questions:
            return jsonify({
                "message": "No valid questions extracted from the extractedJson."
            }), 400
        
        try:
            db.session.bulk_save_objects(questions)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            return jsonify({
                "message": "An error occurred while saving questions to the database."
            }), 500
        
        return jsonify({
            "message": f"{len(questions)} questions extracted and saved successfully.",
            "questions_saved": len(questions),
            "generationId": generationId
        }), 201

    except Exception as e:
        return jsonify({
            "message": "An unexpected error occurred."
        }), 500






@app.route('/api/get_all_versions', methods=['POST'])
def get_all_versions():
    try:
        data = request.json        
        generationId = data.get('generationId')
        if not generationId:
            return jsonify({
                "message": "generationId is required"
            }), 400
        
        questions = Question.query.filter_by(generationId=generationId).all()
        print(" eut",questions)
        
        if not questions:
            return jsonify({
                "message": f"No questions found for generationId {generationId}"
            }), 404
        
        responseData = []
        for question in questions:
            responseData.append({
                "id": question.questionId,
                "question": question.questionText,
                "type": question.questionType,
                "modificationType":question.modificationType,
                "version": question.version,
                "templateId": question.templateId,
                "assignment": question.assignment,
                "updateTime": question.updateTime.isoformat()  
            })
                    
        return jsonify({
            "message": "Questions retrieved successfully",
            "generationId": generationId,
            "questions": responseData
        }), 200

    except Exception as e:
        return jsonify({
            "message": "An unexpected error occurred."
        }), 500


@app.route('/api/add-references', methods=['POST'])
def add_references():
    data = request.json    
    current_problem = data.get('currentProblem')
    generationId = data.get('generationId')

    if not current_problem or not generationId:
        return jsonify({"error": "Both currentProblem and generationid are required"}), 400
    
    try:
        generations = Question.query.filter_by(generationId=generationId).first_or_404()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    templateId=generations.templateId
    assignment=generations.assignment
 
    finalPrompt = f'''You have previously generated a set of problems. Now, I will provide a specific problem from that set, and your task is to focus only on this specific problem. Your task is to:
Add any relevant references or additional information to enhance the problem's clarity.
For example, if the problem mentions a function that hasn't been defined, include its definition within the problem.
Ensure that any referenced concepts, terms, or functions are clearly explained within the problem itself.
If no references or additional information are needed to clarify the problem, add a reference to where the problem or information is taken from (e.g., a book, paper, or source of information).
Important:

Do not modify any other parts of the problem or its format.
Do not add any extra text or new fields (such as "references"). Embed any additional information directly into the problem where appropriate.
Maintain the original structure of the problem as much as possible.
Return the problem in the JSON format with all keys and values enclosed in double quotes , and enclose the entire updated content within ### and ###.

The specific problem you need to update is: {current_problem}.
'''

    updatedGptResponse = generate_gptResponse(finalPrompt)
   
    generationId = generations.generationId
    generationObj = {
        "generationId": generationId,
        "templateId": templateId,
        "gptResponse": updatedGptResponse,
        "createdAt": datetime.now(),
        "promptStr":finalPrompt,
        "assignments":assignment,
        "modificationType":"Added Reference "
        
    } 

  
    return jsonify({
        "message": "References added successfully",
        "updatedGptResponse": updatedGptResponse,
        "generationObj":generationObj
        
    }), 200



@app.route('/api/fix-distractors', methods=['POST'])
def fix_distractors():
    data = request.json
    current_problem = data.get('currentProblem')
    generationId = data.get('generationId')
    if not current_problem or not generationId:
        return jsonify({"error": "Both currentProblem and generationId are required"}), 400

    try:
        generations = Question.query.filter_by(generationId=generationId).first_or_404()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    templateId=generations.templateId
    assignment=generations.assignment
    
    finalPrompt = f'''You have previously generated a set of problems. Now, I will provide a specific problem from that set, and your task is to focus only on this specific problem. Your task is to:

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

The specific problem you need to update is: {current_problem}.
    '''

    updatedGptResponse = generate_gptResponse(finalPrompt)
    

    generationId = generations.generationId
    generationObj = {
        "generationId": generationId,
        "templateId": templateId,
        "gptResponse": updatedGptResponse,
        "createdAt": datetime.now(),
        "promptStr":finalPrompt,
        "assignments":assignment,
        "modificationType":"Fixed Distractor "
        
    } 

    print("genOb",generationObj)
    return jsonify({
        "message": "References added successfully",
        "updatedGptResponse": updatedGptResponse,
        "generationObj":generationObj
        
    }), 200





@app.route('/api/remove-ambiguity', methods=['POST'])
def remove_ambiguity():
    data = request.json    
    current_problem = data.get('currentProblem')
    generationId = data.get('generationId')
    
    if not current_problem or not generationId:
        return jsonify({"error": "Both currentProblem and gptResponse are required"}), 400

    try:
        generations = Question.query.filter_by(generationId=generationId).first_or_404()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    templateId=generations.templateId
    assignment=generations.assignment

   
    finalPrompt = f'''You have previously generated a set of problems. Now, I will provide a specific problem from that set, and your task is to focus only on this specific problem. Your task is to:

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

The specific problem you need to update is: {current_problem}.
    '''
    updatedGptResponse = generate_gptResponse(finalPrompt)

    generationId = generations.generationId
    generationObj = {
        "generationId": generationId,
        "templateId": templateId,
        "gptResponse": updatedGptResponse,
        "createdAt": datetime.now(),
        "promptStr":finalPrompt,
        "assignments":assignment,
        "modificationType":"Removed Ambiguity "
        
    } 

    return jsonify({
        "message": "References added successfully",
        "updatedGptResponse": updatedGptResponse,
        "generationObj":generationObj
        
    }), 200

if __name__ == '__main__':
    app.run(debug=True)

