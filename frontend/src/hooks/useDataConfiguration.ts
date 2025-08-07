import { useState, useEffect } from 'react';

export interface DateRange {
  start: string;
  end: string;
}

export interface DataAvailability {
  contract: string;
  start_date: string;
  end_date: string;
  level1_available: boolean;
  level2_available: boolean;
  quality_score: number;
  tick_count: number;
  file_size_mb: number;
  data_gaps: DateRange[];
  last_updated: string;
  volume_avg: number;
}

export interface ContractInfo {
  contract: string;
  display_name: string;
  start_date: string;
  end_date: string;
  is_front_month: boolean;
  roll_date: string;
  data_quality: number;
  tick_count: number;
  volume_avg: number;
}

export interface DataConfiguration {
  date_range: DateRange;
  contracts: string[];
  data_level: 'L1' | 'L2';
  include_holidays: boolean;
  time_zone: string;
}

export interface DataEstimate {
  estimated_duration_seconds: number;
  estimated_memory_mb: number;
  estimated_ticks: number;
  estimated_file_size_mb: number;
  warnings: string[];
  recommendations: string[];
}

export interface DataValidation {
  valid: boolean;
  errors: string[];
  warnings: string[];
  available_data: DataAvailability[];
}

export const useDataAvailability = () => {
  const [availability, setAvailability] = useState<DataAvailability[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAvailability = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/data/availability`);
        if (!response.ok) throw new Error('Failed to fetch data availability');
        const data = await response.json();
        setAvailability(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchAvailability();
  }, []);

  return { availability, loading, error };
};

export const useContracts = () => {
  const [contracts, setContracts] = useState<ContractInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContracts = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/data/contracts`);
        if (!response.ok) throw new Error('Failed to fetch contracts');
        const data = await response.json();
        setContracts(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchContracts();
  }, []);

  return { contracts, loading, error };
};

export const useDataValidation = () => {
  const [validating, setValidating] = useState(false);
  const [validation, setValidation] = useState<DataValidation | null>(null);

  const validateConfiguration = async (config: DataConfiguration) => {
    setValidating(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/data/validate`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(config)
        }
      );
      
      if (!response.ok) throw new Error('Validation request failed');
      
      const data = await response.json();
      setValidation(data);
      return data;
    } catch (err) {
      console.error('Validation error:', err);
      return null;
    } finally {
      setValidating(false);
    }
  };

  return { validateConfiguration, validating, validation };
};

export const useDataEstimate = () => {
  const [estimating, setEstimating] = useState(false);
  const [estimate, setEstimate] = useState<DataEstimate | null>(null);

  const estimatePerformance = async (config: DataConfiguration) => {
    setEstimating(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/data/estimate`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(config)
        }
      );
      
      if (!response.ok) throw new Error('Estimate request failed');
      
      const data = await response.json();
      setEstimate(data);
      return data;
    } catch (err) {
      console.error('Estimate error:', err);
      return null;
    } finally {
      setEstimating(false);
    }
  };

  return { estimatePerformance, estimating, estimate };
};

export const useSampleData = (contract: string, dataLevel: 'L1' | 'L2' = 'L1') => {
  const [samples, setSamples] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSamples = async () => {
    if (!contract) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/data/sample/${contract}?data_level=${dataLevel}&limit=100`
      );
      if (!response.ok) throw new Error('Failed to fetch sample data');
      const data = await response.json();
      setSamples(data.samples || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSamples();
  }, [contract, dataLevel]);

  return { samples, loading, error, refresh: fetchSamples };
};