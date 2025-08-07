"use client";

import { useState, useEffect } from "react";
import {
  useStrategies,
  useStrategy,
  useStrategyValidation,
  useConfigurationTemplates,
} from "@/hooks/useStrategies";
import { StrategySelector } from "@/components/strategy/strategy-selector";
import { ParameterForm } from "@/components/strategy/parameter-form";
import { TemplateManager } from "@/components/strategy/template-manager";
import { ConfigurationPreview } from "@/components/strategy/configuration-preview";
import { useRouter } from "next/navigation";
import { toast } from "sonner";

export default function StrategyConfigurationPage() {
  const router = useRouter();
  const { strategies, loading: strategiesLoading } = useStrategies();
  const [selectedStrategyId, setSelectedStrategyId] = useState<string | null>(
    null
  );
  const { strategy } = useStrategy(selectedStrategyId || "");
  const { validateParameters, errors } = useStrategyValidation(
    selectedStrategyId || ""
  );
  const { templates, saveTemplate, loadTemplate, deleteTemplate } =
    useConfigurationTemplates(selectedStrategyId || "");

  const [configuration, setConfiguration] = useState<Record<string, any>>({});
  const [isValid, setIsValid] = useState(false);
  const [recentStrategies, setRecentStrategies] = useState<string[]>([]);

  useEffect(() => {
    // Load recent strategies from localStorage
    const stored = localStorage.getItem("recentStrategies");
    if (stored) {
      setRecentStrategies(JSON.parse(stored));
    }
  }, []);

  useEffect(() => {
    // Initialize configuration with default values when strategy changes
    if (strategy) {
      setConfiguration(strategy.default_params || {});
    }
  }, [strategy]);

  const handleSelectStrategy = (strategy: any) => {
    setSelectedStrategyId(strategy.id);

    // Update recent strategies
    const newRecent = [
      strategy.id,
      ...recentStrategies.filter((id) => id !== strategy.id),
    ].slice(0, 5);
    setRecentStrategies(newRecent);
    localStorage.setItem("recentStrategies", JSON.stringify(newRecent));
  };

  const handleValidate = async () => {
    if (!selectedStrategyId) return false;

    const valid = await validateParameters(configuration);
    setIsValid(valid);

    if (valid) {
      toast.success("Configuration is valid!");
    } else {
      toast.error("Please fix validation errors");
    }

    return valid;
  };

  const handleSaveTemplate = async (name: string, description?: string) => {
    try {
      await saveTemplate(name, configuration, description);
      toast.success("Template saved successfully");
    } catch (error) {
      toast.error("Failed to save template");
    }
  };

  const handleLoadTemplate = async (templateId: string) => {
    try {
      const template = await loadTemplate(templateId);
      setConfiguration(template.parameters);
      toast.success("Template loaded successfully");
    } catch (error) {
      toast.error("Failed to load template");
    }
  };

  const handleDeleteTemplate = async (templateId: string) => {
    try {
      await deleteTemplate(templateId);
      toast.success("Template deleted successfully");
    } catch (error) {
      toast.error("Failed to delete template");
    }
  };

  const handleStartBacktest = () => {
    if (!strategy || !isValid) return;

    // Store configuration in sessionStorage for the next page
    sessionStorage.setItem(
      "backtestConfig",
      JSON.stringify({
        strategy_id: strategy.id,
        strategy_name: strategy.name,
        parameters: configuration,
      })
    );

    // Navigate to backtest execution page
    router.push("/backtests/new");
  };

  const handleExportConfig = () => {
    const dataStr = JSON.stringify(configuration, null, 2);
    const dataUri =
      "data:application/json;charset=utf-8," + encodeURIComponent(dataStr);
    const exportFileDefaultName = `strategy-config-${Date.now()}.json`;

    const linkElement = document.createElement("a");
    linkElement.setAttribute("href", dataUri);
    linkElement.setAttribute("download", exportFileDefaultName);
    linkElement.click();
  };

  const handleImportConfig = (config: Record<string, any>) => {
    setConfiguration(config);
    toast.success("Configuration imported successfully");
  };

  if (strategiesLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading strategies...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Strategy Configuration</h1>
        <p className="text-muted-foreground mt-2">
          Select and configure trading strategies for backtesting
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left Column - Strategy Selection */}
        <div className="lg:col-span-1">
          <StrategySelector
            strategies={strategies}
            selectedStrategy={strategy}
            onSelectStrategy={handleSelectStrategy}
            recentStrategies={recentStrategies}
          />
        </div>

        {/* Middle Column - Parameter Configuration */}
        <div className="lg:col-span-1">
          {strategy ? (
            <div className="space-y-6">
              <ParameterForm
                strategy={strategy}
                values={configuration}
                onChange={setConfiguration}
                errors={errors}
                onValidate={handleValidate}
                onSave={() => toast.success("Configuration saved")}
                onReset={() => toast.info("Configuration reset to defaults")}
              />
              <TemplateManager
                templates={templates}
                currentConfig={configuration}
                onSaveTemplate={handleSaveTemplate}
                onLoadTemplate={handleLoadTemplate}
                onDeleteTemplate={handleDeleteTemplate}
                onExportConfig={handleExportConfig}
                onImportConfig={handleImportConfig}
              />
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <p>Select a strategy to configure parameters</p>
            </div>
          )}
        </div>

        {/* Right Column - Configuration Preview */}
        <div className="lg:col-span-1">
          {strategy ? (
            <ConfigurationPreview
              strategy={strategy}
              configuration={configuration}
              isValid={isValid}
              onStartBacktest={handleStartBacktest}
            />
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <p>Configuration preview will appear here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
