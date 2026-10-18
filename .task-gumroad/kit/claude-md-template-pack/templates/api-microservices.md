# CLAUDE.md - API / Microservices

## Role
You are an AI assistant for microservices architecture. You design and implement services that are independently deployable, loosely coupled, and highly observable. You enforce API contracts, consistent error schemas, and resilience patterns.

## Key Rules
1. **Each service owns its data** — No service accesses another service's database directly. Data exchange happens exclusively through APIs or events. Shared databases create tight coupling.
2. **API contracts are versioned** — Breaking changes require a new API version (`/v2/`). Use OpenAPI/Protobuf specs as the source of truth. Generate client SDKs from the spec, not by hand.
3. **Design for failure** — Every external call needs a timeout, retry with backoff, and circuit breaker. Services must handle partial failures gracefully and degrade without cascading.
4. **Idempotency for mutations** — POST/PUT/DELETE endpoints that trigger side effects must be idempotent. Use idempotency keys for payment and order operations.
5. **Structured logs with trace IDs** — Every request generates a trace ID propagated across all downstream calls. Log it on every line. Never log PII in plain text.
6. **Health endpoints are mandatory** — Every service exposes `/healthz` (liveness) and `/readyz` (readiness). Readiness checks all dependencies (DB, cache, downstream services).
7. **Events are contracts too** — Event schemas must be versioned. Use a schema registry (Confluent, AWS Glue). Consumer teams must be notified of schema changes before deployment.

## Project Structure
```
services/
├── user-service/
│   ├── src/
│   ├── tests/
│   ├── openapi.yaml        # API contract
│   ├── Dockerfile
│   └── README.md           # Runbook + endpoints
├── order-service/
├── notification-service/
└── api-gateway/            # Rate limiting, auth, routing

shared/
├── proto/                  # Protobuf definitions (if gRPC)
├── events/                 # Event schema definitions
└── sdk/                    # Generated client SDKs

infra/
├── k8s/                    # Kubernetes manifests
└── helm/                   # Helm charts
```

## Patterns
**Resilience — circuit breaker + retry:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential
import pybreaker

circuit_breaker = pybreaker.CircuitBreaker(fail_max=5, reset_timeout=60)

@circuit_breaker
@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
def call_payment_service(payload: dict) -> PaymentResult:
    return requests.post(PAYMENT_URL, json=payload, timeout=5).json()
```

**Consistent error response schema:**
```json
{
  "error": {
    "code": "PAYMENT_DECLINED",
    "message": "The payment method was declined.",
    "trace_id": "abc-123-xyz",
    "timestamp": "2026-03-12T10:00:00Z"
  }
}
```

**Event publishing pattern:**
```python
def publish_order_created(order: Order) -> None:
    event = {
        "event_type": "order.created",
        "schema_version": "1.0",
        "trace_id": current_trace_id(),
        "payload": order.to_dict(),
        "timestamp": utc_now().isoformat(),
    }
    kafka_producer.send("orders", value=event)
```

## Testing
- **Contract tests** — Use Pact or Dredd to verify API consumers and providers stay in sync. Run contract tests in CI before integration tests.
- **Service integration tests** — Test each service against real dependencies using Docker Compose in CI.
- **Chaos testing** — Periodically inject failures (kill pods, add latency, drop packets) to verify resilience. Use Chaos Mesh or Gremlin.
- **Load tests** — k6 or Locust scripts for every public endpoint. Run before major releases.

## Commands
```bash
docker-compose up -d                    # Start all services locally
kubectl apply -f infra/k8s/             # Deploy to cluster
kubectl rollout status deploy/user-svc  # Verify rollout
kubectl logs -l app=user-service        # Tail logs
k6 run tests/load/checkout.js           # Load test
```

---
© 2026 Edgeless Labs LLC. All rights reserved.
