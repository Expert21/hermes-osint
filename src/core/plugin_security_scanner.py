# -----------------------------------------------------------------------------
# Hermes OSINT - Plugin Security Scanner
# -----------------------------------------------------------------------------

import ast
import logging
from dataclasses import dataclass
from typing import List, Optional

logger = logging.getLogger(__name__)

@dataclass
class SecurityViolation:
    rule: str
    severity: str  # "error" or "warning"
    line_number: int
    code_snippet: str
    message: str

@dataclass
class ScanResult:
    passed: bool
    confidence: float  # 0.0 to 1.0
    errors: List[SecurityViolation]
    warnings: List[SecurityViolation]

class SecurityVisitor(ast.NodeVisitor):
    def __init__(self, source_code: str):
        self.source_code = source_code.splitlines()
        self.errors: List[SecurityViolation] = []
        self.warnings: List[SecurityViolation] = []

    def _get_snippet(self, lineno: int) -> str:
        if 0 < lineno <= len(self.source_code):
            return self.source_code[lineno - 1].strip()
        return ""

    def visit_Call(self, node: ast.Call):
        # Check for function calls
        if isinstance(node.func, ast.Attribute):
            # os.system()
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'os' and node.func.attr == 'system':
                self.errors.append(SecurityViolation(
                    rule="Command Injection",
                    severity="error",
                    line_number=node.lineno,
                    code_snippet=self._get_snippet(node.lineno),
                    message="Direct use of os.system() is forbidden. Use ExecutionStrategy."
                ))
            
            # subprocess.run(..., shell=True)
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'subprocess' and node.func.attr == 'run':
                for keyword in node.keywords:
                    if keyword.arg == 'shell' and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                        self.errors.append(SecurityViolation(
                            rule="Command Injection",
                            severity="error",
                            line_number=node.lineno,
                            code_snippet=self._get_snippet(node.lineno),
                            message="subprocess.run(shell=True) is forbidden."
                        ))

            # requests.get/post/etc (Network Access)
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'requests':
                self.errors.append(SecurityViolation(
                    rule="Network Access",
                    severity="error",
                    line_number=node.lineno,
                    code_snippet=self._get_snippet(node.lineno),
                    message="Direct network calls via requests are forbidden. Use ExecutionStrategy."
                ))

            # urllib.request (Network Access)
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'urllib' and node.func.attr == 'request':
                self.errors.append(SecurityViolation(
                    rule="Network Access",
                    severity="error",
                    line_number=node.lineno,
                    code_snippet=self._get_snippet(node.lineno),
                    message="Direct network calls via urllib are forbidden. Use ExecutionStrategy."
                ))

            # os.environ.get (Credential Access)
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'os' and node.func.attr == 'environ':
                 self.warnings.append(SecurityViolation(
                    rule="Credential Access",
                    severity="warning",
                    line_number=node.lineno,
                    code_snippet=self._get_snippet(node.lineno),
                    message="Direct access to os.environ detected. Ensure secrets are accessed via SecretsManager."
                ))

        # Check for eval/exec
        if isinstance(node.func, ast.Name):
            if node.func.id in ['eval', 'exec']:
                self.errors.append(SecurityViolation(
                    rule="Dangerous Builtin",
                    severity="error",
                    line_number=node.lineno,
                    code_snippet=self._get_snippet(node.lineno),
                    message=f"Use of {node.func.id}() is forbidden."
                ))
            
            # open()
            if node.func.id == 'open':
                self.warnings.append(SecurityViolation(
                    rule="File System Access",
                    severity="warning",
                    line_number=node.lineno,
                    code_snippet=self._get_snippet(node.lineno),
                    message="Direct file access via open(). Ensure you are writing to allowed directories."
                ))

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name in ['socket', 'telnetlib', 'ftplib']:
                self.errors.append(SecurityViolation(
                    rule="Dangerous Import",
                    severity="error",
                    line_number=node.lineno,
                    code_snippet=self._get_snippet(node.lineno),
                    message=f"Importing {alias.name} is forbidden. Use ExecutionStrategy."
                ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module in ['socket', 'telnetlib', 'ftplib']:
             self.errors.append(SecurityViolation(
                rule="Dangerous Import",
                severity="error",
                line_number=node.lineno,
                code_snippet=self._get_snippet(node.lineno),
                message=f"Importing from {node.module} is forbidden. Use ExecutionStrategy."
            ))
        self.generic_visit(node)


class PluginSecurityScanner:
    """
    Static analysis engine for Hermes plugins.
    """

    def scan_file(self, file_path: str, plugin_type: str = "tool") -> ScanResult:
        """
        Scan a single python file for security violations.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            visitor = SecurityVisitor(source_code)
            visitor.visit(tree)
            
            errors = visitor.errors
            warnings = visitor.warnings
            
            # Calculate confidence
            # Start at 1.0
            # Each error: -0.5 (effectively 0 if > 1)
            # Each warning: -0.1
            confidence = 1.0
            if errors:
                confidence -= (len(errors) * 0.5)
            if warnings:
                confidence -= (len(warnings) * 0.1)
            
            confidence = max(0.0, confidence)
            
            # Pass/Fail logic
            passed = False
            if plugin_type == "core":
                # Core plugins must be perfect
                passed = (len(errors) == 0 and len(warnings) == 0)
            else:
                # Tool plugins can have warnings but no errors, and decent confidence
                passed = (len(errors) == 0 and confidence >= 0.7)
                
            return ScanResult(
                passed=passed,
                confidence=confidence,
                errors=errors,
                warnings=warnings
            )
            
        except SyntaxError as e:
            return ScanResult(
                passed=False,
                confidence=0.0,
                errors=[SecurityViolation(
                    rule="Syntax Error",
                    severity="error",
                    line_number=e.lineno or 0,
                    code_snippet=str(e.text).strip() if e.text else "",
                    message=f"Syntax error in plugin code: {e.msg}"
                )],
                warnings=[]
            )
        except Exception as e:
            logger.error(f"Failed to scan {file_path}: {e}")
            return ScanResult(
                passed=False,
                confidence=0.0,
                errors=[SecurityViolation(
                    rule="Scanner Error",
                    severity="error",
                    line_number=0,
                    code_snippet="",
                    message=f"Scanner crashed: {str(e)}"
                )],
                warnings=[]
            )
