# VM Scale Set
resource "azurerm_linux_virtual_machine_scale_set" "main" {
  name                = "vmss-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.vm_sku
  instances           = var.vm_instances
  tags                = var.tags

  # Disable password authentication
  disable_password_authentication = true

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-focal"
    sku       = "20_04-lts-gen2"
    version   = "latest"
  }

  os_disk {
    storage_account_type = "Standard_LRS"
    caching              = "ReadWrite"
  }

  network_interface {
    name    = "internal"
    primary = true

    ip_configuration {
      name                                   = "internal"
      primary                                = true
      subnet_id                              = azurerm_subnet.vm_subnet.id
      load_balancer_backend_address_pool_ids = [azurerm_lb_backend_address_pool.main.id]
    }

    network_security_group_id = azurerm_network_security_group.vm_nsg.id
  }

  admin_username = var.admin_username

  admin_ssh_key {
    username   = var.admin_username
    public_key = azurerm_ssh_public_key.main.public_key
  }

  # Custom data to install and configure web server
  custom_data = base64encode(templatefile("${path.module}/scripts/cloud-init.yaml", {
    storage_account_name = azurerm_storage_account.main.name
    storage_account_key  = azurerm_storage_account.main.primary_access_key
  }))

  depends_on = [
    azurerm_storage_blob.web_content
  ]
}

# Auto Scaling Settings
resource "azurerm_monitor_autoscale_setting" "main" {
  name                = "autoscale-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  target_resource_id  = azurerm_linux_virtual_machine_scale_set.main.id

  profile {
    name = "default"

    capacity {
      default = var.vm_instances
      minimum = 1
      maximum = var.max_instances
    }

    rule {
      metric_trigger {
        metric_name        = "Percentage CPU"
        metric_resource_id = azurerm_linux_virtual_machine_scale_set.main.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "GreaterThan"
        threshold          = 75
      }

      scale_action {
        direction = "Increase"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT1M"
      }
    }

    rule {
      metric_trigger {
        metric_name        = "Percentage CPU"
        metric_resource_id = azurerm_linux_virtual_machine_scale_set.main.id
        time_grain         = "PT1M"
        statistic          = "Average"
        time_window        = "PT5M"
        time_aggregation   = "Average"
        operator           = "LessThan"
        threshold          = 25
      }

      scale_action {
        direction = "Decrease"
        type      = "ChangeCount"
        value     = "1"
        cooldown  = "PT1M"
      }
    }
  }

  tags = var.tags
}