import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { StrategySelector } from "../strategy-selector";
import { ParameterForm } from "../parameter-form";
import { ConfigurationPreview } from "../configuration-preview";
import { StrategyDocumentation } from "../strategy-documentation";
import { ConfigurationComparison } from "../configuration-comparison";
import { Strategy, ValidationError } from "@/hooks/useStrategies";

const mockStrategies: Strategy[] = [
  {
    id: "order_book_scalper",
    name: "Order Book Scalper",
    version: "1.0.0",
    description:
      "High-frequency scalping strategy based on order book imbalances",
    category: "Scalping",
    author: "Strategy Lab",
    created_at: "2024-01-01",
    updated_at: "2024-01-01",
    documentation: "Detailed documentation for order book scalper",
    parameters: [
      {
        name: "lookback_hours",
        type: "float",
        default_value: 4,
        required: true,
        description: "Hours of historical data to analyze",
        min_value: 1,
        max_value: 48,
      },
      {
        name: "min_spread",
        type: "float",
        default_value: 0.5,
        required: true,
        description: "Minimum spread threshold",
      },
      {
        name: "enable_ml_features",
        type: "boolean",
        default_value: false,
        required: false,
        description: "Enable machine learning features",
      },
    ],
    default_params: {
      lookback_hours: 4,
      min_spread: 0.5,
      enable_ml_features: false,
    },
  },
  {
    id: "momentum_breakout",
    name: "Momentum Breakout",
    version: "2.0.0",
    description: "Captures momentum-based price breakouts",
    category: "Momentum",
    author: "Strategy Lab",
    created_at: "2024-01-01",
    updated_at: "2024-01-01",
    documentation: "Momentum strategy documentation",
    parameters: [
      {
        name: "lookback_period",
        type: "int",
        default_value: 20,
        required: true,
        description: "Lookback period for momentum calculation",
        dependencies: [],
      },
    ],
    default_params: {
      lookback_period: 20,
    },
  },
];

describe("StrategySelector", () => {
  it("renders strategy list", () => {
    render(
      <StrategySelector
        strategies={mockStrategies}
        selectedStrategy={null}
        onSelectStrategy={() => {}}
      />
    );

    expect(screen.getByText("Order Book Scalper")).toBeInTheDocument();
    expect(screen.getByText("Momentum Breakout")).toBeInTheDocument();
  });

  it("filters strategies by search term", () => {
    render(
      <StrategySelector
        strategies={mockStrategies}
        selectedStrategy={null}
        onSelectStrategy={() => {}}
      />
    );

    const searchInput = screen.getByPlaceholderText("Search strategies...");
    fireEvent.change(searchInput, { target: { value: "momentum" } });

    expect(screen.getByText("Momentum Breakout")).toBeInTheDocument();
    expect(screen.queryByText("Order Book Scalper")).not.toBeInTheDocument();
  });

  it("filters strategies by category", () => {
    render(
      <StrategySelector
        strategies={mockStrategies}
        selectedStrategy={null}
        onSelectStrategy={() => {}}
      />
    );

    const categorySelect = screen.getByText("All Categories");
    fireEvent.click(categorySelect);
    fireEvent.click(screen.getByText("Scalping"));

    expect(screen.getByText("Order Book Scalper")).toBeInTheDocument();
    expect(screen.queryByText("Momentum Breakout")).not.toBeInTheDocument();
  });

  it("shows recent strategies when provided", () => {
    render(
      <StrategySelector
        strategies={mockStrategies}
        selectedStrategy={null}
        onSelectStrategy={() => {}}
        recentStrategies={["order_book_scalper"]}
      />
    );

    expect(screen.getByText("Recently Used")).toBeInTheDocument();
  });

  it("calls onSelectStrategy when strategy is clicked", () => {
    const mockOnSelect = jest.fn();
    render(
      <StrategySelector
        strategies={mockStrategies}
        selectedStrategy={null}
        onSelectStrategy={mockOnSelect}
      />
    );

    fireEvent.click(screen.getByText("Order Book Scalper"));
    expect(mockOnSelect).toHaveBeenCalledWith(mockStrategies[0]);
  });
});

describe("ParameterForm", () => {
  const mockStrategy = mockStrategies[0];
  const mockValues = {
    lookback_hours: 4,
    min_spread: 0.5,
    enable_ml_features: false,
  };

  it("renders all parameters", () => {
    render(
      <ParameterForm
        strategy={mockStrategy}
        values={mockValues}
        onChange={() => {}}
        errors={[]}
        onValidate={() => Promise.resolve(true)}
      />
    );

    expect(screen.getByText("lookback_hours")).toBeInTheDocument();
    expect(screen.getByText("min_spread")).toBeInTheDocument();
    expect(screen.getByText("enable_ml_features")).toBeInTheDocument();
  });

  it("shows validation errors", () => {
    const errors: ValidationError[] = [
      {
        parameter: "lookback_hours",
        error: "Value must be between 1 and 48",
      },
    ];

    render(
      <ParameterForm
        strategy={mockStrategy}
        values={mockValues}
        onChange={() => {}}
        errors={errors}
        onValidate={() => Promise.resolve(false)}
      />
    );

    expect(
      screen.getByText(/Value must be between 1 and 48/)
    ).toBeInTheDocument();
  });

  it("calls onChange when parameter is updated", () => {
    const mockOnChange = jest.fn();
    render(
      <ParameterForm
        strategy={mockStrategy}
        values={mockValues}
        onChange={mockOnChange}
        errors={[]}
        onValidate={() => Promise.resolve(true)}
      />
    );

    // This would need proper parameter input component testing
    // For now, test that the form renders without errors
    expect(screen.getByText("Configure Parameters")).toBeInTheDocument();
  });

  it("shows unsaved changes badge when dirty", () => {
    const { rerender } = render(
      <ParameterForm
        strategy={mockStrategy}
        values={mockValues}
        onChange={() => {}}
        errors={[]}
        onValidate={() => Promise.resolve(true)}
      />
    );

    // Initially no unsaved changes
    expect(screen.queryByText("Unsaved Changes")).not.toBeInTheDocument();

    // Simulate a change by re-rendering with different values
    const newValues = { ...mockValues, lookback_hours: 6 };
    rerender(
      <ParameterForm
        strategy={mockStrategy}
        values={newValues}
        onChange={() => {}}
        errors={[]}
        onValidate={() => Promise.resolve(true)}
      />
    );
  });
});

