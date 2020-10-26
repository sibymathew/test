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
* Install Helm
```sh
https://helm.sh/docs/intro/install/

curl https://baltocdn.com/helm/signing.asc | sudo apt-key add -
sudo apt-get install apt-transport-https --yes
echo "deb https://baltocdn.com/helm/stable/debian/ all main" | sudo tee /etc/apt/sources.list.d/helm-stable-debian.list
sudo apt-get update
sudo apt-get install helm
```
* Install GitClient
```sh
https://www.atlassian.com/git/tutorials/install-git

sudo apt-get update
sudo apt-get install git
```
* Install Gcloud Client
```sh
https://cloud.google.com/sdk/docs/install#linux

curl -O https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-313.0.0-linux-x86_64.tar.gz
./google-cloud-sdk/install.sh (untar and run)
``` 


### Checklist 

* Clone the repos
```sh
git clone ssh://git@bitbucket.rks-cloud.com:7999/cd/alto-tf.git
git clone ssh://git@bitbucket.rks-cloud.com:7999/cd/gitops-flux-argosy.git
```
* In GCP, create a google project
* In GCP, create a service account and download the credentials json
* Using gcloud init, configure and connect to GCP


### Native Deployment (Using Raw Application)

* Before Run
```sh
In alto-tf,
	* GCP Infra can deployed in single click or in layers.
	* If the environment is fresh install, recommendation would be to run all layers in one shot.
		* To run in one shot, use the main.tf in the top level directory.
		* In top level directory, variables.tfvars modify all parameter values.
	* For layered approach, go to the individual layer directory and run terrafrom from that location.
	* In layers folder, there are different layers like,
		* Project
		* Cluster
		* Network
	* Based on the need pick and choose the layer you need to run.
	* Replace credentials.json with your GCP service account credentials JSON.
```

* Run
```sh
terraform init
terraform plan --var-file="variables.tfvars"
terraform apply --var-file="variables.tfvars"
terraform destroy --var-file="variables.tfvars"
```

### Run Agrosy Workflow

* Before Run
```sh
In alto-tf,
	* Replace credentials.json with your GCP service account credentials JSON.
	* In layers folder, go to Argosy folder.
	* Make sure kubectl is set with GCP Cluster Config Context.
	
	  gcloud container clusters get-credentials <GKE Cluster Name> --region=<Region Name>
	  
	* In argosy/variables.tfvars modify all parameter values.
```

* Run
```sh
terraform init
terraform plan --var-file="variables.tfvars"
terraform apply --var-file="variables.tfvars"
terraform destroy --var-file="variables.tfvars"
```

### Docker based Deployment (Dockerized Application)

