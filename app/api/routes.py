from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any
import os

from app.models.responses import FileUploadResponse, AnalysisRequest, AnalysisResponse
from app.services.file_handler import FileHandler
from app.services.rtm_generator import RTMGenerator
from app.api.dependencies import get_file_handler, get_rtm_generator
from app.utils.logger import get_logger
from app.utils.exceptions import RTMException

logger = get_logger(__name__)
router = APIRouter()

@router.post("/upload", response_model=FileUploadResponse)
async def upload_excel_file(
    file: UploadFile = File(...),
    file_handler: FileHandler = Depends(get_file_handler)
):
    """
    Upload Excel file for processing
    - Validates file type and size
    - Returns file ID for subsequent operations
    """
    try:
        logger.info(f"Uploading file: {file.filename}")
        
        # Validate file type
        if not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only Excel files (.xlsx, .xls) are allowed."
            )
        
        # Save the uploaded file
        file_path = await file_handler.save_uploaded_file(file)
        
        # Get file info
        file_info = file_handler.get_file_info(file_path)
        file_id = file_handler.get_file_id_from_path(file_path)
        
        response = FileUploadResponse(
            message="File uploaded successfully",
            file_id=file_id,
            file_name=file.filename,
            file_size=file_info['file_size']
        )
        
        logger.info(f"File uploaded successfully: {file.filename} (ID: {file_id})")
        return response
        
    except RTMException as e:
        logger.error(f"RTM error during upload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during file upload")

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_requirements(
    request: AnalysisRequest,
    file_handler: FileHandler = Depends(get_file_handler),
    rtm_generator: RTMGenerator = Depends(get_rtm_generator)
):
    """
    Process uploaded Excel file and generate RTM
    - Reads all sheets with focus on "2- tool Requirements"
    - Uses AI to classify and analyze requirements
    - Generates formatted RTM Excel output
    """
    try:
        logger.info(f"Analyzing requirements for file ID: {request.file_id}")
        
        # Find the uploaded file
        file_path = file_handler.find_file_by_id(request.file_id)
        file_info = file_handler.get_file_info(file_path)
        
        # Process the file and generate RTM
        rtm_output = await rtm_generator.process_excel_to_rtm(
            file_path=file_path,
            file_name=file_info['file_name']
        )
        
        # Prepare response
        response = AnalysisResponse(
            status="completed",
            rtm_file_path=rtm_output.file_path,
            analysis_summary={
                "requirements_processed": rtm_output.requirements_count,
                "processing_time_seconds": rtm_output.processing_time,
                "source_file": rtm_output.source_file_name,
                "generated_at": rtm_output.generated_at.isoformat(),
                "statistics": rtm_output.summary_statistics
            },
            requirements_found=rtm_output.requirements_count,
            processing_details={
                "focus_sheet": request.focus_sheet,
                "include_all_sheets": request.include_all_sheets,
                "output_file": os.path.basename(rtm_output.file_path)
            }
        )
        
        logger.info(f"Analysis completed successfully. Generated RTM: {rtm_output.file_path}")
        return response
        
    except RTMException as e:
        logger.error(f"RTM error during analysis: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during analysis")

@router.get("/download/{file_id}")
async def download_rtm(
    file_id: str,
    file_handler: FileHandler = Depends(get_file_handler)
):
    """
    Download generated RTM Excel file
    """
    try:
        logger.info(f"Download requested for file ID: {file_id}")
        
        # Look for RTM file in output directory
        output_files = list(file_handler.output_dir.glob(f"RTM_*{file_id}*.xlsx"))
        if not output_files:
            # Try to find any RTM file that might match
            output_files = list(file_handler.output_dir.glob("RTM_*.xlsx"))
            if not output_files:
                raise HTTPException(status_code=404, detail="RTM file not found")
        
        # Get the most recent file
        rtm_file = max(output_files, key=lambda f: f.stat().st_mtime)
        
        if not rtm_file.exists():
            raise HTTPException(status_code=404, detail="RTM file not found")
        
        logger.info(f"Serving RTM file: {rtm_file}")
        return FileResponse(
            path=str(rtm_file),
            filename=rtm_file.name,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during download: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during download")

@router.get("/status/{file_id}")
async def get_processing_status(
    file_id: str,
    file_handler: FileHandler = Depends(get_file_handler)
):
    """
    Check processing status for long-running operations with batch progress
    """
    try:
        # Check if original file exists
        try:
            file_path = file_handler.find_file_by_id(file_id)
            file_exists = True
        except:
            file_exists = False
        
        # Check if RTM file exists
        output_files = list(file_handler.output_dir.glob(f"RTM_*{file_id}*.xlsx"))
        rtm_exists = len(output_files) > 0
        
        # Get batch progress from progress tracker
        batch_progress = get_progress_from_tracker(file_id)
        
        if rtm_exists:
            status = "completed"
            rtm_file = max(output_files, key=lambda f: f.stat().st_mtime)
            message = f"RTM generation completed. File: {rtm_file.name}"
            progress_percent = 100
        elif file_exists and batch_progress:
            status = batch_progress.get('status', 'processing')
            current_batch = batch_progress.get('current_batch', 0)
            total_batches = batch_progress.get('total_batches', 0)
            completed_batches = batch_progress.get('completed_batches', 0)
            
            if status == "processing":
                message = f"Processing batch {current_batch}/{total_batches} (completed: {completed_batches})"
            else:
                message = batch_progress.get('current_activity', 'Processing...')
                
            progress_percent = batch_progress.get('progress_percent', 20)
        elif file_exists:
            status = "uploaded"
            message = "File uploaded, ready for analysis"
            progress_percent = 0
        else:
            status = "not_found"
            message = "File not found"
            progress_percent = 0
        
        return {
            "file_id": file_id,
            "status": status,
            "message": message,
            "file_exists": file_exists,
            "rtm_exists": rtm_exists,
            "progress_percent": progress_percent,
            "batch_info": batch_progress or {}
        }
        
    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during status check")

def get_progress_from_tracker(file_id: str) -> dict:
    """Get batch progress from progress tracker"""
    try:
        from app.utils.progress_tracker import progress_tracker
        
        progress_data = progress_tracker.get_progress(file_id)
        if progress_data:
            return progress_data
        
        return {}
        
    except Exception as e:
        logger.debug(f"Error getting progress from tracker: {str(e)}")
        return {}

@router.get("/health")
async def health_check():
    """
    API health check endpoint
    """
    return {
        "status": "healthy",
        "message": "RTM AI Agent is running",
        "version": "1.0.0"
    }

@router.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "RTM AI Agent API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "POST /upload - Upload Excel file",
            "analyze": "POST /analyze - Analyze requirements and generate RTM",
            "download": "GET /download/{file_id} - Download generated RTM",
            "status": "GET /status/{file_id} - Check processing status",
            "health": "GET /health - Health check"
        }
    }
