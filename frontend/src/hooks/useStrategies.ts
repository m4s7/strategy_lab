import { useState, useEffect } from "react";
import { API_URL } from "../lib/config";

export interface ValidationRule {
  min?: number;
  max?: number;
  step?: number;
  required?: boolean;
  pattern?: string;
}

export interface ParameterDefinition {
  name: string;
  type: "number" | "boolean" | "string" | "select" | "date" | "range";
  description: string;
  required: boolean;
  default?: any;
  validation?: ValidationRule;
  options?: any[];
  dependencies?: string[];
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  category: string;
  parameters: ParameterDefinition[];
  documentation?: string;
  default_params?: Record<string, any>;
}

export interface ConfigurationTemplate {
  id: string;
  name: string;
  strategy_id: string;
  parameters: Record<string, any>;
  description?: string;
  created_at: string;
  last_used?: string;
}

export interface ValidationError {
  parameter: string;
  error: string;
}

export const useStrategies = () => {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStrategies = async () => {
      try {
        const response = await fetch(`${API_URL}/v1/strategies`);
        if (!response.ok) throw new Error("Failed to fetch strategies");
        const data = await response.json();
        setStrategies(data.strategies);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchStrategies();
  }, []);

  return { strategies, loading, error };
};

export const useStrategy = (strategyId: string) => {
  const [strategy, setStrategy] = useState<Strategy | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!strategyId) {
      setLoading(false);
      return;
    }

    const fetchStrategy = async () => {
      try {
        const response = await fetch(`${API_URL}/v1/strategies/${strategyId}`);
        if (!response.ok) throw new Error("Failed to fetch strategy");
        const data = await response.json();
        setStrategy(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchStrategy();
  }, [strategyId]);

  return { strategy, loading, error };
};

export const useStrategyValidation = (strategyId: string) => {
  const [validating, setValidating] = useState(false);
  const [errors, setErrors] = useState<ValidationError[]>([]);

  const validateParameters = async (parameters: Record<string, any>) => {
    setValidating(true);
    try {
      const response = await fetch(
        `${API_URL}/v1/strategies/${strategyId}/validate`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ parameters }),
        }
      );

      if (!response.ok) throw new Error("Validation request failed");

      const data = await response.json();
      setErrors(data.errors || []);
      return data.valid;
    } catch (err) {
      console.error("Validation error:", err);
      return false;
    } finally {
      setValidating(false);
    }
  };

  return { validateParameters, validating, errors };
};

export const useConfigurationTemplates = (strategyId: string) => {
  const [templates, setTemplates] = useState<ConfigurationTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!strategyId) return;

    const fetchTemplates = async () => {
      setLoading(true);
      try {
        const response = await fetch(
          `${API_URL}/v1/strategies/${strategyId}/templates`
        );
        if (!response.ok) throw new Error("Failed to fetch templates");
        const data = await response.json();
        setTemplates(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    fetchTemplates();
  }, [strategyId]);

  const saveTemplate = async (
    name: string,
    parameters: Record<string, any>,
    description?: string
  ) => {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/strategies/${strategyId}/templates`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name,
            strategy_id: strategyId,
            parameters,
            description,
          }),
        }
      );

      if (!response.ok) throw new Error("Failed to save template");

      const newTemplate = await response.json();
      setTemplates((prev) => [...prev, newTemplate]);
      return newTemplate;
    } catch (err) {
      throw new Error(
        err instanceof Error ? err.message : "Failed to save template"
      );
    }
  };

  const loadTemplate = async (templateId: string) => {
    try {
      const response = await fetch(
        `${API_URL}/v1/strategies/templates/${templateId}`
      );
      if (!response.ok) throw new Error("Failed to load template");
      const template = await response.json();
      return template;
    } catch (err) {
      throw new Error(
        err instanceof Error ? err.message : "Failed to load template"
      );
    }
  };

  const deleteTemplate = async (templateId: string) => {
    try {
      const response = await fetch(
        `${API_URL}/v1/strategies/templates/${templateId}`,
        { method: "DELETE" }
      );
      if (!response.ok) throw new Error("Failed to delete template");

      setTemplates((prev) => prev.filter((t) => t.id !== templateId));
    } catch (err) {
      throw new Error(
        err instanceof Error ? err.message : "Failed to delete template"
      );
    }
  };

  return {
    templates,
    loading,
    error,
    saveTemplate,
    loadTemplate,
    deleteTemplate,
  };
};
