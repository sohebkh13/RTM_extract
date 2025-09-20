import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from groq import Groq

from app.config import settings
from app.utils.logger import get_logger
from app.utils.exceptions import AIAnalysisError
from app.utils.progress_tracker import progress_tracker
from app.services.intelligent_chunker import IntelligentChunker

logger = get_logger(__name__)

class GroqRateLimiter:
    """
    Manages Groq API rate limiting with exponential backoff
    """
    
    def __init__(self):
        self.requests_per_minute = settings.GROQ_REQUESTS_PER_MINUTE
        self.delay_between_requests = 60 / self.requests_per_minute  # 2 seconds for 30 req/min
        self.last_request_time = 0
        self.daily_tokens_used = 0
        self.daily_requests_made = 0
        
    async def wait_for_rate_limit(self):
        """
        Ensure we don't exceed rate limits
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.delay_between_requests:
            wait_time = self.delay_between_requests - time_since_last
            logger.info(f"⏳ Rate limiting: waiting {wait_time:.1f} seconds")
            await asyncio.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    async def make_request_with_backoff(self, client: Groq, prompt: str, max_retries: int = 3) -> Optional[str]:
        """
        Make request with exponential backoff on errors and model fallback
        """
        # First try with primary model
        primary_model = settings.GROQ_MODEL
        fallback_model = settings.GROQ_FALLBACK_MODEL
        
        for model_name in [primary_model, fallback_model]:
            for attempt in range(max_retries):
                try:
                    # Wait for rate limit
                    await self.wait_for_rate_limit()
                    
                    # Make the request
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=settings.AI_TEMPERATURE,
                        max_tokens=settings.AI_MAX_TOKENS,
                        response_format={"type": "json_object"}
                    )
                    
                    # Track usage
                    self.daily_requests_made += 1
                    if hasattr(response, 'usage') and response.usage:
                        self.daily_tokens_used += response.usage.total_tokens
                    
                    # Log which model was used if not primary
                    if model_name != primary_model:
                        logger.info(f"🔄 Successfully used fallback model: {model_name}")
                    
                    return response.choices[0].message.content
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    if "429" in str(e) or "rate limit" in error_msg:
                        # Rate limit hit, exponential backoff
                        wait_time = (2 ** attempt) * 5  # 5, 10, 20 seconds
                        logger.warning(f"⚠️ Rate limit hit with {model_name}, attempt {attempt + 1}/{max_retries}, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    elif "413" in str(e) or "too large" in error_msg or "token" in error_msg:
                        # Token limit error - try fallback model immediately
                        if model_name == primary_model:
                            logger.warning(f"⚠️ Token limit hit with {primary_model}, trying fallback model {fallback_model}")
                            break  # Break inner loop to try fallback model
                        else:
                            logger.error(f"❌ Token limit hit even with fallback model {fallback_model}")
                            if attempt == max_retries - 1:
                                raise AIAnalysisError(f"Both models failed due to token limits: {str(e)}")
                    else:
                        # Other error, don't retry
                        logger.error(f"❌ Groq API error on attempt {attempt + 1} with {model_name}: {str(e)}")
                        if attempt == max_retries - 1:
                            if model_name == primary_model:
                                logger.info(f"🔄 Primary model {primary_model} failed, trying fallback {fallback_model}")
                                break  # Try fallback model
                            else:
                                raise AIAnalysisError(f"Both models failed after {max_retries} attempts: {str(e)}")
                        await asyncio.sleep(2 ** attempt)  # Brief wait before retry
        
        return None

class GroqAnalyzer:
    """
    Groq-only AI analyzer with intelligent chunking and detailed prompt integration
    """
    
    def __init__(self):
        self.logger = logger
        self.chunker = IntelligentChunker()
        self.rate_limiter = GroqRateLimiter()
        
        # Initialize Groq client
        if not settings.GROQ_API_KEY:
            raise AIAnalysisError("GROQ_API_KEY is required but not found in configuration")
        
        try:
            self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
            self.logger.info("✅ Groq client initialized successfully")
        except Exception as e:
            raise AIAnalysisError(f"Failed to initialize Groq client: {str(e)}")
        
        # Load detailed prompt from file
        self.detailed_prompt = self._load_detailed_prompt()
        self.comprehensive_prompt = self._create_comprehensive_prompt()
    
    def _load_detailed_prompt(self) -> str:
        """
        Load the detailed prompt from prompt_for_ai.txt
        """
        try:
            prompt_file = Path("prompt_for_ai.txt")
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
                self.logger.info("✅ Loaded detailed prompt from prompt_for_ai.txt")
                return prompt_content
            else:
                self.logger.warning("❌ prompt_for_ai.txt not found, using default prompt")
                return self._get_default_detailed_prompt()
        except Exception as e:
            self.logger.error(f"Error loading detailed prompt: {str(e)}")
            return self._get_default_detailed_prompt()
    
    def _get_default_detailed_prompt(self) -> str:
        """
        Fallback detailed prompt if file can't be loaded
        """
        return """You are an expert project manager and business analyst specializing in requirements management.

