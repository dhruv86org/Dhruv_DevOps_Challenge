# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = var.tags
}

# Application Insights
resource "azurerm_application_insights" "main" {
  name                = "ai-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "web"
  tags                = var.tags
}

# VM Insights Data Collection Rule
# resource "azurerm_monitor_data_collection_rule" "vm_insights" {
#   name                = "dcr-vm-insights"
#   resource_group_name = azurerm_resource_group.main.name
#   location            = azurerm_resource_group.main.location
#   tags                = var.tags

#   destinations {
#     log_analytics {
#       workspace_resource_id = azurerm_log_analytics_workspace.main.id
#       name                  = "destination-log"
#     }

#     azure_monitor_metrics {
#       name = "destination-metrics"
#     }
#   }

#   # Separate data flows for each destination type
#   data_flow {
#     streams      = ["Microsoft-VMInsights-Performance"]
#     destinations = ["destination-log"]
#   }

#   data_flow {
#     streams      = ["Microsoft-InsightsMetrics"]
#     destinations = ["destination-metrics"]
#   }

#   data_sources {
#     performance_counter {
#       streams                       = ["Microsoft-VMInsights-Performance", "Microsoft-InsightsMetrics"]
#       sampling_frequency_in_seconds = 60
#       counter_specifiers = [
#         "\\Processor(_Total)\\% Processor Time",
#         "\\Memory\\Available Bytes",
#         "\\Memory\\% Committed Bytes In Use",
#         "\\LogicalDisk(_Total)\\Disk Transfers/sec",
#         "\\LogicalDisk(_Total)\\% Free Space"
#       ]
#       name = "VMInsightsPerfCounters"
#     }
#   }
# }

# resource "azurerm_monitor_data_collection_rule" "vm_insights" {
#   name                = "dcr-vm-insights"
#   resource_group_name = azurerm_resource_group.main.name
#   location            = azurerm_resource_group.main.location
#   tags                = var.tags

#   destinations {
#     log_analytics {
#       workspace_resource_id = azurerm_log_analytics_workspace.main.id
#       name                  = "la-destination"
#     }
#   }

#   data_flow {
#     streams      = ["Microsoft-Perf"]
#     destinations = ["la-destination"]
#   }

#   data_sources {
#     performance_counter {
#       streams                       = ["Microsoft-Perf"]
#       sampling_frequency_in_seconds = 60
#       counter_specifiers = [
#         "\\Processor(_Total)\\% Processor Time",
#         "\\Memory\\Available Bytes"
#       ]
#       name = "perfcounter-datasource"
#     }
#   }
# }

resource "azurerm_monitor_data_collection_rule" "vm_insights" {
  name                = "dcr-vm-insights"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  tags                = var.tags

  destinations {
    log_analytics {
      workspace_resource_id = azurerm_log_analytics_workspace.main.id
      name                  = "la-destination"
    }
    azure_monitor_metrics {
      name = "metrics-destination"
    }
  }

  data_flow {
    streams      = ["Microsoft-Perf"]
    destinations = ["la-destination"]
  }

  data_flow {
    streams      = ["Microsoft-InsightsMetrics"]
    destinations = ["metrics-destination"]
  }

  data_sources {
    performance_counter {
      streams                       = ["Microsoft-Perf", "Microsoft-InsightsMetrics"]
      sampling_frequency_in_seconds = 60
      counter_specifiers = [
        "\\Processor(_Total)\\% Processor Time",
        "\\Memory\\Available Bytes",
        "\\Memory\\% Committed Bytes In Use",
        "\\LogicalDisk(_Total)\\Disk Transfers/sec",
        "\\LogicalDisk(_Total)\\% Free Space"
      ]
      name = "perfcounter-datasource"
    }
  }
}


# Monitor Action Group for Alerts
resource "azurerm_monitor_action_group" "main" {
  name                = "ag-${var.project_name}-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "webapp-ag"
  tags                = var.tags

  # Email notification (add your email here)
  email_receiver {
    name          = "admin-email"
    email_address = "admin@example.com" # Change this to your email
  }
}

# CPU Alert Rule
resource "azurerm_monitor_metric_alert" "high_cpu" {
  name                = "alert-high-cpu"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_linux_virtual_machine_scale_set.main.id]
  description         = "Alert when CPU usage is high"
  severity            = 2
  frequency           = "PT1M"
  window_size         = "PT5M"

  criteria {
    metric_namespace = "Microsoft.Compute/virtualMachineScaleSets"
    metric_name      = "Percentage CPU"
    aggregation      = "Average"
    operator         = "GreaterThan"
    threshold        = 80
  }

  action {
    action_group_id = azurerm_monitor_action_group.main.id
  }

  tags = var.tags
}

# Application availability test
resource "azurerm_application_insights_web_test" "main" {
  name                    = "webtest-${var.project_name}-${var.environment}"
  location                = azurerm_resource_group.main.location
  resource_group_name     = azurerm_resource_group.main.name
  application_insights_id = azurerm_application_insights.main.id
  kind                    = "ping"
  frequency               = 300
  timeout                 = 60
  enabled                 = true
  geo_locations           = ["us-tx-sn1-azr", "us-il-ch1-azr"]

  configuration = <<XML
<WebTest Name="WebTest1" Id="ABD48585-0831-40CB-9069-682EA6BB3583" Enabled="True" CssProjectStructure="" CssIteration="" Timeout="0" WorkItemIds="" xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010" Description="" CredentialUserName="" CredentialPassword="" PreAuthenticate="True" Proxy="default" StopOnError="False" RecordedResultFile="" ResultsLocale="">
  <Items>
    <Request Method="GET" Guid="a5f10126-e4cd-570d-961c-cea43999a200" Version="1.1" Url="http://${azurerm_public_ip.lb_public_ip.ip_address}" ThinkTime="0" Timeout="300" ParseDependentRequests="True" FollowRedirects="True" RecordResult="True" Cache="False" ResponseTimeGoal="0" Encoding="utf-8" ExpectedHttpStatusCode="200" ExpectedResponseUrl="" ReportingName="" IgnoreHttpStatusCode="False" />
  </Items>
</WebTest>
XML

  tags = var.tags

  depends_on = [azurerm_linux_virtual_machine_scale_set.main]
}