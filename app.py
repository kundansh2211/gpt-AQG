from flask import Flask, request, jsonify
from fetchers import get_stex_content , get_recursive_stex 
from flask_cors import CORS
from db import db
from config import Config
from flask_migrate import Migrate
from models import Template, Generation, Question
from dotenv import load_dotenv
from datetime import datetime
from utils import generate_gpt_response, replace_placeholders
import os

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
        defaultAssignments=data.get('defaultAssignments'),
        templateStr=data.get('templateStr'),
        updateMessage=data.get('updateMessage'),
        updater=data.get('updater')
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
        "updatedTime": template.updateTime
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
            "updatedTime": template.updateTime
        })
    
    return jsonify(templates_list), 200


@app.route('/api/generation_api', methods=['POST'])
def generation_api():
    data = request.json
    templateId = data.get('templateId')
    template = Template.query.get_or_404(templateId)
    promptText = template.templateStr

    assignment = data.get('assignment')
    
    final_prompt = replace_placeholders(promptText, assignment)
    print("Final prompt sent to GPT: ", final_prompt)
    gpt_response = generate_gpt_response(final_prompt)
    
    generation = Generation(
        templateId=templateId,
        promptText=promptText,
        assignment=assignment,  
        gptResponse=gpt_response,
        createdAt=datetime.utcnow()
    )

    db.session.add(generation)
    db.session.commit()
    
    return jsonify({
        "message": "Generation created successfully",
        "gpt_response": gpt_response
    }), 201


if __name__ == '__main__':
    app.run(debug=True)
