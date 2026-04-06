"""
Circuit breaker pattern for external service calls.
Prevents cascade failures by failing fast when a service is down.

Option C Panel Architecture v3.0 - Resilience Patterns
"""

import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, field
import threading
import json


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


@dataclass
class CircuitBreaker:
    """
    Circuit breaker implementation.
    
    Usage:
        breaker = CircuitBreaker("supabase")
        result = breaker.call(lambda: supabase_client.query(...))
    
    States:
        CLOSED: Normal operation, requests go through
        OPEN: Service is down, fail fast without trying
        HALF_OPEN: Testing recovery, allow limited requests
    """
    name: str
    failure_threshold: int = 5
    recovery_timeout: int = 300  # 5 minutes
    half_open_max_calls: int = 3
    
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _last_failure_time: Optional[datetime] = field(default=None, init=False)
    _half_open_calls: int = field(default=0, init=False)
    _lock: threading.Lock = field(default_factory=threading.Lock, init=False)
    
    def _should_attempt(self) -> bool:
        """Check if we should attempt the call."""
        with self._lock:
            if self._state == CircuitState.CLOSED:
                return True
            
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has passed
                if self._last_failure_time:
                    elapsed = datetime.now() - self._last_failure_time
                    if elapsed > timedelta(seconds=self.recovery_timeout):
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_calls = 0
                        return True
                return False
            
            if self._state == CircuitState.HALF_OPEN:
                return self._half_open_calls < self.half_open_max_calls
            
            return False
    
    def _record_success(self):
        """Record a successful call."""
        with self._lock:
            self._success_count += 1
            
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1
                if self._half_open_calls >= self.half_open_max_calls:
                    # Recovered!
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            else:
                self._failure_count = 0
    
    def _record_failure(self):
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.now()
            
            if self._state == CircuitState.HALF_OPEN:
                # Failed during recovery test - back to open
                self._state = CircuitState.OPEN
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
    
    def call(
        self,
        func: Callable[[], Any],
        fallback: Optional[Callable[[], Any]] = None
    ) -> Any:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to call
            fallback: Optional fallback function if circuit is open
            
        Returns:
            Result of func() or fallback()
            
        Raises:
            CircuitOpenError if circuit is open and no fallback
        """
        if not self._should_attempt():
            if fallback:
                return fallback()
            raise CircuitOpenError(f"Circuit {self.name} is open")
        
        try:
            result = func()
            self._record_success()
            return result
        except Exception as e:
            self._record_failure()
            if fallback:
                return fallback()
            raise
    
    def get_state(self) -> dict:
        """Get current circuit state for monitoring."""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout_seconds": self.recovery_timeout,
                "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None,
                "time_until_recovery": self._time_until_recovery()
            }
    
    def _time_until_recovery(self) -> Optional[int]:
        """Seconds until circuit will attempt recovery."""
        if self._state != CircuitState.OPEN or not self._last_failure_time:
            return None
        elapsed = (datetime.now() - self._last_failure_time).total_seconds()
        remaining = self.recovery_timeout - elapsed
        return max(0, int(remaining))
    
    def reset(self):
        """Manually reset circuit to closed state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._last_failure_time = None
            self._half_open_calls = 0
    
    def force_open(self):
        """Manually force circuit open (for maintenance)."""
        with self._lock:
            self._state = CircuitState.OPEN
            self._last_failure_time = datetime.now()


# Global circuit breakers for external services
CIRCUIT_BREAKERS: Dict[str, CircuitBreaker] = {
    "supabase": CircuitBreaker("supabase", failure_threshold=5, recovery_timeout=300),
    "chromadb": CircuitBreaker("chromadb", failure_threshold=5, recovery_timeout=300),
    "ollama": CircuitBreaker("ollama", failure_threshold=3, recovery_timeout=60),
    "anthropic": CircuitBreaker("anthropic", failure_threshold=5, recovery_timeout=300),
    "google": CircuitBreaker("google", failure_threshold=5, recovery_timeout=300),
    "openrouter": CircuitBreaker("openrouter", failure_threshold=5, recovery_timeout=300),
}


def get_circuit(name: str) -> CircuitBreaker:
    """Get or create a circuit breaker by name."""
    if name not in CIRCUIT_BREAKERS:
        CIRCUIT_BREAKERS[name] = CircuitBreaker(name)
    return CIRCUIT_BREAKERS[name]


def get_all_circuit_states() -> dict:
    """Get state of all circuit breakers for dashboard."""
    return {name: cb.get_state() for name, cb in CIRCUIT_BREAKERS.items()}


def get_health_summary() -> dict:
    """Get health summary of all circuits."""
    states = get_all_circuit_states()
    
    healthy = sum(1 for s in states.values() if s["state"] == "closed")
    degraded = sum(1 for s in states.values() if s["state"] == "half_open")
    failed = sum(1 for s in states.values() if s["state"] == "open")
    
    return {
        "total": len(states),
        "healthy": healthy,
        "degraded": degraded,
        "failed": failed,
        "status": "healthy" if failed == 0 else "degraded" if healthy > 0 else "failed",
        "circuits": states
    }


def with_circuit_breaker(
    service_name: str,
    fallback: Optional[Callable] = None
):
    """
    Decorator to wrap a function with circuit breaker protection.
    
    Usage:
        @with_circuit_breaker("supabase")
        def query_supabase():
            return client.query(...)
    """
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            circuit = get_circuit(service_name)
            return circuit.call(
                lambda: func(*args, **kwargs),
                fallback
            )
        return wrapper
    return decorator


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python circuit_breaker.py status")
        print("  python circuit_breaker.py reset <service_name>")
        print("  python circuit_breaker.py test <service_name>")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "status":
        summary = get_health_summary()
        print(json.dumps(summary, indent=2))
    
    elif command == "reset":
        service = sys.argv[2]
        if service in CIRCUIT_BREAKERS:
            CIRCUIT_BREAKERS[service].reset()
            print(f"Reset circuit for {service}")
        else:
            print(f"Unknown service: {service}")
            print(f"Available: {list(CIRCUIT_BREAKERS.keys())}")
    
    elif command == "test":
        service = sys.argv[2] if len(sys.argv) > 2 else "test_service"
        
        print(f"Testing circuit breaker for {service}")
        circuit = get_circuit(service)
        
        # Simulate failures
        for i in range(6):
            try:
                def fail():
                    raise Exception("Simulated failure")
                circuit.call(fail)
            except Exception as e:
                print(f"Attempt {i+1}: Failed - {e}")
            print(f"  State: {circuit.get_state()['state']}")
        
        # Try with fallback
        result = circuit.call(
            lambda: "would fail",
            fallback=lambda: "fallback result"
        )
        print(f"\nWith fallback: {result}")
