from flask import Flask, request, jsonify
from fetchers import get_stex_content , get_recursive_stex 
from flask_cors import CORS
from db import db
from config import Config
from flask_migrate import Migrate
from models import Template, Generation, Question
from dotenv import load_dotenv

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
        template_type=data.get('template_type'),
        template_name=data.get('template_name'),
        template_version=data.get('template_version', 1),
        default_assignments=data.get('default_assignments'),
        template_str=data.get('template_str'),
        update_message=data.get('update_message'),
        updater=data.get('updater')
    )
    
    db.session.add(template)
    db.session.commit()

    return jsonify({"message": "Template created successfully", "template_id": template.template_id}), 201

@app.route('/api/templates/<int:template_id>', methods=['GET'])
def get_template(template_id):
    template = Template.query.get_or_404(template_id)
    return jsonify({
        "template_id": template.template_id,
        "template_type": template.template_type,
        "template_name": template.template_name,
        "template_version": template.template_version,
        "default_assignments": template.default_assignments,
        "template_str": template.template_str,
        "update_message": template.update_message,
        "updater": template.updater,
        "updated_time": template.update_time
    }), 200

@app.route('/api/templates/<int:template_id>', methods=['PUT'])
def update_template(template_id):
    template = Template.query.get_or_404(template_id)
    data = request.json
    
    template.template_type = data.get('template_type', template.template_type)
    template.template_name = data.get('template_name', template.template_name)
    template.template_version = data.get('template_version', template.template_version)
    template.default_assignments = data.get('default_assignments', template.default_assignments)
    template.template_str = data.get('template_str', template.template_str)
    template.update_message = data.get('update_message', template.update_message)
    template.updater = data.get('updater', template.updater)
    
    db.session.commit()

    return jsonify({"message": "Template updated successfully"}), 200

@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
def delete_template(template_id):
    template = Template.query.get_or_404(template_id)
    
    db.session.delete(template)
    db.session.commit()

    return jsonify({"message": "Template deleted successfully"}), 200

@app.route('/api/templates', methods=['GET'])
def list_templates():
    templates = Template.query.all()
    templates_list = []
    
    for template in templates:
        templates_list.append({
            "template_id": template.template_id,
            "template_type": template.template_type,
            "template_name": template.template_name,
            "template_version": template.template_version,
            "default_assignments": template.default_assignments,
            "template_str": template.template_str,
            "update_message": template.update_message,
            "updater": template.updater,
            "updated_time": template.update_time
        })
    
    return jsonify(templates_list), 200


# @app.route('/api/create-template', methods=['POST'])
# def create_template_api():
    # Get the request data
    data = request.json

    # Extract template details from the request
    template_str = data.get('template_str')
    template_id = data.get('template_id')
    course = data.get('course')
    section_info = data.get('section')  
    num_questions = data.get('num_questions')
    sample_question = data.get('sample_question')
    concepts = data.get('concepts')

    # Validate that required fields are provided
    if not template_str:
        return jsonify({"error": "Template string must be provided"}), 400

    if not section_info or 'archive' not in section_info or 'filepath' not in section_info:
        return jsonify({"error": "Section information (archive and filepath) must be provided"}), 400

    # Fetch the course content using the archive and filepath
    try:
        section_content = get_stex_content(section_info['archive'], section_info['filepath'])
   
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    # Populate the template with the provided values
    try:
        populated_template = template_str.format(
            course=course,
            section=section_content,  
            num_questions=num_questions,
            sample_question=sample_question,
            concepts=concepts
        )
    except KeyError as e:
        return jsonify({"error": f"Missing placeholder: {str(e)}"}), 400

    # Return the populated template in the response
    response = {
        "TemplateId": template_id,
        "PopulatedTemplate": populated_template
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)
