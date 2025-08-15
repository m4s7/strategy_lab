output "droplet_ip" {
  description = "IP address of the droplet"
  value       = digitalocean_droplet.app.ipv4_address
}

output "floating_ip" {
  description = "Floating IP address"
  value       = digitalocean_floating_ip.main.ip_address
}

output "database_host" {
  description = "Database hostname"
  value       = digitalocean_database_cluster.postgres.host
  sensitive   = true
}

output "database_port" {
  description = "Database port"
  value       = digitalocean_database_cluster.postgres.port
}

output "database_name" {
  description = "Database name"
  value       = digitalocean_database_cluster.postgres.database
}

output "database_user" {
  description = "Database username"
  value       = digitalocean_database_cluster.postgres.user
  sensitive   = true
}

output "database_password" {
  description = "Database password"
  value       = digitalocean_database_cluster.postgres.password
  sensitive   = true
}

output "redis_host" {
  description = "Redis hostname"
  value       = digitalocean_database_cluster.redis.host
  sensitive   = true
}

output "redis_port" {
  description = "Redis port"
  value       = digitalocean_database_cluster.redis.port
}

output "redis_password" {
  description = "Redis password"
  value       = digitalocean_database_cluster.redis.password
  sensitive   = true
}

output "backup_bucket" {
  description = "Backup bucket name"
  value       = digitalocean_spaces_bucket.backups.name
}

output "data_bucket" {
  description = "Data bucket name"
  value       = digitalocean_spaces_bucket.data.name
}

output "cdn_endpoint" {
  description = "CDN endpoint URL"
  value       = digitalocean_cdn.static.endpoint
}
