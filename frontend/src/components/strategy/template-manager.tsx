'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ConfigurationTemplate } from "@/hooks/useStrategies";
import { Save, FolderOpen, Trash2, MoreVertical, Download, Upload } from "lucide-react";
import { formatDistanceToNow } from "date-fns";

interface TemplateManagerProps {
  templates: ConfigurationTemplate[];
  currentConfig: Record<string, any>;
  onSaveTemplate: (name: string, description?: string) => Promise<void>;
  onLoadTemplate: (templateId: string) => Promise<void>;
  onDeleteTemplate: (templateId: string) => Promise<void>;
  onExportConfig: () => void;
  onImportConfig: (config: Record<string, any>) => void;
}

export function TemplateManager({
  templates,
  currentConfig,
  onSaveTemplate,
  onLoadTemplate,
  onDeleteTemplate,
  onExportConfig,
  onImportConfig
}: TemplateManagerProps) {
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [templateName, setTemplateName] = useState('');
  const [templateDescription, setTemplateDescription] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  const handleSaveTemplate = async () => {
    if (!templateName.trim()) return;
    
    await onSaveTemplate(templateName, templateDescription);
    setSaveDialogOpen(false);
    setTemplateName('');
    setTemplateDescription('');
  };

  const handleLoadTemplate = async (templateId: string) => {
    await onLoadTemplate(templateId);
    setSelectedTemplate(templateId);
  };

  const handleImportConfig = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.json';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      
      const text = await file.text();
      try {
        const config = JSON.parse(text);
        onImportConfig(config);
      } catch (error) {
        console.error('Failed to parse configuration file:', error);
      }
    };
    input.click();
  };

  const handleExportConfig = () => {
    const dataStr = JSON.stringify(currentConfig, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `strategy-config-${Date.now()}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Configuration Templates</CardTitle>
            <CardDescription>
              Save and load parameter configurations
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleImportConfig}
            >
              <Upload className="h-4 w-4 mr-2" />
              Import
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportConfig}
            >
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
            <Dialog open={saveDialogOpen} onOpenChange={setSaveDialogOpen}>
              <DialogTrigger asChild>
                <Button size="sm">
                  <Save className="h-4 w-4 mr-2" />
                  Save Template
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Save Configuration Template</DialogTitle>
                  <DialogDescription>
                    Save the current configuration as a reusable template
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label htmlFor="template-name">Template Name</Label>
                    <Input
                      id="template-name"
                      value={templateName}
                      onChange={(e) => setTemplateName(e.target.value)}
                      placeholder="My Strategy Config"
                    />
                  </div>
                  <div>
                    <Label htmlFor="template-description">Description (Optional)</Label>
                    <Textarea
                      id="template-description"
                      value={templateDescription}
                      onChange={(e) => setTemplateDescription(e.target.value)}
                      placeholder="Describe this configuration..."
                      rows={3}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button
                    variant="outline"
                    onClick={() => setSaveDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleSaveTemplate}
                    disabled={!templateName.trim()}
                  >
                    Save Template
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {templates.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FolderOpen className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No saved templates yet</p>
            <p className="text-sm mt-1">Save your first template to get started</p>
          </div>
        ) : (
          <ScrollArea className="h-[300px] pr-4">
            <div className="space-y-2">
              {templates.map(template => (
                <div
                  key={template.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedTemplate === template.id
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-muted/50'
                  }`}
                  onClick={() => handleLoadTemplate(template.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <div className="font-medium">{template.name}</div>
                      {template.description && (
                        <div className="text-sm text-muted-foreground">
                          {template.description}
                        </div>
                      )}
                      <div className="text-xs text-muted-foreground">
                        Created {formatDistanceToNow(new Date(template.created_at), { addSuffix: true })}
                        {template.last_used && (
                          <span>
                            {' • '}Last used {formatDistanceToNow(new Date(template.last_used), { addSuffix: true })}
                          </span>
                        )}
                      </div>
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => handleLoadTemplate(template.id)}>
                          <FolderOpen className="h-4 w-4 mr-2" />
                          Load
                        </DropdownMenuItem>
                        <DropdownMenuItem
                          onClick={() => onDeleteTemplate(template.id)}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </CardContent>
    </Card>
  );
}