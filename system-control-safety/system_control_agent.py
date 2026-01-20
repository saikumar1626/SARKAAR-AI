# system_control_agent.py
"""
Safe System Control Agent for Sarkar AI Assistant
Handles: app launching, file management, terminal commands
Security: allowlists, permission checks, sandboxing, audit logging
"""

import os
import sys
import subprocess
import shutil
import logging
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import platform


logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """Permission levels for system operations"""
    ALWAYS_ALLOW = "always_allow"  # No prompt needed
    ASK_ONCE = "ask_once"  # Ask first time, remember
    ASK_ALWAYS = "ask_always"  # Always require confirmation
    NEVER_ALLOW = "never_allow"  # Blocked


class CommandCategory(Enum):
    """Categories of system commands"""
    FILE_READ = "file_read"
    FILE_WRITE = "file_write"
    FILE_DELETE = "file_delete"
    APP_LAUNCH = "app_launch"
    SYSTEM_INFO = "system_info"
    NETWORK = "network"
    PROCESS = "process"


@dataclass
class CommandRule:
    """Security rule for a command"""
    pattern: str  # Command pattern (e.g., "ls", "open *")
    category: CommandCategory
    permission: PermissionLevel
    description: str
    max_execution_time: int = 30  # seconds
    allow_sudo: bool = False


@dataclass
class AuditLog:
    """Audit log entry for system operations"""
    timestamp: str
    user_id: str
    command: str
    category: str
    approved: bool
    result: str
    error: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


