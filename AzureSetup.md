# Azure OpenAI: CLI Login → Resource → Model Deployment

> **Works in Bash (macOS/Linux, Git Bash, WSL).** For PowerShell users, see the PowerShell block near the end.

---

## 0) Prerequisites

- **Azure CLI** `az` installed and signed in.
- **jq** for JSON parsing (`brew install jq` on macOS, `sudo apt-get install jq` on Debian/Ubuntu).
- You have access/approval to create Azure OpenAI resources in your subscription.

---



## 1) Azure LOgin and Set variables (edit these only)
Run below command on CMD to login to azure, it would prompt login option in browser, make sure to login to azure account.
Post login completion, you will need to select the subscription on your terminal.
type '1' and press enter key

```bash
az login
```

Make sure to change the ACCOUNT_NAME 
```bash
# ====== EDIT THESE 8–10 LINES ONLY ======
SUBSCRIPTION_ID="f1f38cab-25d4-42b5-8f18-26c8f2bf1954"
RESOURCE_GROUP="Tredence-B4"
LOCATION="eastus"                       # e.g., eastus, swedencentral, francecentral (must support Azure OpenAI)
ACCOUNT_NAME="anshuopenai"          # globally unique, 2–24 chars, letters/digits only
DEPLOYMENT_NAME="gpt4o"              # your deployment (serving) name
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
# ✧ Set subscription ✧
az account set --subscription "$SUBSCRIPTION_ID"

# ✧ Register provider (idempotent) ✧
az provider register --namespace Microsoft.CognitiveServices --wait
```

---


## 3) Create the Azure OpenAI account
```bash


az cognitiveservices account create     --name "$ACCOUNT_NAME"     --resource-group "$RESOURCE_GROUP"     --location "$LOCATION"     --kind OpenAI     --sku s0     --yes

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
# ✧ Deploy the GPT-4o mini (or your chosen) model ✧
az cognitiveservices account deployment create     --name "$ACCOUNT_NAME"     --resource-group "$RESOURCE_GROUP"     --deployment-name "$DEPLOYMENT_NAME"     --model-name "$MODEL_NAME"     --model-version "$MODEL_VERSION"     --model-format OpenAI     --sku-name "$SKU_NAME"     --sku-capacity "$SKU_CAPACITY"
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
