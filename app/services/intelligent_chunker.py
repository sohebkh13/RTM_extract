import asyncio
import json
import tiktoken
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

from app.config import settings
from app.utils.logger import get_logger
from app.utils.exceptions import AIAnalysisError
from app.utils.exceptions import AIAnalysisError

logger = get_logger(__name__)

class IntelligentChunker:
    """
    Handles intelligent chunking of Excel data with context preservation
    and dynamic token counting using tiktoken.
    """
    
    def __init__(self):
        self.logger = logger
        # Use tiktoken for accurate token counting
        try:
            self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")  # Compatible with most LLMs
        except Exception as e:
            self.logger.warning(f"Could not load tiktoken encoder, using fallback: {e}")
            self.tokenizer = None
            
        # Chunk settings from config
        self.max_tokens_per_chunk = settings.MAX_TOKENS_PER_CHUNK
        self.token_overlap = settings.TOKEN_OVERLAP
        
        # Prompt overhead estimation (for detailed prompt)
        self.prompt_overhead_tokens = 500  # Updated for larger context usage
        self.effective_chunk_limit = self.max_tokens_per_chunk - self.prompt_overhead_tokens
    
    def count_tokens(self, text: str) -> int:
        """
        Accurate token counting using tiktoken
        """
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text))
            except Exception as e:
                self.logger.warning(f"Tiktoken encoding failed, using fallback: {e}")
                # Fallback to character-based estimation
                return len(text) // 3  # More conservative than 2.5
        else:
            # Fallback calculation
            return len(text) // 3
    
    def create_sheet_chunks(self, sheet_data: Dict, is_focus_sheet: bool = False) -> List[Dict]:
        """
        Create intelligent chunks from sheet data with context preservation
        
        Args:
            sheet_data: Dict containing sheet info and requirements
            is_focus_sheet: Whether this is the user-selected focus sheet
            
        Returns:
            List of chunk dictionaries with context and metadata
        """
        try:
            sheet_name = sheet_data.get('sheet_name', 'Unknown')
            requirements = sheet_data.get('requirements', [])
            
            if not requirements:
                self.logger.warning(f"No requirements found in sheet: {sheet_name}")
                return []
            
            self.logger.info(f"🔄 Creating chunks for sheet '{sheet_name}' ({len(requirements)} requirements)")
            self.logger.info(f"📊 Focus sheet: {'Yes' if is_focus_sheet else 'No'}")
            
            # Validate requirement count for consistency with enhanced detection
            validated_count = len([req for req in requirements if not req.get('is_edge_case', False)])
            edge_case_count = len([req for req in requirements if req.get('is_edge_case', False)])
            if edge_case_count > 0:
                self.logger.info(f"📋 Content breakdown: {validated_count} validated, {edge_case_count} edge cases included")
            
            # With increased token limits and enhanced validation, optimize chunk sizes
            # Focus sheet: detailed analysis but larger chunks for efficiency  
            # Regular sheets: much larger chunks for speed
            target_requirements_per_chunk = 20 if is_focus_sheet else 30
            
            chunks = []
            current_chunk = []
            current_chunk_tokens = 0
            chunk_index = 0
            
            for i, req in enumerate(requirements):
                # Calculate tokens for this requirement
                req_text = self._format_requirement_for_chunking(req)
                req_tokens = self.count_tokens(req_text)
                
                # Check if adding this requirement would exceed limit
                if (current_chunk_tokens + req_tokens > self.effective_chunk_limit 
                    and current_chunk):
                    
                    # Create chunk from current batch
                    chunk = self._create_chunk_object(
                        current_chunk, 
                        sheet_data, 
                        chunk_index,
                        is_focus_sheet
                    )
                    chunks.append(chunk)
                    
                    # Start new chunk with overlap from previous
                    overlap_reqs = self._get_overlap_requirements(current_chunk)
                    current_chunk = overlap_reqs + [req]
                    current_chunk_tokens = sum(
                        self.count_tokens(self._format_requirement_for_chunking(r)) 
                        for r in current_chunk
                    )
                    chunk_index += 1
                else:
                    # Add to current chunk
                    current_chunk.append(req)
                    current_chunk_tokens += req_tokens
                    
                    # Also create chunk if we've reached target requirement count
                    if len(current_chunk) >= target_requirements_per_chunk:
                        chunk = self._create_chunk_object(
                            current_chunk, 
                            sheet_data, 
                            chunk_index,
                            is_focus_sheet
                        )
                        chunks.append(chunk)
                        
                        # Start new chunk with overlap
                        overlap_reqs = self._get_overlap_requirements(current_chunk)
                        current_chunk = overlap_reqs
                        current_chunk_tokens = sum(
                            self.count_tokens(self._format_requirement_for_chunking(r)) 
                            for r in current_chunk
                        )
                        chunk_index += 1
            
            # Add final chunk if not empty
            if current_chunk:
                chunk = self._create_chunk_object(
                    current_chunk, 
                    sheet_data, 
                    chunk_index,
                    is_focus_sheet
                )
                chunks.append(chunk)
            
            self.logger.info(f"✅ Created {len(chunks)} chunks for sheet '{sheet_name}'")
            for i, chunk in enumerate(chunks):
                self.logger.info(f"  Chunk {i+1}: {len(chunk['requirements'])} requirements, ~{chunk['estimated_tokens']} tokens")
            
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error creating chunks for sheet {sheet_data.get('sheet_name', 'Unknown')}: {str(e)}")
            raise AIAnalysisError(f"Chunking failed: {str(e)}")
    
    def _format_requirement_for_chunking(self, requirement: Dict) -> str:
        """
        Format requirement for token counting
        """
        parts = []
        if requirement.get('original_id'):
            parts.append(f"ID: {requirement['original_id']}")
        if requirement.get('description'):
            parts.append(f"Description: {requirement['description']}")
        if requirement.get('source'):
            parts.append(f"Source: {requirement['source']}")
        if requirement.get('additional_info'):
            parts.append(f"Info: {requirement['additional_info']}")
            
        return " | ".join(parts)
    
    def _get_overlap_requirements(self, current_chunk: List[Dict]) -> List[Dict]:
        """
        Get requirements for overlap between chunks to maintain context
        """
        if len(current_chunk) <= 2:
            return []
        
        # Take last 1-2 requirements as overlap
        overlap_count = min(2, len(current_chunk) - 1)
        return current_chunk[-overlap_count:]
    
    def _create_chunk_object(self, requirements: List[Dict], sheet_data: Dict, 
                           chunk_index: int, is_focus_sheet: bool) -> Dict:
        """
        Create a structured chunk object with metadata
        """
        # Calculate actual tokens for this chunk
        total_text = ""
        for req in requirements:
            total_text += self._format_requirement_for_chunking(req) + "\n"
        
        estimated_tokens = self.count_tokens(total_text)
        
        chunk = {
            'chunk_id': f"{sheet_data.get('sheet_name', 'sheet')}_{chunk_index}",
            'sheet_name': sheet_data.get('sheet_name'),
            'chunk_index': chunk_index,
            'is_focus_sheet': is_focus_sheet,
            'requirements': requirements,
            'estimated_tokens': estimated_tokens,
            'requirement_count': len(requirements),
            'has_overlap': chunk_index > 0,  # All chunks except first have overlap
            'metadata': {
                'sheet_total_requirements': len(sheet_data.get('requirements', [])),
                'start_row': requirements[0].get('row_number') if requirements else None,
                'end_row': requirements[-1].get('row_number') if requirements else None,
                'original_sheet_columns': sheet_data.get('detected_columns', {}),
            }
        }
        
        return chunk
    
    def estimate_total_processing_time(self, all_chunks: List[Dict]) -> float:
        """
        Estimate total processing time including rate limiting delays
        """
        total_chunks = len(all_chunks)
        # 3 seconds delay between requests + ~2 seconds processing per request
        estimated_seconds = (total_chunks * 3) + (total_chunks * 2)
        return estimated_seconds / 60  # Convert to minutes
    
    def validate_chunks(self, chunks: List[Dict], original_requirements: List[Dict]) -> bool:
        """
        Validate that chunking preserved all requirements
        """
        try:
            # Count total unique requirements across all chunks
            all_chunk_req_ids = set()
            for chunk in chunks:
                for req in chunk['requirements']:
                    req_id = req.get('original_id') or req.get('description', '')[:50]
                    all_chunk_req_ids.add(req_id)
            
            # Count original requirements
            original_req_ids = set()
            for req in original_requirements:
                req_id = req.get('original_id') or req.get('description', '')[:50]
                original_req_ids.add(req_id)
            
            # Check for missing requirements
            missing = original_req_ids - all_chunk_req_ids
            if missing:
                self.logger.error(f"❌ Chunking lost {len(missing)} requirements")
                return False
            
            # Check for extra requirements (shouldn't happen but good to verify)
            extra = all_chunk_req_ids - original_req_ids
            if extra:
                self.logger.warning(f"⚠️ Chunking added {len(extra)} unexpected requirements")
            
            self.logger.info(f"✅ Chunk validation passed: {len(all_chunk_req_ids)} requirements preserved")
            return True
            
        except Exception as e:
            self.logger.error(f"Chunk validation failed: {str(e)}")
            return False