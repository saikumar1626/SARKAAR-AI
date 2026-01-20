"""
SARKAAR Vision Module
AI-powered image analysis, OCR, code extraction, and diagram understanding

Capabilities:
- Screenshot analysis
- Code extraction from images
- Diagram interpretation
- Security vulnerability detection in UI screenshots
- Architecture diagram analysis
- Error message extraction
"""

import os
import sys
import json
import base64
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - VISION - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from PIL import Image
    import pytesseract
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not installed. Install: pip install Pillow pytesseract")

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not installed. Install: pip install opencv-python")


class SARKAARVision:
    """Main vision processing class"""
    
    def __init__(self):
        self.supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp']
        self.analysis_history = []
        logger.info("SARKAAR Vision Module initialized")
        
        # Check dependencies
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required libraries are installed"""
        issues = []
        
        if not PIL_AVAILABLE:
            issues.append("Pillow (PIL) - Install: pip install Pillow")
        
        if not CV2_AVAILABLE:
            issues.append("OpenCV - Install: pip install opencv-python")
        
        try:
            pytesseract.get_tesseract_version()
        except:
            issues.append("Tesseract OCR - Install: https://github.com/UB-Mannheim/tesseract/wiki")
        
        if issues:
            print("\n⚠️  Missing dependencies:")
            for issue in issues:
                print(f"  • {issue}")
            print()
    
    def analyze_image(self, image_path: str, analysis_type: str = "auto") -> Dict:
        """
        Main image analysis function
        
        Args:
            image_path: Path to image file
            analysis_type: "auto", "ocr", "code", "diagram", "security", "error"
        
        Returns:
            Dictionary with analysis results
        """
        if not os.path.exists(image_path):
            return {"error": f"Image not found: {image_path}"}
        
        file_ext = Path(image_path).suffix.lower()
        if file_ext not in self.supported_formats:
            return {"error": f"Unsupported format: {file_ext}"}
        
        logger.info(f"Analyzing image: {image_path} (type: {analysis_type})")
        
        try:
            # Load image
            if PIL_AVAILABLE:
                img = Image.open(image_path)
                img_array = np.array(img) if CV2_AVAILABLE else None
            else:
                return {"error": "PIL not installed"}
            
            # Perform analysis based on type
            if analysis_type == "auto":
                result = self._auto_detect_and_analyze(img, img_array, image_path)
            elif analysis_type == "ocr":
                result = self._extract_text(img)
            elif analysis_type == "code":
                result = self._extract_code(img)
            elif analysis_type == "diagram":
                result = self._analyze_diagram(img, img_array)
            elif analysis_type == "security":
                result = self._security_analysis(img, img_array)
            elif analysis_type == "error":
                result = self._extract_error_message(img)
            else:
                result = {"error": f"Unknown analysis type: {analysis_type}"}
            
            # Add metadata
            result['metadata'] = {
                'image_path': image_path,
                'image_size': img.size,
                'analysis_type': analysis_type,
                'timestamp': datetime.now().isoformat()
            }
            
            self.analysis_history.append(result)
            return result
        
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return {"error": str(e)}
    
    def _auto_detect_and_analyze(self, img: Image.Image, img_array, path: str) -> Dict:
        """Automatically detect content type and analyze"""
        logger.info("Auto-detecting image content type...")
        
        # Extract all text first
        text = self._extract_text_raw(img)
        
        # Detect content type
        content_type = self._detect_content_type(text, img)
        
        print(f"\n🔍 Detected content type: {content_type.upper()}\n")
        
        if content_type == "code":
            return self._extract_code(img)
        elif content_type == "error":
            return self._extract_error_message(img)
        elif content_type == "diagram":
            return self._analyze_diagram(img, img_array)
        elif content_type == "terminal":
            return self._analyze_terminal(img)
        else:
            return self._extract_text(img)
    
    def _detect_content_type(self, text: str, img: Image.Image) -> str:
        """Detect what type of content the image contains"""
        text_lower = text.lower()
        
        # Check for code indicators
        code_indicators = ['def ', 'class ', 'function', 'import ', 'const ', 'var ', 
                          'public ', 'private ', '{', '}', 'if(', 'for(', '<?php']
        if any(indicator in text_lower for indicator in code_indicators):
            return "code"
        
        # Check for error indicators
        error_indicators = ['error', 'exception', 'traceback', 'failed', 'warning',
                           'at line', 'syntax error', 'undefined']
        if any(indicator in text_lower for indicator in error_indicators):
            return "error"
        
        # Check for terminal/command prompt
        terminal_indicators = ['c:\\', 'ps ', '$ ', '~/', 'root@', 'admin@']
        if any(indicator in text_lower for indicator in terminal_indicators):
            return "terminal"
        
        # Check for diagram (fewer text, more shapes)
        if len(text.strip()) < 100:
            return "diagram"
        
        return "text"
    
    def _extract_text(self, img: Image.Image) -> Dict:
        """Extract all text using OCR"""
        try:
            text = pytesseract.image_to_string(img)
            
            result = {
                'type': 'text_extraction',
                'text': text.strip(),
                'line_count': len(text.strip().split('\n')),
                'word_count': len(text.strip().split()),
                'analysis': self._analyze_extracted_text(text)
            }
            
            self._print_text_result(result)
            return result
        
        except Exception as e:
            return {"error": f"OCR failed: {str(e)}"}
    
    def _extract_text_raw(self, img: Image.Image) -> str:
        """Extract text without formatting"""
        try:
            return pytesseract.image_to_string(img)
        except:
            return ""
    
    def _extract_code(self, img: Image.Image) -> Dict:
        """Extract and analyze code from image"""
        try:
            # Extract text with better code detection
            custom_config = r'--oem 3 --psm 6'
            code_text = pytesseract.image_to_string(img, config=custom_config)
            
            # Detect programming language
            language = self._detect_language(code_text)
            
            # Clean up OCR artifacts
            cleaned_code = self._clean_code_text(code_text)
            
            # Analyze code
            analysis = self._analyze_code(cleaned_code, language)
            
            result = {
                'type': 'code_extraction',
                'language': language,
                'code': cleaned_code,
                'analysis': analysis,
                'suggestion': self._get_code_suggestion(analysis)
            }
            
            self._print_code_result(result)
            return result
        
        except Exception as e:
            return {"error": f"Code extraction failed: {str(e)}"}
    
    def _detect_language(self, code: str) -> str:
        """Detect programming language"""
        code_lower = code.lower()
        
        if 'def ' in code and 'import ' in code:
            return 'Python'
        elif 'function' in code and ('{' in code or '}' in code):
            return 'JavaScript'
        elif 'public class' in code or 'private ' in code:
            return 'Java'
        elif '#include' in code or 'int main' in code:
            return 'C/C++'
        elif '<?php' in code:
            return 'PHP'
        elif 'SELECT' in code.upper() or 'INSERT' in code.upper():
            return 'SQL'
        elif 'echo' in code or 'ls' in code or 'cd ' in code:
            return 'Bash/Shell'
        else:
            return 'Unknown'
    
    def _clean_code_text(self, text: str) -> str:
        """Clean OCR artifacts from code"""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Remove empty lines
            if line.strip():
                # Fix common OCR mistakes
                line = line.replace('|', 'I')
                line = line.replace('O', '0') if any(c.isdigit() for c in line) else line
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _analyze_code(self, code: str, language: str) -> Dict:
        """Analyze extracted code"""
        return {
            'lines': len(code.split('\n')),
            'has_functions': 'def ' in code or 'function' in code,
            'has_classes': 'class ' in code,
            'has_comments': '#' in code or '//' in code or '/*' in code,
            'indentation_detected': code.startswith(' ' * 4) or code.startswith('\t')
        }
    
    def _get_code_suggestion(self, analysis: Dict) -> str:
        """Generate suggestions for code"""
        suggestions = []
        
        if not analysis['has_comments']:
            suggestions.append("Consider adding comments for better readability")
        
        if analysis['lines'] > 50:
            suggestions.append("Long code block - consider breaking into functions")
        
        return " | ".join(suggestions) if suggestions else "Code looks good"
    
    def _extract_error_message(self, img: Image.Image) -> Dict:
        """Extract and analyze error messages"""
        try:
            text = pytesseract.image_to_string(img)
            
            # Find error patterns
            errors = []
            lines = text.split('\n')
            
            for i, line in enumerate(lines):
                if any(keyword in line.lower() for keyword in ['error', 'exception', 'failed', 'traceback']):
                    errors.append({
                        'line': i + 1,
                        'message': line.strip(),
                        'type': self._classify_error(line)
                    })
            
            result = {
                'type': 'error_extraction',
                'errors_found': len(errors),
                'errors': errors,
                'full_text': text.strip(),
                'solution_hints': self._suggest_error_solutions(errors)
            }
            
            self._print_error_result(result)
            return result
        
        except Exception as e:
            return {"error": f"Error extraction failed: {str(e)}"}
    
    def _classify_error(self, error_line: str) -> str:
        """Classify error type"""
        error_lower = error_line.lower()
        
        if 'syntax' in error_lower:
            return 'Syntax Error'
        elif 'type' in error_lower:
            return 'Type Error'
        elif 'name' in error_lower:
            return 'Name Error'
        elif 'import' in error_lower:
            return 'Import Error'
        elif 'attribute' in error_lower:
            return 'Attribute Error'
        elif 'index' in error_lower:
            return 'Index Error'
        else:
            return 'General Error'
    
    def _suggest_error_solutions(self, errors: List[Dict]) -> List[str]:
        """Suggest solutions for common errors"""
        solutions = []
        
        for error in errors:
            error_type = error['type']
            
            if 'Syntax' in error_type:
                solutions.append("Check for missing brackets, quotes, or semicolons")
            elif 'Import' in error_type:
                solutions.append("Verify package is installed: pip install <package>")
            elif 'Name' in error_type:
                solutions.append("Check variable/function name spelling")
            elif 'Type' in error_type:
                solutions.append("Verify data types match expected values")
        
        return solutions[:3]  # Top 3 solutions
    
    def _analyze_diagram(self, img: Image.Image, img_array) -> Dict:
        """Analyze architecture diagrams and flowcharts"""
        try:
            text = pytesseract.image_to_string(img)
            
            # Detect diagram type
            diagram_type = self._detect_diagram_type(text, img)
            
            # Extract components
            components = self._extract_diagram_components(text)
            
            result = {
                'type': 'diagram_analysis',
                'diagram_type': diagram_type,
                'components': components,
                'text_content': text.strip(),
                'insights': self._generate_diagram_insights(diagram_type, components)
            }
            
            self._print_diagram_result(result)
            return result
        
        except Exception as e:
            return {"error": f"Diagram analysis failed: {str(e)}"}
    
    def _detect_diagram_type(self, text: str, img: Image.Image) -> str:
        """Detect type of diagram"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['database', 'db', 'server', 'api', 'client']):
            return 'Architecture Diagram'
        elif any(word in text_lower for word in ['start', 'end', 'decision', 'process']):
            return 'Flowchart'
        elif any(word in text_lower for word in ['class', 'interface', 'extends']):
            return 'UML Class Diagram'
        elif any(word in text_lower for word in ['user', 'system', 'actor']):
            return 'Use Case Diagram'
        else:
            return 'General Diagram'
    
    def _extract_diagram_components(self, text: str) -> List[str]:
        """Extract key components from diagram"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Filter out noise and keep meaningful components
        components = []
        for line in lines:
            if len(line) > 2 and not line.startswith(('|', '-', '+', '=')):
                components.append(line)
        
        return components[:10]  # Top 10 components
    
    def _generate_diagram_insights(self, diagram_type: str, components: List[str]) -> str:
        """Generate insights about the diagram"""
        if diagram_type == 'Architecture Diagram':
            return f"Identified {len(components)} system components. Review for security and scalability."
        elif diagram_type == 'Flowchart':
            return f"Process has {len(components)} steps. Consider optimization opportunities."
        else:
            return f"Diagram contains {len(components)} elements."
    
    def _analyze_terminal(self, img: Image.Image) -> Dict:
        """Analyze terminal/command prompt screenshots"""
        try:
            text = pytesseract.image_to_string(img)
            
            commands = []
            outputs = []
            
            lines = text.split('\n')
            for line in lines:
                if any(prompt in line for prompt in ['$', '>', 'PS', 'C:\\']):
                    commands.append(line.strip())
                else:
                    outputs.append(line.strip())
            
            result = {
                'type': 'terminal_analysis',
                'commands_found': len(commands),
                'commands': commands,
                'output': '\n'.join(outputs),
                'suggestions': self._analyze_terminal_commands(commands)
            }
            
            self._print_terminal_result(result)
            return result
        
        except Exception as e:
            return {"error": f"Terminal analysis failed: {str(e)}"}
    
    def _analyze_terminal_commands(self, commands: List[str]) -> List[str]:
        """Analyze terminal commands for security issues"""
        suggestions = []
        
        for cmd in commands:
            cmd_lower = cmd.lower()
            if 'sudo' in cmd_lower:
                suggestions.append("⚠️  Elevated privileges detected - ensure necessity")
            if 'rm -rf' in cmd_lower:
                suggestions.append("🚨 Destructive command detected - verify target")
            if 'chmod 777' in cmd_lower:
                suggestions.append("⚠️  Overly permissive permissions - security risk")
        
        return suggestions
    
    def _security_analysis(self, img: Image.Image, img_array) -> Dict:
        """Security-focused image analysis"""
        try:
            text = pytesseract.image_to_string(img)
            
            vulnerabilities = []
            
            # Check for exposed credentials
            if any(keyword in text.lower() for keyword in ['password', 'api_key', 'secret', 'token']):
                vulnerabilities.append({
                    'severity': 'HIGH',
                    'type': 'Exposed Credentials',
                    'description': 'Potential credentials visible in screenshot'
                })
            
            # Check for sensitive URLs
            if 'http://' in text and 'https://' not in text:
                vulnerabilities.append({
                    'severity': 'MEDIUM',
                    'type': 'Insecure Protocol',
                    'description': 'HTTP detected instead of HTTPS'
                })
            
            result = {
                'type': 'security_analysis',
                'vulnerabilities_found': len(vulnerabilities),
                'vulnerabilities': vulnerabilities,
                'risk_level': 'HIGH' if len(vulnerabilities) > 0 else 'LOW',
                'recommendation': self._get_security_recommendation(vulnerabilities)
            }
            
            self._print_security_result(result)
            return result
        
        except Exception as e:
            return {"error": f"Security analysis failed: {str(e)}"}
    
    def _get_security_recommendation(self, vulnerabilities: List[Dict]) -> str:
        """Generate security recommendations"""
        if not vulnerabilities:
            return "✅ No obvious security issues detected"
        
        high_severity = any(v['severity'] == 'HIGH' for v in vulnerabilities)
        if high_severity:
            return "🚨 CRITICAL: Remove sensitive data before sharing screenshots"
        else:
            return "⚠️  Review security concerns before public sharing"
    
    def _analyze_extracted_text(self, text: str) -> Dict:
        """Analyze extracted text content"""
        return {
            'contains_code': any(keyword in text for keyword in ['def ', 'function', 'class ']),
            'contains_urls': 'http' in text.lower(),
            'contains_emails': '@' in text and '.' in text,
            'language_detected': 'English'  # Simple detection
        }
    
    # Print methods for better visualization
    def _print_text_result(self, result: Dict):
        print(f"{'='*70}")
        print("TEXT EXTRACTION RESULTS")
        print(f"{'='*70}")
        print(f"Lines: {result['line_count']}")
        print(f"Words: {result['word_count']}")
        print(f"\nExtracted Text:\n{result['text'][:500]}...")
        print(f"{'='*70}\n")
    
    def _print_code_result(self, result: Dict):
        print(f"{'='*70}")
        print("CODE EXTRACTION RESULTS")
        print(f"{'='*70}")
        print(f"Language: {result['language']}")
        print(f"Lines: {result['analysis']['lines']}")
        print(f"\n{result['suggestion']}")
        print(f"\nExtracted Code:\n{result['code']}")
        print(f"{'='*70}\n")
    
    def _print_error_result(self, result: Dict):
        print(f"{'='*70}")
        print("ERROR ANALYSIS")
        print(f"{'='*70}")
        print(f"Errors found: {result['errors_found']}")
        for error in result['errors']:
            print(f"\n{error['type']}: {error['message']}")
        if result['solution_hints']:
            print(f"\n💡 Suggestions:")
            for hint in result['solution_hints']:
                print(f"  • {hint}")
        print(f"{'='*70}\n")
    
    def _print_diagram_result(self, result: Dict):
        print(f"{'='*70}")
        print("DIAGRAM ANALYSIS")
        print(f"{'='*70}")
        print(f"Type: {result['diagram_type']}")
        print(f"Components: {len(result['components'])}")
        print(f"\n{result['insights']}")
        print(f"{'='*70}\n")
    
    def _print_terminal_result(self, result: Dict):
        print(f"{'='*70}")
        print("TERMINAL ANALYSIS")
        print(f"{'='*70}")
        print(f"Commands found: {result['commands_found']}")
        if result['suggestions']:
            print("\n⚠️  Security Alerts:")
            for suggestion in result['suggestions']:
                print(f"  {suggestion}")
        print(f"{'='*70}\n")
    
    def _print_security_result(self, result: Dict):
        print(f"{'='*70}")
        print("SECURITY ANALYSIS")
        print(f"{'='*70}")
        print(f"Risk Level: {result['risk_level']}")
        print(f"Vulnerabilities: {result['vulnerabilities_found']}")
        for vuln in result['vulnerabilities']:
            print(f"\n[{vuln['severity']}] {vuln['type']}")
            print(f"  {vuln['description']}")
        print(f"\n{result['recommendation']}")
        print(f"{'='*70}\n")


def main():
    """Interactive vision module interface"""
    vision = SARKAARVision()
    
    print("\n" + "="*70)
    print("🔍 SARKAAR VISION MODULE")
    print("="*70)
    print("AI-Powered Image Analysis")
    print("="*70 + "\n")
    
    while True:
        print("\nVISION COMMAND CENTER")
        print("="*70)
        print("1. Analyze Image (Auto-detect)")
        print("2. Extract Text (OCR)")
        print("3. Extract Code")
        print("4. Analyze Diagram")
        print("5. Security Analysis")
        print("6. Extract Error Messages")
        print("7. View Analysis History")
        print("8. Exit")
        print("="*70)
        
        choice = input("\nSelect option (1-8): ").strip()
        
        if choice == '1':
            path = input("Enter image path: ").strip().strip('"').strip("'")
            if path:
                vision.analyze_image(path, "auto")
        
        elif choice == '2':
            path = input("Enter image path: ").strip().strip('"').strip("'")
            if path:
                vision.analyze_image(path, "ocr")
        
        elif choice == '3':
            path = input("Enter image path: ").strip().strip('"').strip("'")
            if path:
                vision.analyze_image(path, "code")
        
        elif choice == '4':
            path = input("Enter image path: ").strip().strip('"').strip("'")
            if path:
                vision.analyze_image(path, "diagram")
        
        elif choice == '5':
            path = input("Enter image path: ").strip().strip('"').strip("'")
            if path:
                vision.analyze_image(path, "security")
        
        elif choice == '6':
            path = input("Enter image path: ").strip().strip('"').strip("'")
            if path:
                vision.analyze_image(path, "error")
        
        elif choice == '7':
            print(f"\n📊 Analysis History: {len(vision.analysis_history)} items")
            for i, analysis in enumerate(vision.analysis_history[-5:], 1):
                print(f"{i}. {analysis.get('type', 'unknown')} - {analysis.get('metadata', {}).get('timestamp', 'N/A')}")
        
        elif choice == '8':
            print("\n👋 Vision module shutting down!")
            break
        
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Goodbye!")
        sys.exit(0)