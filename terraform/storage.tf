# Spaces for backups and static assets
resource "digitalocean_spaces_bucket" "backups" {
  name   = "strategy-lab-${var.environment}-backups"
  region = var.region
  acl    = "private"

  lifecycle_rule {
    id      = "expire-old-backups"
    enabled = true

    expiration {
      days = var.backup_retention_days
    }
  }

  versioning {
    enabled = true
  }

  cors_rule {
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["https://${var.domain}"]
    allowed_headers = ["*"]
    max_age_seconds = 3000
  }
}

# Spaces for application data
resource "digitalocean_spaces_bucket" "data" {
  name   = "strategy-lab-${var.environment}-data"
  region = var.region
  acl    = "private"

  versioning {
    enabled = true
  }

  lifecycle_rule {
    id      = "archive-old-data"
    enabled = true

    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}

# CDN for static assets
resource "digitalocean_cdn" "static" {
  origin         = digitalocean_spaces_bucket.data.bucket_domain_name
  custom_domain  = "cdn.${var.domain}"

  certificate_name = digitalocean_certificate.cdn.name
}

# SSL certificate for CDN
resource "digitalocean_certificate" "cdn" {
  name    = "strategy-lab-cdn-cert"
  type    = "lets_encrypt"
  domains = ["cdn.${var.domain}"]
}
