"""
Personal AI Assistant - Automation & Monitoring System
A comprehensive system for background tasks, monitoring, and proactive alerts
"""

import json
import time
import schedule
import psutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Callable, Any
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import winsound  # Windows-specific audio alerts

# ============================================================================
# CONFIGURATION & DATA MODELS
# ============================================================================

class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class Alert:
    id: str
    timestamp: str
    priority: Priority
    title: str
    message: str
    category: str
    acknowledged: bool = False

@dataclass
class Task:
    id: str
    name: str
    status: TaskStatus
    last_run: str
    next_run: str
    interval: str
    priority: Priority
    failure_count: int = 0

@dataclass
class SystemMetrics:
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    battery_percent: float
    is_charging: bool

# ============================================================================
# SAFETY RULES ENGINE
# ============================================================================

class SafetyRules:
    """Enforces safety constraints on automation actions"""
    
    # Maximum limits
    MAX_CPU_USAGE = 80.0  # Don't run intensive tasks if CPU > 80%
    MAX_MEMORY_USAGE = 85.0  # Don't run if memory > 85%
    MAX_FAILURES = 3  # Max consecutive failures before pause
    MIN_BATTERY = 20.0  # Don't run intensive tasks if battery < 20%
    
    # Rate limiting
    MAX_ALERTS_PER_HOUR = 10
    MAX_TASKS_CONCURRENT = 5
    
    # Time restrictions
    QUIET_HOURS_START = 22  # 10 PM
    QUIET_HOURS_END = 7     # 7 AM
    
    alert_history: List[datetime] = []
    running_tasks: int = 0
    
    @classmethod
    def can_run_task(cls, task: Task) -> tuple[bool, str]:
        """Check if a task can safely run"""
        
        # Check concurrent tasks
        if cls.running_tasks >= cls.MAX_TASKS_CONCURRENT:
            return False, "Max concurrent tasks reached"
        
        # Check system resources
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        
        if cpu > cls.MAX_CPU_USAGE:
            return False, f"CPU usage too high: {cpu}%"
        
        if memory > cls.MAX_MEMORY_USAGE:
            return False, f"Memory usage too high: {memory}%"
        
        # Check battery for high-priority tasks
        if task.priority in [Priority.HIGH, Priority.CRITICAL]:
            battery = psutil.sensors_battery()
            if battery and not battery.power_plugged:
                if battery.percent < cls.MIN_BATTERY:
                    return False, f"Battery too low: {battery.percent}%"
        
        # Check failure count
        if task.failure_count >= cls.MAX_FAILURES:
            return False, "Too many consecutive failures"
        
        return True, "OK"
    
    @classmethod
    def can_send_alert(cls, priority: Priority) -> bool:
        """Check if an alert can be sent (rate limiting)"""
        
        # Critical alerts always go through
        if priority == Priority.CRITICAL:
            return True
        
        # Check quiet hours for non-critical
        current_hour = datetime.now().hour
        if cls.QUIET_HOURS_START <= current_hour or current_hour < cls.QUIET_HOURS_END:
            if priority != Priority.HIGH:
                return False
        
        # Rate limiting
        now = datetime.now()
        cls.alert_history = [t for t in cls.alert_history if now - t < timedelta(hours=1)]
        
        if len(cls.alert_history) >= cls.MAX_ALERTS_PER_HOUR:
            return False
        
        cls.alert_history.append(now)
        return True

# ============================================================================
# EVENT-BASED EXECUTION ENGINE
# ============================================================================

class EventType(Enum):
    SCHEDULED = "scheduled"  # Time-based
    THRESHOLD = "threshold"  # Metric crosses threshold
    FILE_CHANGE = "file_change"  # File system change
    SYSTEM_EVENT = "system_event"  # OS event
    MANUAL = "manual"  # User triggered

@dataclass
class Event:
    type: EventType
    timestamp: datetime
    data: Dict[str, Any]
    priority: Priority

class EventBus:
    """Central event bus for event-driven architecture"""
    
    def __init__(self):
        self.listeners: Dict[EventType, List[Callable]] = {et: [] for et in EventType}
        self.event_queue: List[Event] = []
        self.lock = threading.Lock()
    
    def subscribe(self, event_type: EventType, callback: Callable):
        """Subscribe to an event type"""
        with self.lock:
            self.listeners[event_type].append(callback)
    
    def publish(self, event: Event):
        """Publish an event to all subscribers"""
        with self.lock:
            self.event_queue.append(event)
            for callback in self.listeners[event.type]:
                threading.Thread(target=callback, args=(event,), daemon=True).start()
    
    def get_event_history(self, limit: int = 50) -> List[Event]:
        """Get recent events"""
        with self.lock:
            return self.event_queue[-limit:]

# ============================================================================
# MONITORING SYSTEM
# ============================================================================

