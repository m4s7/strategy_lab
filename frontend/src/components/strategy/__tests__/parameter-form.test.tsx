import {
  renderWithProviders,
  screen,
  waitFor,
  userEvent,
} from "@/tests/utils/test-helpers";
import { ParameterForm } from "../parameter-form";
import { act } from "@testing-library/react";

const mockStrategy = {
  id: "test-strategy",
  name: "Test Strategy",
  type: "scalping",
  parameters: {
    stopLoss: {
      type: "number",
      min: 5,
      max: 50,
      default: 10,
      description: "Stop loss in ticks",
    },
    takeProfit: {
      type: "number",
      min: 10,
      max: 100,
      default: 20,
      description: "Take profit in ticks",
    },
    positionSize: {
      type: "number",
      min: 1,
      max: 10,
      default: 1,
      description: "Position size",
    },
    useTrailingStop: {
      type: "boolean",
      default: false,
      description: "Enable trailing stop",
    },
  },
};

describe("ParameterForm", () => {
  const mockOnSubmit = jest.fn();
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("should render all parameter inputs", () => {
    renderWithProviders(
      <ParameterForm
        strategy={mockStrategy}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByLabelText("Stop Loss")).toBeInTheDocument();
    expect(screen.getByLabelText("Take Profit")).toBeInTheDocument();
    expect(screen.getByLabelText("Position Size")).toBeInTheDocument();
    expect(screen.getByLabelText("Use Trailing Stop")).toBeInTheDocument();
  });

  it("should display default values", () => {
    renderWithProviders(
      <ParameterForm
        strategy={mockStrategy}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByLabelText("Stop Loss")).toHaveValue(10);
    expect(screen.getByLabelText("Take Profit")).toHaveValue(20);
    expect(screen.getByLabelText("Position Size")).toHaveValue(1);
    expect(screen.getByLabelText("Use Trailing Stop")).not.toBeChecked();
  });

  it("should handle input changes", async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <ParameterForm
        strategy={mockStrategy}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    const stopLossInput = screen.getByLabelText("Stop Loss");

    await user.clear(stopLossInput);
    await user.type(stopLossInput, "15");

    expect(stopLossInput).toHaveValue(15);
  });

  it("should validate numeric inputs", async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <ParameterForm
        strategy={mockStrategy}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    const stopLossInput = screen.getByLabelText("Stop Loss");

    // Test minimum value
    await user.clear(stopLossInput);
    await user.type(stopLossInput, "3");
    await user.tab();

    expect(screen.getByText(/must be at least 5/i)).toBeInTheDocument();

    // Test maximum value
    await user.clear(stopLossInput);
    await user.type(stopLossInput, "55");
    await user.tab();

    expect(screen.getByText(/must be at most 50/i)).toBeInTheDocument();
  });

  it("should submit form with valid data", async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <ParameterForm
        strategy={mockStrategy}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    // Change some values
    await user.clear(screen.getByLabelText("Stop Loss"));
    await user.type(screen.getByLabelText("Stop Loss"), "15");

    await user.click(screen.getByLabelText("Use Trailing Stop"));

    // Submit form
    await user.click(
      screen.getByRole("button", { name: "Save Configuration" })
    );

    await waitFor(() => {
      expect(mockOnSubmit).toHaveBeenCalledWith({
        stopLoss: 15,
        takeProfit: 20,
        positionSize: 1,
        useTrailingStop: true,
      });
    });
  });

  it("should not submit form with invalid data", async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <ParameterForm
        strategy={mockStrategy}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    // Set invalid value
    await user.clear(screen.getByLabelText("Stop Loss"));
    await user.type(screen.getByLabelText("Stop Loss"), "100");

    // Try to submit
    await user.click(
      screen.getByRole("button", { name: "Save Configuration" })
    );

    expect(mockOnSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/must be at most 50/i)).toBeInTheDocument();
  });

  it("should handle cancel action", async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <ParameterForm
        strategy={mockStrategy}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    await user.click(screen.getByRole("button", { name: "Cancel" }));

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it("should load initial values when provided", () => {
    const initialValues = {
      stopLoss: 25,
      takeProfit: 50,
      positionSize: 2,
      useTrailingStop: true,
    };

    renderWithProviders(
      <ParameterForm
        strategy={mockStrategy}
        initialValues={initialValues}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByLabelText("Stop Loss")).toHaveValue(25);
    expect(screen.getByLabelText("Take Profit")).toHaveValue(50);
    expect(screen.getByLabelText("Position Size")).toHaveValue(2);
    expect(screen.getByLabelText("Use Trailing Stop")).toBeChecked();
  });

  it("should show tooltips for parameter descriptions", async () => {
    const user = userEvent.setup();

    renderWithProviders(
      <ParameterForm
        strategy={mockStrategy}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    const helpIcon = screen.getByTestId("help-icon-stopLoss");

    await user.hover(helpIcon);

    await waitFor(() => {
      expect(screen.getByText("Stop loss in ticks")).toBeInTheDocument();
    });
  });

  it("should be accessible", async () => {
    renderWithProviders(
      <ParameterForm
        strategy={mockStrategy}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    // Check form has proper role
    expect(screen.getByRole("form")).toBeInTheDocument();

    // Check all inputs have labels
    const inputs = screen.getAllByRole("spinbutton");
    inputs.forEach((input) => {
      expect(input).toHaveAccessibleName();
    });

    // Check checkbox has label
    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toHaveAccessibleName("Use Trailing Stop");

    // Check buttons are accessible
    expect(
      screen.getByRole("button", { name: "Save Configuration" })
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Cancel" })).toBeInTheDocument();
  });

  it("should disable form while submitting", async () => {
    const user = userEvent.setup();

    // Mock async submit
    mockOnSubmit.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 100))
    );

    renderWithProviders(
      <ParameterForm
        strategy={mockStrategy}
        onSubmit={mockOnSubmit}
        onCancel={mockOnCancel}
      />
    );

    await user.click(
      screen.getByRole("button", { name: "Save Configuration" })
    );

    // Check form is disabled
    expect(screen.getByLabelText("Stop Loss")).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Save Configuration" })
    ).toBeDisabled();
    expect(screen.getByText("Saving...")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByLabelText("Stop Loss")).not.toBeDisabled();
    });
  });
});