Analyze the provided Excel requirements and create a comprehensive Requirements Traceability Matrix (RTM).

For each requirement, provide:
1. Requirement Classification (Functional, Non-functional, Business, Technical, User)
2. Priority Assessment (High, Medium, Low) based on business impact
3. Related Deliverables identification
4. Test Case suggestions (2-3 specific scenarios)

CRITICAL INSTRUCTIONS:
- Use EXACT requirement descriptions from source - do NOT paraphrase
- Preserve original requirement IDs if present
- Reference specific sheet names and cell locations
- Focus extra attention on focus sheet requirements
- Generate comprehensive test case suggestions

Return structured JSON format with "requirements" array."""
    
    def _create_comprehensive_prompt(self) -> str:
        """
        Create a comprehensive but lighter prompt for non-focus sheets
        """
        return """You are an expert business analyst. Analyze the following Excel requirements comprehensively.

For each requirement, determine:
1. Requirement Type: Functional, Non-functional, Business, Technical, or User
2. Priority: High, Medium, or Low based on business impact
3. Related Deliverables: Identify relevant project components
4. Test Case Suggestions: Provide 2-3 test scenario ideas

INSTRUCTIONS:
- Maintain EXACT requirement descriptions - do not modify text
- Preserve original IDs and formatting
- Consider business impact for priority assignment
- Be specific with deliverables and test cases

