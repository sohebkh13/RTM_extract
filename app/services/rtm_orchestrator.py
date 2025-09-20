import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from app.config import settings
from app.utils.logger import get_logger
from app.utils.exceptions import RTMProcessingError
from app.services.dynamic_excel_processor import DynamicExcelProcessor
from app.services.groq_analyzer import GroqAnalyzer
from app.services.rtm_output_generator import RTMOutputGenerator
from app.models.rtm import RTMOutput

logger = get_logger(__name__)

class RTMOrchestrator:
    """
    Main orchestrator that coordinates the entire RTM generation process:
    1. Dynamic Excel processing
    2. Focus sheet selection
    3. Intelligent AI analysis with chunking
    4. 3-sheet RTM output generation
    """
    
    def __init__(self):
        self.logger = logger
        self.excel_processor = DynamicExcelProcessor()
        self.groq_analyzer = GroqAnalyzer()
        self.rtm_generator = RTMOutputGenerator()
    
    async def process_excel_to_rtm(self, file_path: str, focus_sheet_name: str) -> RTMOutput:
        """
        Complete RTM processing pipeline
        """
        try:
            start_time = datetime.now()
            self.logger.info("🚀 Starting complete RTM processing pipeline")
            self.logger.info(f"📂 Input file: {Path(file_path).name}")
            self.logger.info(f"🎯 Focus sheet: {focus_sheet_name}")
            
            # Phase 1: Load and analyze Excel file structure
            self.logger.info("📋 Phase 1: Loading and analyzing Excel structure")
            file_info = self.excel_processor.load_excel_file(file_path)
            
            if focus_sheet_name not in file_info['sheet_names']:
                raise RTMProcessingError(f"Focus sheet '{focus_sheet_name}' not found in Excel file")
            
            # Phase 2: Extract requirements from all sheets
            self.logger.info("📋 Phase 2: Extracting requirements from all sheets")
            all_sheets_requirements = {}
            
            for sheet_name in file_info['sheet_names']:
                sheet_requirements = self.excel_processor.extract_requirements_from_sheet(
                    sheet_name, file_info, preserve_original_ids=True
                )
                
                if sheet_requirements:
                    all_sheets_requirements[sheet_name] = sheet_requirements
                    self.logger.info(f"   ✅ {sheet_name}: {len(sheet_requirements)} requirements")
                else:
                    self.logger.info(f"   ⏭️ {sheet_name}: No requirements found (skipped)")
            
            if not all_sheets_requirements:
                raise RTMProcessingError("No requirements found in any sheet")
            
            # Phase 3: AI Analysis with focus on selected sheet
            self.logger.info("📋 Phase 3: AI analysis with intelligent chunking")
            
            # Analyze focus sheet with detailed analysis
            focus_sheet_analysis = []
            if focus_sheet_name in all_sheets_requirements:
                self.logger.info(f"🎯 Detailed analysis for focus sheet: {focus_sheet_name}")
                focus_sheet_data = {
                    'sheet_name': focus_sheet_name,
                    'requirements': all_sheets_requirements[focus_sheet_name]
                }
                
                focus_sheet_analysis = await self.groq_analyzer.analyze_sheet_chunks(
                    focus_sheet_data, is_focus_sheet=True
                )
                
                self.logger.info(f"✅ Focus sheet analysis complete: {len(focus_sheet_analysis)} requirements processed")
            
            # Analyze all other sheets with comprehensive analysis
            all_sheets_analysis = {}
            
            for sheet_name, requirements in all_sheets_requirements.items():
                self.logger.info(f"📊 Analyzing sheet: {sheet_name}")
                
                sheet_data = {
                    'sheet_name': sheet_name,
                    'requirements': requirements
                }
                
                is_focus = (sheet_name == focus_sheet_name)
                
                if is_focus:
                    # Use the detailed analysis we already did
                    all_sheets_analysis[sheet_name] = focus_sheet_analysis
                else:
                    # Do comprehensive analysis for non-focus sheets
                    sheet_analysis = await self.groq_analyzer.analyze_sheet_chunks(
                        sheet_data, is_focus_sheet=False
                    )
                    all_sheets_analysis[sheet_name] = sheet_analysis
                
                analyzed_count = len(all_sheets_analysis[sheet_name])
                self.logger.info(f"   ✅ {sheet_name}: {analyzed_count} requirements analyzed")
            
            # Phase 4: Generate 3-sheet RTM output
            self.logger.info("📋 Phase 4: Generating comprehensive RTM output")
            
            rtm_output = self.rtm_generator.generate_complete_rtm(
                focus_sheet_analysis=focus_sheet_analysis,
                all_sheets_analysis=all_sheets_analysis,
                source_file_info=file_info,
                focus_sheet_name=focus_sheet_name
            )
            
            # Calculate total processing time
            total_time = (datetime.now() - start_time).total_seconds()
            
            # Log completion summary
            total_requirements = sum(len(reqs) for reqs in all_sheets_analysis.values())
            self.logger.info("🎉 RTM processing completed successfully!")
            self.logger.info(f"   ⏱️ Total processing time: {total_time:.2f} seconds")
            self.logger.info(f"   📊 Total requirements processed: {total_requirements}")
            self.logger.info(f"   🎯 Focus sheet requirements: {len(focus_sheet_analysis)}")
            self.logger.info(f"   📁 Output file: {Path(rtm_output.file_path).name}")
            
            # Log API usage statistics
            usage_stats = self.groq_analyzer.get_usage_statistics()
            self.logger.info(f"   🔢 API requests made: {usage_stats['daily_requests_made']}")
            self.logger.info(f"   🎫 API tokens used: {usage_stats['daily_tokens_used']}")
            
            return rtm_output
            
        except Exception as e:
            self.logger.error(f"RTM processing failed: {str(e)}")
            raise RTMProcessingError(f"RTM processing failed: {str(e)}")
    
    def get_available_sheets(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Get list of available sheets with recommendations for focus selection
        """
        try:
            self.logger.info(f"📋 Analyzing sheets in: {Path(file_path).name}")
            
            # Load file and analyze structure
            file_info = self.excel_processor.load_excel_file(file_path)
            
            # Get sheet suggestions
            suggestions = self.excel_processor.get_sheet_suggestions_for_focus(file_info)
            
            self.logger.info(f"✅ Found {len(suggestions)} sheets with requirements")
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error analyzing sheets: {str(e)}")
            return []
    
    def validate_focus_sheet(self, file_path: str, focus_sheet_name: str) -> Tuple[bool, str]:
        """
        Validate that the focus sheet exists and contains requirements
        """
        try:
            file_info = self.excel_processor.load_excel_file(file_path)
            
            if focus_sheet_name not in file_info['sheet_names']:
                return False, f"Sheet '{focus_sheet_name}' not found in the Excel file"
            
            sheet_analysis = file_info['sheets_analysis'].get(focus_sheet_name, {})
            
            if not sheet_analysis.get('has_requirements', False):
                return False, f"Sheet '{focus_sheet_name}' does not appear to contain requirements"
            
            confidence = sheet_analysis.get('confidence_score', 0.0)
            if confidence < 0.3:
                return False, f"Sheet '{focus_sheet_name}' has low confidence for containing requirements (score: {confidence:.2f})"
            
            return True, f"Sheet '{focus_sheet_name}' validated successfully (confidence: {confidence:.2f})"
            
        except Exception as e:
            return False, f"Error validating focus sheet: {str(e)}"
    
    def get_processing_estimate(self, file_path: str, focus_sheet_name: str) -> Dict[str, Any]:
        """
        Provide accurate estimate of processing time and resource usage using lightweight counting
        """
        try:
            file_info = self.excel_processor.load_excel_file(file_path)
            
            # Count total requirements using the new lightweight method
            total_requirements = 0
            sheets_with_reqs = 0
            
            for sheet_name in file_info['sheet_names']:
                sheet_req_count = self.excel_processor.get_lightweight_requirement_count(
                    sheet_name, file_info
                )
                if sheet_req_count > 0:
                    total_requirements += sheet_req_count
                    sheets_with_reqs += 1
                    self.logger.debug(f"Sheet '{sheet_name}': {sheet_req_count} requirements detected")
            
            # Get focus sheet count specifically
            focus_reqs = 0
            if focus_sheet_name in file_info['sheet_names']:
                focus_reqs = self.excel_processor.get_lightweight_requirement_count(
                    focus_sheet_name, file_info
                )
            
            other_reqs = total_requirements - focus_reqs
            
            # Estimate processing time with updated chunk sizes
            # Focus sheet: ~3 seconds per requirement (detailed analysis with larger chunks)
            # Other sheets: ~1.5 seconds per requirement (comprehensive analysis with larger chunks)
            estimated_seconds = (focus_reqs * 3) + (other_reqs * 1.5)
            estimated_minutes = estimated_seconds / 60
            
            # Estimate API usage with new chunk sizes (20 for focus, 30 for others)
            focus_chunks = max(1, (focus_reqs + 19) // 20) if focus_reqs > 0 else 0
            other_chunks = max(1, (other_reqs + 29) // 30) if other_reqs > 0 else 0
            estimated_api_calls = focus_chunks + other_chunks
            
            return {
                'total_requirements': total_requirements,
                'focus_sheet_requirements': focus_reqs,
                'other_sheets_requirements': other_reqs,
                'sheets_with_requirements': sheets_with_reqs,
                'estimated_processing_minutes': round(estimated_minutes, 1),
                'estimated_api_calls': estimated_api_calls,
                'estimated_tokens': estimated_api_calls * 4500,  # Updated for larger chunks
                'processing_feasible': estimated_api_calls < settings.GROQ_DAILY_REQUEST_LIMIT,
                'method_used': 'lightweight_validation'  # For debugging
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating processing estimate: {str(e)}")
            return {
                'error': str(e),
                'processing_feasible': False
            }