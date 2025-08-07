import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { InfoCircledIcon } from "@radix-ui/react-icons";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { ParameterDefinition } from "@/hooks/useStrategies";
import { cn } from "@/lib/utils";

interface ParameterInputProps {
  parameter: ParameterDefinition;
  value: any;
  onChange: (value: any) => void;
  error?: string;
  disabled?: boolean;
}

export function ParameterInput({
  parameter,
  value,
  onChange,
  error,
  disabled = false,
}: ParameterInputProps) {
  const renderInput = () => {
    switch (parameter.type) {
      case "number":
        return (
          <Input
            type="number"
            value={value ?? parameter.default ?? ""}
            onChange={(e) =>
              onChange(e.target.value ? Number(e.target.value) : null)
            }
            min={parameter.validation?.min}
            max={parameter.validation?.max}
            step={parameter.validation?.step || 1}
            disabled={disabled}
            className={cn(error && "border-red-500")}
          />
        );

      case "boolean":
        return (
          <div className="flex items-center space-x-2">
            <Switch
              checked={value ?? parameter.default ?? false}
              onCheckedChange={onChange}
              disabled={disabled}
            />
            <Label className="text-sm text-muted-foreground">
              {value ? "Enabled" : "Disabled"}
            </Label>
          </div>
        );

      case "string":
        return (
          <Input
            type="text"
            value={value ?? parameter.default ?? ""}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className={cn(error && "border-red-500")}
          />
        );

      case "select":
        return (
          <Select
            value={value ?? parameter.default ?? ""}
            onValueChange={onChange}
            disabled={disabled}
          >
            <SelectTrigger className={cn(error && "border-red-500")}>
              <SelectValue placeholder="Select an option" />
            </SelectTrigger>
            <SelectContent>
              {parameter.options?.map((option) => (
                <SelectItem key={option} value={option}>
                  {option}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        );

      case "range":
        const min = parameter.validation?.min ?? 0;
        const max = parameter.validation?.max ?? 100;
        const step = parameter.validation?.step ?? 1;
        const currentValue = value ?? parameter.default ?? min;

        return (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{min}</span>
              <span className="text-sm font-medium">{currentValue}</span>
              <span className="text-sm text-muted-foreground">{max}</span>
            </div>
            <Slider
              value={[currentValue]}
              onValueChange={([v]) => onChange(v)}
              min={min}
              max={max}
              step={step}
              disabled={disabled}
              className="w-full"
            />
          </div>
        );

      case "date":
        return (
          <Input
            type="date"
            value={value ?? parameter.default ?? ""}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className={cn(error && "border-red-500")}
          />
        );

      default:
        return (
          <Input
            type="text"
            value={value ?? parameter.default ?? ""}
            onChange={(e) => onChange(e.target.value)}
            disabled={disabled}
            className={cn(error && "border-red-500")}
          />
        );
    }
  };

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <Label htmlFor={parameter.name} className="flex items-center space-x-2">
          <span>{parameter.name}</span>
          {parameter.required && <span className="text-red-500">*</span>}
        </Label>
        {parameter.description && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger>
                <InfoCircledIcon className="h-4 w-4 text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent className="max-w-xs">
                <p>{parameter.description}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>

      {renderInput()}

      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  );
}
