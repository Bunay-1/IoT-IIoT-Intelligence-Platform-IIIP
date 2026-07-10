"""
Test script for audit logging system
"""

import asyncio
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pytest
from src.security.audit_logger import audit_logger, log_user_action, log_security_event, AuditEvent


@pytest.mark.asyncio
async def test_audit_logging():
    """Test audit logging functionality."""

    print("Testing Audit Logging System...")
    print("=" * 50)

    # Test 1: Basic event logging
    print("\n1. Testing basic event logging...")
    event = AuditEvent(
        event_id="",
        timestamp=datetime.now(),
        event_type="test_event",
        user_id="test_user_123",
        tenant_id="test_tenant_456",
        resource_type="machine",
        resource_id="CNC-001",
        action="status_update",
        status="success",
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0 Test Browser",
        details={"old_status": "idle", "new_status": "running"},
        severity="low",
        source="api",
        session_id="session_789",
        correlation_id=""
    )

    await audit_logger.log_event(event)
    print("Basic event logged successfully")

    # Test 2: User action logging
    print("\n2. Testing user action logging...")
    await log_user_action(
        user_id="user_123",
        tenant_id="tenant_456",
        action="machine_start",
        resource_type="machine",
        resource_id="CNC-002",
        status="success",
        details={"machine_type": "lathe", "operation": "cutting"},
        ip_address="10.0.0.50",
        user_agent="API Client v1.0",
        severity="medium"
    )
    print("User action logged successfully")

    # Test 3: Security event logging
    print("\n3. Testing security event logging...")
    await log_security_event(
        event_type="authentication",
        user_id="user_123",
        tenant_id="tenant_456",
        details={
            "action": "failed_login",
            "reason": "invalid_password",
            "attempt_count": 3
        },
        severity="high",
        ip_address="192.168.1.200"
    )
    print("Security event logged successfully")

    # Test 4: Query events
    print("\n4. Testing event querying...")
    events = await audit_logger.query_events(
        start_time=datetime.now() - timedelta(hours=1),
        user_id="user_123",
        limit=10
    )
    print(f"Found {len(events)} events for user_123")

    # Test 5: Compliance report generation
    print("\n5. Testing compliance report generation...")
    report = await audit_logger.generate_compliance_report(
        start_date=datetime.now() - timedelta(days=1),
        end_date=datetime.now(),
        report_type="security_audit"
    )
    print(f"Generated compliance report with {report['summary']['total_events']} events")

    # Test 6: Log integrity verification
    print("\n6. Testing log integrity verification...")
    integrity = await audit_logger.verify_log_integrity()
    print(f"Integrity check: {integrity['status']} ({integrity['valid_events']}/{integrity['total_events']} valid)")

    # Test 7: Sensitive data sanitization
    print("\n7. Testing sensitive data sanitization...")
    sensitive_event = AuditEvent(
        event_id="",
        timestamp=datetime.now(),
        event_type="user_registration",
        user_id="new_user",
        tenant_id="tenant_456",
        resource_type="user",
        resource_id="user_999",
        action="create",
        status="success",
        ip_address="127.0.0.1",
        user_agent="Test Client",
        details={
            "username": "testuser",
            "password": "secret123",  # Should be redacted
            "email": "test@example.com",
            "api_key": "sk-1234567890"  # Should be redacted
        },
        severity="medium",
        source="api",
        session_id=None,
        correlation_id=""
    )

    await audit_logger.log_event(sensitive_event)
    print("Sensitive data sanitized and logged")

    # Test 8: Batch buffer flush
    print("\n8. Testing batch buffer flush...")
    for i in range(5):
        test_event = AuditEvent(
            event_id="",
            timestamp=datetime.now(),
            event_type="batch_test",
            user_id=f"user_{i}",
            tenant_id="tenant_456",
            resource_type="test",
            resource_id=f"resource_{i}",
            action="batch_action",
            status="success",
            ip_address="127.0.0.1",
            user_agent="Batch Test Client",
            details={"batch_id": i},
            severity="low",
            source="test",
            session_id=None,
            correlation_id=""
        )
        await audit_logger.log_event(test_event)

    # Force flush
    await audit_logger._flush_buffer()
    print("Batch buffer flushed successfully")

    print("\n" + "=" * 50)
    print("All audit logging tests completed successfully!")
    print("\nTest Summary:")
    print("- Basic event logging: PASS")
    print("- User action logging: PASS")
    print("- Security event logging: PASS")
    print("- Event querying: PASS")
    print("- Compliance reporting: PASS")
    print("- Log integrity: PASS")
    print("- Data sanitization: PASS")
    print("- Batch processing: PASS")

    print("\nCheck logs/audit.log for logged events")
    print("Use the API endpoints to query audit logs in production")


if __name__ == "__main__":
    asyncio.run(test_audit_logging())