class SystemMonitor:
    """Monitors system resources and triggers alerts"""
    
    def __init__(self, event_bus: EventBus, alert_manager):
        self.event_bus = event_bus
        self.alert_manager = alert_manager
        self.metrics_history: List[SystemMetrics] = []
        self.thresholds = {
            'cpu': 90.0,
            'memory': 90.0,
            'disk': 95.0,
            'battery': 15.0
        }
    
    def collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        battery = psutil.sensors_battery()
        
        metrics = SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=psutil.virtual_memory().percent,
            disk_percent=psutil.disk_usage('/').percent,
            battery_percent=battery.percent if battery else 100.0,
            is_charging=battery.power_plugged if battery else True
        )
        
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        return metrics
    
    def check_thresholds(self, metrics: SystemMetrics):
        """Check if any thresholds are exceeded"""
        
        if metrics.cpu_percent > self.thresholds['cpu']:
            self.event_bus.publish(Event(
                type=EventType.THRESHOLD,
                timestamp=datetime.now(),
                data={'metric': 'cpu', 'value': metrics.cpu_percent},
                priority=Priority.HIGH
            ))
            self.alert_manager.create_alert(
                Priority.HIGH,
                "High CPU Usage",
                f"CPU usage at {metrics.cpu_percent}%",
                "system"
            )
        
        if metrics.memory_percent > self.thresholds['memory']:
            self.event_bus.publish(Event(
                type=EventType.THRESHOLD,
                timestamp=datetime.now(),
                data={'metric': 'memory', 'value': metrics.memory_percent},
                priority=Priority.HIGH
            ))
            self.alert_manager.create_alert(
                Priority.HIGH,
                "High Memory Usage",
                f"Memory usage at {metrics.memory_percent}%",
                "system"
            )
        
        if metrics.battery_percent < self.thresholds['battery'] and not metrics.is_charging:
            self.alert_manager.create_alert(
                Priority.CRITICAL,
                "Low Battery",
                f"Battery at {metrics.battery_percent}%",
                "system"
            )
    
    def monitor_loop(self):
        """Continuous monitoring loop"""
        metrics = self.collect_metrics()
        self.check_thresholds(metrics)

# ============================================================================
# STUDY SCHEDULE MANAGER
# ============================================================================

class StudySchedule:
    """Manages study schedules and sends reminders"""
    
    def __init__(self, event_bus: EventBus, alert_manager):
        self.event_bus = event_bus
        self.alert_manager = alert_manager
        self.schedule_file = Path("study_schedule.json")
        self.subjects: Dict[str, List[Dict]] = self.load_schedule()
    
    def load_schedule(self) -> Dict:
        """Load study schedule from file"""
        if self.schedule_file.exists():
            with open(self.schedule_file, 'r') as f:
                return json.load(f)
        return {
            "Monday": [
                {"time": "09:00", "subject": "Mathematics", "duration": 90},
                {"time": "14:00", "subject": "Physics", "duration": 120}
            ],
            "Tuesday": [
                {"time": "10:00", "subject": "Computer Science", "duration": 90}
            ]
        }
    
    def save_schedule(self):
        """Save schedule to file"""
        with open(self.schedule_file, 'w') as f:
            json.dump(self.subjects, f, indent=2)
    
    def check_upcoming_sessions(self):
        """Check for upcoming study sessions"""
        today = datetime.now().strftime("%A")
        current_time = datetime.now()
        
        if today in self.subjects:
            for session in self.subjects[today]:
                session_time = datetime.strptime(session['time'], "%H:%M").replace(
                    year=current_time.year,
                    month=current_time.month,
                    day=current_time.day
                )
                
                # Alert 15 minutes before
                time_diff = (session_time - current_time).total_seconds() / 60
                
                if 14 <= time_diff <= 16:
                    self.alert_manager.create_alert(
                        Priority.MEDIUM,
                        "Study Session Starting Soon",
                        f"{session['subject']} in 15 minutes ({session['duration']} min session)",
                        "study"
                    )

# ============================================================================
# ALERT MANAGER
# ============================================================================

