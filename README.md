<h2 align="center">CLOUD DEPLOYMENT MANAGER</h2>


Terraform is a tool for building, changing, and versioning infrastructure safely and efficiently. Terraform can manage existing and popular service providers as well as custom in-house solutions.

Ruckus Devops Workflow is broadly divided into two categories,
    <ul style="padding-left:20px">
      <li>Infrastructure Create/Destroy/Manage</li>
      <li>Application/Services Deployment (K8S and Other Applications/VMs)</li>
    </ul>
      
Terraform offers different kind of providers which enables us to perform and complete the above workflows. This includes Google Provider (for Infra creation), Kubernetes Provider (for K8S Cluster Deployment) and other Custom Provider options (for custom applications like vSZ VM)

<a href="https://jira-wiki.ruckuswireless.com/display/KUMO/Ruckus+Cloud+Continuous+Deployment">Internal Wiki Doc for Terraform and Ruckus Cloud Deployment</a>

## Getting Started

To get a local copy up and running, follow these simple steps.

### Prerequisites (with debian linux example)

* Install Terraform (HashiCorp)
```sh
https://learn.hashicorp.com/tutorials/terraform/install-cli

curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install terraform
```
* Install Kubectl (Kubernetes)
```sh
https://kubernetes.io/docs/tasks/tools/install-kubectl/

sudo apt-get update && sudo apt-get install -y apt-transport-https gnupg2 curl
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee -a /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-get install -y kubectl
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
