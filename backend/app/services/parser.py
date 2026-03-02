import traceback
import pandas as pd
import fitz  # PyMuPDF
from sqlalchemy.orm import Session
from app.models.models import Questionnaire, Question, DocumentStatus

def parse_questionnaire(db: Session, questionnaire: Questionnaire, file_path: str, job_id: int = None):
    try:
        extracted_questions = []
        file_ext = file_path.lower().split('.')[-1]

        if file_ext in ['csv', 'xlsx']:
            # Read tabular data
            if file_ext == 'csv':
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Simple heuristic: try to find a column with "Question" or take the first column
            q_col = None
            for col in df.columns:
                if 'question' in str(col).lower():
                    q_col = col
                    break
            
            if not q_col and len(df.columns) > 0:
                q_col = df.columns[0] # Fallback to first column

            if q_col:
                # Drop empty questions
                df = df.dropna(subset=[q_col])
                for index, row in df.iterrows():
                    question_text = str(row[q_col]).strip()
                    if question_text:
                        extracted_questions.append({
                            "question_number": str(index + 1),
                            "question_text": question_text,
                        })

        elif file_ext == 'pdf':
            # Extract from PDF
            import re
            doc = fitz.open(file_path)
            q_index = 1
            
            all_lines = []
            for page in doc:
                text = page.get_text()
                # Split and clean lines while preserving sequence
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                all_lines.extend(lines)
            
            current_q_text = ""
            instruction_text = ""
            
            for line in all_lines:
                # Heuristic: A new question typically starts with a number (1., 1), etc.) 
                # or a "Q" prefix (Q1, Q2.1, etc.)
                is_new_q_start = re.match(r'^(\d+[\.\)\:]|Q\d+[\.\)\:]|[a-z][\.\)\:])', line, re.I)
                
                # Check for common instruction keywords
                is_instruction = re.match(r'^(note|instruction|please|attention|guideline|disclaimer)', line, re.I)
                
                if is_new_q_start and not is_instruction:
                    # Save the previous question if it exists
                    if current_q_text:
                        extracted_questions.append({
                            "question_number": str(q_index),
                            "question_text": current_q_text,
                            "metadata": {"instructions": instruction_text}
                        })
                        q_index += 1
                        instruction_text = "" # Reset instructions after attaching to a question
                    current_q_text = line
                elif is_instruction:
                    instruction_text += " " + line
                else:
                    # If it doesn't look like a new question and not an instruction, 
                    # it's likely a continuation or a sub-instruction
                    if current_q_text:
                        current_q_text += " " + line
                    else:
                        instruction_text += " " + line
            
            # Finalize the last question
            if current_q_text:
                extracted_questions.append({
                    "question_number": str(q_index),
                    "question_text": current_q_text,
                    "metadata": {"instructions": instruction_text}
                })
        
        # Save to DB
        order_idx = 1
        for q_data in extracted_questions:
            q_text = q_data["question_text"]
            instr = q_data.get("metadata", {}).get("instructions", "")
            
            # Clean question text: Strip number/prefix from the start of the text
            # e.g., "1. Is the report..." -> "Is the report..."
            import re
            q_text = re.sub(r'^(\d+[\.\)\:]\s*|Q\d+[\.\)\:]\s*|[a-z][\.\)\:]\s*)', '', q_text, flags=re.I).strip()
            
            question_obj = Question(
                questionnaire_id=questionnaire.id,
                project_id=questionnaire.project_id,
                question_number=q_data["question_number"],
                question_text=q_text,
                instructions=instr,
                order_index=order_idx
            )
            db.add(question_obj)
            order_idx += 1
            
        questionnaire.parsing_status = DocumentStatus.COMPLETED
        db.commit()
    except Exception as e:
        db.rollback()
        questionnaire.parsing_status = DocumentStatus.FAILED
        db.commit()
        raise e