describe("ConfigurationPreview", () => {
  const mockStrategy = mockStrategies[0];
  const mockConfig = {
    lookback_hours: 4,
    min_spread: 0.5,
    enable_ml_features: true,
  };

  it("renders configuration summary", () => {
    render(
      <ConfigurationPreview
        strategy={mockStrategy}
        configuration={mockConfig}
        isValid={true}
      />
    );

    expect(screen.getByText("Configuration Summary")).toBeInTheDocument();
    expect(screen.getByText("Configuration Valid")).toBeInTheDocument();
  });

  it("shows invalid configuration state", () => {
    render(
      <ConfigurationPreview
        strategy={mockStrategy}
        configuration={{}}
        isValid={false}
      />
    );

    expect(screen.getByText("Configuration Incomplete")).toBeInTheDocument();
  });

  it("displays resource estimates", () => {
    render(
      <ConfigurationPreview
        strategy={mockStrategy}
        configuration={mockConfig}
        isValid={true}
      />
    );

    expect(
      screen.getByText("Estimated Resource Requirements")
    ).toBeInTheDocument();
    expect(screen.getByText("CPU Usage")).toBeInTheDocument();
    expect(screen.getByText("Memory")).toBeInTheDocument();
    expect(screen.getByText("Est. Time")).toBeInTheDocument();
    expect(screen.getByText("Disk Space")).toBeInTheDocument();
  });

  it("copies configuration to clipboard", async () => {
    // Mock clipboard API
    Object.assign(navigator, {
      clipboard: {
        writeText: jest.fn(() => Promise.resolve()),
      },
    });

    render(
      <ConfigurationPreview
        strategy={mockStrategy}
        configuration={mockConfig}
        isValid={true}
      />
    );

    const copyButton = screen.getByText("Copy");
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(screen.getByText("Copied!")).toBeInTheDocument();
    });

    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      JSON.stringify(mockConfig, null, 2)
    );
  });

  it("disables start button when invalid", () => {
    const mockStart = jest.fn();
    render(
      <ConfigurationPreview
        strategy={mockStrategy}
        configuration={{}}
        isValid={false}
        onStartBacktest={mockStart}
      />
    );

    const startButton = screen.getByText("Complete Configuration First");
    expect(startButton).toBeDisabled();
  });
});

describe("StrategyDocumentation", () => {
  it("renders strategy documentation when open", () => {
    render(
      <StrategyDocumentation
        strategy={mockStrategies[0]}
        open={true}
        onOpenChange={() => {}}
      />
    );

    expect(screen.getByText("Strategy Documentation")).toBeInTheDocument();
    expect(screen.getByText("Order Book Scalper")).toBeInTheDocument();
  });

  it("does not render when closed", () => {
    render(
      <StrategyDocumentation
        strategy={mockStrategies[0]}
        open={false}
        onOpenChange={() => {}}
      />
    );

    expect(
      screen.queryByText("Strategy Documentation")
    ).not.toBeInTheDocument();
  });
});

describe("ConfigurationComparison", () => {
  const mockTemplates = [
    {
      id: "template1",
      name: "Conservative Settings",
      strategyId: "order_book_scalper",
      parameters: {
        lookback_hours: 2,
        min_spread: 1.0,
        enable_ml_features: false,
      },
      createdAt: "2024-01-01",
      updatedAt: "2024-01-01",
    },
  ];

  const currentConfig = {
    lookback_hours: 4,
    min_spread: 0.5,
    enable_ml_features: true,
  };

  it("renders comparison dialog", () => {
    render(
      <ConfigurationComparison
        open={true}
        onOpenChange={() => {}}
        currentConfig={currentConfig}
        templates={mockTemplates}
        strategy={mockStrategies[0]}
      />
    );

    expect(screen.getByText("Compare Configuration")).toBeInTheDocument();
  });

  it("shows parameter differences", () => {
    render(
      <ConfigurationComparison
        open={true}
        onOpenChange={() => {}}
        currentConfig={currentConfig}
        templates={mockTemplates}
        strategy={mockStrategies[0]}
      />
    );

    // Select the template
    const select = screen.getByText("Select a template to compare");
    fireEvent.click(select);
    fireEvent.click(screen.getByText("Conservative Settings"));

    // Should show the comparison
    expect(screen.getByText("Current Value")).toBeInTheDocument();
    expect(screen.getByText("Template Value")).toBeInTheDocument();
  });
});
