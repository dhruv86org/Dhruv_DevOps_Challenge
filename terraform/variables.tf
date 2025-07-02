variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "webapp"
}

variable "vm_sku" {
  description = "VM SKU for the scale set"
  type        = string
  default     = "Standard_B1s"
}

variable "vm_instances" {
  description = "Number of VM instances in scale set"
  type        = number
  default     = 2
}

variable "max_instances" {
  description = "Maximum number of instances for auto-scaling"
  type        = number
  default     = 5
}

variable "admin_username" {
  description = "Admin username for VMs"
  type        = string
  default     = "azureuser"
}

variable "allowed_ip_ranges" {
  description = "IP ranges allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Restrict this in production
}

variable "tags" {
  description = "Resource tags"
  type        = map(string)
  default = {
    Environment = "dev"
    Project     = "webapp-iac"
    ManagedBy   = "terraform"
    CreatedBy   = "dhruv86"
  }
}