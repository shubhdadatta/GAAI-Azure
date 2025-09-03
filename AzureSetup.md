# Azure OpenAI: CLI Login → Resource → Model Deployment

> **Works in Bash (macOS/Linux, Git Bash, WSL).** For PowerShell users, see the PowerShell block near the end.

---

## 0) Prerequisites

- **Azure CLI** `az` installed and signed in.
- **jq** for JSON parsing (`brew install jq` on macOS, `sudo apt-get install jq` on Debian/Ubuntu).
- You have access/approval to create Azure OpenAI resources in your subscription.

---

## 1) Set variables (edit these only)

```bash
# ====== EDIT THESE 8–10 LINES ONLY ======
SUBSCRIPTION_ID="00000000-0000-0000-0000-000000000000"
RESOURCE_GROUP="Tredence-Batch1"
LOCATION="eastus"                       # e.g., eastus, swedencentral, francecentral (must support Azure OpenAI)
ACCOUNT_NAME="myopenaiacct123"          # globally unique, 2–24 chars, letters/digits only
DEPLOYMENT_NAME="telcogpt"              # your deployment (serving) name
MODEL_NAME="gpt-4o-mini"                # e.g., gpt-4o, gpt-4o-mini, o3-mini, text-embedding-3-large
MODEL_VERSION="2024-07-18"              # keep as provided or change as needed
SKU_NAME="Standard"                     # Standard or Enterprise (if available to you)
SKU_CAPACITY="1"                        # compute units; 1 is typical
API_VERSION="2024-08-01-preview"        # pin the API version; adjust if your org requires a different one
# =======================================
```

---

## 2) One-time setup and login

```bash
set -euo pipefail

# ✧ Login ✧
az login   # opens browser for interactive login

# (Optional) If you have multiple tenants:
# az login --tenant "<tenant-id-or-domain>"

# ✧ Set subscription ✧
az account set --subscription "$SUBSCRIPTION_ID"

# ✧ Register provider (idempotent) ✧
az provider register --namespace Microsoft.CognitiveServices --wait
```

---

## 3) Create (or re-use) the resource group

```bash
# Create RG if it does not exist
if ! az group show --name "$RESOURCE_GROUP" >/dev/null 2>&1; then
  az group create --name "$RESOURCE_GROUP" --location "$LOCATION" >/dev/null
  echo "Created resource group: $RESOURCE_GROUP"
else
  echo "Resource group exists: $RESOURCE_GROUP"
fi
```

---

## 4) Create (or re-use) the Azure OpenAI account

```bash
# ✧ Create the Cognitive Services (OpenAI) account ✧
if ! az cognitiveservices account show       --name "$ACCOUNT_NAME"       --resource-group "$RESOURCE_GROUP" >/dev/null 2>&1; then

  az cognitiveservices account create     --name "$ACCOUNT_NAME"     --resource-group "$RESOURCE_GROUP"     --location "$LOCATION"     --kind OpenAI     --sku s0     --yes

  echo "Created Azure OpenAI account: $ACCOUNT_NAME"
else
  echo "Azure OpenAI account exists: $ACCOUNT_NAME"
fi
```

---

## 5) Fetch endpoint and keys, save to `.env`

```bash
# ✧ Fetch the endpoint URL ✧
ENDPOINT="$(az cognitiveservices account show   --name "$ACCOUNT_NAME"   --resource-group "$RESOURCE_GROUP"   --query "properties.endpoint" -o tsv)"

# ✧ Fetch the primary key ✧
PRIMARY_KEY="$(az cognitiveservices account keys list   --name "$ACCOUNT_NAME"   --resource-group "$RESOURCE_GROUP"   --query "key1" -o tsv)"

echo "Endpoint: $ENDPOINT"
echo "Primary key acquired."

# ✧ Write a clean .env file (no variable expansion inside block) ✧
cat > .env <<'EOF'
# Azure OpenAI environment variables
AZURE_OPENAI_ENDPOINT=""
AZURE_OPENAI_API_KEY=""
AZURE_OPENAI_API_VERSION=""
AZURE_OPENAI_DEPLOYMENT=""
EOF

# Fill values safely
# (Use GNU sed -i on Linux; on macOS BSD sed, -i '' is used.)
if sed --version >/dev/null 2>&1; then
  # Likely GNU sed (Linux)
  sed -i "s|AZURE_OPENAI_ENDPOINT=\"\"|AZURE_OPENAI_ENDPOINT=\"${ENDPOINT}\"|g" .env
  sed -i "s|AZURE_OPENAI_API_KEY=\"\"|AZURE_OPENAI_API_KEY=\"${PRIMARY_KEY}\"|g" .env
  sed -i "s|AZURE_OPENAI_API_VERSION=\"\"|AZURE_OPENAI_API_VERSION=\"${API_VERSION}\"|g" .env
  sed -i "s|AZURE_OPENAI_DEPLOYMENT=\"\"|AZURE_OPENAI_DEPLOYMENT=\"${DEPLOYMENT_NAME}\"|g" .env
else
  # macOS BSD sed fallback
  sed -i '' "s|AZURE_OPENAI_ENDPOINT=\"\"|AZURE_OPENAI_ENDPOINT=\"${ENDPOINT}\"|g" .env
  sed -i '' "s|AZURE_OPENAI_API_KEY=\"\"|AZURE_OPENAI_API_KEY=\"${PRIMARY_KEY}\"|g" .env
  sed -i '' "s|AZURE_OPENAI_API_VERSION=\"\"|AZURE_OPENAI_API_VERSION=\"${API_VERSION}\"|g" .env
  sed -i '' "s|AZURE_OPENAI_DEPLOYMENT=\"\"|AZURE_OPENAI_DEPLOYMENT=\"${DEPLOYMENT_NAME}\"|g" .env
fi

echo "Wrote credentials to .env"
```

