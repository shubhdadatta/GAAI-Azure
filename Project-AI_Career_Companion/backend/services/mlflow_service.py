
import mlflow
import os
from typing import Optional
from .keyvault_service import get_secret
from utils.logger_config import get_logger

# Initialize logger
logger = get_logger(__name__)

# Initialize MLflow
try:
    MLFLOW_TRACKING_URI = get_secret("MLflowTrackingURI")
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    logger.info(f"MLflow tracking URI set successfully: {MLFLOW_TRACKING_URI}")
except Exception as e:
    logger.error(f"Failed to initialize MLflow tracking URI: {e}", exc_info=True)
    raise

def register_prompt(prompt_name: str, prompt: str, model: str = 'gpt-4o-mini') -> str:
    """
    Register a new prompt in MLflow
    
    Args:
        prompt_name: Name of the prompt to register
        prompt: The actual prompt template
        model: Model name for tagging
    
    Returns:
        Success message
    """
    try:
        logger.info(f"Starting prompt registration for: {prompt_name}")
        
        prompt_obj = mlflow.genai.register_prompt(
            name=prompt_name, 
            template=prompt,
            commit_message="Prompt Registration",
            tags={
                "author": "Anshu Pandey",
                "task": "Content Generation",
                "language": "en",
                'llm': model
            }
        )
        
        logger.info(f"Prompt registered successfully: '{prompt_obj.name}' (version {prompt_obj.version})")
        
        # Deploy prompt to production
        mlflow.set_prompt_alias(prompt_name, alias="production", version=1)
        logger.info(f"Prompt deployed to production: {prompt_name}")
        
        return f"Prompt '{prompt_name}' successfully registered and deployed"
        
    except Exception as e:
        logger.error(f"Failed to register prompt '{prompt_name}': {e}", exc_info=True)
        raise

def load_prompt(prompt_name: str, alias: str = 'production'):
    """
    Load a prompt from MLflow registry
    
    Args:
        prompt_name: Name of the prompt to load
        alias: Alias to load (default: production)
    
    Returns:
        Loaded prompt object
    """
    try:
        path = f"prompts:/{prompt_name}@{alias}"
        logger.info(f"Attempting to load prompt from path: {path}")
        
        prompt = mlflow.genai.load_prompt(name_or_uri=path)
        logger.info(f"Prompt loaded successfully: {prompt_name}")
        
        return prompt
        
    except Exception as e:
        logger.error(f"Failed to load prompt '{prompt_name}' with alias '{alias}': {e}", exc_info=True)
        raise

def load_prompt_with_fallback(prompt_name: str, prompt_file_path: str, alias: str = 'production'):
    """
    Load prompt from MLflow, with fallback to register and retry if not found
    
    Args:
        prompt_name: Name of the prompt to load
        prompt_file_path: Path to the prompt file for registration fallback
        alias: Alias to load (default: production)
    
    Returns:
        Loaded prompt object
    """
    try:
        logger.info(f"Attempting to load prompt: {prompt_name}")
        return load_prompt(prompt_name, alias)
        
    except Exception as load_error:
        logger.warning(f"Failed to load prompt '{prompt_name}': {load_error}")
        logger.info(f"Attempting to register prompt from file: {prompt_file_path}")
        
        try:
            # Read prompt from file
            if not os.path.exists(prompt_file_path):
                error_msg = f"Prompt file not found: {prompt_file_path}"
                logger.error(error_msg)
                raise FileNotFoundError(error_msg)
            
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                prompt_content = f.read()
            
            logger.info(f"Read prompt content from file: {prompt_file_path}")
            
            # Register the prompt
            register_result = register_prompt(prompt_name, prompt_content)
            logger.info(f"Registration result: {register_result}")
            
            # Retry loading after registration
            logger.info(f"Retrying prompt load after registration: {prompt_name}")
            return load_prompt(prompt_name, alias)
            
        except Exception as register_error:
            logger.error(f"Failed to register and load prompt '{prompt_name}': {register_error}", exc_info=True)
            raise

def log_prompt_interaction(endpoint: str, prompt: str, response: str, model: str = 'gpt-4o-mini'):
    """
    Log prompt interaction to MLflow
    
    Args:
        endpoint: API endpoint name
        prompt: The prompt used
        response: The response received
        model: Model used for generation
    """
    try:
        logger.info(f"Logging prompt interaction for endpoint: {endpoint}")
        
        with mlflow.start_run(run_name=f"{endpoint}_run"):
            mlflow.log_param("endpoint", endpoint)
            mlflow.log_param("model", model)
            mlflow.log_param("prompt_length", len(prompt))
            mlflow.log_param("response_length", len(response))
            
            # Log as artifacts for better organization
            mlflow.log_text(prompt, f"prompt_{endpoint}.txt")
            mlflow.log_text(response, f"response_{endpoint}.txt")
            
        logger.info(f"Prompt interaction logged successfully for: {endpoint}")
        
    except Exception as e:
        logger.error(f"Failed to log prompt interaction for '{endpoint}': {e}", exc_info=True)
        # Don't raise here as logging failure shouldn't break the main flow