from db import db
from datetime import datetime

class Template(db.Model):
    __tablename__ = 'template'

    template_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    template_type = db.Column(db.Enum(
        'CONTEXT_BASED', 
        'FROM_SAMPLE_PROBLEM', 
        'FROM_MORE_EXAMPLES', 
        'FROM_CONCEPT_COMPARISON', 
        'REMOVE_AMBIGUITY', 
        'FIX_REFERENCES', 
        'FIX_DISTRACTORS'
    ), nullable=False)
    template_name = db.Column(db.String(255), nullable=False)
    template_version = db.Column(db.Integer, nullable=False)
    default_assignments = db.Column(db.JSON)
    template_str = db.Column(db.Text)
    update_message = db.Column(db.Text)
    updater = db.Column(db.String(255))
    update_time = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<Template {self.template_name}>'


class Generation(db.Model):
    __tablename__ = 'generation'

    generation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    template_id = db.Column(db.Integer, db.ForeignKey('template.template_id'), nullable=False)
    prompt_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # JSON assignment field containing specific keys
    assignment = db.Column(db.JSON, nullable=True)

    gpt_response = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Generation {self.generation_id}>'

class Question(db.Model):
    __tablename__ = 'question'

    question_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    generation_id = db.Column(db.Integer, db.ForeignKey('generation.generation_id'), nullable=False)
    question_type = db.Column(db.String(50), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    version = db.Column(db.Integer, nullable=False)
    modification_type = db.Column(db.String(255), nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey('template.template_id'))
    assignment = db.Column(db.JSON)
    updater = db.Column(db.String(255))
    update_time = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<Question {self.question_id}>'


