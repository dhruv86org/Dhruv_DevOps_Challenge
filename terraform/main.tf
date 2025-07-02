# Random string for unique resource naming
resource "random_string" "suffix" {
  length  = 6
  special = false
  upper   = false
}

# Resource Group
resource "azurerm_resource_group" "main" {
  #name     = "rg-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  name     = var.resource_group
  location = var.location
  tags     = var.tags
}

# SSH Key for VMs
resource "azurerm_ssh_public_key" "main" {
  name                = "ssh-key-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  public_key          = file("~/.ssh/id_rsa.pub")
  tags                = var.tags
}