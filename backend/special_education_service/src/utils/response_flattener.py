"""Response flattener to prevent [object Object] errors in frontend"""

import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class SimpleIEPFlattener:
    """
    Lightweight flattener that prevents [object Object] errors by converting
    complex nested structures to frontend-friendly formats.
    
    Designed to work with existing architecture without breaking changes.
    """
    
    def __init__(self, enable_detailed_logging: bool = None):
        """
        Initialize flattener with optional detailed logging.
        
        Args:
            enable_detailed_logging: If None, reads from env var FLATTENER_DETAILED_LOGGING
        """
        self.logger = logging.getLogger(__name__)
        
        # Configuration from environment
        self.enabled = os.getenv('ENABLE_FLATTENER', 'true').lower() == 'true'
        self.detailed_logging = (
            enable_detailed_logging if enable_detailed_logging is not None 
            else os.getenv('FLATTENER_DETAILED_LOGGING', 'true').lower() == 'true'
        )
        self.max_log_length = int(os.getenv('FLATTENER_MAX_LOG_LENGTH', '500'))
        
        # Statistics tracking
        self.stats = {
            'total_operations': 0,
            'total_structures_flattened': 0,
            'total_time_ms': 0,
            'error_count': 0,
            'complex_structures_detected': 0
        }
        
        self.logger.info(f"flattener_initialized: enabled={self.enabled}, detailed_logging={self.detailed_logging}, max_log_length={self.max_log_length}")
    
    @staticmethod
    def flatten_for_frontend(iep_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Static method for backward compatibility and simple usage.
        
        Args:
            iep_data: IEP response data from backend
            
        Returns:
            Flattened IEP data safe for frontend consumption
        """
        # Use the global instance for statistics tracking
        global _global_flattener
        return _global_flattener.flatten(iep_data)
    
    def flatten(self, iep_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main flattening method with comprehensive logging.
        
        Args:
            iep_data: IEP response data from backend
            
        Returns:
            Flattened IEP data safe for frontend consumption
        """
        # Early validation for non-dict inputs
        if not isinstance(iep_data, dict):
            if self.detailed_logging:
                self.logger.error(f"invalid_input_type: expected dict, got {type(iep_data).__name__}")
            self.stats['error_count'] += 1
            return iep_data
        
        if not self.enabled:
            self.logger.debug(f"flattener_disabled for iep_id={iep_data.get('id', 'unknown')}")
            return iep_data
        
        start_time = time.time()
        iep_id = iep_data.get('id', 'unknown')
        student_id = iep_data.get('student_id', 'unknown')
        
        self.logger.info(f"flattening_started: iep_id={iep_id}, student_id={student_id}, input_size={len(str(iep_data))}")
        
        try:
            
            # Check if content section exists
            if 'content' not in iep_data:
                self.logger.info(f"no_content_section: iep_id={iep_id}, available_keys={list(iep_data.keys())}")
                return iep_data
            
            # Create deep copy to avoid modifying original
            flattened_data = self._deep_copy_dict(iep_data)
            
            # Analyze complex structures before flattening
            problem_analysis = self._analyze_complex_structures(flattened_data['content'])
            
            if problem_analysis['problems_found']:
                self.logger.warning(f"complex_structures_detected: iep_id={iep_id}, student_id={student_id}, total_problems={len(problem_analysis['problems'])}")
                if self.detailed_logging:
                    self.logger.debug(f"problems_detail: {problem_analysis['problems']}")
                self.stats['complex_structures_detected'] += len(problem_analysis['problems'])
            
            # Apply flattening transformations
            flattened_content, transformation_summary = self._flatten_content(
                flattened_data['content'], 
                iep_id, 
                student_id
            )
            
            flattened_data['content'] = flattened_content
            
            # Add transformation metadata if detailed logging enabled
            if self.detailed_logging:
                flattened_data['_transformation_metadata'] = {
                    'flattened_at': datetime.utcnow().isoformat(),
                    'transformation_summary': transformation_summary,
                    'problems_detected': problem_analysis['problems'],
                    'flattener_version': '1.0.0'
                }
            
            # Performance and success logging
            duration_ms = (time.time() - start_time) * 1000
            self.stats['total_operations'] += 1
            self.stats['total_structures_flattened'] += transformation_summary['total_transformed']
            self.stats['total_time_ms'] += duration_ms
            
            input_size = len(str(iep_data))
            output_size = len(str(flattened_data))
            size_change_percent = round(((output_size - input_size) / input_size) * 100, 2)
            
            self.logger.info(f"flattening_completed: iep_id={iep_id}, student_id={student_id}, duration_ms={round(duration_ms, 2)}, structures_flattened={transformation_summary['total_transformed']}, size_change={size_change_percent}%")
            
            # Log transformation details if enabled
            if self.detailed_logging and transformation_summary['total_transformed'] > 0:
                self.logger.debug(f"transformation_details: iep_id={iep_id}, transformations={transformation_summary['transformations']}")
            
            return flattened_data
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.stats['error_count'] += 1
            
            self.logger.error(f"flattening_failed: iep_id={iep_id}, student_id={student_id}, duration_ms={round(duration_ms, 2)}, error={str(e)}, error_type={type(e).__name__}", exc_info=True)
            
            # Return original data on error
            return iep_data
    
    def _analyze_complex_structures(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze content for complex structures that cause [object Object] errors.
        
        Args:
            content: Content section of IEP data
            
        Returns:
            Analysis results with problems found
        """
        problems = []
        
        for key, value in content.items():
            problem_info = self._check_for_problem_patterns(key, value)
            if problem_info:
                problems.append(problem_info)
        
        return {
            'problems_found': len(problems) > 0,
            'problems': problems,
            'total_keys_analyzed': len(content)
        }
    
    def _check_for_problem_patterns(self, key: str, value: Any) -> Optional[Dict[str, Any]]:
        """
        Check if a key-value pair matches known problematic patterns.
        
        Args:
            key: The key being checked
            value: The value being checked
            
        Returns:
            Problem information if found, None otherwise
        """
        # Triple-nested services pattern
        if key == 'services' and isinstance(value, dict) and 'services' in value:
            nested_services = value['services']
            if isinstance(nested_services, dict):
                return {
                    'key': key,
                    'pattern': 'triple_nested_services',
                    'description': 'services.services.{category} structure',
                    'value_type': type(value).__name__,
                    'nested_keys': list(nested_services.keys()) if isinstance(nested_services, dict) else None
                }
        
        # Double-nested present_levels pattern
        if key == 'present_levels' and isinstance(value, dict) and 'present_levels' in value:
            return {
                'key': key,
                'pattern': 'double_nested_present_levels',
                'description': 'present_levels.present_levels structure',
                'value_type': type(value).__name__,
                'nested_value_type': type(value['present_levels']).__name__
            }
        
        # Complex assessment_summary objects
        if key == 'assessment_summary' and isinstance(value, dict) and len(value) > 3:
            return {
                'key': key,
                'pattern': 'complex_assessment_object',
                'description': f'Complex object with {len(value)} fields',
                'value_type': type(value).__name__,
                'field_count': len(value)
            }
        
        # Arrays of complex objects
        if isinstance(value, list) and len(value) > 0:
            complex_objects = [item for item in value if isinstance(item, dict)]
            if len(complex_objects) > 0:
                return {
                    'key': key,
                    'pattern': 'array_of_complex_objects',
                    'description': f'Array containing {len(complex_objects)} complex objects',
                    'value_type': type(value).__name__,
                    'array_length': len(value),
                    'complex_objects_count': len(complex_objects)
                }
        
        # Generic complex objects (fallback)
        if isinstance(value, dict) and len(value) > 5:
            return {
                'key': key,
                'pattern': 'generic_complex_object',
                'description': f'Large object with {len(value)} fields',
                'value_type': type(value).__name__,
                'field_count': len(value)
            }
        
        return None
    
    def _flatten_content(self, content: Dict[str, Any], iep_id: str, student_id: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Apply flattening transformations to content.
        
        Args:
            content: Content section to flatten
            iep_id: IEP ID for logging
            student_id: Student ID for logging
            
        Returns:
            Tuple of (flattened_content, transformation_summary)
        """
        flattened_content = {}
        transformations = []
        
        # Known problematic fields and their transformation strategies
        PROBLEM_FIELDS = {
            'services': self._flatten_services,
            'present_levels': self._flatten_present_levels,
            'assessment_summary': self._flatten_assessment_summary,
            'goals': self._flatten_goals,
            'accommodations': self._flatten_accommodations,
            'transition_planning': self._flatten_transition_planning
        }
        
        for key, value in content.items():
            try:
                if key in PROBLEM_FIELDS:
                    # Apply specific transformation
                    flattened_value, transformation_info = PROBLEM_FIELDS[key](value, key)
                    flattened_content[key] = flattened_value
                    
                    if transformation_info:
                        transformations.append(transformation_info)
                        
                        if self.detailed_logging:
                            self.logger.debug(f"field_transformed: iep_id={iep_id}, student_id={student_id}, field={key}, strategy={transformation_info['strategy']}, {transformation_info['original_type']}->{transformation_info['result_type']}")
                else:
                    # Keep simple values as-is
                    flattened_content[key] = value
                    
            except Exception as e:
                self.logger.error(f"field_transformation_failed: iep_id={iep_id}, student_id={student_id}, field={key}, error={str(e)}, error_type={type(e).__name__}")
                # Keep original value if transformation fails
                flattened_content[key] = value
        
        transformation_summary = {
            'total_transformed': len(transformations),
            'transformations': transformations,
            'fields_processed': len(content),
            'fields_kept_original': len(content) - len(transformations)
        }
        
        return flattened_content, transformation_summary
    
    def _flatten_services(self, value: Any, key: str) -> Tuple[Any, Optional[Dict[str, Any]]]:
        """Flatten services structure"""
        if isinstance(value, dict) and 'services' in value:
            nested_services = value['services']
            if isinstance(nested_services, dict):
                # Convert to list of formatted strings
                service_list = []
                for category, items in nested_services.items():
                    if isinstance(items, list):
                        for item in items:
                            if isinstance(item, dict):
                                service_text = self._format_service_item(category, item)
                                service_list.append(service_text)
                            else:
                                service_list.append(f"{category}: {str(item)}")
                    else:
                        service_list.append(f"{category}: {str(items)}")
                
                result = '\n'.join(service_list) if service_list else str(value)
                return result, {
                    'field': key,
                    'strategy': 'triple_nested_to_formatted_list',
                    'original_type': 'dict',
                    'result_type': 'str',
                    'items_processed': len(service_list)
                }
        
        # Fallback for other complex service structures
        if isinstance(value, dict):
            return json.dumps(value, indent=2), {
                'field': key,
                'strategy': 'dict_to_json_string',
                'original_type': 'dict',
                'result_type': 'str',
                'fallback': True
            }
        
        return value, None
    
    def _flatten_present_levels(self, value: Any, key: str) -> Tuple[Any, Optional[Dict[str, Any]]]:
        """Flatten present_levels structure"""
        if isinstance(value, dict) and 'present_levels' in value:
            # Extract the nested value
            nested_value = value['present_levels']
            return nested_value, {
                'field': key,
                'strategy': 'extract_nested_value',
                'original_type': 'dict',
                'result_type': type(nested_value).__name__,
                'extracted_key': 'present_levels'
            }
        
        # Fallback for other complex present_levels structures
        if isinstance(value, dict):
            return json.dumps(value, indent=2), {
                'field': key,
                'strategy': 'dict_to_json_string',
                'original_type': 'dict',
                'result_type': 'str',
                'fallback': True
            }
        
        return value, None
    
    def _flatten_assessment_summary(self, value: Any, key: str) -> Tuple[Any, Optional[Dict[str, Any]]]:
        """Flatten assessment_summary structure"""
        if isinstance(value, dict):
            return json.dumps(value, indent=2), {
                'field': key,
                'strategy': 'dict_to_formatted_json',
                'original_type': 'dict',
                'result_type': 'str',
                'field_count': len(value)
            }
        
        return value, None
    
    def _flatten_goals(self, value: Any, key: str) -> Tuple[Any, Optional[Dict[str, Any]]]:
        """Flatten goals structure"""
        if isinstance(value, list):
            # Check if list contains complex objects
            has_complex_objects = any(isinstance(item, dict) for item in value)
            if has_complex_objects:
                return json.dumps(value, indent=2), {
                    'field': key,
                    'strategy': 'list_with_objects_to_json',
                    'original_type': 'list',
                    'result_type': 'str',
                    'items_count': len(value)
                }
        elif isinstance(value, dict):
            return json.dumps(value, indent=2), {
                'field': key,
                'strategy': 'dict_to_json_string',
                'original_type': 'dict',
                'result_type': 'str'
            }
        
        return value, None
    
    def _flatten_accommodations(self, value: Any, key: str) -> Tuple[Any, Optional[Dict[str, Any]]]:
        """Flatten accommodations structure"""
        if isinstance(value, (dict, list)):
            return json.dumps(value, indent=2), {
                'field': key,
                'strategy': 'complex_structure_to_json',
                'original_type': type(value).__name__,
                'result_type': 'str'
            }
        
        return value, None
    
    def _flatten_transition_planning(self, value: Any, key: str) -> Tuple[Any, Optional[Dict[str, Any]]]:
        """Flatten transition_planning structure"""
        if isinstance(value, dict):
            return json.dumps(value, indent=2), {
                'field': key,
                'strategy': 'dict_to_formatted_json',
                'original_type': 'dict',
                'result_type': 'str',
                'field_count': len(value)
            }
        
        return value, None
    
    def _format_service_item(self, category: str, item: Dict[str, Any]) -> str:
        """Format a service item into a readable string"""
        name = item.get('name', 'Unknown Service')
        frequency = item.get('frequency', '')
        duration = item.get('duration', '')
        
        parts = [f"{category}: {name}"]
        if frequency:
            parts.append(f"Frequency: {frequency}")
        if duration:
            parts.append(f"Duration: {duration}")
        
        return " - ".join(parts)
    
    def _deep_copy_dict(self, original: Dict[str, Any]) -> Dict[str, Any]:
        """Create a deep copy of dictionary to avoid modifying original"""
        try:
            return json.loads(json.dumps(original))
        except (TypeError, ValueError) as e:
            if self.detailed_logging:
                self.logger.warning(f"deep_copy_fallback: error={str(e)}, using_shallow_copy=True")
            return original.copy()
    
    def _truncate_for_log(self, text: str) -> str:
        """Truncate text for logging to prevent log spam"""
        if len(text) <= self.max_log_length:
            return text
        return text[:self.max_log_length] + "... (truncated)"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get flattener performance statistics"""
        if self.stats['total_operations'] > 0:
            avg_time = self.stats['total_time_ms'] / self.stats['total_operations']
            avg_structures = self.stats['total_structures_flattened'] / self.stats['total_operations']
        else:
            avg_time = 0
            avg_structures = 0
        
        return {
            'total_operations': self.stats['total_operations'],
            'total_structures_flattened': self.stats['total_structures_flattened'],
            'total_time_ms': round(self.stats['total_time_ms'], 2),
            'error_count': self.stats['error_count'],
            'complex_structures_detected': self.stats['complex_structures_detected'],
            'average_time_per_operation_ms': round(avg_time, 2),
            'average_structures_per_operation': round(avg_structures, 2),
            'error_rate': self.stats['error_count'] / self.stats['total_operations'] if self.stats['total_operations'] > 0 else 0
        }
    
    def reset_statistics(self):
        """Reset performance statistics"""
        self.stats = {
            'total_operations': 0,
            'total_structures_flattened': 0,
            'total_time_ms': 0,
            'error_count': 0,
            'complex_structures_detected': 0
        }
        self.logger.info("flattener_statistics_reset")


# Module-level instance for global statistics tracking
_global_flattener = SimpleIEPFlattener()

def get_flattener_statistics() -> Dict[str, Any]:
    """Get global flattener statistics"""
    return _global_flattener.get_statistics()

def reset_flattener_statistics():
    """Reset global flattener statistics"""
    _global_flattener.reset_statistics()