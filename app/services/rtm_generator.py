import time
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from app.config import settings
from app.utils.logger import get_logger
from app.models.requirement import Requirement, RequirementType, Priority, Status
from app.models.rtm import RTMOutput
from app.services.excel_processor import ExcelProcessor
from app.services.ai_analyzer import AIAnalyzer

logger = get_logger(__name__)

class RTMGenerator:
    def __init__(self):
        self.excel_processor = ExcelProcessor()
        self.ai_analyzer = AIAnalyzer()
        self.logger = logger
    
    async def create_rtm(self, requirements: List[Requirement], source_file_info: dict) -> RTMOutput:
        """
        Generate complete RTM Excel file
        """
        try:
            start_time = time.time()
            self.logger.info("Starting RTM generation")
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            source_name = Path(source_file_info.get('file_name', 'requirements')).stem
            output_filename = f"RTM_{source_name}_{timestamp}.xlsx"
            output_path = Path(settings.OUTPUT_DIR) / output_filename
            
            # Generate the Excel file
            excel_path = self.excel_processor.generate_rtm_excel(requirements, str(output_path))
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Generate summary statistics
            summary_stats = self.create_summary_statistics(requirements)
            
            # Create RTM output object
            rtm_output = RTMOutput(
                file_path=excel_path,
                requirements_count=len(requirements),
                summary_statistics=summary_stats,
                processing_time=processing_time,
                source_file_name=source_file_info.get('file_name', 'Unknown'),
                generated_at=datetime.now()
            )
            
            self.logger.info(f"RTM generation completed in {processing_time:.2f} seconds")
            return rtm_output
            
        except Exception as e:
            self.logger.error(f"Error creating RTM: {str(e)}")
            raise
    
    def generate_requirement_ids(self, requirements: List[Dict]) -> List[Dict]:
        """
        Assign unique REQ-001, REQ-002, etc. identifiers
        """
        for i, req in enumerate(requirements, 1):
            req_id = f"{settings.REQUIREMENT_ID_PREFIX}-{i:03d}"
            req['id'] = req_id
        
        return requirements
    
    def generate_test_case_ids(self, requirements: List[Dict]) -> List[Dict]:
        """
        Assign unique TC-001, TC-002, etc. identifiers
        """
        for i, req in enumerate(requirements, 1):
            test_case_id = f"{settings.TEST_CASE_ID_PREFIX}-{i:03d}"
            req['test_case_id'] = test_case_id
        
        return requirements
    
    def create_summary_statistics(self, requirements: List[Requirement]) -> Dict:
        """
        Generate summary stats for the RTM
        """
        try:
            # Helper function to safely get enum values
            def safe_get_value(attr):
                return attr.value if hasattr(attr, 'value') else str(attr)
            
            stats = {
                'total_requirements': len(requirements),
                'by_type': {},
                'by_priority': {},
                'by_status': {},
                'by_source_sheet': {}
            }
            
            for req in requirements:
                # Count by type (safely handle both enum and string values)
                req_type = safe_get_value(req.requirement_type)
                stats['by_type'][req_type] = stats['by_type'].get(req_type, 0) + 1
                
                # Count by priority
                priority = safe_get_value(req.priority)
                stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
                
                # Count by status
                status = safe_get_value(req.status)
                stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
                
                # Count by source sheet
                sheet_name = req.source.split('!')[0] if '!' in req.source else 'Unknown'
                stats['by_source_sheet'][sheet_name] = stats['by_source_sheet'].get(sheet_name, 0) + 1
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error creating summary statistics: {str(e)}")
            return {'error': str(e)}
    
    async def process_excel_to_rtm(self, file_path: str, file_name: str) -> RTMOutput:
        """
        Complete workflow: Excel file -> RTM
        """
        try:
            self.logger.info(f"Processing Excel file to RTM: {file_name}")
            
            # Step 1: Read Excel file
            sheets_data = await self.excel_processor.read_excel_file(file_path)
            
            # Step 2: Extract requirements from all sheets
            all_requirements = []
            focus_sheet_found = False
            
            for sheet_name, df in sheets_data.items():
                sheet_requirements = self.excel_processor.extract_requirements_from_sheet(df, sheet_name)
                all_requirements.extend(sheet_requirements)
                
                # Check for focus sheet with flexible matching
                if (settings.FOCUS_SHEET_NAME in sheet_name or 
                    "tool Requirements" in sheet_name or
                    "2-  tool Requirements" in sheet_name):
                    focus_sheet_found = True
                    self.logger.info(f"Found focus sheet: {sheet_name}")
            
            if not focus_sheet_found:
                self.logger.warning(f"Focus sheet '{settings.FOCUS_SHEET_NAME}' not found")
            
            if not all_requirements:
                raise Exception("No requirements found in the Excel file")
            
            # Step 3: Generate IDs
            all_requirements = self.generate_requirement_ids(all_requirements)
            all_requirements = self.generate_test_case_ids(all_requirements)
            
            # Step 4: AI Analysis
            # Extract file_id from file path for progress tracking
            file_id = Path(file_path).stem.split('_')[0] if '_' in Path(file_path).stem else "unknown"
            
            context = {
                'file_name': file_name,
                'sheet_names': list(sheets_data.keys()),
                'focus_sheet': settings.FOCUS_SHEET_NAME,
                'total_count': len(all_requirements),
                'file_id': file_id
            }
            
            analyzed_requirements = await self.ai_analyzer.batch_analyze_requirements(all_requirements, context)
            
            # Step 5: Convert to Requirement objects
            requirement_objects = []
            for i, (original_req, analyzed_req) in enumerate(zip(all_requirements, analyzed_requirements)):
                try:
                    # Parse requirement type
                    req_type_str = analyzed_req.get('requirement_type', 'Functional')
                    requirement_type = RequirementType(req_type_str)
                except ValueError:
                    requirement_type = RequirementType.FUNCTIONAL
                
                try:
                    # Parse priority
                    priority_str = analyzed_req.get('priority', 'Medium')
                    priority = Priority(priority_str)
                except ValueError:
                    priority = Priority.MEDIUM
                
                requirement_obj = Requirement(
                    id=original_req['id'],
                    description=original_req['description'],
                    source=original_req['source'],
                    requirement_type=requirement_type,
                    priority=priority,
                    status=Status.NOT_TESTED,
                    related_deliverables=analyzed_req.get('related_deliverables', ''),
                    test_case_id=original_req['test_case_id'],
                    comments=analyzed_req.get('comments', '')
                )
                requirement_objects.append(requirement_obj)
            
            # Step 6: Generate RTM
            source_file_info = {
                'file_name': file_name,
                'file_path': file_path
            }
            
            rtm_output = await self.create_rtm(requirement_objects, source_file_info)
            
            self.logger.info(f"Successfully processed {len(requirement_objects)} requirements")
            return rtm_output
            
        except Exception as e:
            self.logger.error(f"Error processing Excel to RTM: {str(e)}")
            raise
