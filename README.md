<h2 align="center">CLOUD DEPLOYMENT MANAGER</h2>


Terraform is a tool for building, changing, and versioning infrastructure safely and efficiently. Terraform can manage existing and popular service providers as well as custom in-house solutions.

Ruckus Devops Workflow is broadly divided into two categories,
    <ul style="padding-left:20px">
      <li>Infrastructure Create/Destroy/Manage</li>
      <li>Application/Services Deployment (K8S and Other Applications/VMs)</li>
    </ul>
      
Terraform offers different kind of providers which enables us to perform and complete the above workflows. This includes Google Provider (for Infra creation), Kubernetes Provider (for K8S Cluster Deployment) and other Custom Provider options (for custom applications like vSZ VM)

<a href="https://jira-wiki.ruckuswireless.com/display/KUMO/Ruckus+Cloud+Continuous+Deployment">Wiki Document</a>

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites

* Terraform (HashiCorp)
```sh
https://learn.hashicorp.com/tutorials/terraform/install-cl
```

### Installation

1. Clone the repo
```sh
git clone https://github.com/github_username/repo_name.git
```
2. Install Terraform (MAC OS)
```sh
brew install hashicorp/tap/terraform
```

### Run

1. Before Run
```sh
Replace credentials.json with your GCP service account credentials JSON.
In root folder, main.tf comment or uncomment the modules that needs to be deployed.
```

2. Run
```sh
terraform init
terraform plan --var-file="variables.tfvars"
terraform apply --var-file="variables.tfvars"
terraform destroy --var-file="variables.tfvars"
```

