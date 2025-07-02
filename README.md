# Azure Web Application Infrastructure as Code

This repository contains a complete Infrastructure as Code (IaC) solution for deploying a scalable, secure, and highly available web application on Microsoft Azure using Terraform.

## 🏗️ Architecture Overview

The solution deploys the following Azure resources:

### Core Infrastructure
- **Resource Group**: Container for all resources
- **Virtual Network**: Isolated network environment with multiple subnets
- **Network Security Groups**: Firewall rules for secure network access
- **Virtual Machine Scale Set**: Auto-scaling compute instances (B1s SKU for cost optimization)
- **Load Balancer**: Traffic distribution across VM instances (Standard SKU, basic tier compatible)
- **Storage Account**: Hosts static web content
- **Public IP**: Internet-facing endpoint

### Security Features
- **Network Security Groups**: Restrict access to only necessary ports (80, 443)
- **SSL/TLS Termination**: Self-signed certificates with HTTPS redirect
- **Firewall Rules**: Block unauthorized ports and protocols
- **Secure Storage**: TLS 1.2+ encryption for storage accounts

### Observability & Monitoring
- **Log Analytics Workspace**: Centralized logging
- **Application Insights**: Application performance monitoring
- **Azure Monitor**: Metrics collection and alerting
- **Auto-scaling Rules**: CPU-based scaling policies
- **Health Checks**: Application availability monitoring

## 🚀 Quick Start

### Prerequisites

1. **Azure Subscription** with sufficient permissions
2. **Azure CLI** installed and configured
3. **Terraform** (>= 1.0) installed
4. **GitHub repository** with required secrets configured
5. **SSH Key Pair** for VM access

### Required GitHub Secrets

Configure the following secrets in your GitHub repository:

```bash
AZURE_CLIENT_ID          # Azure Service Principal Client ID
AZURE_CLIENT_SECRET      # Azure Service Principal Client Secret
AZURE_SUBSCRIPTION_ID    # Azure Subscription ID
AZURE_TENANT_ID         # Azure Tenant ID
SSH_PUBLIC_KEY          # SSH public key content
SSH_PRIVATE_KEY         # SSH private key content
TERRAFORM_STATE_RG      # Resource group for Terraform state
TERRAFORM_STATE_SA      # Storage account for Terraform state
```
### Required GitHub Variables
Configure the following variable(s) in your GitHub repository:

```bash
RESOURCE_GROUP_NAME # Name of the resource group where infrastructure is created

```

### Setup Azure Service Principal

```bash
# Create service principal
az ad sp create-for-rbac --name "terraform-sp" --role="Contributor" --scopes="/subscriptions/YOUR_SUBSCRIPTION_ID"

# Create storage account for Terraform state
az group create --name "rg-terraform-state" --location "East US"
az storage account create --name "stterraformstate" --resource-group "rg-terraform-state" --location "East US" --sku "Standard_LRS"
```

### Deployment

1. **Fork/Clone this repository**
2. **Configure GitHub Secrets** as listed above
3. **Push changes to main branch** to trigger deployment

The GitHub Actions workflow will automatically:
- Deploy infrastructure using Terraform
- Configure and deploy the web application
- Run comprehensive security tests
- Provide deployment summary

## 📁 Project Structure

```
.
├── terraform/                 # Infrastructure as Code
│   ├── main.tf               # Main Terraform configuration
│   ├── variables.tf          # Variable definitions
│   ├── outputs.tf            # Output values
│   ├── providers.tf          # Provider configurations
│   ├── network.tf            # Network resources
│   ├── security.tf           # Security groups and rules
│   ├── compute.tf            # VM scale set and load balancer
│   ├── storage.tf            # Storage account
│   ├── monitoring.tf         # Monitoring and observability
│   └── scripts/
│       └── cloud-init.yaml   # VM initialization script
├── web-app/
│   └── index.html            # Static web application
├── tests/
│   └── security-tests.py     # Automated security tests
├── .github/workflows/
│   └── deploy.yml            # CI/CD pipeline
└── README.md                 # This file
```

## 🔧 Configuration

### Environment Variables

The solution supports environment-specific configurations:

| Variable | Description | Default |
|----------|-------------|---------|
| `environment` | Environment name (dev/prod) | `dev` |
| `location` | Azure region | `East US` |
| `vm_sku` | Virtual machine size | `Standard_B1s` |
| `vm_instances` | Initial VM instances | `2` |
| `max_instances` | Maximum instances for scaling | `5` |

### Scaling Configuration

Auto-scaling is configured based on CPU utilization:
- **Scale Out**: When CPU > 75% for 5 minutes
- **Scale In**: When CPU < 25% for 5 minutes
- **Cooldown**: 1 minute between scaling actions

## 🔒 Security Features

### Network Security
- **Port Restrictions**: Only ports 80 and 443 are accessible from the internet
- **SSH Access**: Limited to internal network only
- **Network Segmentation**: Separate subnets for VMs and load balancer

