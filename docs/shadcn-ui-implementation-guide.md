# shadcn/ui Implementation Guide for Strategy Lab

## Overview

This guide documents how to use shadcn/ui components with the MCP server integration for the Strategy Lab Web UI project. The shadcn/ui MCP server provides component discovery, documentation, and installation capabilities.

## MCP Server Integration

### Available Commands

The shadcn/ui MCP server provides these tools:
- `list-components`: Get list of all available components
- `get-component-docs`: Get detailed documentation for a component
- `install-component`: Install a component into the project
- `list-blocks`: Get list of available blocks
- `get-block-docs`: Get documentation for blocks
- `install-blocks`: Install blocks into the project

### Basic Usage

```bash
# List all available components
npx mcp__shadcn-ui-server__list-components

# Get documentation for a specific component
npx mcp__shadcn-ui-server__get-component-docs --component="button"

# Install a component
npx mcp__shadcn-ui-server__install-component --component="button" --runtime="pnpm"
```

## Core Components for Strategy Lab

### Essential Components by Epic

#### Epic 1: Foundation Infrastructure
**Required Components:**
- `sidebar` - Main navigation component
- `button` - Interactive elements
- `card` - Content containers
- `input` - Form inputs
- `dialog` - Modals and overlays
- `toast` - Notifications
- `skeleton` - Loading states

#### Epic 2: Core Backtesting Features
**Required Components:**
- `form` - Configuration forms
- `select` - Dropdowns
- `progress` - Progress indicators
- `tabs` - Interface organization
- `badge` - Status indicators
- `alert` - Error/warning messages

#### Epic 3: Advanced Analysis & Visualization
**Required Components:**
- `chart` - Data visualization
- `data-table` - Tabular data
- `pagination` - Large dataset navigation
- `scroll-area` - Scrollable content
- `resizable` - Adjustable layouts
- `hover-card` - Detail overlays

#### Epic 4: Strategy Optimization Module
**Required Components:**
- `slider` - Parameter inputs
- `combobox` - Advanced selection
- `popover` - Context menus
- `dropdown-menu` - Action menus
- `toggle` - Settings switches
- `separator` - Layout division

#### Epic 5: Polish, Performance & Production
**Required Components:**
- `tooltip` - Help and guidance
- `breadcrumb` - Navigation aids
- `context-menu` - Right-click actions
- `menubar` - Top-level navigation
- `navigation-menu` - Complex navigation

## Component Implementation Patterns

### 1. Dashboard Layout with Sidebar

```typescript
// Using shadcn/ui Sidebar for main layout
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar"

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <main className="flex-1">
        <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
          <SidebarTrigger className="-ml-1" />
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold">Strategy Lab</h1>
          </div>
        </header>
        <div className="p-4">
          {children}
        </div>
      </main>
    </SidebarProvider>
  )
}
```

### 2. Interactive Charts with shadcn/ui

```typescript
import { ChartContainer, ChartTooltip, ChartTooltipContent } from "@/components/ui/chart"
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from "recharts"

const chartConfig = {
  equity: {
    label: "Portfolio Equity",
    color: "hsl(var(--chart-1))",
  },
  benchmark: {
    label: "Benchmark",
    color: "hsl(var(--chart-2))",
  },
} satisfies ChartConfig

export function EquityCurveChart({ data }: { data: EquityDataPoint[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Equity Curve</CardTitle>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="min-h-[400px] w-full">
          <LineChart data={data} accessibilityLayer>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Line
              type="monotone"
              dataKey="equity"
              stroke="var(--color-equity)"
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="benchmark"
              stroke="var(--color-benchmark)"
              strokeWidth={2}
            />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  )
}
```

### 3. Data Tables for Trade Analysis