Return JSON with "requirements" array containing analysis for each requirement."""

    async def analyze_sheet_chunks(self, sheet_data: Dict, is_focus_sheet: bool = False, 
                                 file_id: str = 'unknown') -> List[Dict]:
        """
        Analyze all chunks from a sheet with appropriate prompt and chunking strategy
        """
        try:
            sheet_name = sheet_data.get('sheet_name', 'Unknown')
            requirements = sheet_data.get('requirements', [])
            
            if not requirements:
                self.logger.warning(f"No requirements found in sheet: {sheet_name}")
                return []
            
            self.logger.info(f"🚀 Starting analysis for sheet '{sheet_name}' ({len(requirements)} requirements)")
            self.logger.info(f"📋 Analysis type: {'DETAILED (Focus Sheet)' if is_focus_sheet else 'COMPREHENSIVE'}")
            
            # Create intelligent chunks
            chunks = self.chunker.create_sheet_chunks(sheet_data, is_focus_sheet)
            
            if not chunks:
                self.logger.error(f"No chunks created for sheet: {sheet_name}")
                return []
            
            # Validate chunking
            if not self.chunker.validate_chunks(chunks, requirements):
                self.logger.error(f"Chunk validation failed for sheet: {sheet_name}")
                return []
            
            # Estimate processing time
            estimated_minutes = self.chunker.estimate_total_processing_time(chunks)
            self.logger.info(f"⏱️ Estimated processing time: {estimated_minutes:.1f} minutes")
            
            # Process chunks with rate limiting
            all_analyzed_requirements = []
            successful_chunks = 0
            failed_chunks = 0
            
            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = chunk.get('chunk_id', f'chunk_{chunk_idx}')
                requirement_count = chunk.get('requirement_count', 0)
                estimated_tokens = chunk.get('estimated_tokens', 0)
                
                self.logger.info(f"🔄 Processing chunk {chunk_idx + 1}/{len(chunks)}: {chunk_id}")
                self.logger.info(f"   📊 {requirement_count} requirements, ~{estimated_tokens} tokens")
                
                try:
                    # Build appropriate prompt
                    prompt = self._build_chunk_prompt(chunk, is_focus_sheet)
                    
                    # Analyze chunk with rate limiting
                    chunk_results = await self._analyze_chunk_with_groq(prompt, chunk)
                    
                    if chunk_results:
                        all_analyzed_requirements.extend(chunk_results)
                        successful_chunks += 1
                        self.logger.info(f"   ✅ Chunk {chunk_idx + 1} completed successfully")
                    else:
                        # Use fallback analysis for failed chunk
                        fallback_results = self._fallback_analysis_for_chunk(chunk)
                        all_analyzed_requirements.extend(fallback_results)
                        failed_chunks += 1
                        self.logger.warning(f"   ⚠️ Chunk {chunk_idx + 1} failed, used fallback analysis")
                
                except Exception as e:
                    self.logger.error(f"   ❌ Error processing chunk {chunk_idx + 1}: {str(e)}")
                    # Use fallback for error case
                    fallback_results = self._fallback_analysis_for_chunk(chunk)
                    all_analyzed_requirements.extend(fallback_results)
                    failed_chunks += 1
            
            # Log final results
            self.logger.info(f"🎉 Sheet '{sheet_name}' analysis complete!")
            self.logger.info(f"   ✅ Successful chunks: {successful_chunks}/{len(chunks)}")
            self.logger.info(f"   ⚠️ Failed chunks (fallback): {failed_chunks}/{len(chunks)}")
            self.logger.info(f"   📋 Total requirements analyzed: {len(all_analyzed_requirements)}")
            
            return all_analyzed_requirements
            
        except Exception as e:
            self.logger.error(f"Error analyzing sheet chunks for '{sheet_name}': {str(e)}")
            # Return fallback analysis for entire sheet
            return self._fallback_analysis_for_sheet(sheet_data)
    
    def _build_chunk_prompt(self, chunk: Dict, is_focus_sheet: bool) -> str:
        """
        Build appropriate prompt for chunk analysis
        """
        # Choose base prompt based on whether it's focus sheet
        base_prompt = self.detailed_prompt if is_focus_sheet else self.comprehensive_prompt
        
        # Extract chunk information
        requirements_data = []
        for req in chunk.get('requirements', []):
            req_data = {
                'original_id': req.get('original_id', ''),
                'description': req.get('description', ''),
                'source': req.get('source', ''),
                'additional_info': req.get('additional_info', ''),
                'row_number': req.get('row_number', '')
            }
            requirements_data.append(req_data)
        
        # Build context information
        context_info = f"""
CHUNK PROCESSING CONTEXT:
- Sheet Name: {chunk.get('sheet_name', 'Unknown')}
- Chunk ID: {chunk.get('chunk_id', 'Unknown')}
- Analysis Type: {"DETAILED FOCUS SHEET" if is_focus_sheet else "COMPREHENSIVE ANALYSIS"}
- Requirements in this chunk: {chunk.get('requirement_count', 0)}
- Estimated tokens: {chunk.get('estimated_tokens', 0)}
- Row range: {chunk['metadata'].get('start_row', 'N/A')} - {chunk['metadata'].get('end_row', 'N/A')}

REQUIREMENTS DATA FOR ANALYSIS:
{json.dumps(requirements_data, indent=2)}