---

## 6) Deploy the model (idempotent)

```bash
# Check if deployment exists
if ! az cognitiveservices account deployment show       --name "$ACCOUNT_NAME"       --resource-group "$RESOURCE_GROUP"       --deployment-name "$DEPLOYMENT_NAME" >/dev/null 2>&1; then

  # ✧ Deploy the GPT-4o mini (or your chosen) model ✧
  az cognitiveservices account deployment create     --name "$ACCOUNT_NAME"     --resource-group "$RESOURCE_GROUP"     --deployment-name "$DEPLOYMENT_NAME"     --model-name "$MODEL_NAME"     --model-version "$MODEL_VERSION"     --model-format OpenAI     --sku-name "$SKU_NAME"     --sku-capacity "$SKU_CAPACITY"

  echo "Created deployment: $DEPLOYMENT_NAME → $MODEL_NAME:$MODEL_VERSION"
else
  echo "Deployment exists: $DEPLOYMENT_NAME"
fi
```

---

## 7) Quick sanity test with `curl` (Chat Completions)

```bash
# Load env (optional but handy within current shell)
set -a
source ./.env
set +a

# Simple chat prompt
curl -sS "$AZURE_OPENAI_ENDPOINT/openai/deployments/$AZURE_OPENAI_DEPLOYMENT/chat/completions?api-version=$AZURE_OPENAI_API_VERSION"   -H "Content-Type: application/json"   -H "api-key: $AZURE_OPENAI_API_KEY"   -d '{
        "messages": [
          {"role": "system", "content": "You are a helpful assistant."},
          {"role": "user", "content": "In one sentence, explain what RAG is."}
        ]
      }' | jq '.choices[0].message.content'
```

---

## 8) (Optional) Quick embedding test

```bash
curl -sS "$AZURE_OPENAI_ENDPOINT/openai/deployments/$AZURE_OPENAI_DEPLOYMENT/embeddings?api-version=$AZURE_OPENAI_API_VERSION"   -H "Content-Type: application/json"   -H "api-key: $AZURE_OPENAI_API_KEY"   -d '{"input": "hello from azure openai"}' | jq '.data[0].embedding | length'
```

---

## PowerShell version (Core/Windows)

```powershell
# ====== EDIT THESE LINES ======
$SubscriptionId = "00000000-0000-0000-0000-000000000000"
$ResourceGroup  = "Tredence-Batch1"
$Location       = "eastus"
$AccountName    = "myopenaiacct123"
$DeployName     = "telcogpt"
$ModelName      = "gpt-4o-mini"
$ModelVersion   = "2024-07-18"
$SkuName        = "Standard"
$SkuCapacity    = 1
$ApiVersion     = "2024-08-01-preview"
# ==============================

az login | Out-Null
az account set --subscription $SubscriptionId

az provider register --namespace Microsoft.CognitiveServices --wait

if (-not (az group show --name $ResourceGroup 2>$null)) {
  az group create --name $ResourceGroup --location $Location | Out-Null
}

if (-not (az cognitiveservices account show --name $AccountName --resource-group $ResourceGroup 2>$null)) {
  az cognitiveservices account create `
    --name $AccountName `
    --resource-group $ResourceGroup `
    --location $Location `
    --kind OpenAI `
    --sku s0 `
    --yes | Out-Null
}

$Endpoint = az cognitiveservices account show --name $AccountName --resource-group $ResourceGroup --query "properties.endpoint" -o tsv
$PrimaryKey = az cognitiveservices account keys list --name $AccountName --resource-group $ResourceGroup --query "key1" -o tsv

@"
AZURE_OPENAI_ENDPOINT="$Endpoint"
AZURE_OPENAI_API_KEY="$PrimaryKey"
AZURE_OPENAI_API_VERSION="$ApiVersion"
AZURE_OPENAI_DEPLOYMENT="$DeployName"
"@ | Out-File -FilePath .env -Encoding ascii -Force

if (-not (az cognitiveservices account deployment show --name $AccountName --resource-group $ResourceGroup --deployment-name $DeployName 2>$null)) {
  az cognitiveservices account deployment create `
    --name $AccountName `
    --resource-group $ResourceGroup `
    --deployment-name $DeployName `
    --model-name $ModelName `
    --model-version $ModelVersion `
    --model-format OpenAI `
    --sku-name $SkuName `
    --sku-capacity $SkuCapacity | Out-Null
}

Write-Host "Endpoint: $Endpoint"
Write-Host "Deployment ready: $DeployName"
```

---

## Considerations & Tips

- **Quota/Throttling:** `Standard` SKU typically provides 1 compute unit per deployment. If you exceed throughput, responses may be throttled.
- **Naming:** `ACCOUNT_NAME` must be globally unique (2–24 chars, letters/numbers only).
- **Regions:** Ensure your `LOCATION` supports Azure OpenAI and your chosen `MODEL_NAME`.
- **RBAC & Policies:** Some orgs require approvals or specific API versions; that’s why we keep `API_VERSION` as a **variable** at the top.
- **Idempotency:** The script checks for existing resources/deployments so you can re-run safely.