```typescript
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

interface Trade {
  id: string
  timestamp: Date
  side: 'long' | 'short'
  pnl: number
  status: 'open' | 'closed'
}

export function TradesTable({ trades }: { trades: Trade[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Trades</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-hidden rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Time</TableHead>
                <TableHead>Side</TableHead>
                <TableHead className="text-right">P&L</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {trades.map((trade) => (
                <TableRow key={trade.id}>
                  <TableCell>{trade.timestamp.toLocaleTimeString()}</TableCell>
                  <TableCell>
                    <Badge variant={trade.side === 'long' ? 'default' : 'secondary'}>
                      {trade.side}
                    </Badge>
                  </TableCell>
                  <TableCell className={`text-right ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ${trade.pnl.toFixed(2)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={trade.status === 'open' ? 'outline' : 'default'}>
                      {trade.status}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
```

### 4. Configuration Forms

```typescript
import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

export function StrategyConfigForm() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Strategy Configuration</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="strategy"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Strategy Type</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select strategy" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="scalping">Order Book Scalper</SelectItem>
                      <SelectItem value="momentum">Momentum Strategy</SelectItem>
                      <SelectItem value="mean-revert">Mean Reversion</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="capital"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Initial Capital</FormLabel>
                  <FormControl>
                    <Input type="number" placeholder="100000" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" className="w-full">
              Start Backtest
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}
```

## Theme Configuration

### Custom Color Scheme for Trading

```css
@layer base {
  :root {
    /* Trading-specific colors */
    --profit: 22 163 74;    /* Green for profits */
    --loss: 239 68 68;      /* Red for losses */
    --neutral: 156 163 175; /* Gray for neutral */

    /* Chart colors */
    --chart-1: 12 76% 61%;   /* Primary data series */
    --chart-2: 173 58% 39%;  /* Secondary data series */
    --chart-3: 197 37% 24%;  /* Tertiary data series */
    --chart-4: 43 74% 66%;   /* Quaternary data series */
    --chart-5: 27 87% 67%;   /* Quinary data series */

    /* Sidebar colors */
    --sidebar-background: 240 5.9% 10%;
    --sidebar-foreground: 240 4.8% 95.9%;
    --sidebar-primary: 224.3 76.3% 48%;
    --sidebar-primary-foreground: 0 0% 100%;
    --sidebar-accent: 240 3.7% 15.9%;
    --sidebar-accent-foreground: 240 4.8% 95.9%;
    --sidebar-border: 240 3.7% 15.9%;
    --sidebar-ring: 217.2 91.2% 59.8%;
  }
}
```

## Installation Sequence

### Phase 1: Foundation Components
```bash
# Essential layout and navigation
npx shadcn@latest add sidebar
npx shadcn@latest add button
npx shadcn@latest add card
npx shadcn@latest add input
npx shadcn@latest add dialog
npx shadcn@latest add skeleton
```

### Phase 2: Forms and Data Entry
```bash
# Form components
npx shadcn@latest add form
npx shadcn@latest add select
npx shadcn@latest add label
npx shadcn@latest add checkbox
npx shadcn@latest add radio-group
npx shadcn@latest add textarea
```

### Phase 3: Data Visualization
```bash
# Chart and table components
npx shadcn@latest add chart
npx shadcn@latest add table
npx shadcn@latest add data-table
npx shadcn@latest add scroll-area
npx shadcn@latest add pagination
```

### Phase 4: Advanced UI Elements
```bash
# Complex interactions
npx shadcn@latest add dropdown-menu
npx shadcn@latest add popover
npx shadcn@latest add tooltip
npx shadcn@latest add tabs
npx shadcn@latest add slider
npx shadcn@latest add progress
```

### Phase 5: Polish and Feedback
```bash
# User feedback and notifications
npx shadcn@latest add toast
npx shadcn@latest add alert
npx shadcn@latest add badge
npx shadcn@latest add separator
npx shadcn@latest add breadcrumb
```

## Best Practices

### 1. Component Composition
- Use shadcn/ui components as building blocks
- Extend with custom functionality while maintaining design consistency
- Leverage the `cn()` utility for conditional styling

### 2. Theme Integration
- Always use CSS variables for colors
- Follow the established design tokens
- Ensure dark mode compatibility

### 3. Performance Considerations
- Import only needed components to minimize bundle size
- Use React.memo for expensive chart components
- Implement virtual scrolling for large datasets

### 4. Accessibility
- shadcn/ui components include built-in accessibility features
- Always provide proper labels and descriptions
- Test with keyboard navigation and screen readers

## MCP Server Integration in Development

### Using the MCP Server in Stories

When implementing user stories, developers can:

1. **Discover Components**: Use the MCP server to find suitable components
2. **Get Documentation**: Access component docs directly in development
3. **Install Components**: Add components as needed without leaving the IDE
4. **Browse Blocks**: Find pre-built component combinations

### Example Workflow

```bash
# Discover what chart components are available
mcp__shadcn-ui-server__list-components | grep chart

# Get detailed documentation
mcp__shadcn-ui-server__get-component-docs --component="chart"

# Install the chart component
mcp__shadcn-ui-server__install-component --component="chart"
```

## Common Patterns

### 1. Loading States
```typescript
import { Skeleton } from "@/components/ui/skeleton"

export function DashboardSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-4 w-[250px]" />
      <Skeleton className="h-4 w-[200px]" />
      <Skeleton className="h-4 w-[300px]" />
    </div>
  )
}
```

### 2. Error Handling
```typescript
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertTriangle } from "lucide-react"

export function ErrorAlert({ message }: { message: string }) {
  return (
    <Alert variant="destructive">
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  )
}
```

### 3. Success Notifications
```typescript
import { toast } from "@/components/ui/use-toast"

// In your component
const handleSuccess = () => {
  toast({
    title: "Backtest Complete",
    description: "Your strategy backtest has finished successfully.",
  })
}
```

This implementation guide provides a comprehensive foundation for using shadcn/ui components throughout the Strategy Lab Web UI project, ensuring consistency, accessibility, and maintainability.
