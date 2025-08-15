import { useState, useEffect, useCallback } from "react";

interface DataConfiguration {
  date_range: {
    start: string;
    end: string;
  };
  contracts: string[];
  data_level: "L1" | "L2";
  include_holidays: boolean;
  time_zone: string;
}

interface DateRange {
  start: string;
  end: string;
}

interface ValidationResult {
  valid: boolean;
  errors?: string[];
  warnings?: string[];
}

interface Contract {
  month: string;
  year: string;
  code: string;
  name: string;
  available: boolean;
}

interface DataEstimate {
  estimatedTime: string;
  dataPoints: number;
  memoryUsage: string;
}

export function useContracts() {
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Mock data for now
    setContracts([
      {
        month: "03",
        year: "2024",
        code: "MNQH24",
        name: "March 2024",
        available: true,
      },
      {
        month: "06",
        year: "2024",
        code: "MNQM24",
        name: "June 2024",
        available: true,
      },
      {
        month: "09",
        year: "2024",
        code: "MNQU24",
        name: "September 2024",
        available: true,
      },
      {
        month: "12",
        year: "2024",
        code: "MNQZ24",
        name: "December 2024",
        available: true,
      },
    ]);
    setLoading(false);
  }, []);

  return { contracts, loading, error };
}

export function useInputValidation(
  startDate: string,
  endDate: string,
  contracts: string[]
) {
  const [isValid, setIsValid] = useState(true);
  const [errors, setErrors] = useState<string[]>([]);

  useEffect(() => {
    const validationErrors: string[] = [];

    if (!startDate) validationErrors.push("Start date is required");
    if (!endDate) validationErrors.push("End date is required");
    if (!contracts || contracts.length === 0)
      validationErrors.push("At least one contract must be selected");

    if (startDate && endDate && new Date(startDate) > new Date(endDate)) {
      validationErrors.push("Start date must be before end date");
    }

    setErrors(validationErrors);
    setIsValid(validationErrors.length === 0);
  }, [startDate, endDate, contracts]);

  return { isValid, errors };
}

export function useQuickDataEstimate(
  startDate: string,
  endDate: string,
  contracts: string[]
) {
  const [estimate, setEstimate] = useState<DataEstimate | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!startDate || !endDate || !contracts || contracts.length === 0) {
      setEstimate(null);
      return;
    }

    setLoading(true);
    // Mock estimation
    setTimeout(() => {
      const days = Math.ceil(
        (new Date(endDate).getTime() - new Date(startDate).getTime()) /
          (1000 * 60 * 60 * 24)
      );
      const dataPoints = days * contracts.length * 100000; // Rough estimate

      setEstimate({
        estimatedTime: `${Math.ceil((days * contracts.length) / 10)} seconds`,
        dataPoints: dataPoints,
        memoryUsage: `${(dataPoints * 0.0001).toFixed(2)} MB`,
      });
      setLoading(false);
    }, 500);
  }, [startDate, endDate, contracts]);

  return { estimate, loading };
}

interface DataAvailability {
  contract: string;
  level1_available: boolean;
  level2_available: boolean;
}

export function useDataAvailability() {
  const [availability, setAvailability] = useState<DataAvailability[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Mock data availability - return array format expected by the page
    setAvailability([
      { contract: "MNQH24", level1_available: true, level2_available: true },
      { contract: "MNQM24", level1_available: true, level2_available: true },
      { contract: "MNQU24", level1_available: true, level2_available: false },
      { contract: "MNQZ24", level1_available: true, level2_available: true },
    ]);
    setLoading(false);
  }, []);

  return { availability, loading };
}

// Additional hooks expected by the data configuration page
export function useDataValidation() {
  const [validation, setValidation] = useState<ValidationResult | null>(null);
  const [validating, setValidating] = useState(false);

  const validateConfiguration = useCallback(
    async (config: DataConfiguration) => {
      setValidating(true);

      // Simulate validation
      await new Promise((resolve) => setTimeout(resolve, 1000));

      const errors: string[] = [];
      const warnings: string[] = [];

      if (!config.date_range.start) errors.push("Start date is required");
      if (!config.date_range.end) errors.push("End date is required");
      if (config.contracts.length === 0)
        errors.push("At least one contract must be selected");

      if (config.date_range.start && config.date_range.end) {
        const start = new Date(config.date_range.start);
        const end = new Date(config.date_range.end);
        if (start > end) errors.push("Start date must be before end date");

        const daysDiff = (end.getTime() - start.getTime()) / (1000 * 3600 * 24);
        if (daysDiff > 365)
          warnings.push("Large date range may impact performance");
      }

      const result = {
        valid: errors.length === 0,
        errors: errors.length > 0 ? errors : undefined,
        warnings: warnings.length > 0 ? warnings : undefined,
      };

      setValidation(result);
      setValidating(false);

      return result;
    },
    []
  );

  return { validateConfiguration, validating, validation };
}

export function useDataEstimate() {
  const [estimate, setEstimate] = useState<any>(null);
  const [estimating, setEstimating] = useState(false);

  const estimatePerformance = useCallback(async (config: DataConfiguration) => {
    setEstimating(true);

    // Simulate estimation
    await new Promise((resolve) => setTimeout(resolve, 800));

    const start = new Date(config.date_range.start);
    const end = new Date(config.date_range.end);
    const daysDiff = Math.ceil(
      (end.getTime() - start.getTime()) / (1000 * 3600 * 24)
    );
    const dataPoints = daysDiff * config.contracts.length * 100000;

    const result = {
      estimatedTime: `${Math.ceil(
        (daysDiff * config.contracts.length) / 10
      )} seconds`,
      dataPoints: dataPoints,
      memoryUsage: `${(dataPoints * 0.0001).toFixed(2)} MB`,
      processingTime: `${Math.ceil(dataPoints / 50000)} seconds`,
    };

    setEstimate(result);
    setEstimating(false);

    return result;
  }, []);

  return { estimatePerformance, estimating, estimate };
}

// Export types for use in components
export type { DataConfiguration, DateRange, ValidationResult };
