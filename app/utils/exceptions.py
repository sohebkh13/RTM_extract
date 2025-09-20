class RTMException(Exception):
    """Base exception for RTM Agent"""
    pass

class ExcelProcessingError(RTMException):
    """Excel file processing related errors"""
    pass

class AIAnalysisError(RTMException):
    """AI analysis related errors"""
    pass

class FileHandlingError(RTMException):
    """File handling related errors"""
    pass

class ConfigurationError(RTMException):
    """Configuration related errors"""
    pass

class RTMProcessingError(RTMException):
    """RTM processing related errors"""
    pass

class RTMProcessingError(RTMException):
    """RTM processing pipeline related errors"""
    pass
