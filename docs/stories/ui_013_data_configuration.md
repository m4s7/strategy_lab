# Story UI_013: Data Configuration Interface

## Story Details
- **Story ID**: UI_013
- **Epic**: Epic 2 - Core Backtesting Features
- **Story Points**: 5
- **Priority**: High
- **Type**: User Interface + Data Integration

## User Story
**As a** trading researcher
**I want** to configure data parameters for backtests
**So that** I can specify date ranges, contracts, and data levels visually with confidence in data availability

## Acceptance Criteria

### 1. Date Range Selection
- [ ] Interactive calendar date picker for start and end dates
- [ ] Data availability indicators overlaid on calendar
- [ ] Quick preset buttons (Last 30 days, Last 3 months, etc.)
- [ ] Date validation with available data range
- [ ] Visual indicators for data gaps or quality issues
- [ ] Holiday and market closure awareness

### 2. Contract Month Selection
- [ ] Multi-select dropdown for MNQ contract months
- [ ] Visual timeline showing contract lifespans
- [ ] Roll dates and contract transitions highlighted
- [ ] Data availability per contract displayed
- [ ] Front month vs back month indicators
- [ ] Contract volume and liquidity information

### 3. Data Level Configuration
- [ ] Radio button or toggle for Level 1 vs Level 2 data
- [ ] Clear explanation of data level differences
- [ ] Performance impact warnings for Level 2
- [ ] Data size estimation based on selection
- [ ] Quality metrics for each data level
- [ ] Recommendation engine for optimal data level

### 4. Data Quality Assessment
- [ ] Data quality score display (completeness, accuracy)
- [ ] Missing data periods highlighted
- [ ] Tick count and coverage statistics
- [ ] Anomaly detection warnings
- [ ] Data source information and timestamps
- [ ] Quality comparison across different periods

### 5. Performance Estimation
- [ ] Estimated backtest duration based on data selection
- [ ] Memory usage estimation
- [ ] Processing speed indicators
- [ ] Resource impact warnings for large selections
- [ ] Optimization suggestions for better performance
- [ ] Cost estimation (if applicable)

### 6. Data Preview
- [ ] Sample data display for selected configuration
- [ ] Basic statistics (tick count, date range, price range)
- [ ] Data format preview
- [ ] Quality metrics summary
- [ ] Export sample data capability
- [ ] Data lineage information

## Technical Requirements

### Data Index Integration
```typescript
interface DataAvailability {
  contract: string;
  startDate: string;
  endDate: string;
  level1Available: boolean;
  level2Available: boolean;
  qualityScore: number;
  tickCount: number;
  fileSizeMB: number;
  dataGaps: DateRange[];
  lastUpdated: string;
}

interface DataConfiguration {
  dateRange: {
    start: string;
    end: string;
  };
  contracts: string[];
  dataLevel: 'L1' | 'L2';
  includeHolidays: boolean;
  timeZone: string;
  estimatedDuration?: number;
  estimatedMemoryMB?: number;
}

// API endpoints
GET /api/data/availability - Get data availability index
GET /api/data/contracts - Get available contract months
POST /api/data/validate - Validate data configuration
GET /api/data/estimate - Get performance estimates
```

### Calendar Component with Data Overlay
```typescript
const DataCalendar: React.FC<{
  availability: DataAvailability[];
  selectedRange: DateRange;
  onChange: (range: DateRange) => void;
}> = ({ availability, selectedRange, onChange }) => {

  const getDateStatus = (date: Date) => {
    const dateStr = date.toISOString().split('T')[0];
    const hasData = availability.some(contract =>
      dateStr >= contract.startDate && dateStr <= contract.endDate
    );

    const qualityScore = availability
      .filter(contract => dateStr >= contract.startDate && dateStr <= contract.endDate)
      .reduce((avg, contract) => avg + contract.qualityScore, 0) / availability.length;

    return {
      hasData,
      quality: qualityScore,
      isHoliday: isMarketHoliday(date),
      isWeekend: date.getDay() === 0 || date.getDay() === 6
    };
  };

  return (
    <Calendar
      range={selectedRange}
      onChange={onChange}
      dayRenderer={(date) => (
        <CalendarDay
          date={date}
          status={getDateStatus(date)}
          selected={isDateInRange(date, selectedRange)}
        />
      )}
      legend={<DataAvailabilityLegend />}
    />
  );
};
```

