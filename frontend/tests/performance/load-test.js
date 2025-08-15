import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

// Custom metrics
const errorRate = new Rate("errors");
const backtestCreationTime = new Trend("backtest_creation_time");
const resultsLoadTime = new Trend("results_load_time");
const websocketConnectionTime = new Trend("websocket_connection_time");

export const options = {
  stages: [
    { duration: "2m", target: 100 }, // Ramp up to 100 users
    { duration: "5m", target: 100 }, // Stay at 100 users
    { duration: "2m", target: 200 }, // Ramp up to 200 users
    { duration: "5m", target: 200 }, // Stay at 200 users
    { duration: "2m", target: 0 }, // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ["p(95)<500", "p(99)<1000"], // 95% under 500ms, 99% under 1s
    errors: ["rate<0.1"], // Error rate under 10%
    http_req_failed: ["rate<0.1"], // HTTP failure rate under 10%
    backtest_creation_time: ["p(95)<1000"], // 95% of backtest creations under 1s
    results_load_time: ["p(95)<800"], // 95% of results loads under 800ms
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:3000";
const API_URL = __ENV.API_URL || "http://localhost:8000";

export function setup() {
  // Setup code - create test data
  const setupData = {
    strategyId: "perf-test-strategy",
    contracts: ["03-24", "06-24"],
  };

  return setupData;
}

export default function (data) {
  // Test 1: Homepage load
  const homeResponse = http.get(`${BASE_URL}/`);
  check(homeResponse, {
    "homepage loads successfully": (r) => r.status === 200,
    "homepage loads quickly": (r) => r.timings.duration < 500,
  }) || errorRate.add(1);

  sleep(1);

  // Test 2: Create backtest
  const backtestPayload = JSON.stringify({
    strategyId: data.strategyId,
    config: {
      startDate: "2023-01-01",
      endDate: "2023-12-31",
      initialCapital: 100000,
      dataLevel: "level1",
      contracts: data.contracts,
    },
  });

  const backtestResponse = http.post(
    `${API_URL}/api/backtests`,
    backtestPayload,
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${__ENV.AUTH_TOKEN || "test-token"}`,
      },
    }
  );

  backtestCreationTime.add(backtestResponse.timings.duration);

  const backtestCreated = check(backtestResponse, {
    "backtest created successfully": (r) => r.status === 201,
    "backtest response has id": (r) => r.json("id") !== null,
  });

  if (!backtestCreated) {
    errorRate.add(1);
    return;
  }

  const backtestId = backtestResponse.json("id");
  sleep(2);

  // Test 3: Load results
  const resultsResponse = http.get(
    `${API_URL}/api/backtests/${backtestId}/results`
  );

  resultsLoadTime.add(resultsResponse.timings.duration);

  check(resultsResponse, {
    "results load successfully": (r) => r.status === 200,
    "results contain metrics": (r) => r.json("sharpeRatio") !== null,
  }) || errorRate.add(1);

  sleep(1);

  // Test 4: Load trades with pagination
  const tradesResponse = http.get(
    `${API_URL}/api/backtests/${backtestId}/trades?page=1&pageSize=50`
  );

  check(tradesResponse, {
    "trades load successfully": (r) => r.status === 200,
    "trades response is paginated": (r) => r.json("total") !== null,
  }) || errorRate.add(1);

  // Test 5: WebSocket connection (simulated)
  const wsStartTime = Date.now();
  const wsCheckResponse = http.get(`${API_URL}/ws/health`);
  const wsConnectionDuration = Date.now() - wsStartTime;

  websocketConnectionTime.add(wsConnectionDuration);

  check(wsCheckResponse, {
    "websocket endpoint available": (r) => r.status < 400,
  }) || errorRate.add(1);

  // Test 6: Strategy list
  const strategiesResponse = http.get(`${API_URL}/api/strategies`);

  check(strategiesResponse, {
    "strategies load successfully": (r) => r.status === 200,
    "strategies response is array": (r) => Array.isArray(r.json("strategies")),
  }) || errorRate.add(1);

  sleep(2);

  // Test 7: System status
  const statusResponse = http.get(`${API_URL}/api/system/status`);

  check(statusResponse, {
    "system status available": (r) => r.status === 200,
    "cpu usage reported": (r) => r.json("cpuUsage") !== null,
    "memory usage reported": (r) => r.json("memoryUsage") !== null,
  }) || errorRate.add(1);

  // Test 8: Data contracts
  const contractsResponse = http.get(`${API_URL}/api/data/contracts`);

  check(contractsResponse, {
    "contracts load successfully": (r) => r.status === 200,
    "contracts contain data": (r) => r.json("contracts").length > 0,
  }) || errorRate.add(1);

  sleep(3);
}

export function teardown(data) {
  // Cleanup code if needed
  console.log("Test completed");
}
