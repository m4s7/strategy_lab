# SSH Key
resource "digitalocean_ssh_key" "main" {
  name       = "strategy-lab-key"
  public_key = file("~/.ssh/strategy-lab.pub")
}

# Main application droplet
resource "digitalocean_droplet" "app" {
  name     = "strategy-lab-${var.environment}"
  size     = var.droplet_size
  image    = "ubuntu-22-04-x64"
  region   = var.region
  ssh_keys = concat([digitalocean_ssh_key.main.fingerprint], var.ssh_keys)

  vpc_uuid = digitalocean_vpc.main.id

  user_data = templatefile("${path.module}/cloud-init.yaml", {
    domain      = var.domain
    environment = var.environment
    db_host     = digitalocean_database_cluster.postgres.host
    db_port     = digitalocean_database_cluster.postgres.port
    db_name     = digitalocean_database_cluster.postgres.database
    db_user     = digitalocean_database_cluster.postgres.user
    db_password = digitalocean_database_cluster.postgres.password
  })

  lifecycle {
    create_before_destroy = true
  }

  tags = ["strategy-lab", var.environment, "app"]
}

# Floating IP for zero-downtime deployments
resource "digitalocean_floating_ip" "main" {
  region = var.region
}

resource "digitalocean_floating_ip_assignment" "main" {
  ip_address = digitalocean_floating_ip.main.ip_address
  droplet_id = digitalocean_droplet.app.id
}

# Firewall rules
resource "digitalocean_firewall" "web" {
  name = "strategy-lab-${var.environment}-firewall"

  droplet_ids = [digitalocean_droplet.app.id]

  # SSH access (restrict to specific IPs in production)
  inbound_rule {
    protocol         = "tcp"
    port_range       = "22"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # HTTP
  inbound_rule {
    protocol         = "tcp"
    port_range       = "80"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # HTTPS
  inbound_rule {
    protocol         = "tcp"
    port_range       = "443"
    source_addresses = ["0.0.0.0/0", "::/0"]
  }

  # Allow all outbound traffic
  outbound_rule {
    protocol              = "tcp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "udp"
    port_range            = "1-65535"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }

  outbound_rule {
    protocol              = "icmp"
    destination_addresses = ["0.0.0.0/0", "::/0"]
  }
}

# VPC for network isolation
resource "digitalocean_vpc" "main" {
  name     = "strategy-lab-${var.environment}-vpc"
  region   = var.region
  ip_range = "10.10.10.0/24"
}