RESPONSE REQUIREMENTS:
- Return valid JSON object with "requirements" array
- Each requirement object must include: original_requirement, requirement_type, priority, priority_reasoning, related_deliverables, test_case_suggestions, comments
- Preserve EXACT original requirement text - do not modify descriptions
- Use original IDs if present, otherwise note as "Generated: [description_start]"
"""
        
        return base_prompt + context_info
    
    async def _analyze_chunk_with_groq(self, prompt: str, chunk: Dict) -> Optional[List[Dict]]:
        """
        Analyze a single chunk using Groq API
        """
        try:
            # Make request with rate limiting and retries
            response_text = await self.rate_limiter.make_request_with_backoff(
                self.groq_client, prompt, max_retries=3
            )
            
            if not response_text:
                self.logger.error("No response from Groq API")
                return None
            
            # Parse JSON response
            try:
                response_data = json.loads(response_text)
                if 'requirements' in response_data:
                    return response_data['requirements']
                else:
                    self.logger.error("Response missing 'requirements' key")
                    return None
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {str(e)}")
                self.logger.debug(f"Raw response: {response_text[:500]}...")
                return None
                
        except Exception as e:
            self.logger.error(f"Groq analysis error: {str(e)}")
            return None
    
    def _fallback_analysis_for_chunk(self, chunk: Dict) -> List[Dict]:
        """
        Provide rule-based fallback analysis for a chunk
        """
        fallback_results = []
        requirements = chunk.get('requirements', [])
        
        for req in requirements:
            analyzed_req = {
                "original_requirement": req.get('description', ''),
                "requirement_type": self._classify_requirement_type_fallback(req.get('description', '')),
                "priority": self._determine_priority_fallback(req.get('description', '')),
                "priority_reasoning": "Rule-based fallback analysis - AI analysis unavailable",
                "related_deliverables": self._extract_deliverables_fallback(req.get('description', '')),
                "test_case_suggestions": self._generate_test_suggestions_fallback(req.get('description', '')),
                "comments": "Generated using rule-based fallback due to AI service unavailability",
                "analysis_confidence": 0.5,
                "original_id": req.get('original_id', ''),
                "source": req.get('source', ''),
                "fallback_analysis": True
            }
            fallback_results.append(analyzed_req)
        
        return fallback_results
    
    def _fallback_analysis_for_sheet(self, sheet_data: Dict) -> List[Dict]:
        """
        Provide rule-based fallback analysis for entire sheet
        """
        requirements = sheet_data.get('requirements', [])
        return [self._fallback_analysis_for_chunk({'requirements': requirements})[0] 
                if requirements else []]
    
    def _classify_requirement_type_fallback(self, description: str) -> str:
        """Rule-based requirement type classification"""
        desc_lower = description.lower()
        
        if any(keyword in desc_lower for keyword in ['user', 'interface', 'ui', 'display', 'screen']):
            return 'User'
        elif any(keyword in desc_lower for keyword in ['performance', 'speed', 'response', 'memory', 'cpu']):
            return 'Non-functional'
        elif any(keyword in desc_lower for keyword in ['business', 'process', 'workflow', 'policy']):
            return 'Business'
        elif any(keyword in desc_lower for keyword in ['technical', 'system', 'integration', 'api', 'database']):
            return 'Technical'
        else:
            return 'Functional'
    
    def _determine_priority_fallback(self, description: str) -> str:
        """Rule-based priority determination"""
        desc_lower = description.lower()
        
        if any(keyword in desc_lower for keyword in ['critical', 'essential', 'must', 'required', 'mandatory']):
            return 'High'
        elif any(keyword in desc_lower for keyword in ['important', 'should', 'recommended']):
            return 'Medium'
        else:
            return 'Low'
    
    def _extract_deliverables_fallback(self, description: str) -> str:
        """Rule-based deliverable extraction"""
        desc_lower = description.lower()
        
        deliverables = []
        if any(keyword in desc_lower for keyword in ['interface', 'ui', 'screen']):
            deliverables.append("User Interface")
        if any(keyword in desc_lower for keyword in ['database', 'data', 'storage']):
            deliverables.append("Database")
        if any(keyword in desc_lower for keyword in ['api', 'service', 'integration']):
            deliverables.append("API/Integration")
        if any(keyword in desc_lower for keyword in ['report', 'dashboard']):
            deliverables.append("Reporting")
        
        return ", ".join(deliverables) if deliverables else "Core System Component"
    
    def _generate_test_suggestions_fallback(self, description: str) -> List[str]:
        """Rule-based test case suggestions"""
        return [
            f"Verify basic functionality: {description[:50]}...",
            f"Test error handling and edge cases",
            f"Validate integration with related components"
        ]
    
    def get_usage_statistics(self) -> Dict:
        """
        Get current API usage statistics
        """
        return {
            'daily_requests_made': self.rate_limiter.daily_requests_made,
            'daily_tokens_used': self.rate_limiter.daily_tokens_used,
            'requests_remaining': settings.GROQ_DAILY_REQUEST_LIMIT - self.rate_limiter.daily_requests_made,
            'tokens_remaining': settings.GROQ_DAILY_TOKEN_LIMIT - self.rate_limiter.daily_tokens_used,
            'rate_limit_requests_per_minute': self.rate_limiter.requests_per_minute
        }