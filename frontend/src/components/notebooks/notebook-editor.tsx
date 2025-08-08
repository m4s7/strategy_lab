"use client";

import React, { useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import {
  Plus,
  Play,
  Save,
  Download,
  Code,
  Type,
  BarChart3,
  Trash2,
  ChevronUp,
  ChevronDown,
  Copy,
} from "lucide-react";

type CellType = "code" | "markdown" | "chart";

interface NotebookCell {
  id: string;
  type: CellType;
  content: string;
  output?: any;
  isExecuting?: boolean;
  executionCount?: number;
  metadata?: Record<string, any>;
}

interface Notebook {
  id: string;
  title: string;
  cells: NotebookCell[];
  createdAt: string;
  modifiedAt: string;
  metadata: {
    author?: string;
    tags?: string[];
    description?: string;
  };
}

interface NotebookEditorProps {
  notebook?: Notebook;
  onSave?: (notebook: Notebook) => void;
  onExecute?: (cellId: string, code: string) => Promise<any>;
}

export function NotebookEditor({
  notebook: initialNotebook,
  onSave,
  onExecute,
}: NotebookEditorProps) {
  const [notebook, setNotebook] = useState<Notebook>(
    initialNotebook || {
      id: `nb_${Date.now()}`,
      title: "Untitled Analysis",
      cells: [],
      createdAt: new Date().toISOString(),
      modifiedAt: new Date().toISOString(),
      metadata: {},
    }
  );
  const [selectedCellId, setSelectedCellId] = useState<string | null>(null);

  const addCell = (type: CellType, afterCellId?: string) => {
    const newCell: NotebookCell = {
      id: `cell_${Date.now()}`,
      type,
      content:
        type === "markdown" ? "# New Cell\n\nEnter your markdown here..." : "",
    };

    setNotebook((prev) => {
      const cells = [...prev.cells];
      if (afterCellId) {
        const index = cells.findIndex((c) => c.id === afterCellId);
        cells.splice(index + 1, 0, newCell);
      } else {
        cells.push(newCell);
      }
      return {
        ...prev,
        cells,
        modifiedAt: new Date().toISOString(),
      };
    });
    setSelectedCellId(newCell.id);
  };

  const updateCell = (cellId: string, updates: Partial<NotebookCell>) => {
    setNotebook((prev) => ({
      ...prev,
      cells: prev.cells.map((cell) =>
        cell.id === cellId ? { ...cell, ...updates } : cell
      ),
      modifiedAt: new Date().toISOString(),
    }));
  };

  const deleteCell = (cellId: string) => {
    setNotebook((prev) => ({
      ...prev,
      cells: prev.cells.filter((cell) => cell.id !== cellId),
      modifiedAt: new Date().toISOString(),
    }));
  };

  const moveCell = (cellId: string, direction: "up" | "down") => {
    setNotebook((prev) => {
      const cells = [...prev.cells];
      const index = cells.findIndex((c) => c.id === cellId);
      if (
        (direction === "up" && index > 0) ||
        (direction === "down" && index < cells.length - 1)
      ) {
        const newIndex = direction === "up" ? index - 1 : index + 1;
        [cells[index], cells[newIndex]] = [cells[newIndex], cells[index]];
      }
      return {
        ...prev,
        cells,
        modifiedAt: new Date().toISOString(),
      };
    });
  };

  const executeCell = async (cellId: string) => {
    const cell = notebook.cells.find((c) => c.id === cellId);
    if (!cell || cell.type !== "code") return;

    updateCell(cellId, { isExecuting: true });

    try {
      let output;
      if (onExecute) {
        output = await onExecute(cellId, cell.content);
      } else {
        // Mock execution for demo
        output = `Executed: ${cell.content.split("\n")[0]}...`;
      }

      updateCell(cellId, {
        output,
        isExecuting: false,
        executionCount: (cell.executionCount || 0) + 1,
      });
    } catch (error) {
      updateCell(cellId, {
        output: { error: error.message },
        isExecuting: false,
      });
    }
  };

  const saveNotebook = () => {
    if (onSave) {
      onSave(notebook);
    }
  };

  const exportNotebook = () => {
    const blob = new Blob([JSON.stringify(notebook, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${notebook.title}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Input
                value={notebook.title}
                onChange={(e) =>
                  setNotebook((prev) => ({ ...prev, title: e.target.value }))
                }
                className="text-xl font-bold border-none p-0 h-auto"
                placeholder="Notebook Title"
              />
              <Badge variant="outline">{notebook.cells.length} cells</Badge>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={saveNotebook}>
                <Save className="h-4 w-4 mr-2" />
                Save
              </Button>
              <Button variant="outline" size="sm" onClick={exportNotebook}>
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="space-y-4">
        {notebook.cells.map((cell, index) => (
          <Card
            key={cell.id}
            className={`transition-all ${
              selectedCellId === cell.id ? "ring-2 ring-primary" : ""
            }`}
            onClick={() => setSelectedCellId(cell.id)}
          >
            <CardContent className="p-4">
              <div className="flex items-start gap-2">
                <div className="flex flex-col gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => moveCell(cell.id, "up")}
                    disabled={index === 0}
                  >
                    <ChevronUp className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => moveCell(cell.id, "down")}
                    disabled={index === notebook.cells.length - 1}
                  >
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                </div>

                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {cell.type === "code" && <Code className="h-4 w-4" />}
                      {cell.type === "markdown" && <Type className="h-4 w-4" />}
                      {cell.type === "chart" && (
                        <BarChart3 className="h-4 w-4" />
                      )}
                      <Badge variant="outline">{cell.type}</Badge>
                      {cell.executionCount && (
                        <span className="text-xs text-muted-foreground">
                          [{cell.executionCount}]
                        </span>
                      )}
                    </div>
                    <div className="flex gap-1">
                      {cell.type === "code" && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => executeCell(cell.id)}
                          disabled={cell.isExecuting}
                        >
                          <Play
                            className={`h-4 w-4 ${
                              cell.isExecuting ? "animate-pulse" : ""
                            }`}
                          />
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteCell(cell.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {cell.type === "code" ? (
                    <Textarea
                      value={cell.content}
                      onChange={(e) =>
                        updateCell(cell.id, { content: e.target.value })
                      }
                      className="font-mono text-sm min-h-[100px]"
                      placeholder="Enter code..."
                    />
                  ) : (
                    <Textarea
                      value={cell.content}
                      onChange={(e) =>
                        updateCell(cell.id, { content: e.target.value })
                      }
                      className="min-h-[100px]"
                      placeholder="Enter markdown..."
                    />
                  )}

                  {cell.output && (
                    <div className="mt-2 p-3 bg-muted rounded text-sm">
                      {cell.output.error ? (
                        <div className="text-destructive">
                          Error: {cell.output.error}
                        </div>
                      ) : (
                        <pre className="whitespace-pre-wrap">
                          {typeof cell.output === "string"
                            ? cell.output
                            : JSON.stringify(cell.output, null, 2)}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex justify-center gap-2">
        <Button
          variant="outline"
          onClick={() => addCell("code", selectedCellId || undefined)}
        >
          <Code className="h-4 w-4 mr-2" />
          Add Code Cell
        </Button>
        <Button
          variant="outline"
          onClick={() => addCell("markdown", selectedCellId || undefined)}
        >
          <Type className="h-4 w-4 mr-2" />
          Add Markdown Cell
        </Button>
        <Button
          variant="outline"
          onClick={() => addCell("chart", selectedCellId || undefined)}
        >
          <BarChart3 className="h-4 w-4 mr-2" />
          Add Chart Cell
        </Button>
      </div>
    </div>
  );
}
