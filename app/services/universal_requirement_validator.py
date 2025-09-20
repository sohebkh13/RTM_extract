"""
Universal Requirement Validator - Comprehensive requirement detection across all Excel formats
"""

import pandas as pd
import numpy as np
import re
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass
from app.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class RequirementCandidate:
    """Represents a potential requirement found in Excel"""
    content: str
    source_column: str
    row_index: int
    confidence_score: float
    category: str
    metadata: Dict[str, Any]
    is_valid_requirement: bool = False

class UniversalRequirementValidator:
    """
    Comprehensive validator that identifies ALL possible requirements
    across different Excel formats and structures.
    
    Handles:
    - Named and unnamed columns
    - Missing IDs and irregular numbering
    - Merged cells and complex formatting  
    - Multiple languages and character sets
    - Technical specifications and descriptive content
    - Edge cases and ambiguous content
    """
    
    def __init__(self):
        self.logger = logger
        
        # Comprehensive requirement indicators
        self.strong_requirement_words = {
            'shall', 'must', 'will', 'should', 'can', 'may', 'need to', 'able to',
            'required', 'mandatory', 'essential', 'necessary', 'obligatory'
        }
        
        self.technical_requirement_words = {
            'system', 'provide', 'support', 'manage', 'ensure', 'enable', 'allow',
            'capability', 'feature', 'function', 'functionality', 'service',
            'interface', 'protocol', 'api', 'database', 'security', 'authentication',
            'authorization', 'encryption', 'backup', 'monitoring', 'logging'
        }
        
        self.action_words = {
            'send', 'receive', 'process', 'handle', 'generate', 'create', 'delete',
            'update', 'modify', 'configure', 'install', 'deploy', 'monitor', 'track',
            'report', 'validate', 'verify', 'check', 'execute', 'perform', 'implement'
        }
        
        # Content exclusion patterns (things that are NOT requirements)
        self.exclusion_patterns = [
            r'^s\.?no\.?$',  # Serial number headers
            r'^no\.?$',      # Number headers
            r'^#\d*$',       # Just hash numbers
            r'^[A-Z]{1,3}$', # Short codes like FC, PC, NC
            r'^\d+$',        # Pure numbers
            r'^[.]+$',       # Just dots
            r'^[-]+$',       # Just dashes
            r'^[_]+$',       # Just underscores
            r'^vendor\s*response.*key',  # Response key explanations
            r'^page \d+',    # Page numbers
            r'^table \d+',   # Table references
        ]
        
        # Header/category indicators
        self.header_patterns = [
            r'^[A-Z\s]{3,20}$',  # All caps short phrases
            r'^##.*',            # Markdown headers
            r'^#.*',             # Hash headers
            r'.*requirements?$', # Ends with "requirement(s)"
            r'.*specifications?$', # Ends with "specification(s)"
        ]
        
    def validate_excel_requirements(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """
        Comprehensively analyze DataFrame to find ALL possible requirements
        
        Returns:
        - All requirement candidates with confidence scores
        - Validated requirements
        - Edge cases that need human review
        - Statistics and recommendations
        """
        
        self.logger.info(f"🔍 Starting comprehensive requirement validation for sheet '{sheet_name}'")
        
        results = {
            'sheet_name': sheet_name,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'requirement_candidates': [],
            'validated_requirements': [],
            'edge_cases': [],
            'headers_categories': [],
            'excluded_content': [],
            'statistics': {},
            'column_analysis': {}
        }
        
        # Analyze each column comprehensively
        for col_idx, col_name in enumerate(df.columns):
            column_analysis = self._analyze_column_comprehensively(df, col_name, col_idx)
            results['column_analysis'][col_name] = column_analysis
            
            # Extract all candidates from this column
            candidates = self._extract_candidates_from_column(df, col_name, col_idx)
            results['requirement_candidates'].extend(candidates)
            
        # Classify all candidates
        self._classify_candidates(results)
        
        # Generate statistics
        results['statistics'] = self._generate_statistics(results)
        
        self.logger.info(f"✅ Validation complete: {len(results['validated_requirements'])} requirements found")
        self.logger.info(f"📊 Additional candidates: {len(results['edge_cases'])} edge cases, {len(results['headers_categories'])} headers")
        
        return results
    
    def _analyze_column_comprehensively(self, df: pd.DataFrame, col_name: str, col_idx: int) -> Dict[str, Any]:
        """Analyze a single column for all possible requirement content"""
        
        analysis = {
            'column_name': col_name,
            'column_index': col_idx,
            'is_unnamed': 'unnamed' in col_name.lower(),
            'total_entries': len(df[col_name]),
            'non_empty_entries': df[col_name].count(),
            'empty_entries': df[col_name].isnull().sum(),
            'unique_values': df[col_name].nunique(),
            'potential_requirements': 0,
            'potential_headers': 0,
            'potential_metadata': 0,
            'content_types': set(),
            'confidence_level': 'unknown'
        }
        
        non_empty = df[col_name].dropna()
        if len(non_empty) == 0:
            return analysis
            
        # Analyze content patterns
        for value in non_empty:
            content_type = self._classify_content_type(str(value))
            analysis['content_types'].add(content_type)
            
            if content_type == 'requirement':
                analysis['potential_requirements'] += 1
            elif content_type == 'header':
                analysis['potential_headers'] += 1
            elif content_type == 'metadata':
                analysis['potential_metadata'] += 1
                
        # Determine confidence level
        req_ratio = analysis['potential_requirements'] / analysis['non_empty_entries'] if analysis['non_empty_entries'] > 0 else 0
        
        if req_ratio > 0.7:
            analysis['confidence_level'] = 'high'
        elif req_ratio > 0.3:
            analysis['confidence_level'] = 'medium'
        elif req_ratio > 0.1:
            analysis['confidence_level'] = 'low'
        else:
            analysis['confidence_level'] = 'very_low'
            
        return analysis
    
    def _extract_candidates_from_column(self, df: pd.DataFrame, col_name: str, col_idx: int) -> List[RequirementCandidate]:
        """Extract all potential requirement candidates from a column"""
        
        candidates = []
        non_empty = df[col_name].dropna()
        
        for row_idx, value in enumerate(non_empty):
            content = str(value).strip()
            
            # Skip very short or empty content
            if len(content) < 3:
                continue
                
            # Calculate confidence score
            confidence = self._calculate_confidence_score(content)
            category = self._classify_content_type(content)
            
            # Create metadata
            metadata = {
                'original_row': df.index[row_idx] if row_idx < len(df) else row_idx,
                'column_index': col_idx,
                'content_length': len(content),
                'word_count': len(content.split()),
                'has_numbers': any(c.isdigit() for c in content),
                'has_special_chars': bool(re.search(r'[•→◦✓✗○●]', content)),
                'is_all_caps': content.isupper(),
                'language_detected': self._detect_language_hints(content)
            }
            
            candidate = RequirementCandidate(
                content=content,
                source_column=col_name,
                row_index=row_idx,
                confidence_score=confidence,
                category=category,
                metadata=metadata
            )
            
            candidates.append(candidate)
            
        return candidates
    
    def _classify_content_type(self, content: str) -> str:
        """Classify content into requirement, header, metadata, etc."""
        
        content_lower = content.lower()
        content_clean = content.strip()
        
        # Check exclusion patterns first
        for pattern in self.exclusion_patterns:
            if re.match(pattern, content_lower, re.IGNORECASE):
                return 'excluded'
                
        # Check header patterns
        for pattern in self.header_patterns:
            if re.match(pattern, content_clean, re.IGNORECASE):
                return 'header'
                
        # Check requirement patterns
        
        # Strong requirement indicators
        if any(word in content_lower for word in self.strong_requirement_words):
            return 'requirement'
            
        # Technical requirement indicators
        if any(word in content_lower for word in self.technical_requirement_words):
            if len(content.split()) >= 3:  # Must have substance
                return 'requirement'
                
        # Action-oriented content
        if any(word in content_lower for word in self.action_words):
            if len(content.split()) >= 4:  # Must have context
                return 'requirement'
                
        # Descriptive content with substance
        if len(content.split()) >= 5:
            # Check if it's not just metadata
            if not content_clean.isdigit() and not content_clean.isupper():
                return 'descriptive'
                
        # Short but potentially meaningful
        if len(content.split()) >= 3:
            return 'short_meaningful'
            
        return 'metadata'
    
    def _calculate_confidence_score(self, content: str) -> float:
        """Calculate confidence score that this content is a requirement"""
        
        score = 0.0
        content_lower = content.lower()
        word_count = len(content.split())
        
        # Strong requirement words
        strong_matches = sum(1 for word in self.strong_requirement_words if word in content_lower)
        score += strong_matches * 0.3
        
        # Technical words
        tech_matches = sum(1 for word in self.technical_requirement_words if word in content_lower)
        score += tech_matches * 0.2
        
        # Action words
        action_matches = sum(1 for word in self.action_words if word in content_lower)
        score += action_matches * 0.15
        
        # Length bonus (substantial content)
        if word_count >= 5:
            score += 0.2
        elif word_count >= 3:
            score += 0.1
            
        # Penalty for likely exclusions
        if content.isupper() and word_count <= 3:
            score -= 0.3
            
        if content.isdigit():
            score -= 0.5
            
        # Cap at 1.0
        return min(1.0, max(0.0, score))
    
    def _classify_candidates(self, results: Dict[str, Any]) -> None:
        """Classify all candidates into final categories"""
        
        for candidate in results['requirement_candidates']:
            
            # High confidence requirements
            if candidate.confidence_score >= 0.7:
                candidate.is_valid_requirement = True
                results['validated_requirements'].append(candidate)
                
            # Medium confidence - potential requirements
            elif candidate.confidence_score >= 0.3:
                if candidate.category in ['requirement', 'descriptive', 'technical']:
                    candidate.is_valid_requirement = True
                    results['validated_requirements'].append(candidate)
                else:
                    results['edge_cases'].append(candidate)
                    
            # Low confidence - edge cases or headers
            elif candidate.confidence_score >= 0.1:
                if candidate.category == 'requirement':
                    results['edge_cases'].append(candidate)
                elif candidate.category == 'header':
                    results['headers_categories'].append(candidate)
                else:
                    results['edge_cases'].append(candidate)
                    
            # Very low confidence
            else:
                if candidate.category == 'header':
                    results['headers_categories'].append(candidate)
                elif candidate.category == 'excluded':
                    results['excluded_content'].append(candidate)
                else:
                    results['edge_cases'].append(candidate)
    
    def _detect_language_hints(self, content: str) -> str:
        """Detect potential non-English content"""
        
        # Basic detection - can be expanded
        if any(ord(char) > 127 for char in content):
            return 'non_english'
        return 'english'
    
    def _generate_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive statistics"""
        
        return {
            'total_candidates': len(results['requirement_candidates']),
            'validated_requirements': len(results['validated_requirements']),
            'edge_cases': len(results['edge_cases']),
            'headers_categories': len(results['headers_categories']),
            'excluded_content': len(results['excluded_content']),
            'confidence_distribution': self._calculate_confidence_distribution(results['requirement_candidates']),
            'category_distribution': self._calculate_category_distribution(results['requirement_candidates']),
            'column_contributions': self._calculate_column_contributions(results['requirement_candidates']),
            'recommendations': self._generate_recommendations(results)
        }
    
    def _calculate_confidence_distribution(self, candidates: List[RequirementCandidate]) -> Dict[str, int]:
        """Calculate confidence score distribution"""
        
        distribution = {'high': 0, 'medium': 0, 'low': 0, 'very_low': 0}
        
        for candidate in candidates:
            if candidate.confidence_score >= 0.7:
                distribution['high'] += 1
            elif candidate.confidence_score >= 0.3:
                distribution['medium'] += 1
            elif candidate.confidence_score >= 0.1:
                distribution['low'] += 1
            else:
                distribution['very_low'] += 1
                
        return distribution
    
    def _calculate_category_distribution(self, candidates: List[RequirementCandidate]) -> Dict[str, int]:
        """Calculate category distribution"""
        
        categories = {}
        for candidate in candidates:
            categories[candidate.category] = categories.get(candidate.category, 0) + 1
        return categories
    
    def _calculate_column_contributions(self, candidates: List[RequirementCandidate]) -> Dict[str, int]:
        """Calculate how many candidates each column contributes"""
        
        contributions = {}
        for candidate in candidates:
            col = candidate.source_column
            contributions[col] = contributions.get(col, 0) + 1
        return contributions
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving requirement extraction"""
        
        recommendations = []
        
        validated_count = len(results['validated_requirements'])
        edge_case_count = len(results['edge_cases'])
        
        if edge_case_count > validated_count * 0.3:
            recommendations.append("High number of edge cases detected - consider manual review")
            
        # Check for unnamed columns with high content
        for col_name, analysis in results['column_analysis'].items():
            if 'unnamed' in col_name.lower() and analysis['potential_requirements'] > 10:
                recommendations.append(f"Column '{col_name}' contains significant requirement content")
                
        if validated_count == 0:
            recommendations.append("No validated requirements found - check column selection or content patterns")
            
        return recommendations
    
    def get_lightweight_count(self, df: pd.DataFrame, sheet_name: str) -> int:
        """Fast requirement counting without full validation"""
        
        total_count = 0
        
        for col_name in df.columns:
            non_empty = df[col_name].dropna()
            for value in non_empty:
                content = str(value).strip()
                if len(content) >= 3:
                    score = self._calculate_confidence_score(content)
                    if score >= 0.3:  # Medium confidence threshold
                        total_count += 1
                        
        return total_count