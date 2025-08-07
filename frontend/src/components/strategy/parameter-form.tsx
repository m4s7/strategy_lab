'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { ParameterInput } from "./parameter-input";
import { Strategy, ValidationError } from "@/hooks/useStrategies";
import { Save, RotateCcw, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface ParameterFormProps {
  strategy: Strategy;
  values: Record<string, any>;
  onChange: (values: Record<string, any>) => void;
  errors: ValidationError[];
  onValidate: () => Promise<boolean>;
  onSave?: () => void;
  onReset?: () => void;
}

export function ParameterForm({
  strategy,
  values,
  onChange,
  errors,
  onValidate,
  onSave,
  onReset
}: ParameterFormProps) {
  const [localErrors, setLocalErrors] = useState<Record<string, string>>({});
  const [isDirty, setIsDirty] = useState(false);

  useEffect(() => {
    // Convert validation errors to local error format
    const errorMap: Record<string, string> = {};
    errors.forEach(error => {
      errorMap[error.parameter] = error.error;
    });
    setLocalErrors(errorMap);
  }, [errors]);

  const updateParameter = (name: string, value: any) => {
    const newValues = { ...values, [name]: value };
    onChange(newValues);
    setIsDirty(true);
    
    // Clear error for this field when user makes changes
    if (localErrors[name]) {
      const newErrors = { ...localErrors };
      delete newErrors[name];
      setLocalErrors(newErrors);
    }
  };

  const handleReset = () => {
    const defaultValues = strategy.default_params || {};
    onChange(defaultValues);
    setIsDirty(false);
    setLocalErrors({});
    if (onReset) onReset();
  };

  const handleValidate = async () => {
    const isValid = await onValidate();
    if (isValid) {
      setLocalErrors({});
    }
  };

  // Group parameters by category if they have dependencies
  const groupedParameters = strategy.parameters.reduce((acc, param) => {
    const group = param.dependencies && param.dependencies.length > 0 ? 'Advanced' : 'Basic';
    if (!acc[group]) acc[group] = [];
    acc[group].push(param);
    return acc;
  }, {} as Record<string, typeof strategy.parameters>);

  const hasMultipleGroups = Object.keys(groupedParameters).length > 1;

  const renderParameters = (parameters: typeof strategy.parameters) => (
    <div className="space-y-4">
      {parameters.map(param => (
        <ParameterInput
          key={param.name}
          parameter={param}
          value={values[param.name]}
          onChange={(value) => updateParameter(param.name, value)}
          error={localErrors[param.name]}
        />
      ))}
    </div>
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Configure Parameters</CardTitle>
            <CardDescription>
              Set the parameters for {strategy.name}
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            {isDirty && (
              <Badge variant="outline" className="text-yellow-600">
                Unsaved Changes
              </Badge>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleReset}
              disabled={!isDirty}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset
            </Button>
            {onSave && (
              <Button
                size="sm"
                onClick={onSave}
                disabled={Object.keys(localErrors).length > 0}
              >
                <Save className="h-4 w-4 mr-2" />
                Save
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Validation Summary */}
        {Object.keys(localErrors).length > 0 && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Please fix the following errors:
              <ul className="list-disc list-inside mt-2">
                {Object.entries(localErrors).map(([param, error]) => (
                  <li key={param} className="text-sm">
                    <strong>{param}:</strong> {error}
                  </li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        {/* Parameter Inputs */}
        {hasMultipleGroups ? (
          <Tabs defaultValue="Basic" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              {Object.keys(groupedParameters).map(group => (
                <TabsTrigger key={group} value={group}>
                  {group} Parameters
                </TabsTrigger>
              ))}
            </TabsList>
            {Object.entries(groupedParameters).map(([group, params]) => (
              <TabsContent key={group} value={group} className="mt-4">
                {renderParameters(params)}
              </TabsContent>
            ))}
          </Tabs>
        ) : (
          renderParameters(strategy.parameters)
        )}

        {/* Validation Button */}
        <div className="pt-4 border-t">
          <Button
            variant="outline"
            className="w-full"
            onClick={handleValidate}
          >
            Validate Configuration
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}