import http from "k6/http";
import { check, group, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

// Metrics for critical user journeys
const errorRate = new Rate("errors");
const strategyCreationJourney = new Trend("strategy_creation_journey");
const backtestExecutionJourney = new Trend("backtest_execution_journey");
const resultAnalysisJourney = new Trend("result_analysis_journey");
const optimizationJourney = new Trend("optimization_journey");

export const options = {
  scenarios: {
    // Scenario 1: New user creating first strategy
    new_user_journey: {
      executor: "constant-vus",
      vus: 10,
      duration: "5m",
    },
    // Scenario 2: Power user running multiple backtests
    power_user_journey: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "2m", target: 50 },
        { duration: "5m", target: 50 },
        { duration: "2m", target: 0 },
      ],
    },
    // Scenario 3: Spike test for result viewing
    result_viewing_spike: {
      executor: "constant-arrival-rate",
      rate: 100,
      timeUnit: "1s",
      duration: "2m",
      preAllocatedVUs: 200,
    },
  },
  thresholds: {
    "http_req_duration{scenario:new_user_journey}": ["p(95)<1000"],
    "http_req_duration{scenario:power_user_journey}": ["p(95)<800"],
    "http_req_duration{scenario:result_viewing_spike}": ["p(95)<500"],
    errors: ["rate<0.05"], // 5% error rate threshold
    strategy_creation_journey: ["p(95)<5000"], // Full journey under 5s
    backtest_execution_journey: ["p(95)<3000"], // Execution start under 3s
    result_analysis_journey: ["p(95)<2000"], // Results load under 2s
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:3000";
const API_URL = __ENV.API_URL || "http://localhost:8000";

// Simulate authentication
function authenticate() {
  const authResponse = http.post(
    `${API_URL}/api/auth/login`,
    JSON.stringify({
      username: `user_${__VU}_${Date.now()}`,
      password: "test123",
    }),
    {
      headers: { "Content-Type": "application/json" },
    }
  );

  if (authResponse.status !== 200) {
    errorRate.add(1);
    return null;
  }

  return authResponse.json("token");
}

// Critical Path 1: Strategy Creation Journey
function strategyCreationFlow(authToken) {
  const journeyStart = Date.now();

  group("Strategy Creation Journey", () => {
    // Step 1: Load strategies page
    const strategiesPage = http.get(`${BASE_URL}/strategies`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    check(strategiesPage, {
      "strategies page loads": (r) => r.status === 200,
    }) || errorRate.add(1);

    sleep(1);

    // Step 2: Get strategy templates
    const templates = http.get(`${API_URL}/api/strategies/templates`);

    check(templates, {
      "templates load": (r) => r.status === 200,
    }) || errorRate.add(1);

    // Step 3: Create new strategy
    const strategyData = {
      name: `Perf Test Strategy ${Date.now()}`,
      type: "scalping",
      parameters: {
        stopLoss: 15,
        takeProfit: 30,
        positionSize: 2,
      },
    };

    const createResponse = http.post(
      `${API_URL}/api/strategies`,
      JSON.stringify(strategyData),
      {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
      }
    );

    const strategyCreated = check(createResponse, {
      "strategy created": (r) => r.status === 201,
      "strategy has id": (r) => r.json("id") !== null,
    });

    if (!strategyCreated) {
      errorRate.add(1);
      return null;
    }

    strategyCreationJourney.add(Date.now() - journeyStart);
    return createResponse.json("id");
  });
}

// Critical Path 2: Backtest Execution Journey
function backtestExecutionFlow(authToken, strategyId) {
  const journeyStart = Date.now();

  group("Backtest Execution Journey", () => {
    // Step 1: Load backtest configuration page
    const configPage = http.get(`${BASE_URL}/backtests/new`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    check(configPage, {
      "config page loads": (r) => r.status === 200,
    }) || errorRate.add(1);

    // Step 2: Validate data availability
    const dataValidation = http.post(
      `${API_URL}/api/data/validate`,
      JSON.stringify({
        startDate: "2023-01-01",
        endDate: "2023-06-30",
        contracts: ["03-24", "06-24"],
      }),
      {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
      }
    );

    check(dataValidation, {
      "data validated": (r) => r.status === 200,
    }) || errorRate.add(1);

    // Step 3: Start backtest
    const backtestData = {
      strategyId: strategyId,
      config: {
        startDate: "2023-01-01",
        endDate: "2023-06-30",
        initialCapital: 100000,
        dataLevel: "level1",
        contracts: ["03-24", "06-24"],
      },
    };

    const startResponse = http.post(
      `${API_URL}/api/backtests`,
      JSON.stringify(backtestData),
      {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
      }
    );

    const backtestStarted = check(startResponse, {
      "backtest started": (r) => r.status === 201,
      "backtest has id": (r) => r.json("id") !== null,
    });

    if (!backtestStarted) {
      errorRate.add(1);
      return null;
    }

    backtestExecutionJourney.add(Date.now() - journeyStart);
    return startResponse.json("id");
  });
}

// Critical Path 3: Result Analysis Journey
function resultAnalysisFlow(authToken, backtestId) {
  const journeyStart = Date.now();

  group("Result Analysis Journey", () => {
    // Step 1: Load results overview
    const resultsPage = http.get(`${BASE_URL}/results/${backtestId}`, {
      headers: { Authorization: `Bearer ${authToken}` },
    });

    check(resultsPage, {
      "results page loads": (r) => r.status === 200,
    }) || errorRate.add(1);

    // Step 2: Get detailed metrics
    const metrics = http.get(`${API_URL}/api/backtests/${backtestId}/results`);

    check(metrics, {
      "metrics load": (r) => r.status === 200,
      "has performance data": (r) => r.json("sharpeRatio") !== null,
    }) || errorRate.add(1);

    // Step 3: Load trades
    const trades = http.get(
      `${API_URL}/api/backtests/${backtestId}/trades?page=1&pageSize=100`
    );

    check(trades, {
      "trades load": (r) => r.status === 200,
      "has trade data": (r) => r.json("trades").length > 0,
    }) || errorRate.add(1);

    // Step 4: Generate chart data
    const chartData = http.get(
      `${API_URL}/api/backtests/${backtestId}/charts/equity-curve`
    );

    check(chartData, {
      "chart data loads": (r) => r.status === 200,
    }) || errorRate.add(1);

    resultAnalysisJourney.add(Date.now() - journeyStart);
  });
}

// Critical Path 4: Optimization Journey
function optimizationFlow(authToken, strategyId) {
  const journeyStart = Date.now();

  group("Optimization Journey", () => {
    // Step 1: Configure optimization
    const optimConfig = {
      strategyId: strategyId,
      type: "grid-search",
      parameters: {
        stopLoss: { min: 5, max: 20, step: 5 },
        takeProfit: { min: 10, max: 40, step: 10 },
      },
      config: {
        startDate: "2023-01-01",
        endDate: "2023-06-30",
        metric: "sharpeRatio",
      },
    };

    const startOptim = http.post(
      `${API_URL}/api/optimization/grid-search`,
      JSON.stringify(optimConfig),
      {
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${authToken}`,
        },
      }
    );

    check(startOptim, {
      "optimization started": (r) => r.status === 201,
    }) || errorRate.add(1);

    // Step 2: Check status
    if (startOptim.status === 201) {
      const optimId = startOptim.json("id");
      sleep(2);

      const status = http.get(`${API_URL}/api/optimization/${optimId}/status`);

      check(status, {
        "status available": (r) => r.status === 200,
        "has progress": (r) => r.json("progress") !== null,
      }) || errorRate.add(1);
    }

    optimizationJourney.add(Date.now() - journeyStart);
  });
}

export default function () {
  const scenario = __ENV.SCENARIO || "new_user_journey";

  // Authenticate
  const authToken = authenticate();
  if (!authToken) {
    console.error("Authentication failed");
    return;
  }

  // Execute flows based on scenario
  if (scenario === "new_user_journey") {
    const strategyId = strategyCreationFlow(authToken);
    if (strategyId) {
      sleep(2);
      const backtestId = backtestExecutionFlow(authToken, strategyId);
      if (backtestId) {
        sleep(5);
        resultAnalysisFlow(authToken, backtestId);
      }
    }
  } else if (scenario === "power_user_journey") {
    // Simulate power user with existing strategy
    const strategyId = "existing-strategy-123";

    // Run multiple backtests
    for (let i = 0; i < 3; i++) {
      const backtestId = backtestExecutionFlow(authToken, strategyId);
      if (backtestId) {
        sleep(2);
        resultAnalysisFlow(authToken, backtestId);
      }
      sleep(3);
    }

    // Run optimization
    optimizationFlow(authToken, strategyId);
  } else if (scenario === "result_viewing_spike") {
    // Simulate viewing existing results
    const backtestId = `existing-backtest-${Math.floor(Math.random() * 100)}`;
    resultAnalysisFlow(authToken, backtestId);
  }

  sleep(1);
}