class SafePathValidator:
    """Validates file paths to prevent directory traversal and unauthorized access"""
    
    def __init__(self, allowed_base_dirs: Optional[List[str]] = None):
        if allowed_base_dirs is None:
            # Windows-compatible default paths
            home = str(Path.home())
            if platform.system() == "Windows":
                allowed_base_dirs = [
                    home,
                    str(Path.cwd()),  # Current working directory
                    os.environ.get("TEMP", "C:\\Windows\\Temp"),
                    "D:\\",  # Common data drive
                    "C:\\Users",
                ]
            else:
                allowed_base_dirs = [home, "/tmp", str(Path.cwd())]
        
        self.allowed_base_dirs = [str(Path(d).resolve()) for d in allowed_base_dirs]
        
        # Forbidden paths (system-critical)
        if platform.system() == "Windows":
            self.forbidden_paths = [
                "C:\\Windows\\System32",
                "C:\\Windows\\SysWOW64",
                "C:\\Program Files\\WindowsApps",
                "C:\\ProgramData",
            ]
        else:
            self.forbidden_paths = [
                "/etc/passwd",
                "/etc/shadow",
                "/System",
                "/root",
                "/.ssh",
            ]
    
    def is_safe_path(self, path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a path is safe to access
        Returns: (is_safe, error_message)
        """
        try:
            # Resolve to absolute path and normalize
            abs_path = Path(path).resolve()
            
            # Check forbidden paths
            for forbidden in self.forbidden_paths:
                if str(abs_path).startswith(forbidden):
                    return False, f"Access denied: {forbidden} is protected"
            
            # Check if within allowed base directories
            is_allowed = any(
                str(abs_path).startswith(base_dir)
                for base_dir in self.allowed_base_dirs
            )
            
            if not is_allowed:
                return False, f"Path outside allowed directories"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid path: {str(e)}"


class CommandAllowlist:
    """Manages allowed commands and their security rules"""
    
    def __init__(self, config_path: str = "command_allowlist.json"):
        self.config_path = config_path
        self.rules: Dict[str, CommandRule] = {}
        self._load_rules()
    
    def _load_rules(self):
        """Load command rules from config"""
        try:
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                for key, rule_data in data.items():
                    rule_data['category'] = CommandCategory(rule_data['category'])
                    rule_data['permission'] = PermissionLevel(rule_data['permission'])
                    self.rules[key] = CommandRule(**rule_data)
            logger.info(f"Loaded {len(self.rules)} command rules")
        except FileNotFoundError:
            logger.warning("No allowlist found, initializing defaults")
            self._initialize_default_rules()
    
    def _save_rules(self):
        """Persist rules to storage"""
        data = {}
        for key, rule in self.rules.items():
            rule_dict = asdict(rule)
            rule_dict['category'] = rule.category.value
            rule_dict['permission'] = rule.permission.value
            data[key] = rule_dict
        
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _initialize_default_rules(self):
        """Set up default safe command rules"""
        os_type = platform.system()
        
        # Common commands
        defaults = {
            # Safe read operations (cross-platform)
            "ls": CommandRule("ls", CommandCategory.FILE_READ, PermissionLevel.ALWAYS_ALLOW, "List directory contents"),
            "dir": CommandRule("dir", CommandCategory.FILE_READ, PermissionLevel.ALWAYS_ALLOW, "List directory (Windows)"),
            "pwd": CommandRule("pwd", CommandCategory.SYSTEM_INFO, PermissionLevel.ALWAYS_ALLOW, "Print working directory"),
            "cd": CommandRule("cd", CommandCategory.SYSTEM_INFO, PermissionLevel.ALWAYS_ALLOW, "Show current directory"),
            "cat": CommandRule("cat", CommandCategory.FILE_READ, PermissionLevel.ASK_ONCE, "Read file contents"),
            "type": CommandRule("type", CommandCategory.FILE_READ, PermissionLevel.ASK_ONCE, "Read file (Windows)"),
            "head": CommandRule("head", CommandCategory.FILE_READ, PermissionLevel.ALWAYS_ALLOW, "Show file start"),
            "tail": CommandRule("tail", CommandCategory.FILE_READ, PermissionLevel.ALWAYS_ALLOW, "Show file end"),
            
            # System info (safe)
            "date": CommandRule("date", CommandCategory.SYSTEM_INFO, PermissionLevel.ALWAYS_ALLOW, "Show date/time"),
            "time": CommandRule("time", CommandCategory.SYSTEM_INFO, PermissionLevel.ALWAYS_ALLOW, "Show time"),
            "whoami": CommandRule("whoami", CommandCategory.SYSTEM_INFO, PermissionLevel.ALWAYS_ALLOW, "Show current user"),
            "hostname": CommandRule("hostname", CommandCategory.SYSTEM_INFO, PermissionLevel.ALWAYS_ALLOW, "Show hostname"),
            "uname": CommandRule("uname", CommandCategory.SYSTEM_INFO, PermissionLevel.ALWAYS_ALLOW, "System information"),
            "echo": CommandRule("echo", CommandCategory.SYSTEM_INFO, PermissionLevel.ALWAYS_ALLOW, "Echo text"),
            
            # File operations (need permission)
            "mkdir": CommandRule("mkdir", CommandCategory.FILE_WRITE, PermissionLevel.ASK_ONCE, "Create directory"),
            "touch": CommandRule("touch", CommandCategory.FILE_WRITE, PermissionLevel.ASK_ONCE, "Create file"),
            "cp": CommandRule("cp", CommandCategory.FILE_WRITE, PermissionLevel.ASK_ALWAYS, "Copy files"),
            "copy": CommandRule("copy", CommandCategory.FILE_WRITE, PermissionLevel.ASK_ALWAYS, "Copy files (Windows)"),
            "mv": CommandRule("mv", CommandCategory.FILE_WRITE, PermissionLevel.ASK_ALWAYS, "Move/rename files"),
            "move": CommandRule("move", CommandCategory.FILE_WRITE, PermissionLevel.ASK_ALWAYS, "Move files (Windows)"),
            "ren": CommandRule("ren", CommandCategory.FILE_WRITE, PermissionLevel.ASK_ALWAYS, "Rename (Windows)"),
            
            # Dangerous operations
            "rm": CommandRule("rm", CommandCategory.FILE_DELETE, PermissionLevel.ASK_ALWAYS, "Delete files"),
            "del": CommandRule("del", CommandCategory.FILE_DELETE, PermissionLevel.ASK_ALWAYS, "Delete files (Windows)"),
            "rmdir": CommandRule("rmdir", CommandCategory.FILE_DELETE, PermissionLevel.ASK_ALWAYS, "Remove directory"),
            "sudo": CommandRule("sudo", CommandCategory.PROCESS, PermissionLevel.NEVER_ALLOW, "Superuser access", allow_sudo=False),
            "chmod": CommandRule("chmod", CommandCategory.FILE_WRITE, PermissionLevel.ASK_ALWAYS, "Change permissions"),
            
            # Network (restricted)
            "curl": CommandRule("curl", CommandCategory.NETWORK, PermissionLevel.ASK_ALWAYS, "Network request"),
            "wget": CommandRule("wget", CommandCategory.NETWORK, PermissionLevel.ASK_ALWAYS, "Download file"),
            "ping": CommandRule("ping", CommandCategory.NETWORK, PermissionLevel.ASK_ONCE, "Network ping"),
        }
        
        # Windows-specific additions
        if os_type == "Windows":
            defaults.update({
                "powershell": CommandRule("powershell", CommandCategory.PROCESS, PermissionLevel.ASK_ALWAYS, "PowerShell command"),
                "start": CommandRule("start", CommandCategory.APP_LAUNCH, PermissionLevel.ASK_ONCE, "Start application"),
                "tasklist": CommandRule("tasklist", CommandCategory.SYSTEM_INFO, PermissionLevel.ALWAYS_ALLOW, "List processes"),
                "systeminfo": CommandRule("systeminfo", CommandCategory.SYSTEM_INFO, PermissionLevel.ALWAYS_ALLOW, "System info"),
            })
        
        self.rules = defaults
        self._save_rules()
    
    def get_rule(self, command: str) -> Optional[CommandRule]:
        """Get rule for a command (base command only)"""
        base_cmd = command.split()[0] if command else ""
        return self.rules.get(base_cmd)
    
    def is_allowed(self, command: str) -> Tuple[bool, Optional[CommandRule], Optional[str]]:
        """
        Check if command is allowed
        Returns: (is_allowed, rule, error_message)
        """
        base_cmd = command.split()[0] if command else ""
        
        # Check if command exists in allowlist
        rule = self.get_rule(command)
        if not rule:
            return False, None, f"Command '{base_cmd}' not in allowlist"
        
        # Check NEVER_ALLOW
        if rule.permission == PermissionLevel.NEVER_ALLOW:
            return False, rule, f"Command '{base_cmd}' is blocked"
        
        # Check sudo
        if "sudo" in command and not rule.allow_sudo:
            return False, rule, "Sudo not allowed for this command"
        
        return True, rule, None


class PermissionManager:
    """Manages user permissions and remembered decisions"""
    
    def __init__(self, storage_path: str = "permissions.json"):
        self.storage_path = storage_path
        self.remembered_permissions: Dict[str, bool] = {}
        self._load_permissions()
    
    def _load_permissions(self):
        """Load remembered permissions"""
        try:
            with open(self.storage_path, 'r') as f:
                self.remembered_permissions = json.load(f)
        except FileNotFoundError:
            self.remembered_permissions = {}
    
    def _save_permissions(self):
        """Save remembered permissions"""
        with open(self.storage_path, 'w') as f:
            json.dump(self.remembered_permissions, f, indent=2)
    
    def check_permission(
        self, 
        command: str, 
        rule: CommandRule,
        user_callback: Optional[callable] = None
    ) -> bool:
        """
        Check if command has permission to execute
        
        Args:
            command: Full command string
            rule: Command rule
            user_callback: Function to ask user for permission (returns bool)
        """
        # ALWAYS_ALLOW: no check needed
        if rule.permission == PermissionLevel.ALWAYS_ALLOW:
            return True
        
        # NEVER_ALLOW: always denied
        if rule.permission == PermissionLevel.NEVER_ALLOW:
            return False
        
        # Generate permission key
        perm_key = self._generate_permission_key(command, rule)
        
        # ASK_ONCE: check if already remembered
        if rule.permission == PermissionLevel.ASK_ONCE:
            if perm_key in self.remembered_permissions:
                return self.remembered_permissions[perm_key]
        
        # Need to ask user
        if user_callback:
            approved = user_callback(command, rule)
            
            # Remember if ASK_ONCE
            if rule.permission == PermissionLevel.ASK_ONCE:
                self.remembered_permissions[perm_key] = approved
                self._save_permissions()
            
            return approved
        
        # No callback provided, default to deny for safety
        logger.warning(f"No permission callback for {command}, defaulting to DENY")
        return False
    
    def _generate_permission_key(self, command: str, rule: CommandRule) -> str:
        """Generate unique key for permission"""
        key_data = f"{rule.pattern}:{rule.category.value}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def revoke_permission(self, command: str):
        """Revoke remembered permission for a command"""
        keys_to_remove = [
            key for key in self.remembered_permissions.keys()
            if command in key
        ]
        for key in keys_to_remove:
            del self.remembered_permissions[key]
        self._save_permissions()


class AuditLogger:
    """Logs all system operations for security auditing"""
    
    def __init__(self, log_path: str = "system_audit.log"):
        self.log_path = log_path
        self._setup_logger()
    
    def _setup_logger(self):
        """Set up dedicated audit logger"""
        self.audit_logger = logging.getLogger("sarkar_audit")
        self.audit_logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(self.log_path)
        handler.setFormatter(
            logging.Formatter('%(asctime)s | %(message)s')
        )
        self.audit_logger.addHandler(handler)
    
    def log(self, entry: AuditLog):
        """Log an audit entry"""
        log_data = asdict(entry)
        self.audit_logger.info(json.dumps(log_data))
    
    def get_recent_logs(self, n: int = 50) -> List[Dict]:
        """Get recent audit logs"""
        logs = []
        try:
            with open(self.log_path, 'r') as f:
                lines = f.readlines()[-n:]
                for line in lines:
                    if '|' in line:
                        log_json = line.split('|', 1)[1].strip()
                        logs.append(json.loads(log_json))
        except FileNotFoundError:
            pass
        return logs


class SystemControlAgent:
    """
    Safe system control agent for Sarkar
    Handles app launching, file operations, and terminal commands
    """
    
    def __init__(
        self,
        user_id: str = "default_user",
        permission_callback: Optional[callable] = None
    ):
        self.user_id = user_id
        self.permission_callback = permission_callback
        
        # Initialize security components
        self.path_validator = SafePathValidator()
        self.allowlist = CommandAllowlist()
        self.permission_manager = PermissionManager()
        self.audit_logger = AuditLogger()
        
        # Detect OS
        self.os_type = platform.system()
        
        logger.info(f"SystemControlAgent initialized for {self.os_type}")
    
    def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Safely execute a terminal command
        
        Returns: {
            "success": bool,
            "output": str,
            "error": Optional[str],
            "approved": bool
        }
        """
        # Check allowlist
        is_allowed, rule, error = self.allowlist.is_allowed(command)
        if not is_allowed:
            self._log_audit(command, CommandCategory.PROCESS, False, f"Blocked: {error}", error)
            return {"success": False, "output": "", "error": error, "approved": False}
        
        # Check permission
        approved = self.permission_manager.check_permission(
            command, rule, self.permission_callback
        )
        
        if not approved:
            error = "User denied permission"
            self._log_audit(command, rule.category, False, "Denied by user", error)
            return {"success": False, "output": "", "error": error, "approved": False}
        
        # Execute command safely
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=rule.max_execution_time,
                check=False
            )
            
            output = result.stdout
            error = result.stderr if result.returncode != 0 else None
            success = result.returncode == 0
            
            self._log_audit(command, rule.category, True, output[:200], error)
            
            return {
                "success": success,
                "output": output,
                "error": error,
                "approved": True,
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            error = f"Command timeout after {rule.max_execution_time}s"
            self._log_audit(command, rule.category, False, "Timeout", error)
            return {"success": False, "output": "", "error": error, "approved": True}
        
        except Exception as e:
            error = f"Execution error: {str(e)}"
            self._log_audit(command, rule.category, False, "Exception", error)
            return {"success": False, "output": "", "error": error, "approved": True}
    
    def open_application(self, app_name: str) -> Dict[str, Any]:
        """
        Open an application safely
        Cross-platform: macOS, Windows, Linux
        """
        command = None
        
        if self.os_type == "Darwin":  # macOS
            command = f"open -a '{app_name}'"
        elif self.os_type == "Windows":
            command = f"start {app_name}"
        elif self.os_type == "Linux":
            command = f"xdg-open {app_name} &"
        
        if not command:
            return {"success": False, "error": f"Unsupported OS: {self.os_type}"}
        
        # Add to allowlist if not present
        if "open" not in self.allowlist.rules:
            self.allowlist.rules["open"] = CommandRule(
                "open", CommandCategory.APP_LAUNCH, 
                PermissionLevel.ASK_ONCE, "Open application"
            )
        
        return self.execute_command(command)
    
    def read_file(self, file_path: str) -> Dict[str, Any]:
        """Safely read a file"""
        # Validate path
        is_safe, error = self.path_validator.is_safe_path(file_path)
        if not is_safe:
            self._log_audit(f"read {file_path}", CommandCategory.FILE_READ, False, "Blocked", error)
            return {"success": False, "error": error, "content": None}
        
        # Check permission
        command = f"read {file_path}"
        rule = CommandRule("read", CommandCategory.FILE_READ, PermissionLevel.ASK_ONCE, "Read file")
        
        approved = self.permission_manager.check_permission(command, rule, self.permission_callback)
        if not approved:
            return {"success": False, "error": "Permission denied", "content": None}
        
        # Read file
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            self._log_audit(command, CommandCategory.FILE_READ, True, f"Read {len(content)} bytes")
            return {"success": True, "content": content, "error": None}
        
        except Exception as e:
            error = f"Read error: {str(e)}"
            self._log_audit(command, CommandCategory.FILE_READ, False, "Error", error)
            return {"success": False, "error": error, "content": None}
    
    def write_file(self, file_path: str, content: str) -> Dict[str, Any]:
        """Safely write to a file"""
        # Validate path
        is_safe, error = self.path_validator.is_safe_path(file_path)
        if not is_safe:
            self._log_audit(f"write {file_path}", CommandCategory.FILE_WRITE, False, "Blocked", error)
            return {"success": False, "error": error}
        
        # Check permission
        command = f"write {file_path}"
        rule = CommandRule("write", CommandCategory.FILE_WRITE, PermissionLevel.ASK_ALWAYS, "Write file")
        
        approved = self.permission_manager.check_permission(command, rule, self.permission_callback)
        if not approved:
            return {"success": False, "error": "Permission denied"}
        
        # Write file
        try:
            with open(file_path, 'w') as f:
                f.write(content)
            
            self._log_audit(command, CommandCategory.FILE_WRITE, True, f"Wrote {len(content)} bytes")
            return {"success": True, "error": None}
        
        except Exception as e:
            error = f"Write error: {str(e)}"
            self._log_audit(command, CommandCategory.FILE_WRITE, False, "Error", error)
            return {"success": False, "error": error}
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """Safely delete a file"""
        # Validate path
        is_safe, error = self.path_validator.is_safe_path(file_path)
        if not is_safe:
            self._log_audit(f"delete {file_path}", CommandCategory.FILE_DELETE, False, "Blocked", error)
            return {"success": False, "error": error}
        
        # Check permission (ALWAYS ask for deletes)
        command = f"delete {file_path}"
        rule = CommandRule("delete", CommandCategory.FILE_DELETE, PermissionLevel.ASK_ALWAYS, "Delete file")
        
        approved = self.permission_manager.check_permission(command, rule, self.permission_callback)
        if not approved:
            return {"success": False, "error": "Permission denied"}
        
        # Delete file
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
            else:
                return {"success": False, "error": "Path not found"}
            
            self._log_audit(command, CommandCategory.FILE_DELETE, True, "Deleted")
            return {"success": True, "error": None}
        
        except Exception as e:
            error = f"Delete error: {str(e)}"
            self._log_audit(command, CommandCategory.FILE_DELETE, False, "Error", error)
            return {"success": False, "error": error}
    
    def list_directory(self, dir_path: str = ".") -> Dict[str, Any]:
        """Safely list directory contents"""
        # Validate path
        is_safe, error = self.path_validator.is_safe_path(dir_path)
        if not is_safe:
            return {"success": False, "error": error, "files": []}
        
        # No permission needed for listing (safe operation)
        try:
            path = Path(dir_path)
            if not path.exists():
                return {"success": False, "error": "Directory not found", "files": []}
            
            files = []
            for item in path.iterdir():
                files.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else 0
                })
            
            self._log_audit(f"ls {dir_path}", CommandCategory.FILE_READ, True, f"Listed {len(files)} items")
            return {"success": True, "files": files, "error": None}
        
        except Exception as e:
            error = f"List error: {str(e)}"
            return {"success": False, "error": error, "files": []}
    
    def _log_audit(
        self, 
        command: str, 
        category: CommandCategory, 
        approved: bool, 
        result: str,
        error: Optional[str] = None
    ):
        """Create audit log entry"""
        entry = AuditLog(
            timestamp=datetime.utcnow().isoformat(),
            user_id=self.user_id,
            command=command,
            category=category.value,
            approved=approved,
            result=result,
            error=error
        )
        self.audit_logger.log(entry)
    
    def get_audit_logs(self, n: int = 50) -> List[Dict]:
        """Get recent audit logs"""
        return self.audit_logger.get_recent_logs(n)


