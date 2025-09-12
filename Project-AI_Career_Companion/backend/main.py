from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import mlflow
import traceback
from models.schemas import (
    SkillGapRequest, CareerPlanRequest,
    ReviewRequest, MentorRequest
)
from services import openai_service, mlflow_service, telemetry, keyvault_service
from utils.memory import session_memory
from utils.logger_config import get_logger, RequestLogger

# Initialize logger
logger = get_logger("career_ai_companion")

# Initialize FastAPI app
app = FastAPI(
    title="AI Career Companion", 
    version="0.1.0",
    description="AI-powered career guidance and mentorship platform"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Unhandled exception in {request.method} {request.url}: {str(exc)}",
        extra={
            'endpoint': str(request.url),
            'method': request.method,
            'exception_type': type(exc).__name__
        },
        exc_info=True
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
            "request_id": getattr(request.state, 'request_id', 'unknown')
        }
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    try:
        logger.info("Starting AI Career Companion Backend")
        
        # Initialize MLflow
        logger.info("Initializing MLflow tracking")
        
        # Pre-load commonly used prompts
        prompt_files = {
            "skill_gap_analysis": "prompts/skill_gap_prompt.txt",
            "career_plan_generation": "prompts/career_plan_prompt.txt",
            "performance_review": "prompts/review_prompt.txt",
            "mentor_simulation": "prompts/mentor_prompt.txt"
        }
        
        for prompt_name, file_path in prompt_files.items():
            try:
                mlflow_service.load_prompt_with_fallback(prompt_name, file_path)
                logger.info(f"Successfully loaded/registered prompt: {prompt_name}")
            except Exception as e:
                logger.warning(f"Failed to load prompt {prompt_name}: {e}")
        
        logger.info("AI Career Companion Backend started successfully")
        
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
        raise

# Health Check
@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        with RequestLogger(logger, "/health"):
            telemetry.log_event("health_check")
            logger.info("Health check requested")
            
            return {
                "status": "ok", 
                "message": "AI Career Companion Backend is running",
                "version": "0.1.0"
            }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Health check failed")

# Skills Gap Analysis
@app.post("/analyze_skills")
def analyze_skills(req: SkillGapRequest):
    """Analyze skills gap for career development"""
    try:
        with RequestLogger(logger, "/analyze_skills", req.dict()):
            logger.info("Starting skills gap analysis")
            print(req.dict())
            
            # Load prompt with fallback
            prompt_template = mlflow_service.load_prompt(
                "skill_gap_analysis2")
            
            # Build prompt
            prompt = prompt_template.format(**req.dict())
            logger.info("Prompt built successfully for skills analysis")
            print(prompt)
            
            # Call OpenAI
            response = openai_service.call_openai(prompt)
            logger.info("Received response from OpenAI for skills analysis")
            print(response)
            
            # Log to MLflow
            mlflow_service.log_prompt_interaction("analyze_skills", prompt, response)
            
            # Log telemetry
            telemetry.log_event("analyze_skills_completed")
            
            logger.info("Skills gap analysis completed successfully")
            return {"analysis": response}
            
    except Exception as e:
        logger.error(f"Skills gap analysis failed: {e}", exc_info=True)
        telemetry.log_event("analyze_skills_failed")
        raise HTTPException(
            status_code=500, 
            detail=f"Skills analysis failed: {str(e)}"
        )

# Career Plan Generator
@app.post("/generate_plan")
def generate_plan(req: CareerPlanRequest):
    """Generate personalized career development plan"""
    try:
        with RequestLogger(logger, "/generate_plan", req.dict()):
            logger.info("Starting career plan generation")
            
            # Load prompt with fallback
            prompt_template = mlflow_service.load_prompt(
                "career_plan_generation"
            )
            
            # Build prompt
            prompt = prompt_template.format(**req)
            logger.info("Prompt built successfully for career plan generation")
            
            # Call OpenAI
            response = openai_service.call_openai(prompt)
            logger.info("Received response from OpenAI for career plan generation")
            
            # Log to MLflow
            mlflow_service.log_prompt_interaction("generate_plan", prompt, response)
            
            # Log telemetry
            telemetry.log_event("generate_plan_completed")
            
            logger.info("Career plan generation completed successfully")
            return {"plan": response}
            
    except Exception as e:
        logger.error(f"Career plan generation failed: {e}", exc_info=True)
        telemetry.log_event("generate_plan_failed")
        raise HTTPException(
            status_code=500, 
            detail=f"Career plan generation failed: {str(e)}"
        )

# Performance Review Draft
@app.post("/performance_review")
def performance_review(req: ReviewRequest):
    """Generate performance review draft"""
    try:
        with RequestLogger(logger, "/performance_review", req.dict()):
            logger.info("Starting performance review generation")
            
            # Load prompt with fallback
            prompt_template = mlflow_service.load_prompt(
                "performance_review")
            
            # Build prompt
            prompt = prompt_template.format(**req)
            logger.info("Prompt built successfully for performance review")
            
            # Call OpenAI
            response = openai_service.call_openai(prompt)
            logger.info("Received response from OpenAI for performance review")
            
            # Log to MLflow
            mlflow_service.log_prompt_interaction("performance_review", prompt, response)
            
            # Log telemetry
            telemetry.log_event("performance_review_completed")
            
            logger.info("Performance review generation completed successfully")
            return {"review": response}
            
    except Exception as e:
        logger.error(f"Performance review generation failed: {e}", exc_info=True)
        telemetry.log_event("performance_review_failed")
        raise HTTPException(
            status_code=500, 
            detail=f"Performance review generation failed: {str(e)}"
        )

# Mentorship Simulation
@app.post("/mentor_simulation")
def mentor_simulation(req: MentorRequest):
    """Simulate mentorship conversation"""
    try:
        with RequestLogger(logger, "/mentor_simulation", req.dict()):
            logger.info("Starting mentor simulation")
            
            # Load prompt with fallback
            prompt_template = mlflow_service.load_prompt(
                "mentor_simulation",
            )
            
            # Build prompt
            prompt = prompt_template.format(**req)
            logger.info("Prompt built successfully for mentor simulation")
            
            # Call OpenAI
            response = openai_service.call_openai(prompt)
            logger.info("Received response from OpenAI for mentor simulation")
            
            # Log to MLflow
            mlflow_service.log_prompt_interaction("mentor_simulation", prompt, response)
            
            # Log telemetry
            telemetry.log_event("mentor_simulation_completed")
            
            logger.info("Mentor simulation completed successfully")
            return {"mentor_response": response}
            
    except Exception as e:
        logger.error(f"Mentor simulation failed: {e}", exc_info=True)
        telemetry.log_event("mentor_simulation_failed")
        raise HTTPException(
            status_code=500, 
            detail=f"Mentor simulation failed: {str(e)}"
        )

# Additional utility endpoints
@app.get("/logs/health")
def logs_health():
    """Check logging system health"""
    try:
        logger.info("Logging system health check")
        return {
            "status": "ok",
            "message": "Logging system is operational",
            "logger_name": logger.name,
            "log_level": logger.level
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Logging system error: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting server with uvicorn")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")