"use client";

import { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Eye,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Filter,
  Download,
  Search,
} from "lucide-react";
import { Trade, TradeFilters, SortConfig } from "@/lib/trades/types";
import { filterTrades, sortTrades } from "@/lib/trades/calculations";
import { TradeExporter } from "@/lib/trades/export";

interface TradeTableProps {
  trades: Trade[];
  onTradeSelect: (trade: Trade) => void;
  className?: string;
}

export function TradeTable({
  trades,
  onTradeSelect,
  className,
}: TradeTableProps) {
  const [filters, setFilters] = useState<TradeFilters>({
    dateRange: { start: null, end: null },
    profitability: "all",
    minDuration: null,
    maxDuration: null,
    tags: [],
    side: "all",
  });

  const [sortConfig, setSortConfig] = useState<SortConfig>({
    key: "entryTime",
    direction: "desc",
  });

  const [searchTerm, setSearchTerm] = useState("");
  const [showFilters, setShowFilters] = useState(false);

  // Filter and sort trades
  const processedTrades = useMemo(() => {
    let filtered = filterTrades(trades, filters);

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(
        (trade) =>
          trade.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
          trade.entryReason.toLowerCase().includes(searchTerm.toLowerCase()) ||
          trade.exitReason.toLowerCase().includes(searchTerm.toLowerCase()) ||
          trade.signalType.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return sortTrades(filtered, sortConfig);
  }, [trades, filters, searchTerm, sortConfig]);

  const handleSort = (key: keyof Trade) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === "asc" ? "desc" : "asc",
    }));
  };

  const handleExport = async () => {
    await TradeExporter.exportToCSV(
      processedTrades,
      `trades-${new Date().toISOString().split("T")[0]}.csv`
    );
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPrice = (value: number) => {
    return value.toFixed(2);
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const formatDuration = (duration: number) => {
    const minutes = Math.floor(duration / 60000);
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m`;
  };

  const getSortIcon = (columnKey: keyof Trade) => {
    if (sortConfig.key !== columnKey) {
      return <ArrowUpDown className="h-4 w-4 opacity-50" />;
    }
    return sortConfig.direction === "asc" ? (
      <ArrowUp className="h-4 w-4" />
    ) : (
      <ArrowDown className="h-4 w-4" />
    );
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <span>Trade History</span>
            <Badge variant="outline">
              {processedTrades.length} of {trades.length}
            </Badge>
          </CardTitle>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
            >
              <Filter className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              disabled={processedTrades.length === 0}
            >
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search trades by ID, reason, or signal type..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 p-4 bg-muted/20 rounded-lg">
              <Select
                value={filters.profitability}
                onValueChange={(value: "all" | "winners" | "losers") =>
                  setFilters((prev) => ({ ...prev, profitability: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Trades</SelectItem>
                  <SelectItem value="winners">Winners Only</SelectItem>
                  <SelectItem value="losers">Losers Only</SelectItem>
                </SelectContent>
              </Select>

              <Select
                value={filters.side || "all"}
                onValueChange={(value: "all" | "long" | "short") =>
                  setFilters((prev) => ({ ...prev, side: value }))
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Sides</SelectItem>
                  <SelectItem value="long">Long Only</SelectItem>
                  <SelectItem value="short">Short Only</SelectItem>
                </SelectContent>
              </Select>

              <Input
                type="number"
                placeholder="Min P&L"
                value={filters.minPnl || ""}
                onChange={(e) =>
                  setFilters((prev) => ({
                    ...prev,
                    minPnl: e.target.value
                      ? parseFloat(e.target.value)
                      : undefined,
                  }))
                }
              />

              <Input
                type="number"
                placeholder="Max P&L"
                value={filters.maxPnl || ""}
                onChange={(e) =>
                  setFilters((prev) => ({
                    ...prev,
                    maxPnl: e.target.value
                      ? parseFloat(e.target.value)
                      : undefined,
                  }))
                }
              />
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-20">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSort("id")}
                  >
                    ID {getSortIcon("id")}
                  </Button>
                </TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSort("entryTime")}
                  >
                    Entry Time {getSortIcon("entryTime")}
                  </Button>
                </TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSort("exitTime")}
                  >
                    Exit Time {getSortIcon("exitTime")}
                  </Button>
                </TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSort("side")}
                  >
                    Side {getSortIcon("side")}
                  </Button>
                </TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSort("entryPrice")}
                  >
                    Entry {getSortIcon("entryPrice")}
                  </Button>
                </TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSort("exitPrice")}
                  >
                    Exit {getSortIcon("exitPrice")}
                  </Button>
                </TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSort("quantity")}
                  >
                    Size {getSortIcon("quantity")}
                  </Button>
                </TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSort("pnl")}
                  >
                    P&L {getSortIcon("pnl")}
                  </Button>
                </TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSort("returnPct")}
                  >
                    Return % {getSortIcon("returnPct")}
                  </Button>
                </TableHead>
                <TableHead>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleSort("duration")}
                  >
                    Duration {getSortIcon("duration")}
                  </Button>
                </TableHead>
                <TableHead className="w-20">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {processedTrades.map((trade) => (
                <TableRow key={trade.id} className="hover:bg-muted/50">
                  <TableCell>
                    <Badge variant="outline" className="font-mono text-xs">
                      {trade.id.slice(-6)}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {formatDateTime(trade.entryTime)}
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {formatDateTime(trade.exitTime)}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={trade.side === "long" ? "default" : "secondary"}
                      className="text-xs"
                    >
                      {trade.side.toUpperCase()}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono">
                    {formatPrice(trade.entryPrice)}
                  </TableCell>
                  <TableCell className="font-mono">
                    {formatPrice(trade.exitPrice)}
                  </TableCell>
                  <TableCell>{trade.quantity}</TableCell>
                  <TableCell>
                    <span
                      className={
                        trade.pnl >= 0 ? "text-green-600" : "text-red-600"
                      }
                    >
                      {formatCurrency(trade.pnl)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span
                      className={
                        trade.returnPct >= 0 ? "text-green-600" : "text-red-600"
                      }
                    >
                      {(trade.returnPct * 100).toFixed(2)}%
                    </span>
                  </TableCell>
                  <TableCell className="font-mono text-sm">
                    {formatDuration(trade.duration)}
                  </TableCell>
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onTradeSelect(trade)}
                    >
                      <Eye className="h-4 w-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {processedTrades.length === 0 && (
                <TableRow>
                  <TableCell
                    colSpan={11}
                    className="text-center py-8 text-muted-foreground"
                  >
                    No trades match the current filters
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>

        {processedTrades.length > 0 && (
          <div className="flex items-center justify-between mt-4 pt-4 border-t">
            <div className="text-sm text-muted-foreground">
              Showing {processedTrades.length} of {trades.length} trades
            </div>
            <div className="text-sm">
              Total P&L:{" "}
              <span
                className={
                  processedTrades.reduce((sum, t) => sum + t.pnl, 0) >= 0
                    ? "text-green-600"
                    : "text-red-600"
                }
              >
                {formatCurrency(
                  processedTrades.reduce((sum, t) => sum + t.pnl, 0)
                )}
              </span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
