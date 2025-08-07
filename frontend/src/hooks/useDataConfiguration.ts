import { useState, useEffect } from "react";
import { useToast } from "@/hooks/use-toast";

export interface DateRange {
  start: Date | null;
  end: Date | null;
}

export interface ContractInfo {
  symbol: string;
  month: string;
  year: number;
  displayName: string;
  firstTradeDate: string;
  lastTradeDate: string;
  isFrontMonth: boolean;
  dataAvailable: {
    level1: boolean;
    level2: boolean;
  };
  qualityScore: number;
  tickCount: number;
  sizeMB: number;
}

export interface DataAvailability {
  date: string;
  hasData: boolean;
  qualityScore: number;
  contracts: string[];
  isHoliday: boolean;
  isWeekend: boolean;
  tickCount?: number;
}

export interface DataConfiguration {
  dateRange: {
    start: string;
    end: string;
  };
  contracts: string[];
  dataLevel: "L1" | "L2";
  includeHolidays: boolean;
  timeZone: string;
}

export interface PerformanceEstimate {
  totalTicks: number;
  estimatedDurationMinutes: number;
  memoryRequirementMB: number;
  diskSpaceMB: number;
  recommendedThreads: number;
  warnings: string[];
  suggestions: string[];
}

export interface QualityDetails {
  completeness: number;
  accuracy: number;
  timeliness: number;
  gaps: Array<{ start: string; end: string }>;
  anomalies: Array<{ date: string; description: string }>;
}

// Mock data for development
const mockContracts: ContractInfo[] = [
  {
    symbol: "MNQZ24",
    month: "December",
    year: 2024,
    displayName: "MNQ Dec 2024",
    firstTradeDate: "2024-09-01",
    lastTradeDate: "2024-12-31",
    isFrontMonth: true,
    dataAvailable: { level1: true, level2: true },
    qualityScore: 0.98,
    tickCount: 5432100,
    sizeMB: 1250,
  },
  {
    symbol: "MNQH25",
    month: "March",
    year: 2025,
    displayName: "MNQ Mar 2025",
    firstTradeDate: "2024-12-01",
    lastTradeDate: "2025-03-31",
    isFrontMonth: false,
    dataAvailable: { level1: true, level2: true },
    qualityScore: 0.96,
    tickCount: 3210500,
    sizeMB: 850,
  },
  {
    symbol: "MNQM25",
    month: "June",
    year: 2025,
    displayName: "MNQ Jun 2025",
    firstTradeDate: "2025-03-01",
    lastTradeDate: "2025-06-30",
    isFrontMonth: false,
    dataAvailable: { level1: true, level2: false },
    qualityScore: 0.92,
    tickCount: 1850000,
    sizeMB: 450,
  },
];

// Market holidays for 2024-2025
const marketHolidays = [
  "2024-01-01", "2024-01-15", "2024-02-19", "2024-03-29",
  "2024-05-27", "2024-06-19", "2024-07-04", "2024-09-02",
  "2024-11-28", "2024-12-25",
  "2025-01-01", "2025-01-20", "2025-02-17", "2025-04-18",
  "2025-05-26", "2025-06-19", "2025-07-04", "2025-09-01",
  "2025-11-27", "2025-12-25",
];