### Application Security
- **HTTPS Enforcement**: HTTP traffic automatically redirected to HTTPS
- **TLS Configuration**: TLS 1.2+ with secure cipher suites
- **Self-signed Certificates**: Automatically generated SSL certificates
- **Security Headers**: Basic security headers configured

### Infrastructure Security
- **Resource Isolation**: All resources deployed in dedicated virtual network
- **Access Controls**: Network Security Groups with least-privilege rules
- **Encryption**: Storage accounts encrypted with TLS 1.2+

## 📊 Monitoring & Observability

### Metrics & Monitoring
- **Application Insights**: Application performance and user analytics
- **Log Analytics**: Centralized log collection and analysis
- **Azure Monitor**: Infrastructure metrics and alerting
- **VM Insights**: Detailed virtual machine performance metrics

### Alerting
- **High CPU Alert**: Triggered when CPU usage exceeds 80%
- **Application Availability**: Web tests to monitor application uptime
- **Email Notifications**: Configured through Action Groups

### Health Checks
- **Load Balancer Probes**: HTTP health checks on port 80
- **Application Health Endpoint**: `/health` endpoint for application status
- **Availability Tests**: Synthetic monitoring from multiple regions

## 🧪 Testing

### Automated Security Tests

The solution includes comprehensive security tests that validate:

1. **Port Accessibility**: Ensures only required ports are open
2. **SSL Configuration**: Validates TLS setup and cipher strength
3. **HTTP to HTTPS Redirect**: Confirms traffic redirection
4. **Security Headers**: Checks for essential security headers
5. **Application Availability**: Verifies application functionality
6. **Health Endpoints**: Tests monitoring endpoints

Run tests manually:
```bash
python tests/security-tests.py <PUBLIC_IP>
```

### Manual Testing

Test the deployment:
```bash
# Check application availability
curl -k https://YOUR_PUBLIC_IP

# Test HTTP to HTTPS redirect
curl -v http://YOUR_PUBLIC_IP

# Test health endpoint
curl -k https://YOUR_PUBLIC_IP/health
```

## 🔄 CI/CD Pipeline

The GitHub Actions workflow consists of three main jobs:

### 1. Terraform Job
- **Trigger**: Changes to terraform files or main branch push
- **Actions**: 
  - Validates Terraform configuration
  - Plans infrastructure changes
  - Applies changes (main branch only)
  - Outputs infrastructure details

### 2. Deploy Application Job
- **Trigger**: After successful terraform deployment
- **Actions**:
  - Updates web content in storage
  - Restarts VM scale set instances
  - Waits for application readiness

### 3. Security Tests Job
- **Trigger**: After successful application deployment
- **Actions**:
  - Runs comprehensive security validation
  - Tests network security
  - Validates SSL configuration
  - Uploads test results as artifacts

## 💰 Cost Optimization

The solution is optimized for cost efficiency:

- **VM SKU**: Uses B1s instances (burstable, cost-effective)
- **Storage**: Standard LRS replication
- **Load Balancer**: Standard SKU (no additional charges for basic features)
- **Monitoring**: 30-day log retention
- **Auto-scaling**: Scales down during low usage

### Estimated Monthly Cost
- **VM Scale Set (2x B1s)**: ~$30-40
- **Load Balancer**: ~$20
- **Storage Account**: ~$2-5
- **Monitoring**: ~$5-10
- **Total**: ~$60-80/month

## 🔧 Customization

### Adding Custom Domain
To use a custom domain:

1. Update DNS records to point to the load balancer IP
2. Replace self-signed certificates with valid SSL certificates
3. Update nginx configuration with proper server names

### Scaling Configuration
Modify scaling parameters in `terraform/variables.tf`:
```hcl
variable "max_instances" {
  default = 10  # Increase maximum instances
}
```

### Additional Security
For production environments, consider:
- Azure Key Vault for certificate management
- Azure Application Gateway with WAF
- Azure Front Door for global load balancing
- Network Virtual Appliances for advanced security

## 🚨 Troubleshooting

### Common Issues

1. **Terraform State Lock**: 
   ```bash
   terraform force-unlock LOCK_ID
   ```

2. **VM Scale Set Health Issues**:
   ```bash
   az vmss get-instance-view --resource-group RG_NAME --name VMSS_NAME
   ```

3. **Application Not Loading**:
   - Check VM scale set instance health
   - Verify nginx service status
   - Review cloud-init logs: `/var/log/cloud-init-output.log`

4. **SSL Certificate Issues**:
   - Regenerate self-signed certificates
   - Check nginx SSL configuration
   - Verify certificate paths and permissions

### Logs and Diagnostics

- **VM Logs**: Available in Log Analytics workspace
- **Application Insights**: Application performance data
- **Load Balancer Health**: Azure portal monitoring
- **Security Test Results**: GitHub Actions artifacts

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests locally
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions and support:
- Create an issue in this repository
- Review Azure documentation
- Check Terraform Azure provider documentation

---

**Note**: This solution uses self-signed SSL certificates suitable for development and testing. For production use, implement proper certificate management with Azure Key Vault or Let's Encrypt.