# Example usage
if __name__ == "__main__":
    # Mock permission callback (in real system, this would prompt the user)
    def mock_permission_callback(command: str, rule: CommandRule) -> bool:
        print(f"\n🔐 Permission Request:")
        print(f"   Command: {command}")
        print(f"   Description: {rule.description}")
        print(f"   Category: {rule.category.value}")
        response = input(f"   Approve? (y/n): ")
        return response.lower() == 'y'
    
    # Initialize agent
    agent = SystemControlAgent(
        user_id="demo_user",
        permission_callback=mock_permission_callback
    )
    
    # Test operations
    print("\n=== Testing System Control Agent ===\n")
    
    # 1. List directory (safe, no permission needed)
    result = agent.list_directory(".")
    if result["success"]:
        print(f"✓ Listed {len(result['files'])} items in current directory")
    
    # 2. Execute safe command
    result = agent.execute_command("pwd")
    if result["success"]:
        print(f"✓ Current directory: {result['output'].strip()}")
    
    # 3. Try to execute dangerous command (should be blocked)
    result = agent.execute_command("sudo rm -rf /")
    if not result["success"]:
        print(f"✓ Dangerous command blocked: {result['error']}")
    
    # 4. Open application (will ask for permission)
    # result = agent.open_application("TextEdit")
    
    # 5. View audit logs
    print("\n📋 Recent Audit Logs:")
    logs = agent.get_audit_logs(5)
    for log in logs:
        status = "✓" if log['approved'] else "✗"
        print(f"{status} {log['command']} - {log['result'][:50]}")