export function useDataConfiguration() {
  const { toast } = useToast();
  const [contracts, setContracts] = useState<ContractInfo[]>([]);
  const [selectedContracts, setSelectedContracts] = useState<string[]>([]);
  const [dateRange, setDateRange] = useState<DateRange>({ start: null, end: null });
  const [dataLevel, setDataLevel] = useState<"L1" | "L2">("L1");
  const [includeHolidays, setIncludeHolidays] = useState(false);
  const [timeZone, setTimeZone] = useState("America/Chicago");
  const [isLoading, setIsLoading] = useState(false);
  const [performanceEstimate, setPerformanceEstimate] = useState<PerformanceEstimate | null>(null);

  // Load available contracts
  useEffect(() => {
    loadContracts();
  }, []);

  // Update performance estimate when configuration changes
  useEffect(() => {
    if (dateRange.start && dateRange.end && selectedContracts.length > 0) {
      estimatePerformance();
    }
  }, [dateRange, selectedContracts, dataLevel, includeHolidays]);

  const loadContracts = async () => {
    setIsLoading(true);
    try {
      // In production, this would be an API call
      // const response = await fetch("/api/data/contracts");
      // const data = await response.json();
      setContracts(mockContracts);
    } catch (error) {
      toast({
        title: "Error loading contracts",
        description: "Failed to load available contracts. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const estimatePerformance = async () => {
    if (!dateRange.start || !dateRange.end || selectedContracts.length === 0) {
      setPerformanceEstimate(null);
      return;
    }

    try {
      // Calculate days in range
      const days = Math.ceil(
        (dateRange.end.getTime() - dateRange.start.getTime()) / (1000 * 60 * 60 * 24)
      );

      // Calculate total ticks and size based on selected contracts
      const selectedContractInfo = contracts.filter(c => 
        selectedContracts.includes(c.symbol)
      );
      
      const avgTicksPerDay = selectedContractInfo.reduce((sum, c) => 
        sum + (c.tickCount / 90), 0
      ) / selectedContractInfo.length;
      
      const totalTicks = Math.floor(avgTicksPerDay * days);
      const totalSizeMB = selectedContractInfo.reduce((sum, c) => 
        sum + (c.sizeMB * days / 90), 0
      );

      // Estimate processing time (simplified)
      const baseTimePerMillion = dataLevel === "L1" ? 0.5 : 1.2; // minutes
      const estimatedMinutes = Math.ceil((totalTicks / 1000000) * baseTimePerMillion);

      // Memory estimate
      const memoryBase = dataLevel === "L1" ? 512 : 1024;
      const memoryPerContract = dataLevel === "L1" ? 256 : 512;
      const memoryMB = memoryBase + (selectedContracts.length * memoryPerContract);

      // Generate warnings and suggestions
      const warnings: string[] = [];
      const suggestions: string[] = [];

      if (days > 180) {
        warnings.push("Large date range may result in extended processing time");
        suggestions.push("Consider splitting into smaller date ranges for faster results");
      }

      if (dataLevel === "L2" && selectedContracts.length > 2) {
        warnings.push("Level 2 data with multiple contracts requires significant memory");
        suggestions.push("Consider using Level 1 data or fewer contracts");
      }

      if (totalSizeMB > 5000) {
        warnings.push("Large data size may impact performance");
      }

      setPerformanceEstimate({
        totalTicks,
        estimatedDurationMinutes: estimatedMinutes,
        memoryRequirementMB: memoryMB,
        diskSpaceMB: Math.ceil(totalSizeMB),
        recommendedThreads: Math.min(selectedContracts.length, 4),
        warnings,
        suggestions,
      });
    } catch (error) {
      console.error("Failed to estimate performance:", error);
    }
  };

  const getDataAvailability = (date: Date): DataAvailability => {
    const dateStr = date.toISOString().split("T")[0];
    const dayOfWeek = date.getDay();
    const isWeekend = dayOfWeek === 0 || dayOfWeek === 6;
    const isHoliday = marketHolidays.includes(dateStr);

    // Check which contracts have data for this date
    const availableContracts = contracts.filter(contract => {
      const contractStart = new Date(contract.firstTradeDate);
      const contractEnd = new Date(contract.lastTradeDate);
      return date >= contractStart && date <= contractEnd;
    });

    const hasData = availableContracts.length > 0 && !isWeekend && !isHoliday;
    const qualityScore = hasData
      ? availableContracts.reduce((sum, c) => sum + c.qualityScore, 0) / availableContracts.length
      : 0;

    return {
      date: dateStr,
      hasData,
      qualityScore,
      contracts: availableContracts.map(c => c.symbol),
      isHoliday,
      isWeekend,
      tickCount: hasData ? 
        Math.floor(availableContracts.reduce((sum, c) => sum + c.tickCount / 90, 0)) : 0,
    };
  };

  const validateConfiguration = (): { isValid: boolean; errors: string[] } => {
    const errors: string[] = [];

    if (!dateRange.start || !dateRange.end) {
      errors.push("Please select both start and end dates");
    } else if (dateRange.start > dateRange.end) {
      errors.push("Start date must be before end date");
    }

    if (selectedContracts.length === 0) {
      errors.push("Please select at least one contract");
    }

    // Check if selected contracts have data for the date range
    if (dateRange.start && dateRange.end) {
      const hasValidContract = selectedContracts.some(contractSymbol => {
        const contract = contracts.find(c => c.symbol === contractSymbol);
        if (!contract) return false;
        
        const contractStart = new Date(contract.firstTradeDate);
        const contractEnd = new Date(contract.lastTradeDate);
        
        return !(dateRange.end! < contractStart || dateRange.start! > contractEnd);
      });

      if (!hasValidContract) {
        errors.push("Selected contracts have no data in the specified date range");
      }
    }

    return {
      isValid: errors.length === 0,
      errors,
    };
  };

  const getConfiguration = (): DataConfiguration => {
    return {
      dateRange: {
        start: dateRange.start?.toISOString().split("T")[0] || "",
        end: dateRange.end?.toISOString().split("T")[0] || "",
      },
      contracts: selectedContracts,
      dataLevel,
      includeHolidays,
      timeZone,
    };
  };

  return {
    // State
    contracts,
    selectedContracts,
    dateRange,
    dataLevel,
    includeHolidays,
    timeZone,
    isLoading,
    performanceEstimate,

    // Actions
    setSelectedContracts,
    setDateRange,
    setDataLevel,
    setIncludeHolidays,
    setTimeZone,

    // Utilities
    getDataAvailability,
    validateConfiguration,
    getConfiguration,
    estimatePerformance,
  };
}