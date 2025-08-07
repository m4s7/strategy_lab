import { useEffect, useState } from "react";
import { Strategy } from "@/hooks/useStrategies";

interface CrossParameterRule {
  parameters: string[];
  validate: (values: Record<string, any>) => string | null;
  message?: string;
}

// Define cross-parameter validation rules for different strategies
const crossParameterRules: Record<string, CrossParameterRule[]> = {
  order_book_scalper: [
    {
      parameters: ["stop_loss", "take_profit"],
      validate: (values) => {
        if (
          values.stop_loss &&
          values.take_profit &&
          values.stop_loss >= values.take_profit
        ) {
          return "Stop loss must be less than take profit";
        }
        return null;
      },
    },
    {
      parameters: ["min_spread", "max_spread"],
      validate: (values) => {
        if (
          values.min_spread &&
          values.max_spread &&
          values.min_spread > values.max_spread
        ) {
          return "Minimum spread must be less than or equal to maximum spread";
        }
        return null;
      },
    },
  ],
  momentum_breakout: [
    {
      parameters: ["lookback_period", "entry_threshold"],
      validate: (values) => {
        if (
          values.lookback_period &&
          values.lookback_period < 10 &&
          values.entry_threshold > 2
        ) {
          return "High entry threshold requires longer lookback period (at least 10)";
        }
        return null;
      },
    },
  ],
  mean_reversion: [
    {
      parameters: ["bollinger_period", "bollinger_std"],
      validate: (values) => {
        if (
          values.bollinger_period &&
          values.bollinger_period < 20 &&
          values.bollinger_std > 2.5
        ) {
          return "High standard deviation requires longer Bollinger period (at least 20)";
        }
        return null;
      },
    },
    {
      parameters: ["entry_z_score", "exit_z_score"],
      validate: (values) => {
        if (
          values.entry_z_score &&
          values.exit_z_score &&
          Math.abs(values.entry_z_score) <= Math.abs(values.exit_z_score)
        ) {
          return "Entry Z-score magnitude must be greater than exit Z-score magnitude";
        }
        return null;
      },
    },
  ],
};

export function useCrossParameterValidation(
  strategy: Strategy | null,
  values: Record<string, any>
): Record<string, string> {
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!strategy) {
      setErrors({});
      return;
    }

    const newErrors: Record<string, string> = {};
    const rules = crossParameterRules[strategy.id] || [];

    rules.forEach((rule, index) => {
      const error = rule.validate(values);
      if (error) {
        // Add error to each parameter involved in the rule
        rule.parameters.forEach((param) => {
          newErrors[param] = error;
        });
      }
    });

    setErrors(newErrors);
  }, [strategy, values]);

  return errors;
}

// Validation function for use in the strategy validation hook
export function validateCrossParameters(
  strategyId: string,
  values: Record<string, any>
): { isValid: boolean; errors: Array<{ parameter: string; error: string }> } {
  const rules = crossParameterRules[strategyId] || [];
  const errors: Array<{ parameter: string; error: string }> = [];
  const seenErrors = new Set<string>();

  rules.forEach((rule) => {
    const error = rule.validate(values);
    if (error && !seenErrors.has(error)) {
      seenErrors.add(error);
      // Add error only to the first parameter to avoid duplication
      errors.push({
        parameter: rule.parameters[0],
        error,
      });
    }
  });

  return {
    isValid: errors.length === 0,
    errors,
  };
}
