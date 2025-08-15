"use client";

import { useEffect, useState } from "react";
import { API_URL } from "@/lib/config";

export default function ApiTestPage() {
  const [apiUrl, setApiUrl] = useState<string>("");
  const [testResult, setTestResult] = useState<any>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    // Show the API URL from config
    setApiUrl(API_URL);

    // Test API call
    if (API_URL) {
      fetch(`${API_URL}/v1/system/status`)
        .then((res) => res.json())
        .then((data) => setTestResult(data))
        .catch((err) => setError(err.message));
    }
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">API Test Page</h1>

      <div className="space-y-4">
        <div>
          <strong>NEXT_PUBLIC_API_URL:</strong>
          <code className="ml-2 p-1 bg-gray-100">{apiUrl}</code>
        </div>

        <div>
          <strong>Test API Call Result:</strong>
          {error && <div className="text-red-500">{error}</div>}
          {testResult && (
            <pre className="mt-2 p-4 bg-gray-100 rounded">
              {JSON.stringify(testResult, null, 2)}
            </pre>
          )}
        </div>
      </div>
    </div>
  );
}
