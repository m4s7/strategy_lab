"use client";

import { useState } from "react";
import { Clock, Calendar, Save } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { HelpTooltip } from "@/components/ui/help-tooltip";
import {
  useOptimisticUpdate,
  OptimisticUpdateIndicator,
} from "@/components/ui/optimistic-update";

interface BackupSchedule {
  daily: {
    enabled: boolean;
    time: string;
    type: "full" | "incremental";
    retention: number;
  };
  weekly: {
    enabled: boolean;
    dayOfWeek: number;
    time: string;
    type: "full" | "incremental";
    retention: number;
  };
  monthly: {
    enabled: boolean;
    dayOfMonth: number;
    time: string;
    type: "full" | "incremental";
    retention: number;
  };
}

export function BackupScheduleConfig() {
  const [schedule, setSchedule] = useState<BackupSchedule>({
    daily: {
      enabled: true,
      time: "02:00",
      type: "incremental",
      retention: 7,
    },
    weekly: {
      enabled: true,
      dayOfWeek: 0, // Sunday
      time: "03:00",
      type: "full",
      retention: 4,
    },
    monthly: {
      enabled: true,
      dayOfMonth: 1,
      time: "03:00",
      type: "full",
      retention: 12,
    },
  });

  const { update, status } = useOptimisticUpdate(schedule, {
    onUpdate: async (newSchedule) => {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));
      return newSchedule;
    },
    timeout: 3000,
  });

  const handleScheduleChange = (
    frequency: keyof BackupSchedule,
    field: string,
    value: any
  ) => {
    const newSchedule = {
      ...schedule,
      [frequency]: {
        ...schedule[frequency],
        [field]: value,
      },
    };
    setSchedule(newSchedule);
  };

  const handleSave = () => {
    update(schedule);
  };

  const daysOfWeek = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
  ];

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Backup Schedule</CardTitle>
            <CardDescription>
              Configure automatic backup timing and retention
            </CardDescription>
          </div>
          <OptimisticUpdateIndicator status={status} />
        </div>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="daily" className="space-y-4">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="daily">Daily</TabsTrigger>
            <TabsTrigger value="weekly">Weekly</TabsTrigger>
            <TabsTrigger value="monthly">Monthly</TabsTrigger>
          </TabsList>

          <TabsContent value="daily" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Enable Daily Backups</Label>
                <p className="text-sm text-muted-foreground">
                  Run automatic backups every day
                </p>
              </div>
              <Switch
                checked={schedule.daily.enabled}
                onCheckedChange={(checked) =>
                  handleScheduleChange("daily", "enabled", checked)
                }
              />
            </div>

            {schedule.daily.enabled && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label
                      htmlFor="daily-time"
                      className="flex items-center gap-2"
                    >
                      <Clock className="w-4 h-4" />
                      Backup Time
                      <HelpTooltip
                        content="Time when the daily backup will run (24-hour format)"
                        size="sm"
                      />
                    </Label>
                    <Input
                      id="daily-time"
                      type="time"
                      value={schedule.daily.time}
                      onChange={(e) =>
                        handleScheduleChange("daily", "time", e.target.value)
                      }
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="daily-type">Backup Type</Label>
                    <Select
                      value={schedule.daily.type}
                      onValueChange={(value) =>
                        handleScheduleChange("daily", "type", value)
                      }
                    >
                      <SelectTrigger id="daily-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="incremental">Incremental</SelectItem>
                        <SelectItem value="full">Full</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label
                    htmlFor="daily-retention"
                    className="flex items-center gap-2"
                  >
                    Retention Period
                    <HelpTooltip
                      content="How many days to keep daily backups"
                      size="sm"
                    />
                  </Label>
                  <div className="flex items-center gap-2">
                    <Input
                      id="daily-retention"
                      type="number"
                      min="1"
                      max="365"
                      value={schedule.daily.retention}
                      onChange={(e) =>
                        handleScheduleChange(
                          "daily",
                          "retention",
                          parseInt(e.target.value)
                        )
                      }
                      className="w-24"
                    />
                    <span className="text-sm text-muted-foreground">days</span>
                  </div>
                </div>
              </>
            )}
          </TabsContent>

          <TabsContent value="weekly" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Enable Weekly Backups</Label>
                <p className="text-sm text-muted-foreground">
                  Run automatic backups once a week
                </p>
              </div>
              <Switch
                checked={schedule.weekly.enabled}
                onCheckedChange={(checked) =>
                  handleScheduleChange("weekly", "enabled", checked)
                }
              />
            </div>

            {schedule.weekly.enabled && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label
                      htmlFor="weekly-day"
                      className="flex items-center gap-2"
                    >
                      <Calendar className="w-4 h-4" />
                      Day of Week
                    </Label>
                    <Select
                      value={schedule.weekly.dayOfWeek.toString()}
                      onValueChange={(value) =>
                        handleScheduleChange(
                          "weekly",
                          "dayOfWeek",
                          parseInt(value)
                        )
                      }
                    >
                      <SelectTrigger id="weekly-day">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {daysOfWeek.map((day, index) => (
                          <SelectItem key={day} value={index.toString()}>
                            {day}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label
                      htmlFor="weekly-time"
                      className="flex items-center gap-2"
                    >
                      <Clock className="w-4 h-4" />
                      Backup Time
                    </Label>
                    <Input
                      id="weekly-time"
                      type="time"
                      value={schedule.weekly.time}
                      onChange={(e) =>
                        handleScheduleChange("weekly", "time", e.target.value)
                      }
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="weekly-type">Backup Type</Label>
                    <Select
                      value={schedule.weekly.type}
                      onValueChange={(value) =>
                        handleScheduleChange("weekly", "type", value)
                      }
                    >
                      <SelectTrigger id="weekly-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="incremental">Incremental</SelectItem>
                        <SelectItem value="full">Full</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="weekly-retention">Retention Period</Label>
                    <div className="flex items-center gap-2">
                      <Input
                        id="weekly-retention"
                        type="number"
                        min="1"
                        max="52"
                        value={schedule.weekly.retention}
                        onChange={(e) =>
                          handleScheduleChange(
                            "weekly",
                            "retention",
                            parseInt(e.target.value)
                          )
                        }
                        className="w-24"
                      />
                      <span className="text-sm text-muted-foreground">
                        weeks
                      </span>
                    </div>
                  </div>
                </div>
              </>
            )}
          </TabsContent>

          <TabsContent value="monthly" className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Enable Monthly Backups</Label>
                <p className="text-sm text-muted-foreground">
                  Run automatic backups once a month
                </p>
              </div>
              <Switch
                checked={schedule.monthly.enabled}
                onCheckedChange={(checked) =>
                  handleScheduleChange("monthly", "enabled", checked)
                }
              />
            </div>

            {schedule.monthly.enabled && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label
                      htmlFor="monthly-day"
                      className="flex items-center gap-2"
                    >
                      <Calendar className="w-4 h-4" />
                      Day of Month
                    </Label>
                    <Input
                      id="monthly-day"
                      type="number"
                      min="1"
                      max="28"
                      value={schedule.monthly.dayOfMonth}
                      onChange={(e) =>
                        handleScheduleChange(
                          "monthly",
                          "dayOfMonth",
                          parseInt(e.target.value)
                        )
                      }
                    />
                  </div>

                  <div className="space-y-2">
                    <Label
                      htmlFor="monthly-time"
                      className="flex items-center gap-2"
                    >
                      <Clock className="w-4 h-4" />
                      Backup Time
                    </Label>
                    <Input
                      id="monthly-time"
                      type="time"
                      value={schedule.monthly.time}
                      onChange={(e) =>
                        handleScheduleChange("monthly", "time", e.target.value)
                      }
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="monthly-type">Backup Type</Label>
                    <Select
                      value={schedule.monthly.type}
                      onValueChange={(value) =>
                        handleScheduleChange("monthly", "type", value)
                      }
                    >
                      <SelectTrigger id="monthly-type">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="incremental">Incremental</SelectItem>
                        <SelectItem value="full">Full</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="monthly-retention">Retention Period</Label>
                    <div className="flex items-center gap-2">
                      <Input
                        id="monthly-retention"
                        type="number"
                        min="1"
                        max="120"
                        value={schedule.monthly.retention}
                        onChange={(e) =>
                          handleScheduleChange(
                            "monthly",
                            "retention",
                            parseInt(e.target.value)
                          )
                        }
                        className="w-24"
                      />
                      <span className="text-sm text-muted-foreground">
                        months
                      </span>
                    </div>
                  </div>
                </div>
              </>
            )}
          </TabsContent>
        </Tabs>

        <div className="flex justify-end mt-6">
          <Button onClick={handleSave}>
            <Save className="w-4 h-4 mr-2" />
            Save Schedule
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
