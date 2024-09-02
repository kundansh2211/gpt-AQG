from flask import Flask, request, jsonify
from fetchers import get_stex_content , get_recursive_stex 
from flask_cors import CORS
from db import db
from config import Config
from flask_migrate import Migrate
from models import Template, Generation, Question
from dotenv import load_dotenv
from datetime import datetime
from utils import generate_gpt_response

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


@app.route('/api/generation_api', methods=['POST'])
def generation_api():
    # Get the request data
    data = request.json

    # Extract template details from the request
    template_id = data.get('template_id')
    
    # Fetch the template_str (prompt_text) from the Template table using the template_id
    template = Template.query.get_or_404(template_id)
    prompt_text = template.template_str
    print(f"Prompt text: {prompt_text}")  # Add this line to print the prompt_text)

    # Extract course and assignment details from the request
    course = data.get('course')
    
    # Extract the assignment object, which should be a dictionary containing "course", "section", "num_questions", etc.
    assignment = data.get('assignment')
    
    # Get section content based on the archive and filepath provided in the assignment
    section_content = get_stex_content(assignment['section']['archive'], assignment['section']['filepath'])
    
    # Replace placeholders in prompt_text with corresponding values from the assignment
    final_prompt = prompt_text.format(
        course=course,
        section=section_content,  
        num_questions=assignment.get('num_questions'),
        sample_question=assignment.get('sample_question'),
        concepts=assignment.get('concepts')
    )

    # Generate GPT response using the final prompt
    gpt_response = generate_gpt_response(final_prompt)

    # Add the generation to the database
    generation = Generation(
        template_id=template_id,
        prompt_text=prompt_text,
        assignment=assignment,  # Store the assignment as a JSON object in the database
        gpt_response=gpt_response,
        created_at=datetime.utcnow()
    )

    db.session.add(generation)
    db.session.commit()

    # Return the GPT response and a success message in JSON format
    return jsonify({
        "message": "Generation created successfully",
        "gpt_response": gpt_response
    }), 201


if __name__ == '__main__':
    app.run(debug=True)