class AlertManager:
    """Manages alerts and notifications"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.alert_file = Path("alerts.json")
        self.load_alerts()
    
    def load_alerts(self):
        """Load alerts from file"""
        if self.alert_file.exists():
            with open(self.alert_file, 'r') as f:
                data = json.load(f)
                self.alerts = [Alert(**a) for a in data]
    
    def save_alerts(self):
        """Save alerts to file"""
        with open(self.alert_file, 'w') as f:
            json.dump([asdict(a) for a in self.alerts], f, indent=2)
    
    def create_alert(self, priority: Priority, title: str, message: str, category: str):
        """Create a new alert"""
        
        if not SafetyRules.can_send_alert(priority):
            return
        
        alert = Alert(
            id=f"alert_{len(self.alerts)}_{int(time.time())}",
            timestamp=datetime.now().isoformat(),
            priority=priority,
            title=title,
            message=message,
            category=category
        )
        
        self.alerts.append(alert)
        self.save_alerts()
        self.notify(alert)
    
    def notify(self, alert: Alert):
        """Send notification"""
        print(f"\n{'='*60}")
        print(f"🔔 ALERT [{alert.priority.name}] - {alert.category.upper()}")
        print(f"{'='*60}")
        print(f"📌 {alert.title}")
        print(f"💬 {alert.message}")
        print(f"⏰ {alert.timestamp}")
        print(f"{'='*60}\n")
        
        # Play sound for high priority
        if alert.priority in [Priority.HIGH, Priority.CRITICAL]:
            try:
                winsound.Beep(1000, 500)
            except:
                pass
    
    def get_unacknowledged(self) -> List[Alert]:
        """Get unacknowledged alerts"""
        return [a for a in self.alerts if not a.acknowledged]

# ============================================================================
# TASK AUTOMATION ENGINE
# ============================================================================

class AutomationEngine:
    """Core automation engine"""
    
    def __init__(self):
        self.event_bus = EventBus()
        self.alert_manager = AlertManager()
        self.monitor = SystemMonitor(self.event_bus, self.alert_manager)
        self.study_schedule = StudySchedule(self.event_bus, self.alert_manager)
        self.tasks: Dict[str, Task] = {}
        self.setup_logging()
        self.setup_scheduled_tasks()
    
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('automation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_scheduled_tasks(self):
        """Setup all scheduled tasks"""
        
        # System monitoring every 5 minutes
        schedule.every(5).minutes.do(self.monitor.monitor_loop)
        
        # Study schedule check every 10 minutes
        schedule.every(10).minutes.do(self.study_schedule.check_upcoming_sessions)
        
        # Cleanup old logs daily
        schedule.every().day.at("00:00").do(self.cleanup_old_data)
        
        # Health check every hour
        schedule.every().hour.do(self.health_check)
        
        self.logger.info("Scheduled tasks configured")
    
    def cleanup_old_data(self):
        """Clean up old data files"""
        self.logger.info("Running cleanup task")
        # Keep only last 7 days of alerts
        cutoff = datetime.now() - timedelta(days=7)
        self.alert_manager.alerts = [
            a for a in self.alert_manager.alerts
            if datetime.fromisoformat(a.timestamp) > cutoff
        ]
        self.alert_manager.save_alerts()
    
    def health_check(self):
        """Perform system health check"""
        self.logger.info("Running health check")
        metrics = self.monitor.collect_metrics()
        
        status = {
            'cpu': 'OK' if metrics.cpu_percent < 70 else 'WARNING',
            'memory': 'OK' if metrics.memory_percent < 70 else 'WARNING',
            'disk': 'OK' if metrics.disk_percent < 80 else 'WARNING'
        }
        
        self.logger.info(f"Health check results: {status}")
    
    def run_task_safely(self, task_func: Callable, task: Task):
        """Execute a task with safety checks"""
        
        can_run, reason = SafetyRules.can_run_task(task)
        if not can_run:
            self.logger.warning(f"Task {task.name} skipped: {reason}")
            return
        
        SafetyRules.running_tasks += 1
        task.status = TaskStatus.RUNNING
        
        try:
            self.logger.info(f"Starting task: {task.name}")
            task_func()
            task.status = TaskStatus.COMPLETED
            task.failure_count = 0
            self.logger.info(f"Task completed: {task.name}")
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.failure_count += 1
            self.logger.error(f"Task failed: {task.name} - {str(e)}")
            
            if task.failure_count >= SafetyRules.MAX_FAILURES:
                self.alert_manager.create_alert(
                    Priority.HIGH,
                    "Task Failed Multiple Times",
                    f"Task '{task.name}' has failed {task.failure_count} times",
                    "system"
                )
        finally:
            SafetyRules.running_tasks -= 1
            task.last_run = datetime.now().isoformat()
    
    def start(self):
        """Start the automation engine"""
        self.logger.info("🚀 Starting Personal AI Assistant Automation System")
        self.logger.info(f"Safety Rules Active: CPU<{SafetyRules.MAX_CPU_USAGE}%, "
                        f"Memory<{SafetyRules.MAX_MEMORY_USAGE}%, "
                        f"Quiet Hours: {SafetyRules.QUIET_HOURS_START}:00-{SafetyRules.QUIET_HOURS_END}:00")
        
        print("\n" + "="*60)
        print("🤖 Personal AI Assistant - Automation System")
        print("="*60)
        print("✅ System initialized and monitoring started")
        print("📊 Dashboard: Check automation.log for details")
        print("🔔 Alerts will appear in this console")
        print("⏸️  Press Ctrl+C to stop")
        print("="*60 + "\n")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Shutting down automation system")
            print("\n👋 Automation system stopped gracefully")

# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    engine = AutomationEngine()
    engine.start()