### Contract Selection Interface
```typescript
const ContractSelector: React.FC<{
  availableContracts: ContractInfo[];
  selectedContracts: string[];
  onChange: (contracts: string[]) => void;
}> = ({ availableContracts, selectedContracts, onChange }) => {

  return (
    <div className="contract-selector">
      <div className="contract-timeline">
        <ContractTimeline
          contracts={availableContracts}
          selected={selectedContracts}
          onContractClick={toggleContract}
        />
      </div>

      <div className="contract-list">
        {availableContracts.map(contract => (
          <ContractCard
            key={contract.symbol}
            contract={contract}
            selected={selectedContracts.includes(contract.symbol)}
            onChange={() => toggleContract(contract.symbol)}
          />
        ))}
      </div>

      <div className="selection-summary">
        <DataSummary
          contracts={selectedContracts}
          totalSize={calculateTotalSize(selectedContracts)}
          estimatedDuration={calculateDuration(selectedContracts)}
        />
      </div>
    </div>
  );
};
```

### Performance Estimation Engine
```typescript
const useDataEstimation = (config: DataConfiguration) => {
  const [estimation, setEstimation] = useState<PerformanceEstimate | null>(null);

  useEffect(() => {
    const calculateEstimation = async () => {
      if (!config.dateRange.start || !config.contracts.length) return;

      try {
        const response = await fetch('/api/data/estimate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(config)
        });

        const estimate: PerformanceEstimate = await response.json();
        setEstimation(estimate);
      } catch (error) {
        console.error('Failed to calculate estimation:', error);
      }
    };

    // Debounce estimation calculation
    const timer = setTimeout(calculateEstimation, 500);
    return () => clearTimeout(timer);
  }, [config]);

  return estimation;
};

interface PerformanceEstimate {
  totalTicks: number;
  estimatedDurationMinutes: number;
  memoryRequirementMB: number;
  recommendedThreads: number;
  warnings: string[];
  suggestions: string[];
}
```

### Data Quality Indicators
```typescript
const DataQualityIndicator: React.FC<{
  quality: number;
  details?: QualityDetails;
}> = ({ quality, details }) => {
  const getQualityColor = (score: number) => {
    if (score >= 0.95) return 'text-green-600';
    if (score >= 0.85) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getQualityLabel = (score: number) => {
    if (score >= 0.95) return 'Excellent';
    if (score >= 0.85) return 'Good';
    if (score >= 0.7) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="data-quality-indicator">
      <div className={`quality-score ${getQualityColor(quality)}`}>
        {(quality * 100).toFixed(1)}% - {getQualityLabel(quality)}
      </div>
      {details && (
        <div className="quality-details">
          <div>Completeness: {(details.completeness * 100).toFixed(1)}%</div>
          <div>Accuracy: {(details.accuracy * 100).toFixed(1)}%</div>
          <div>Timeliness: {(details.timeliness * 100).toFixed(1)}%</div>
          {details.gaps.length > 0 && (
            <div className="data-gaps">
              Gaps: {details.gaps.map(gap => `${gap.start} - ${gap.end}`).join(', ')}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
```

## Definition of Done
- [ ] Date picker shows data availability overlay
- [ ] Contract selection displays availability and quality
- [ ] Data level selection shows performance implications
- [ ] Quality indicators are accurate and helpful
- [ ] Performance estimation provides realistic numbers
- [ ] Configuration validation prevents invalid selections
- [ ] Data preview shows representative sample
- [ ] All components work together smoothly

## Testing Checklist
- [ ] Calendar correctly shows data available/unavailable dates
- [ ] Contract selection handles multiple selections properly
- [ ] Data level toggle shows appropriate warnings
- [ ] Quality scores match actual data quality
- [ ] Performance estimates are within reasonable accuracy
- [ ] Large date ranges show appropriate warnings
- [ ] Invalid configurations are caught and explained
- [ ] Data preview loads quickly and shows relevant information

## Integration Points
- **MNQ Data Index**: Integration with Parquet file metadata
- **Performance Calculator**: Backend service for duration/memory estimation
- **Data Quality Service**: Real-time quality assessment
- **Next Stories**: Configuration feeds into UI_014 (Backtest Execution)

## Performance Requirements
- Data availability lookup < 1 second
- Calendar rendering < 500ms
- Performance estimation < 2 seconds
- Data quality calculation < 1 second
- UI remains responsive during data loading

## Accessibility Requirements
- Calendar keyboard navigation
- Screen reader support for data indicators
- High contrast mode for quality indicators
- Alternative text for visual elements

## Follow-up Stories
- UI_014: Backtest Execution Control (uses data configuration)
- UI_024: Order Book Visualization (uses Level 2 data configuration)
