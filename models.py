from datetime import datetime
from db import db

class Template(db.Model):
    __tablename__ = 'template'

    templateId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    templateType = db.Column(db.Enum(
        'CONTEXT_BASED', 
        'FROM_SAMPLE_PROBLEM', 
        'FROM_MORE_EXAMPLES', 
        'FROM_CONCEPT_COMPARISON', 
        'REMOVE_AMBIGUITY', 
        'FIX_REFERENCES', 
        'FIX_DISTRACTORS'
    ), nullable=False)
    templateName = db.Column(db.String(255), nullable=False)
    templateVersion = db.Column(db.Integer, nullable=False)
    defaultAssignments = db.Column(db.JSON)
    templateStr = db.Column(db.Text)
    updateMessage = db.Column(db.Text)
    updater = db.Column(db.String(255))
    updateTime = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    # New field: Generate Question Format
    generateQuestionFormat = db.Column(db.Enum(
        'SINGLE_CHOICE', 
        'MULTIPLE_CHOICE', 
        'FILL_IN_THE_BLANKS', 
        'TEXT_BASED'
    ), nullable=False, default='SINGLE_CHOICE')

    def __repr__(self):
        return f'<Template {self.templateName}>'


class Generation(db.Model):
    __tablename__ = 'generation'

    generationId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    templateId = db.Column(db.Integer, db.ForeignKey('template.templateId'), nullable=False)
    promptText = db.Column(db.Text, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    
    # JSON assignment field containing specific keys
    assignment = db.Column(db.JSON, nullable=True)

    gptResponse = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Generation {self.generationId}>'


class Question(db.Model):
    __tablename__ = 'question'

    questionId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    generationId = db.Column(db.Integer, db.ForeignKey('generation.generationId'), nullable=False)
    questionType = db.Column(db.String(50), nullable=False)
    questionText = db.Column(db.Text, nullable=False)
    version = db.Column(db.Integer, nullable=False)
    modificationType = db.Column(db.String(255), nullable=True)
    templateId = db.Column(db.Integer, db.ForeignKey('template.templateId'))
    assignment = db.Column(db.JSON)
    updater = db.Column(db.String(255))
    updateTime = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<Question {self.questionId}>'


