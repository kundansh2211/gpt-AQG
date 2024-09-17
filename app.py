from flask import Flask, request, jsonify
from fetchers import get_stex_content , get_recursive_stex 
from flask_cors import CORS
from db import db
from config import Config
from flask_migrate import Migrate
from models import Template, Generation, Question
from dotenv import load_dotenv
from datetime import datetime
from utils import generate_gptResponse,lastTextGenerationApi,process_questions,finalPromptAddReferences,finalPromptFixDistractors,finalPromptRemoveAmbiguity
from sqlalchemy import desc

import json
import os
import re

app = Flask(__name__)
CORS(app)

app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
load_dotenv()




@app.route('/api/templates/check', methods=['GET'])
def check_template_exists():
    templateName = request.args.get('name')
    existingTemplate = Template.query.filter_by(templateName=templateName) \
                                     .order_by(desc(Template.templateVersion)) \
                                     .first()
    if existingTemplate:
        return jsonify({
            'exists': True,
            'templateId': existingTemplate.templateId,
            'templateVersion': existingTemplate.templateVersion
        })
    else:
        return jsonify({'exists': False})
    


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
        gptResponseFormat=data.get('selectedResponseFormat'),

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

    return jsonify({"message": "Template updated successfully","templateVersion":template.templateVersion}), 200



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
    section_value=None
    section_content=""
    for item in assignment:
        if item.get('key') == 'SECTION_STEX' or item.get('key') == 'SECTION_TIDY_STEX':
            section_value = item.get('value')
            break  
    # archieve and filepath receieved as 'archive||filepath' in section_value
    if section_value and '||' in section_value:
        archive, filepath = section_value.split('||')
    
        section_content = get_stex_content(archive, filepath)
    else:
        print("Invalid section format or no section value provided")

    last = lastTextGenerationApi(section_content)
    finalPrompt=mergedPromptText+". assignment: "+str(assignment)+", gptResponseFormat: "+gptResponseFormat +last
    # gptResponse="###[{asdfasdfasdf}]###"
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




# @app.route('/api/question_extraction', methods=['POST'])
# def question_extraction_api():
#     try:
#         data = request.json
#         generationObj = data.get('generationObj')

#         if isinstance(generationObj, str):
#             generationObj = json.loads(generationObj)

#         generationId = generationObj.get('generationId')
#         modificationType = generationObj.get('modificationType', None)
        
#         generation = Generation.query.get(generationId)
#         if not generation:
#             return jsonify({
#                 "message": f"Generation record with ID {generationId} not found."
#             }), 404

#         extractedJson = data.get('extractedJson', [])
#         if not isinstance(extractedJson, list):
#             extractedJson = [extractedJson]        
#             return jsonify({
#                 "message": "Invalid extractedJson format. Expected a list of questions."
#             }), 400
        
#         questions = process_questions(extractedJson, generation, modificationType)
        
#         if not questions:
#             return jsonify({
#                 "message": "No valid questions extracted from the extractedJson."
#             }), 400
        
#         try:
#             db.session.bulk_save_objects(questions)
#             db.session.commit()

#         except Exception as e:
#             db.session.rollback()
#             return jsonify({
#                 "message": "An error occurred while saving questions to the database."
#             }), 500
        
#         return jsonify({
#             "message": f"{len(questions)} questions extracted and saved successfully.",
#             "questions_saved": len(questions),
#             "generationId": generationId
#         }), 201

#     except Exception as e:
#         return jsonify({
#             "message": "An unexpected error occurred."
#         }), 500

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
            
        
        questions = process_questions(extractedJson, generation, modificationType)
        
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
        
        if not questions:
            return jsonify({
                "message": f"No questions found for generationId {generationId}"
            }), 404
        
        questionData = []
        for question in questions:
            questionData.append({
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
            "questions": questionData
        }), 200

    except Exception as e:
        return jsonify({
            "message": "An unexpected error occurred."
        }), 500


@app.route('/api/add-references', methods=['POST'])
def add_references():
    data = request.json    
    currentProblem = data.get('currentProblem')
    generationId = data.get('generationId')

    if not currentProblem or not generationId:
        return jsonify({"error": "Both currentProblem and generationid are required"}), 400
    
    try:
        generations = Question.query.filter_by(generationId=generationId).first_or_404()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    templateId=generations.templateId
    assignment=generations.assignment
 
    finalPrompt = finalPromptAddReferences(currentProblem)

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
    currentProblem = data.get('currentProblem')
    generationId = data.get('generationId')
    if not currentProblem or not generationId:
        return jsonify({"error": "Both currentProblem and generationId are required"}), 400

    try:
        generation = Question.query.filter_by(generationId=generationId).first_or_404()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    templateId=generation.templateId
    assignment=generation.assignment
    
    finalPrompt = finalPromptFixDistractors(currentProblem)

    updatedGptResponse = generate_gptResponse(finalPrompt)
    

    generationObj = {
        "generationId": generationId,
        "templateId": templateId,
        "gptResponse": updatedGptResponse,
        "createdAt": datetime.now(),
        "promptStr":finalPrompt,
        "assignments":assignment,
        "modificationType":"Fixed Distractor"
        
    } 

    return jsonify({
        "message": "Distractors fixed successfully",
        "updatedGptResponse": updatedGptResponse,
        "generationObj":generationObj
        
    }), 200





@app.route('/api/remove-ambiguity', methods=['POST'])
def remove_ambiguity():
    data = request.json    
    currentProblem = data.get('currentProblem')
    generationId = data.get('generationId')
    
    if not currentProblem or not generationId:
        return jsonify({"error": "Both currentProblem and gptResponse are required"}), 400

    try:
        generation = Question.query.filter_by(generationId=generationId).first_or_404()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    templateId=generation.templateId
    assignment=generation.assignment

   
    finalPrompt = finalPromptRemoveAmbiguity(currentProblem)
    updatedGptResponse = generate_gptResponse(finalPrompt)

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
        "message": "Ambiguity removed successfully",
        "updatedGptResponse": updatedGptResponse,
        "generationObj":generationObj
        
    }), 200

if __name__ == '__main__':
    app.run(debug=True)

