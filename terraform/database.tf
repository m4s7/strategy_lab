# PostgreSQL Database Cluster
resource "digitalocean_database_cluster" "postgres" {
  name       = "strategy-lab-${var.environment}-db"
  engine     = "pg"
  version    = "15"
  size       = var.db_size
  region     = var.region
  node_count = 1

  private_network_uuid = digitalocean_vpc.main.id

  maintenance_window {
    day  = "sunday"
    hour = "02:00:00"
  }

  tags = ["strategy-lab", var.environment, "database"]
}

# Database firewall rules
resource "digitalocean_database_firewall" "postgres" {
  cluster_id = digitalocean_database_cluster.postgres.id

  rule {
    type  = "droplet"
    value = digitalocean_droplet.app.id
  }
}

# Database user for application
resource "digitalocean_database_user" "app" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "strategy_lab_app"
}

# Database for application
resource "digitalocean_database_db" "app" {
  cluster_id = digitalocean_database_cluster.postgres.id
  name       = "strategy_lab"
}

# Redis Database
resource "digitalocean_database_cluster" "redis" {
  name       = "strategy-lab-${var.environment}-redis"
  engine     = "redis"
  version    = "7"
  size       = "db-s-1vcpu-1gb"
  region     = var.region
  node_count = 1

  private_network_uuid = digitalocean_vpc.main.id

  maintenance_window {
    day  = "sunday"
    hour = "03:00:00"
  }

  eviction_policy = "allkeys-lru"

  tags = ["strategy-lab", var.environment, "cache"]
}

# Redis firewall rules
resource "digitalocean_database_firewall" "redis" {
  cluster_id = digitalocean_database_cluster.redis.id

  rule {
    type  = "droplet"
    value = digitalocean_droplet.app.id
  }
}
