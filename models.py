from db import db
from datetime import datetime
from sqlalchemy import PrimaryKeyConstraint


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
    gptResponseFormat = db.Column(db.Enum(
        'JSON_FORMAT',
        'LATEX_FORMAT'
    ), nullable=False)
    templateName = db.Column(db.String(255), nullable=False)
    templateVersion = db.Column(db.Integer, nullable=False)
    defaultAssignments = db.Column(db.JSON)
    templateStr = db.Column(db.Text)
    updateMessage = db.Column(db.Text)
    updater = db.Column(db.String(255))
    updateTime = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<Template {self.templateName}>'


class Generation(db.Model):
    __tablename__ = 'generation'

    generationId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    templateId = db.Column(db.Integer, db.ForeignKey('template.templateId'), nullable=False)
    promptText = db.Column(db.Text, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.now)
    
    assignment = db.Column(db.JSON, nullable=True)

    gptResponse = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Generation {self.generationId}>'

class Question(db.Model):
    __tablename__ = 'question'

    generationId = db.Column(db.Integer, db.ForeignKey('generation.generationId'), nullable=False,primary_key=True)
    version = db.Column(db.Integer, nullable=False,primary_key=True)
    questionId = db.Column(db.Integer, nullable=False,primary_key=True)

    questionType = db.Column(db.String(50), nullable=False)
    questionText = db.Column(db.Text, nullable=False)
    modificationType = db.Column(db.String(255), default="FROM Template", nullable=True)
    templateId = db.Column(db.Integer, db.ForeignKey('template.templateId'))
    assignment = db.Column(db.JSON)
    updater = db.Column(db.String(255))
    updateTime = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

   

    def __repr__(self):
        return f'<Question {self.generationId}, {self.questionId}, {self.version}>'
