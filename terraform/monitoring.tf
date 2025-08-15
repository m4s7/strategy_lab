# Monitoring alerts
resource "digitalocean_monitor_alert" "cpu_usage" {
  alerts {
    email = [var.admin_email]
  }
  window      = "5m"
  type        = "v1/insights/droplet/cpu"
  compare     = "GreaterThan"
  value       = 80
  enabled     = true
  entities    = [digitalocean_droplet.app.id]
  description = "CPU usage is above 80%"
  tags        = ["strategy-lab", var.environment]
}

resource "digitalocean_monitor_alert" "memory_usage" {
  alerts {
    email = [var.admin_email]
  }
  window      = "5m"
  type        = "v1/insights/droplet/memory_utilization_percent"
  compare     = "GreaterThan"
  value       = 85
  enabled     = true
  entities    = [digitalocean_droplet.app.id]
  description = "Memory usage is above 85%"
  tags        = ["strategy-lab", var.environment]
}

resource "digitalocean_monitor_alert" "disk_usage" {
  alerts {
    email = [var.admin_email]
  }
  window      = "5m"
  type        = "v1/insights/droplet/disk_utilization_percent"
  compare     = "GreaterThan"
  value       = 90
  enabled     = true
  entities    = [digitalocean_droplet.app.id]
  description = "Disk usage is above 90%"
  tags        = ["strategy-lab", var.environment]
}

resource "digitalocean_monitor_alert" "load_average" {
  alerts {
    email = [var.admin_email]
  }
  window      = "5m"
  type        = "v1/insights/droplet/load_5"
  compare     = "GreaterThan"
  value       = 4.0
  enabled     = true
  entities    = [digitalocean_droplet.app.id]
  description = "Load average is high"
  tags        = ["strategy-lab", var.environment]
}

# Database monitoring
resource "digitalocean_monitor_alert" "db_cpu" {
  alerts {
    email = [var.admin_email]
  }
  window      = "5m"
  type        = "v1/insights/dbaas/cpu"
  compare     = "GreaterThan"
  value       = 80
  enabled     = true
  entities    = [digitalocean_database_cluster.postgres.id]
  description = "Database CPU usage is above 80%"
  tags        = ["strategy-lab", var.environment, "database"]
}

resource "digitalocean_monitor_alert" "db_memory" {
  alerts {
    email = [var.admin_email]
  }
  window      = "5m"
  type        = "v1/insights/dbaas/memory_utilization_percent"
  compare     = "GreaterThan"
  value       = 85
  enabled     = true
  entities    = [digitalocean_database_cluster.postgres.id]
  description = "Database memory usage is above 85%"
  tags        = ["strategy-lab", var.environment, "database"]
}

# Uptime monitoring
resource "digitalocean_uptime_check" "main" {
  name    = "strategy-lab-${var.environment}"
  target  = "https://${var.domain}"
  type    = "https"
  regions = ["us_east", "eu_west", "ap_south"]
  enabled = true

  alert {
    type   = "email"
    emails = [var.admin_email]
    period = "2m"
  }
}

resource "digitalocean_uptime_check" "api" {
  name    = "strategy-lab-${var.environment}-api"
  target  = "https://${var.domain}/api/health"
  type    = "https"
  regions = ["us_east", "eu_west", "ap_south"]
  enabled = true

  alert {
    type   = "email"
    emails = [var.admin_email]
    period = "2m"
  }
}
