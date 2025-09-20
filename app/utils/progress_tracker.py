"""
Progress tracking utility for batch processing
"""
import time
from typing import Dict, Optional
from dataclasses import dataclass
from loguru import logger

@dataclass
class BatchProgress:
    file_id: str
    total_batches: int = 0
    current_batch: int = 0
    completed_batches: int = 0
    status: str = "pending"  # pending, processing, completed, failed
    start_time: float = 0
    last_update: float = 0
    current_activity: str = ""
    recent_activities: list = None
    
    def __post_init__(self):
        if self.recent_activities is None:
            self.recent_activities = []
    
    def to_dict(self) -> dict:
        return {
            "file_id": self.file_id,
            "total_batches": self.total_batches,
            "current_batch": self.current_batch,
            "completed_batches": self.completed_batches,
            "status": self.status,
            "start_time": self.start_time,
            "last_update": self.last_update,
            "current_activity": self.current_activity,
            "recent_activities": self.recent_activities[-10:],  # Keep last 10 activities
            "elapsed_time": time.time() - self.start_time if self.start_time > 0 else 0,
            "progress_percent": self._calculate_progress_percent()
        }
    
    def _calculate_progress_percent(self) -> int:
        if self.total_batches <= 0:
            return 0
        if self.status == "completed":
            return 100
        
        # Calculate based on completed batches (20-90% range for processing)
        base_progress = 20
        processing_range = 70
        
        if self.total_batches > 0:
            batch_progress = (self.completed_batches / self.total_batches) * processing_range
            return min(int(base_progress + batch_progress), 90)
        
        return base_progress

class ProgressTracker:
    """Singleton progress tracker for batch processing"""
    
    _instance = None
    _progress_store: Dict[str, BatchProgress] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._progress_store = {}
        return cls._instance
    
    def start_processing(self, file_id: str, total_batches: int) -> BatchProgress:
        """Start tracking progress for a file"""
        progress = BatchProgress(
            file_id=file_id,
            total_batches=total_batches,
            status="processing",
            start_time=time.time(),
            last_update=time.time(),
            current_activity="Starting batch processing..."
        )
        
        self._progress_store[file_id] = progress
        logger.info(f"📊 Started progress tracking for {file_id}: {total_batches} batches")
        
        return progress
    
    def update_batch_start(self, file_id: str, batch_number: int, batch_size: int, estimated_tokens: int):
        """Update progress when starting a new batch"""
        if file_id not in self._progress_store:
            return
        
        progress = self._progress_store[file_id]
        progress.current_batch = batch_number
        progress.last_update = time.time()
        progress.current_activity = f"Processing batch {batch_number}/{progress.total_batches} ({batch_size} requirements)"
        
        activity = f"🔄 Batch {batch_number}: {batch_size} requirements (~{estimated_tokens:,} tokens)"
        progress.recent_activities.append(activity)
        
        logger.info(f"📊 Updated progress: {file_id} - Batch {batch_number}/{progress.total_batches}")
    
    def update_batch_complete(self, file_id: str, batch_number: int, success: bool):
        """Update progress when a batch completes"""
        if file_id not in self._progress_store:
            return
        
        progress = self._progress_store[file_id]
        
        if success:
            progress.completed_batches = batch_number
            activity = f"✅ Batch {batch_number} completed successfully"
        else:
            activity = f"⚠️ Batch {batch_number} failed, using fallback"
        
        progress.recent_activities.append(activity)
        progress.last_update = time.time()
        
        logger.info(f"📊 Batch {batch_number} {'completed' if success else 'failed'}: {file_id}")
    
    def update_waiting(self, file_id: str, wait_seconds: int):
        """Update progress during waiting period"""
        if file_id not in self._progress_store:
            return
        
        progress = self._progress_store[file_id]
        progress.current_activity = f"⏳ Waiting {wait_seconds}s before next batch..."
        progress.recent_activities.append(f"⏳ Rate limit delay: {wait_seconds} seconds")
        progress.last_update = time.time()
    
    def complete_processing(self, file_id: str, success: bool = True):
        """Mark processing as complete"""
        if file_id not in self._progress_store:
            return
        
        progress = self._progress_store[file_id]
        progress.status = "completed" if success else "failed"
        progress.current_activity = "✅ Analysis complete!" if success else "❌ Analysis failed"
        progress.last_update = time.time()
        
        if success:
            progress.recent_activities.append("🎉 All batches processed successfully!")
        
        logger.info(f"📊 Processing {'completed' if success else 'failed'}: {file_id}")
    
    def get_progress(self, file_id: str) -> Optional[dict]:
        """Get current progress for a file"""
        if file_id not in self._progress_store:
            return None
        
        return self._progress_store[file_id].to_dict()
    
    def cleanup_progress(self, file_id: str):
        """Clean up progress tracking for a file"""
        if file_id in self._progress_store:
            del self._progress_store[file_id]
            logger.info(f"📊 Cleaned up progress tracking for {file_id}")
    
    def get_all_active_progress(self) -> Dict[str, dict]:
        """Get all active progress tracking"""
        return {fid: progress.to_dict() for fid, progress in self._progress_store.items()}

# Global instance
progress_tracker = ProgressTracker()
