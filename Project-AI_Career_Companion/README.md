# Login
az login

# Variables
NAME=anshu
RESOURCE_GROUP=Tredence-b4
LOCATION=eastus
ACR_NAME=careercompanionacr$NAME
KV_NAME=careercompanionkv-$NAME
APPINSIGHTS_NAME=careercompanionai-$NAME
ACI_NAME=careercompanion-aci-$NAME
SP=sp-$NAME

# Azure Container Registry
az acr create --resource-group $RESOURCE_GROUP --name $ACR_NAME --sku Basic --admin-enabled true

# Azure Key Vault
az keyvault create --name $KV_NAME --resource-group $RESOURCE_GROUP --location $LOCATION

# Store secrets in Key Vault
az keyvault secret set --vault-name $KV_NAME --name "OpenAIKey" --value "cda78233ab594eebb674d0b65dbcc084"
az keyvault secret set --vault-name $KV_NAME --name "MLflowTrackingURI" --value "http://20.75.92.162:5000/"

# Application Insights
az monitor app-insights component create \
  --app $APPINSIGHTS_NAME \
  --location $LOCATION \
  --resource-group $RESOURCE_GROUP


APP_INSIGHTS_KEY=$(az monitor app-insights component show \
  --app  $APPINSIGHTS_NAME\
  --resource-group  $RESOURCE_GROUP\
  --query instrumentationKey -o tsv)

az keyvault secret set \
  --vault-name $KV_NAME \
  --name "AppInsightsKey" \
  --value "$APP_INSIGHTS_KEY"


az ad sp create-for-rbac -n $SP \
  --role "Key Vault Secrets User" \
  --scopes $(az keyvault show -n $KV_NAME --query id -o tsv) \
  --sdk-auth > sp.json

# build backend docker images
docker build -f Dockerfile -t backend-image2 . 

# run the image as contianer
docker run -d -p 8000:8000 --name backend-service backend-image2

# login to ACR

ACR_USERNAME=$(az acr credential show --name $ACR_NAME --query "username" -o tsv)
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

sudo az acr login -n $ACR_NAME -u $ACR_USERNAME -p $ACR_PASSWORD


# push backend image to ACR

sudo docker tag backend-image2 $ACR_NAME.azurecr.io/backend-image2:latest
sudo docker push $ACR_NAME.azurecr.io/backend-image2:latest

# deploy to ACI
az container create -g $RESOURCE_GROUP -n $ACI_NAME \
  --image $ACR_NAME.azurecr.io/backend-image2 \
  --registry-login-server $ACR_NAME.azurecr.io \
  --registry-username $(az acr credential show -n $ACR_NAME --query username -o tsv) \
  --registry-password $(az acr credential show -n $ACR_NAME --query passwords[0].value -o tsv) \
  --cpu 1 --memory 1 --ports 8000 --os-type Linux --ip-address public \
  --dns-name-label aicareer-demo

# check list of containers on ACI
az container list -g $RESOURCE_GROUP -o table