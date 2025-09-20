import asyncio
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import google.generativeai as genai
from groq import Groq

from app.config import settings
from app.utils.logger import get_logger
from app.utils.exceptions import AIAnalysisError
from app.models.requirement import RequirementType, Priority, Status
from app.utils.progress_tracker import progress_tracker

logger = get_logger(__name__)

class AIAnalyzer:
    def __init__(self):
        self.logger = logger
        self.gemini_client = None
        self.groq_client = None
        
        # Load detailed prompt from file
        self.detailed_prompt = self._load_detailed_prompt()
        
        # Initialize Gemini if API key is available
        if settings.GEMINI_API_KEY:
            try:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self.gemini_client = genai.GenerativeModel(settings.GEMINI_MODEL)
                self.logger.info("Gemini AI client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Gemini: {str(e)}")
        
        # Initialize Groq if API key is available
        if settings.GROQ_API_KEY:
            try:
                self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
                self.logger.info("Groq AI client initialized")
            except Exception as e:
                self.logger.warning(f"Failed to initialize Groq: {str(e)}")
        
        if not self.gemini_client and not self.groq_client:
            self.logger.warning("No AI clients available. Will use rule-based fallback analysis.")
    
    def _load_detailed_prompt(self) -> str:
        """Load the detailed prompt from prompt_for_ai.txt"""
        try:
            prompt_file = Path("prompt_for_ai.txt")
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
                self.logger.info("✅ Loaded detailed prompt from prompt_for_ai.txt")
                return prompt_content
            else:
                self.logger.warning("❌ prompt_for_ai.txt not found, using default prompt")
                return self._get_default_prompt()
        except Exception as e:
            self.logger.error(f"Error loading detailed prompt: {str(e)}")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Fallback default prompt if detailed prompt can't be loaded"""
        return """You are an expert business analyst and project manager. Analyze the following requirements and provide structured analysis for each.

For each requirement, determine:
1. Requirement Type: Classify as Functional, Non-functional, Business, Technical, or User
2. Priority: Determine if High, Medium, or Low based on business impact and complexity  
3. Related Deliverables: Identify project components this requirement affects
4. Test Case Suggestions: Provide 2-3 specific test scenario ideas

PROJECT CONTEXT:
- Focus on requirements from the "2- tool Requirements" sheet
- Maintain exact requirement descriptions from source
- Generate unique, sequential test case IDs
- Consider business impact for priority assignment

Return analysis as JSON with "requirements" array containing the analysis for each requirement."""
    
    async def analyze_requirements(self, requirements_text: str, context: dict) -> List[Dict]:
        """
        Use AI to classify and analyze requirements
        Returns: Enhanced requirement data with classifications
        """
        try:
            self.logger.info(f"Analyzing requirements with AI")
            
            # Prepare the prompt
            prompt = self._build_analysis_prompt(requirements_text, context)
            
            # Try Groq first (since Gemini is rate limited), fallback to Gemini
            result = None
            
            if self.groq_client:
                try:
                    self.logger.info("🚀 Using Groq (Llama 3.1 8B Instant) for analysis...")
                    result = await self._analyze_with_groq(prompt)
                    self.logger.info("✅ Groq analysis successful")
                except Exception as e:
                    self.logger.warning(f"❌ Groq analysis failed: {str(e)}")
            
            if not result and self.gemini_client:
                try:
                    self.logger.info("Attempting analysis with Gemini as fallback...")
                    result = await self._analyze_with_gemini(prompt)
                    self.logger.info("✅ Gemini analysis successful")
                except Exception as e:
                    self.logger.warning(f"❌ Gemini analysis failed (possibly rate limited): {str(e)}")
            
            if not result:
                self.logger.warning("🔄 All AI services failed, using rule-based analysis")
                return None  # Will trigger fallback
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in AI analysis: {str(e)}")
            return None  # Will trigger fallback
    
    async def _analyze_with_gemini(self, prompt: str) -> List[Dict]:
        """Analyze requirements using Gemini"""
        try:
            self.logger.debug("Using Gemini for analysis")
            response = self.gemini_client.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=settings.AI_TEMPERATURE,
                    max_output_tokens=settings.AI_MAX_TOKENS,
                )
            )
            
            # Parse JSON response
            result_text = response.text.strip()
            if result_text.startswith("```json"):
                result_text = result_text[7:-3]
            elif result_text.startswith("```"):
                result_text = result_text[3:-3]
            
            return json.loads(result_text)
            
        except Exception as e:
            self.logger.error(f"Gemini analysis error: {str(e)}")
            raise
    
    async def _analyze_with_groq(self, prompt: str) -> List[Dict]:
        """Analyze requirements using Groq"""
        try:
            self.logger.debug("Using Groq for analysis")
            response = self.groq_client.chat.completions.create(
                model=settings.GROQ_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=settings.AI_TEMPERATURE,
                max_tokens=settings.AI_MAX_TOKENS,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            return json.loads(result_text)
            
        except Exception as e:
            self.logger.error(f"Groq analysis error: {str(e)}")
            raise
    
    def classify_requirement_type(self, requirement: str) -> RequirementType:
        """
        Classify requirement into functional/non-functional/business/etc.
        """
        requirement_lower = requirement.lower()
        
        # Simple rule-based classification as fallback
        if any(word in requirement_lower for word in ['performance', 'speed', 'response time', 'scalability', 'security', 'reliability']):
            return RequirementType.NON_FUNCTIONAL
        elif any(word in requirement_lower for word in ['business', 'process', 'workflow', 'policy', 'compliance']):
            return RequirementType.BUSINESS
        elif any(word in requirement_lower for word in ['technical', 'infrastructure', 'platform', 'architecture', 'integration']):
            return RequirementType.TECHNICAL
        elif any(word in requirement_lower for word in ['user', 'interface', 'ui', 'ux', 'usability', 'accessibility']):
            return RequirementType.USER
        else:
            return RequirementType.FUNCTIONAL
    
    def determine_priority(self, requirement: str, context: str = "") -> Priority:
        """
        Analyze requirement to determine business priority
        """
        requirement_lower = requirement.lower()
        
        # High priority indicators
        if any(word in requirement_lower for word in ['critical', 'essential', 'must', 'mandatory', 'required', 'shall']):
            return Priority.HIGH
        # Low priority indicators
        elif any(word in requirement_lower for word in ['nice to have', 'optional', 'future', 'enhancement', 'may', 'could']):
            return Priority.LOW
        else:
            return Priority.MEDIUM
    
    def generate_test_case_suggestions(self, requirement: str) -> List[str]:
        """
        Generate test case ideas for the requirement
        """
        # Simple test case generation based on requirement patterns
        suggestions = []
        
        if "login" in requirement.lower():
            suggestions = [
                "Test valid login credentials",
                "Test invalid login credentials", 
                "Test login with empty fields"
            ]
        elif "search" in requirement.lower():
            suggestions = [
                "Test search with valid criteria",
                "Test search with no results",
                "Test search with special characters"
            ]
        elif "save" in requirement.lower() or "create" in requirement.lower():
            suggestions = [
                "Test successful creation/save",
                "Test creation with invalid data",
                "Test creation with missing required fields"
            ]
        else:
            suggestions = [
                f"Test positive scenario for: {requirement[:50]}...",
                f"Test negative scenario for: {requirement[:50]}...",
                f"Test boundary conditions for: {requirement[:50]}..."
            ]
        
        return suggestions[:3]  # Return max 3 suggestions
    
    def extract_deliverables(self, requirement: str, project_context: str = "") -> str:
        """
        Identify related deliverables for the requirement
        """
        deliverables = []
        requirement_lower = requirement.lower()
        
        # Common deliverable patterns
        if any(word in requirement_lower for word in ['interface', 'ui', 'screen', 'page']):
            deliverables.append("User Interface")
        if any(word in requirement_lower for word in ['database', 'data', 'storage']):
            deliverables.append("Database Schema")
        if any(word in requirement_lower for word in ['api', 'service', 'integration']):
            deliverables.append("API Documentation")
        if any(word in requirement_lower for word in ['report', 'dashboard', 'analytics']):
            deliverables.append("Reporting Module")
        if any(word in requirement_lower for word in ['security', 'authentication', 'authorization']):
            deliverables.append("Security Framework")
        
        return ", ".join(deliverables) if deliverables else "Core System"
    
    async def batch_analyze_requirements(self, requirements_list: List[Dict], context: dict) -> List[Dict]:
        """
        Process multiple requirements using smart batching with 5000-token chunks
        """
        try:
            total_requirements = len(requirements_list)
            self.logger.info(f"🚀 Starting smart batch analysis for {total_requirements} requirements")
            
            # If no AI client available, use rule-based analysis
            if not self.gemini_client and not self.groq_client:
                self.logger.warning("No AI clients available, using rule-based analysis")
                return self._fallback_analysis(requirements_list)
            
            # Check if we need batching (if estimated tokens > 5000)
            estimated_tokens = self._estimate_total_tokens(requirements_list)
            self.logger.info(f"📊 Estimated total tokens: {estimated_tokens:,}")
            
            if estimated_tokens <= 5000:
                # Small enough for single batch
                self.logger.info("✅ Requirements fit in single batch, processing directly")
                return await self._process_single_batch(requirements_list, context)
            else:
                # Use smart batching
                self.logger.info(f"🔄 Using smart batching (target: 3000 tokens per batch)")
                return await self._process_with_smart_batching(requirements_list, context)
                
        except Exception as e:
            self.logger.error(f"Error in batch analysis: {str(e)}")
            return self._fallback_analysis(requirements_list)
    
    async def _process_single_batch(self, requirements_list: List[Dict], context: dict) -> List[Dict]:
        """Process requirements in a single batch"""
        try:
            formatted_requirements = self._format_requirements_for_analysis(requirements_list)
            prompt = self._build_batch_analysis_prompt(formatted_requirements, context)
            
            result = await self.analyze_requirements(prompt, context)
            if result:
                return result
            else:
                return self._fallback_analysis(requirements_list)
        except Exception as e:
            self.logger.warning(f"Single batch processing failed: {str(e)}")
            return self._fallback_analysis(requirements_list)
    
    async def _process_with_smart_batching(self, requirements_list: List[Dict], context: dict) -> List[Dict]:
        """Process requirements using smart 3000-token batching with progress tracking"""
        try:
            batches = self._create_smart_batches(requirements_list, max_tokens=3000)
            total_batches = len(batches)
            
            self.logger.info(f"📦 Created {total_batches} batches for processing")
            
            # Get file_id from context for progress tracking
            file_id = context.get('file_id', 'unknown')
            
            # Start progress tracking
            progress_tracker.start_processing(file_id, total_batches)
            
            all_results = []
            successful_batches = 0
            
            for batch_idx, batch in enumerate(batches, 1):
                batch_size = len(batch)
                estimated_tokens = self._estimate_batch_tokens(batch)
                
                # Update progress - starting batch
                progress_tracker.update_batch_start(file_id, batch_idx, batch_size, estimated_tokens)
                
                self.logger.info(f"🔄 Processing batch {batch_idx}/{total_batches} ({batch_size} requirements, ~{estimated_tokens:,} tokens including prompt)")
                self.logger.info(f"📊 Batch breakdown: {batch_size} reqs × ~{estimated_tokens//batch_size} tokens each + 2500 prompt = {estimated_tokens} total")
                
                try:
                    # Process this batch
                    batch_results = await self._process_single_batch(batch, context)
                    
                    if batch_results and len(batch_results) == batch_size:
                        all_results.extend(batch_results)
                        successful_batches += 1
                        
                        # Update progress - batch completed successfully
                        progress_tracker.update_batch_complete(file_id, batch_idx, True)
                        self.logger.info(f"✅ Batch {batch_idx}/{total_batches} completed successfully")
                    else:
                        # Fallback for this batch
                        fallback_results = self._fallback_analysis(batch)
                        all_results.extend(fallback_results)
                        
                        # Update progress - batch failed, used fallback
                        progress_tracker.update_batch_complete(file_id, batch_idx, False)
                        self.logger.warning(f"⚠️ Batch {batch_idx}/{total_batches} failed, using rule-based fallback")
                    
                    # Rate limiting delay between batches (except for last batch)
                    if batch_idx < total_batches:
                        progress_tracker.update_waiting(file_id, 5)
                        self.logger.info(f"⏳ Waiting 5 seconds before next batch...")
                        await asyncio.sleep(5)
                        
                except Exception as e:
                    self.logger.error(f"❌ Batch {batch_idx}/{total_batches} error: {str(e)}")
                    # Use fallback for failed batch
                    fallback_results = self._fallback_analysis(batch)
                    all_results.extend(fallback_results)
                    
                    # Update progress - batch failed
                    progress_tracker.update_batch_complete(file_id, batch_idx, False)
            
            # Mark processing as complete
            progress_tracker.complete_processing(file_id, True)
            self.logger.info(f"🎉 Batch processing complete! {successful_batches}/{total_batches} batches used AI analysis")
            return all_results
            
        except Exception as e:
            self.logger.error(f"Smart batching failed: {str(e)}")
            # Mark processing as failed
            file_id = context.get('file_id', 'unknown')
            progress_tracker.complete_processing(file_id, False)
            return self._fallback_analysis(requirements_list)
    
    def _create_smart_batches(self, requirements_list: List[Dict], max_tokens: int = 3000) -> List[List[Dict]]:
        """Create optimal batches based on token count including prompt overhead"""
        batches = []
        current_batch = []
        prompt_overhead = 2000  # Reserve tokens for detailed prompt + JSON formatting
        effective_limit = max_tokens - prompt_overhead  # Actual limit for requirements (1000 tokens)
        
        current_tokens = 0
        
        for req in requirements_list:
            req_tokens = self._estimate_requirement_tokens(req)
            
            # If adding this requirement would exceed effective limit, start new batch
            if current_tokens + req_tokens > effective_limit and current_batch:
                batches.append(current_batch)
                current_batch = [req]
                current_tokens = req_tokens
            else:
                current_batch.append(req)
                current_tokens += req_tokens
        
        # Add final batch if not empty
        if current_batch:
            batches.append(current_batch)
        
        return batches
    
    def _estimate_total_tokens(self, requirements_list: List[Dict]) -> int:
        """Estimate total tokens for all requirements"""
        return sum(self._estimate_requirement_tokens(req) for req in requirements_list)
    
    def _estimate_batch_tokens(self, batch: List[Dict]) -> int:
        """Estimate tokens for a batch including full prompt overhead"""
        # Get requirement tokens
        req_tokens = sum(self._estimate_requirement_tokens(req) for req in batch)
        
        # Add significant prompt overhead (detailed prompt + JSON formatting: ~2000 tokens)
        prompt_overhead = 2000
        
        return req_tokens + prompt_overhead
    
    def _estimate_requirement_tokens(self, requirement: Dict) -> int:
        """Estimate tokens for a single requirement including JSON formatting and prompt overhead"""
        # Include all fields that contribute to token count
        text = f"{requirement.get('description', '')} {requirement.get('source', '')} {requirement.get('priority', '')} {requirement.get('id', '')}"
        
        # Very conservative token estimate (2.5 chars = 1 token)
        base_tokens = len(text) // 2.5
        
        # Add massive formatting overhead (JSON structure, quotes, commas: ~100% extra)
        formatted_tokens = int(base_tokens * 2.0)
        
        # Minimum 50 tokens per requirement (to account for JSON structure)
        return max(formatted_tokens, 50)
    
    def _format_requirements_for_analysis(self, requirements_list: List[Dict]) -> List[Dict]:
        """Format requirements for analysis"""
        formatted_requirements = []
        for i, req in enumerate(requirements_list):
            formatted_requirements.append({
                "index": i,
                "description": req.get('description', ''),
                "source": req.get('source', ''),
                "sheet_name": req.get('sheet_name', '')
            })
        return formatted_requirements
    
    def _fallback_analysis(self, requirements_list: List[Dict]) -> List[Dict]:
        """Rule-based analysis when AI is not available - follows detailed prompt guidelines"""
        self.logger.info("Using fallback rule-based analysis following detailed prompt guidelines")
        
        analyzed_requirements = []
        for i, req in enumerate(requirements_list):
            description = req.get('description', '')
            source = req.get('source', '')
            
            # Enhanced classification following detailed prompt guidelines
            req_type = self._classify_requirement_type_fallback(description, source)
            priority = self._determine_priority_fallback(description, source)
            deliverables = self._extract_deliverables_fallback(description, source)
            test_cases = self._generate_test_case_suggestions_fallback(description, source, i)
            
            analyzed_req = {
                "original_requirement": description,
                "requirement_type": req_type,
                "priority": priority,
                "priority_reasoning": "Rule-based classification following detailed prompt guidelines",
                "related_deliverables": deliverables,
                "test_case_suggestions": test_cases,
                "comments": "Generated using rule-based analysis following detailed prompt guidelines",
                "analysis_confidence": 0.6
            }
            analyzed_requirements.append(analyzed_req)
        
        return analyzed_requirements
    
    def _classify_requirement_type_fallback(self, description: str, source: str) -> str:
        """Enhanced classification following detailed prompt guidelines"""
        desc_lower = description.lower()
        
        # Focus on "2- tool Requirements" sheet items (from detailed prompt)
        if "tool requirements" in source.lower():
            if any(keyword in desc_lower for keyword in ['function', 'feature', 'capability', 'operation', 'tool']):
                return 'Functional'
            elif any(keyword in desc_lower for keyword in ['performance', 'speed', 'response', 'time', 'memory']):
                return 'Non-functional'
            else:
                return 'Functional'  # Default for tool requirements
        
        # General classification following detailed prompt categories
        if any(keyword in desc_lower for keyword in ['user', 'interface', 'display', 'screen', 'button', 'click', 'ui', 'ux']):
            return 'User'
        elif any(keyword in desc_lower for keyword in ['performance', 'speed', 'response', 'time', 'memory', 'cpu', 'bandwidth', 'scalability']):
            return 'Non-functional'
        elif any(keyword in desc_lower for keyword in ['business', 'process', 'workflow', 'policy', 'rule', 'compliance']):
            return 'Business'
        elif any(keyword in desc_lower for keyword in ['technical', 'system', 'integration', 'api', 'database', 'infrastructure']):
            return 'Technical'
        else:
            return 'Functional'
    
    def _determine_priority_fallback(self, description: str, source: str) -> str:
        """Enhanced priority determination following detailed prompt guidelines"""
        desc_lower = description.lower()
        
        # Higher priority for tool requirements (from detailed prompt focus)
        if "tool requirements" in source.lower():
            if any(keyword in desc_lower for keyword in ['critical', 'essential', 'must', 'required', 'mandatory', 'core']):
                return 'High'
            elif any(keyword in desc_lower for keyword in ['important', 'should', 'recommended', 'key']):
                return 'Medium'
            else:
                return 'Medium'  # Default higher priority for tool requirements
        
        # General priority determination
        if any(keyword in desc_lower for keyword in ['critical', 'essential', 'must', 'required', 'mandatory', 'core']):
            return 'High'
        elif any(keyword in desc_lower for keyword in ['important', 'should', 'recommended', 'key']):
            return 'Medium'
        else:
            return 'Low'
    
    def _extract_deliverables_fallback(self, description: str, source: str) -> str:
        """Extract deliverables following detailed prompt guidelines"""
        if "tool requirements" in source.lower():
            return "Tool Development Deliverable"
        elif "general" in source.lower():
            return "General System Deliverable"
        elif "implementation" in source.lower():
            return "Implementation Deliverable"
        elif "operations" in source.lower():
            return "Operations Deliverable"
        elif "sla" in source.lower():
            return "SLA Compliance Deliverable"
        else:
            return "Project Deliverable"
    
    def _generate_test_case_suggestions_fallback(self, description: str, source: str, index: int) -> List[str]:
        """Generate test case suggestions following detailed prompt guidelines"""
        desc_lower = description.lower()
        
        # Generate specific test scenarios based on requirement type and detailed prompt guidelines
        if any(keyword in desc_lower for keyword in ['user', 'interface', 'display', 'screen']):
            return [
                f"Verify user interface displays correctly",
                f"Test user interaction functionality",
                f"Validate user experience requirements"
            ]
        elif any(keyword in desc_lower for keyword in ['performance', 'speed', 'response', 'time']):
            return [
                f"Measure performance metrics",
                f"Test response time under load",
                f"Validate performance requirements"
            ]
        elif any(keyword in desc_lower for keyword in ['integration', 'api', 'system']):
            return [
                f"Test integration with external systems",
                f"Verify API functionality",
                f"Validate system compatibility"
            ]
        else:
            return [
                f"Verify core functionality",
                f"Test under normal conditions",
                f"Validate meets specifications"
            ]
    
    def _build_analysis_prompt(self, requirements_text: str, context: dict) -> str:
        """Build prompt for AI analysis"""
        return f"""You are an expert business analyst and project manager. Analyze the following requirements and provide structured analysis for each.

For each requirement, determine:
1. Requirement Type: Classify as Functional, Non-functional, Business, Technical, or User
2. Priority: Determine if High, Medium, or Low based on business impact and complexity  
3. Related Deliverables: Identify project components this requirement affects
4. Test Case Suggestions: Provide 2-3 specific test scenario ideas

PROJECT CONTEXT:
- Source File: {context.get('file_name', 'Unknown')}
- Focus Sheet: {context.get('focus_sheet', settings.FOCUS_SHEET_NAME)}
- Total Requirements: {context.get('total_count', 'Unknown')}

REQUIREMENTS TO ANALYZE:
{requirements_text}

INSTRUCTIONS:
- Maintain exact requirement descriptions - do not modify the text
- Be specific with deliverables and test cases
- Consider dependencies between requirements
- Focus extra attention on requirements from "{settings.FOCUS_SHEET_NAME}" sheet

Respond with a JSON array where each object contains:
{{
    "original_requirement": "exact text from source",
    "requirement_type": "Functional|Non-functional|Business|Technical|User",
    "priority": "High|Medium|Low", 
    "priority_reasoning": "brief explanation",
    "related_deliverables": "specific project components",
    "test_case_suggestions": ["test case 1", "test case 2", "test case 3"],
    "comments": "additional insights or dependencies",
    "analysis_confidence": 0.95
}}"""
    
    def _build_batch_analysis_prompt(self, requirements: List[Dict], context: dict) -> str:
        """Build prompt for batch analysis using detailed prompt"""
        formatted_reqs = json.dumps(requirements, indent=2)
        
        # Use the detailed prompt as base
        base_prompt = self.detailed_prompt
        
        # Add specific context for this batch
        context_info = f"""
BATCH PROCESSING CONTEXT:
- File: {context.get('file_name', 'Unknown')}
- Sheets Processed: {context.get('sheet_names', [])}
- Primary Focus: "{settings.FOCUS_SHEET_NAME}"
- Total Requirements Found: {context.get('total_count', 'Unknown')}
- Current Batch: {len(requirements)} requirements

REQUIREMENTS DATA FOR THIS BATCH:
{formatted_reqs}

IMPORTANT: Process ONLY the requirements in this batch. Return as a JSON object with "requirements" array containing the analysis for each requirement in this batch.
"""
        
        return base_prompt + context_info
