# Storage Account for web content
resource "azurerm_storage_account" "main" {
  name                     = "st${var.project_name}${var.environment}${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"

  tags = var.tags
}

# Storage Container for web content
resource "azurerm_storage_container" "web_content" {
  name                  = "web-content"
  storage_account_id    = azurerm_storage_account.main.id
  container_access_type = "blob"
}

# Upload web content to storage
resource "azurerm_storage_blob" "web_content" {
  name                   = "index.html"
  storage_account_name   = azurerm_storage_account.main.name
  storage_container_name = azurerm_storage_container.web_content.name
  type                   = "Block"
  source_content         = <<-EOT
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hello World</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>
EOT
  content_type           = "text/html"

  depends_on = [azurerm_storage_container.web_content]
}