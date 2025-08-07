"use client";

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import {
  BarChart3,
  Settings,
  Database,
  Play,
  TrendingUp,
  LineChart,
  Target,
  Zap,
  Activity,
} from "lucide-react";

// Menu items
const items = [
  {
    title: "Dashboard",
    url: "/",
    icon: BarChart3,
  },
  {
    title: "Strategy Config",
    url: "/strategy",
    icon: Settings,
  },
  {
    title: "Data Config",
    url: "/data",
    icon: Database,
  },
  {
    title: "Backtest",
    url: "/backtest",
    icon: Play,
  },
  {
    title: "Results",
    url: "/results",
    icon: TrendingUp,
  },
  {
    title: "Monitor",
    url: "/monitor",
    icon: Activity,
  },
  {
    title: "Portfolio",
    url: "/portfolio",
    icon: Target,
  },
  {
    title: "Charts",
    url: "/charts",
    icon: LineChart,
  },
  {
    title: "Charts Demo",
    url: "/charts/demo",
    icon: BarChart3,
  },
  {
    title: "Advanced Charts",
    url: "/charts/advanced",
    icon: TrendingUp,
  },
  {
    title: "Optimization",
    url: "/optimization",
    icon: Target,
  },
  {
    title: "Real-time",
    url: "/realtime",
    icon: Zap,
  },
];

export function AppSidebar() {
  return (
    <Sidebar>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild>
                    <a href={item.url}>
                      <item.icon className="h-4 w-4" />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
