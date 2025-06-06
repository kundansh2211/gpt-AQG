QUIZ_GENERATION_PROMPT = """
Given the following slide content:
{slides_data}

And the existing problems:
{problem_contents}

### Instructions:

1. **Review the Content:**  
   - Summarize the key concepts, facts, and important points from the slide content. Focus on the essential information necessary for understanding the material.

2. **Analyze Existing Practice Questions:**  
   - Examine your current list of practice questions. Take note of their format (e.g., multiple choice, true/false, fill-in-the-blank), their difficulty levels, and how they relate to the content.

3. **Create a Diverse Set of Questions:**  
   - Generate a variety of question types, including Multiple Choice, Multiple Select, True/False, and Fill-in-the-Blank, based on the slide content.  
   - Ensure all questions are clear, concise, and directly related to the slides.  
   - Provide explanations for the correct answers to reinforce learning.

4. **Question Format (in JSON):**  
   - Structure each question as a JSON object with the following keys:  
     - `question`: The question text  
     - `questionType`: One of `"mcq"` (multiple choice single answer, including true/false), `"msq"` (multiple select multiple answers), or `"fill"` (fill-in-the-blank)  
     - `options`: A non empty array of answer choices (for `"mcq"` and `"msq"` questions); empty array `[]` for `"fill"` questions  
     - `correctAnswer`: The correct answer (a string for `"mcq"` and `"fill"`, or an array of strings for `"msq"`)  
     - `explanation`: A brief explanation of why the answer is correct  

5. **Number of Questions:**  
   - Generate at least 5 to 10 questions, covering different aspects of the content.

6. **Reference Text:**  
   - For each question that needs to refer to specific parts of the slides, include a brief reference note indicating the relevant section or slide.

---

### Example of a Question in JSON Format:

```json
{{
  "question": "What is the primary purpose of a neural network in artificial intelligence?",
  "questionType": "mcq",
  "options": [
    "Data storage",
    "Pattern recognition",
    "Operating system management",
    "Network security"
  ],
  "correctAnswer": "Pattern recognition",
  "explanation": "Neural networks are designed to recognize patterns in data, enabling tasks such as image recognition and speech processing."
}}
```

---

### Final Step:
- After creating the questions, review them for accuracy and alignment with the content, ensuring they serve as effective assessment tools for learners.

### IMPORTANT: ONLY output a JSON array of question objects exactly as specified.  
DO NOT add any explanations, extra text, or formatting outside the JSON array.  
Your entire response must be a valid JSON array.  
No comments, no markdown, no additional text.
"""