from sqlalchemy.orm import Session
from app.models.models import Job, JobType, JobStatus
from datetime import datetime
import traceback
from app.db.session import SessionLocal

def create_job(db: Session, job_type: JobType, project_id: int) -> Job:
    job = Job(
        job_type=job_type,
        project_id=project_id,
        status=JobStatus.QUEUED,
        progress_percent=0
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def update_job_status(db: Session, job_id: int, status: JobStatus, progress: int = None, error: str = None):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        return
    
    job.status = status
    if progress is not None:
        job.progress_percent = progress
    if error:
        job.error_message = error
    
    if status == JobStatus.COMPLETED or status == JobStatus.FAILED:
        job.completed_at = datetime.utcnow()
        
    db.commit()

# Simple synchronous execution for MVP (replace with Celery/Redis later)
from app.services.ingestion import process_document
from app.models.models import Document

def run_ingestion_job(job_id: int, document_id: int):
    db: Session = SessionLocal()
    update_job_status(db, job_id, JobStatus.RUNNING, 0)
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
             raise Exception("Document not found")
             
        process_document(db, document, document.file_path, job_id)
        
        update_job_status(db, job_id, JobStatus.COMPLETED, 100)
    except Exception as e:
        db.rollback() # VERY IMPORTANT: Rollback the session so we can run queries again
        try:
            update_job_status(db, job_id, JobStatus.FAILED, 0, str(e))
        except Exception as inner_e:
            print(f"Could not update job status after failure: {inner_e}")
        print(traceback.format_exc())
    finally:
        db.close()

from app.services.parser import parse_questionnaire
from app.models.models import Questionnaire

def run_questionnaire_parsing_job(job_id: int, questionnaire_id: int):
    db: Session = SessionLocal()
    update_job_status(db, job_id, JobStatus.RUNNING, 0)
    try:
        questionnaire = db.query(Questionnaire).filter(Questionnaire.id == questionnaire_id).first()
        if not questionnaire:
             raise Exception("Questionnaire not found")
             
        # Generate safe file path to parse (assuming stored path is known or passed)
        # For this MVP, we parse it directly by just updating state.
        file_path = f"data/uploads/questionnaire_{questionnaire.project_id}_{questionnaire.filename}"
        
        parse_questionnaire(db, questionnaire, file_path, job_id)
        
        update_job_status(db, job_id, JobStatus.COMPLETED, 100)
    except Exception as e:
        db.rollback()
        try:
            update_job_status(db, job_id, JobStatus.FAILED, 0, str(e))
        except Exception as inner_e:
            print(f"Could not update job status after failure: {inner_e}")
        print(traceback.format_exc())
    finally:
        db.close()

from app.models.models import Project, Question, Answer, AnswerVersion, Citation
from app.services.generation import generate_answer, generate_answer_gemini
from app.core.chroma import get_collection
import concurrent.futures
import time
import json
from func_timeout import func_timeout, FunctionTimedOut

def process_single_question(db: Session, project_id: int, idx_q: Question, project_documents: list, collection, max_retries=5):
    """Process a single question with retries for rate limits and fallback to Gemini."""
    # Query vector DB
    try:
        # Construct retrieval question (clean question + instructions if any)
        retrieval_query = idx_q.question_text
        if idx_q.instructions:
            retrieval_query = f"{idx_q.instructions}\n{idx_q.question_text}"
            
        results = collection.query(
            query_texts=[retrieval_query],
            n_results=5,
            where={"document_id": {"$in": [d.id for d in project_documents]}} if project_documents else None
        )
        
        context = ""
        if results and results['documents'] and len(results['documents'][0]) > 0:
            context = "\n\n".join(results['documents'][0])
        
        # Generate answer with retries for rate limits
        answer_text = ""
        groq_failed = False
        
        # Include instructions in the generation prompt if available
        generation_question = idx_q.question_text
        if idx_q.instructions:
            generation_question = f"INSTRUCTION: {idx_q.instructions}\nQUESTION: {idx_q.question_text}"

        for attempt in range(max_retries):
            try:
                answer_text = generate_answer(context, generation_question)
                break  # Success
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "rate_limit" in error_msg.lower():
                    if attempt < max_retries - 1:
                        sleep_time = (2 ** attempt) * 2  # Exponential backoff: 2s, 4s, 8s, 16s...
                        print(f"Rate limit hit for question {idx_q.id}. Retrying in {sleep_time} seconds... (Attempt {attempt+1}/{max_retries})")
                        time.sleep(sleep_time)
                        continue
                    else:
                        print(f"Max retries reached for Groq on question {idx_q.id}. Switching to Gemini fallback.")
                        groq_failed = True
                else:
                    print(f"Failed to generate answer for question {idx_q.id} (non-429 Groq error): {error_msg}. Switching to Gemini fallback.")
                    groq_failed = True
                    break
                
        if groq_failed:
            try:
                print(f"Attempting Gemini fallback for question {idx_q.id}...")
                answer_text = generate_answer_gemini(context, generation_question)
                print(f"Gemini fallback successful for question {idx_q.id}")
            except Exception as gem_e:
                print(f"Gemini fallback also failed for question {idx_q.id}: {type(gem_e).__name__}: {gem_e}")
                answer_text = json.dumps({
                    "yes_no": "N/A",
                    "answer": f"Failed to generate answer due to repeated API errors. Groq: {error_msg if 'error_msg' in locals() else 'Unknown'}. Gemini: {type(gem_e).__name__}.",
                    "is_question": True
                })

        if not answer_text:
             answer_text = json.dumps({
                 "yes_no": "N/A", 
                 "answer": "Failed to generate answer due to repeated API errors.",
                 "is_question": True
             })

        # Parse JSON response
        try:
            res_data = json.loads(answer_text)
            yes_no = res_data.get("yes_no", "N/A")
            final_answer = res_data.get("answer", "")
            is_question = res_data.get("is_question", True)
        except Exception as parse_e:
            print(f"Failed to parse LLM response as JSON: {parse_e}")
            yes_no = "N/A"
            final_answer = answer_text
            is_question = True

        # Find or create Answer
        answer = db.query(Answer).filter(Answer.question_id == idx_q.id).first()
        if not answer:
            answer = Answer(question_id=idx_q.id, project_id=project_id, status="GENERATED")
            db.add(answer)
            db.flush()
        
        # Create new version
        version = AnswerVersion(
            answer_id=answer.id,
            source_type="AI",
            answer_text=final_answer,
            answerability=yes_no # Storing Yes/No/N/A here
        )
        db.add(version)
        db.flush()

        # Add Citations
        if results and results['ids'] and len(results['ids'][0]) > 0:
            for i in range(len(results['ids'][0])):
                metadata = results['metadatas'][0][i]
                chunk_id = metadata.get('chunk_id')
                page_num = metadata.get('page')
                
                citation = Citation(
                    answer_version_id=version.id,
                    document_chunk_id=chunk_id,
                    citation_text=results['documents'][0][i],
                    relevance_score=1.0, # Or extract from results if available
                    page_number=page_num
                )
                db.add(citation)
        
        answer.current_version_id = version.id
        answer.status = "GENERATED"
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print(f"Error processing question {idx_q.id}: {e}")
        return False


def run_generation_job(job_id: int, project_id: int):
    # Need to instantiate DB session for the main thread to read project
    db_main: Session = SessionLocal()
    update_job_status(db_main, job_id, JobStatus.RUNNING, 0)
    
    try:
        project = db_main.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise Exception("Project not found")
            
        project_documents = project.documents.copy() if project.documents else []
        
        # Get all questions for this project
        questions = db_main.query(Question).filter(Question.project_id == project_id).all()
        if not questions:
            update_job_status(db_main, job_id, JobStatus.COMPLETED, 100)
            return

        collection = get_collection()
        total_q = len(questions)
        completed_q = 0
        
        # Close the main DB session before threading to avoid sharing it across threads
        db_main.close()

        # Using ThreadPoolExecutor for concurrent processing
        # Adjust max_workers based on API limits. Too high might trigger 429s instantly.
        max_workers = 2 
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # We must create a new Session for each thread
            future_to_q = {}
            for q in questions:
                # To be safe with SQLAlchemy, we pass a fresh DB session or create one inside
                # It's cleaner to create the session inside the submitted function, but we wrap it here
                def thread_worker(proj_id, idx_question, docs, col):
                    db_thread = SessionLocal()
                    try:
                        return process_single_question(db_thread, proj_id, idx_question, docs, col)
                    finally:
                        db_thread.close()

                future = executor.submit(thread_worker, project_id, q, project_documents, collection)
                future_to_q[future] = q
                time.sleep(1) # Small delay to avoid burst rate limits
            
            # As each future completes, update progress
            for future in concurrent.futures.as_completed(future_to_q):
                q = future_to_q[future]
                try:
                    success = future.result()
                    if success:
                         completed_q += 1
                except Exception as exc:
                    print(f"Question {q.id} generated an exception: {exc}")
                finally:
                    # Update progress using a fresh short-lived session
                    db_progress = SessionLocal()
                    try:
                        progress = int((completed_q / total_q) * 100)
                        update_job_status(db_progress, job_id, JobStatus.RUNNING, progress=progress)
                    finally:
                        db_progress.close()

        # Final Update
        db_final = SessionLocal()
        try:
             update_job_status(db_final, job_id, JobStatus.COMPLETED, 100)
        finally:
             db_final.close()
             
    except Exception as e:
        # If the whole job fails early
        db_fail = SessionLocal()
        try:
             update_job_status(db_fail, job_id, JobStatus.FAILED, 0, str(e))
        except Exception as inner_e:
             print(f"Could not update job status after failure: {inner_e}")
        finally:
             db_fail.close()
        print(traceback.format_exc())
    finally:
        pass # All DB sessions managed individually
