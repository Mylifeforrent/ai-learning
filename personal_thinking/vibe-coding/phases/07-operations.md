# Phase 7: Operations — Observability & Monitoring

## Purpose

Deployment is NOT the end. Post-deployment operations ensure the application stays healthy, performant, and reliable. This is where most teams fail — they ship code but don't know if it's actually working well for users.

## The Three Pillars of Observability

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Observability Stack                                   │
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                  │
│  │   METRICS    │  │    LOGS      │  │   TRACES     │                  │
│  │              │  │              │  │              │                  │
│  │ "What is     │  │ "What        │  │ "What path   │                  │
│  │  happening?" │  │  happened?"  │  │  did a       │                  │
│  │              │  │              │  │  request     │                  │
│  │ CPU, memory, │  │ Structured   │  │  take?"      │                  │
│  │ request rate │  │ event data   │  │              │                  │
│  │ error rate   │  │ error logs   │  │ Distributed  │                  │
│  │              │  │              │  │ tracing      │                  │
│  │ Prometheus   │  │ Loki / ELK   │  │ Tempo /      │                  │
│  │              │  │              │  │ Jaeger       │                  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                 │                           │
│         └────────┬────────┴────────┬────────┘                          │
│                  │                 │                                    │
│           ┌──────▼───────┐  ┌─────▼──────┐                             │
│           │   Grafana    │  │   Sentry   │                             │
│           │ Dashboards & │  │ Error      │                             │
│           │ Alerting     │  │ Tracking   │                             │
│           └──────────────┘  └────────────┘                             │
└─────────────────────────────────────────────────────────────────────────┘
```

## Recommended Tools

| Tool | Type | Purpose | Link |
|:---|:---|:---|:---|
| **OpenTelemetry** | OSS Standard | Vendor-neutral telemetry collection | [opentelemetry.io](https://opentelemetry.io) |
| **Prometheus** | OSS | Metrics collection & alerting | [prometheus.io](https://prometheus.io) |
| **Grafana** | OSS | Dashboards & visualization | [grafana.com](https://grafana.com) |
| **Loki** | OSS | Log aggregation (Grafana's stack) | [grafana.com/loki](https://grafana.com/oss/loki) |
| **Sentry** | Platform | Error tracking & performance | [sentry.io](https://sentry.io) |
| **Better Stack** | Platform | Uptime monitoring + logs | [betterstack.com](https://betterstack.com) |
| **PagerDuty** | Platform | Incident management & alerting | [pagerduty.com](https://pagerduty.com) |

## Key Metrics to Monitor (The RED Method)

```
For every service, track these three:

  R — Rate:     How many requests per second?
  E — Errors:   What percentage of requests are failing?
  D — Duration: How long do requests take (p50, p95, p99)?

Plus infrastructure metrics:
  • CPU and memory utilization
  • Disk I/O and storage
  • Database connection pool usage
  • Cache hit/miss rates
```

## SLOs, SLIs, and SLAs

```
SLI (Service Level Indicator) — What you measure
  Example: "99.2% of API requests complete in < 500ms"

SLO (Service Level Objective) — What you aim for
  Example: "99.5% of API requests should complete in < 500ms"

SLA (Service Level Agreement) — What you promise
  Example: "We guarantee 99.9% uptime; if breached, customer gets credit"

Practical Setup:
  1. Define SLIs for your critical user journeys
  2. Set SLOs with an "error budget" (how much downtime is acceptable)
  3. Monitor error budget burn rate in Grafana
  4. Alert when error budget is burning too fast
```

## Demo: Basic Monitoring Setup

```javascript
// src/middleware/metrics.js — Prometheus metrics middleware
import promClient from 'prom-client';

// Collect default metrics (CPU, memory, event loop)
promClient.collectDefaultMetrics();

// Custom metrics
const httpRequestDuration = new promClient.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5],
});

const httpRequestTotal = new promClient.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code'],
});

// Middleware
export function metricsMiddleware(req, res, next) {
  const end = httpRequestDuration.startTimer();
  
  res.on('finish', () => {
    const labels = {
      method: req.method,
      route: req.route?.path || req.path,
      status_code: res.statusCode,
    };
    end(labels);
    httpRequestTotal.inc(labels);
  });
  
  next();
}

// Expose /metrics endpoint for Prometheus to scrape
export function metricsEndpoint(req, res) {
  res.set('Content-Type', promClient.register.contentType);
  res.end(promClient.register.metrics());
}
```

```javascript
// src/lib/sentry.js — Sentry error tracking setup
import * as Sentry from '@sentry/node';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  release: process.env.APP_VERSION,
  
  // Performance Monitoring
  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,
  
  // Filter sensitive data
  beforeSend(event) {
    if (event.request?.headers) {
      delete event.request.headers['authorization'];
    }
    return event;
  },
});

export { Sentry };
```

## Incident Response Process

```
┌─────────────────────────────────────────────────────────────┐
│                  Incident Response Flow                     │
│                                                             │
│  1. DETECT                                                  │
│     ├─ Automated alert fires (Grafana/PagerDuty)           │
│     └─ Or user reports issue                               │
│                                                             │
│  2. TRIAGE                                                  │
│     ├─ Assign severity: SEV1 (critical) → SEV4 (minor)     │
│     ├─ Identify affected users/services                     │
│     └─ Communicate status to stakeholders                   │
│                                                             │
│  3. MITIGATE                                                │
│     ├─ First goal: STOP THE BLEEDING (not root cause)      │
│     ├─ Rollback if recent deploy caused it                  │
│     ├─ Scale up if load-related                             │
│     └─ Enable circuit breakers if dependency failed         │
│                                                             │
│  4. RESOLVE                                                 │
│     ├─ Fix root cause                                       │
│     ├─ Deploy fix through normal CI/CD pipeline             │
│     └─ Verify fix in production                              │
│                                                             │
│  5. POST-MORTEM (Blameless)                                 │
│     ├─ Document: what happened, timeline, root cause        │
│     ├─ Action items: how to prevent recurrence              │
│     └─ Share learnings with the team                        │
└─────────────────────────────────────────────────────────────┘
```


---

← [Back to Overview](../overall-view.md)
