"""
Test script for Sarkar AI Assistant
Run this to verify everything works
"""
import sys
from feature_flags import FeatureFlagManager, is_enabled, get_variant
from system_control_agent import SystemControlAgent


def test_feature_flags():
    """Test feature flag system"""
    print("\n" + "="*60)
    print("🚩 Testing Feature Flags")
    print("="*60)
    
    # Initialize
    flags = FeatureFlagManager()
    
    # Test 1: Check if web search is enabled
    if is_enabled("agents.web_search.enabled"):
        print("✅ Web search agent: ENABLED")
    else:
        print("❌ Web search agent: DISABLED")
    
    # Test 2: Check percentage rollout
    user_id = "test_user_123"
    if is_enabled("features.proactive_suggestions", user_id):
        print(f"✅ Proactive suggestions enabled for {user_id}")
    else:
        print(f"❌ Proactive suggestions disabled for {user_id}")
    
    # Test 3: Get A/B test variant
    model = get_variant("model.provider", user_id)
    print(f"✅ Model variant for {user_id}: {model}")
    
    # Test 4: Emergency disable
    print("\n🔴 Testing emergency kill switch...")
    flags.emergency_disable("agents.code_execution.enabled")
    if not is_enabled("agents.code_execution.enabled"):
        print("✅ Emergency disable works!")
    
    # Print all flags
    print("\n📋 All Feature Flags:")
    for key, flag in flags.get_all_flags().items():
        status = "🟢" if flag['enabled'] else "🔴"
        print(f"  {status} {key}")


def mock_permission_callback(command: str, rule) -> bool:
    """Mock permission system for testing"""
    print(f"\n🔐 Permission Request:")
    print(f"   Command: {command}")
    print(f"   Description: {rule.description}")
    print(f"   Category: {rule.category.value}")
    
    # Auto-approve for testing (in production, this would prompt user)
    # For demo: approve safe commands, deny dangerous ones
    if rule.category.value in ["file_read", "system_info", "app_launch"]:
        print("   ✅ AUTO-APPROVED (safe operation)")
        return True
    else:
        print("   ⚠️  Would ask user in production")
        response = input("   Approve? (y/n): ")
        return response.lower() == 'y'


def test_system_control():
    """Test system control agent"""
    print("\n" + "="*60)
    print("🖥️  Testing System Control Agent")
    print("="*60)
    
    # Initialize agent
    agent = SystemControlAgent(
        user_id="test_user",
        permission_callback=mock_permission_callback
    )
    
    # Test 1: List current directory (safe, no permission)
    print("\n📁 Test 1: List current directory")
    result = agent.list_directory(".")
    if result["success"]:
        print(f"✅ Found {len(result['files'])} items")
        for item in result['files'][:5]:  # Show first 5
            print(f"   - {item['name']} ({item['type']})")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 2: Execute safe command
    print("\n💻 Test 2: Execute safe command (pwd)")
    result = agent.execute_command("cd")  # Windows equivalent of pwd
    if result["success"]:
        print(f"✅ Output: {result['output'].strip()}")
    else:
        print(f"❌ Error: {result['error']}")
    
    # Test 3: Try dangerous command (should be blocked)
    print("\n🚫 Test 3: Try dangerous command (should block)")
    result = agent.execute_command("sudo rm -rf /")
    if not result["success"]:
        print(f"✅ Correctly blocked: {result['error']}")
    else:
        print(f"❌ DANGER: Should have been blocked!")
    
    # Test 4: Try unknown command (not in allowlist)
    print("\n🚫 Test 4: Try unknown command")
    result = agent.execute_command("netstat")
    if not result["success"]:
        print(f"✅ Correctly blocked: {result['error']}")
    
    # Test 5: Read a file (will ask permission)
    print("\n📖 Test 5: Read file (with permission)")
    result = agent.read_file("test_sarkar.py")
    if result["success"]:
        lines = result['content'].split('\n')
        print(f"✅ Read {len(lines)} lines from file")
    else:
        print(f"❌ Error: {result['error']}")
    
    # View audit logs
    print("\n📋 Recent Audit Logs:")
    logs = agent.get_audit_logs(10)
    for log in logs:
        status = "✅" if log['approved'] else "❌"
        print(f"  {status} {log['command'][:30]} - {log['result'][:40]}")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🤖 SARKAR AI ASSISTANT - SYSTEM TEST")
    print("="*60)
    
    try:
        # Test feature flags
        test_feature_flags()
        
        # Test system control
        test_system_control()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS COMPLETED!")
        print("="*60)
        print("\n💡 Next steps:")
        print("   1. Check generated config files (flags.json, command_allowlist.json)")
        print("   2. Review audit logs (system_audit.log)")
        print("   3. Build more agents (web search, calendar, etc.)")
        print("   4. Create the core orchestrator")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()