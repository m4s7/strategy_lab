# Appendix A: API Specification

```yaml
openapi: 3.0.0
info:
  title: Strategy Lab API
  version: 1.0.0

paths:
  /api/backtests:
    get:
      summary: List all backtests
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [pending, running, completed, failed]
        - name: limit
          in: query
          schema:
            type: integer
            default: 50

    post:
      summary: Create new backtest
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/BacktestConfig'
```
