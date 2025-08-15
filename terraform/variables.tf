variable "do_token" {
  description = "DigitalOcean API token"
  type        = string
  sensitive   = true
}

variable "cloudflare_token" {
  description = "Cloudflare API token"
  type        = string
  sensitive   = true
}

variable "domain" {
  description = "Domain name for the application"
  type        = string
  default     = "lab.m4s8.dev"
}

variable "region" {
  description = "DigitalOcean region"
  type        = string
  default     = "nyc3"
}

variable "droplet_size" {
  description = "Size of the droplet"
  type        = string
  default     = "s-4vcpu-8gb"
}

variable "db_size" {
  description = "Size of the database cluster"
  type        = string
  default     = "db-s-2vcpu-4gb"
}

variable "ssh_keys" {
  description = "SSH key fingerprints for droplet access"
  type        = list(string)
  default     = []
}

variable "admin_email" {
  description = "Admin email for notifications"
  type        = string
  default     = "admin@m4s8.dev"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
}
