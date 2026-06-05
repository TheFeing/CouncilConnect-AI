# CouncilConnect AI

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.14-blue)](https://www.python.org/)
[![Terraform Version](https://img.shields.io/badge/terraform-1.7.0-purple)](https://www.terraform.io/)
[![Azure](https://img.shields.io/badge/Azure-0089D6?logo=microsoft-azure&logoColor=white)](https://azure.microsoft.com/)
[![Code Coverage](https://img.shields.io/badge/coverage-85%25-brightgreen)](https://pytest-cov.readthedocs.io/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Overview

**CouncilConnect AI** is a Retrieval-Augmented Generation (RAG) system designed to support Salford City Council residents with AI‑powered assistance. It ingests council policies (PDFs, web pages), redacts personally identifiable information (PII), stores embeddings in a vector database, and answers resident queries using Google’s Gemma 4 language model.

This project was developed as part of a **DevOps Engineer Level 4 apprenticeship** and demonstrates:

- Infrastructure as Code (Terraform) on Azure
- CI/CD with GitHub Actions (full automation from commit to deployment)
- Containerisation (Docker, Azure Container Apps)
- Monitoring & observability (Application Insights, custom OpenTelemetry metrics)
- Security (Key Vault, RBAC, PII redaction, dependency scanning, secrets not stored in Terraform state)
- Feature toggling (branching by abstraction)
- Disaster recovery (Azure Blob Storage for durable backups)

## Architecture

The system architecture is documented in [`ARCHITECTURE.md`](./ARCHITECTURE.md) (Mermaid diagram rendered on GitHub).

## Tech Stack

| Component               | Technology                                                                 |
|-------------------------|----------------------------------------------------------------------------|
| Backend API             | Python 3.11+ / FastAPI                                                     |
| Frontend UI             | Streamlit                                                                  |
| Vector Database         | Qdrant (cloud)                                              |
| LLM                     | Google Gemma 4 (via `google-genai` SDK)                                    |
| Embedding Model         | `gemini-embedding-001` (3072 dimensions)                                  |
| Security                | Azure Key Vault, RBAC, Managed Identity, PII redactor                      |
| Disaster Recovery       | Azure Blob Storage (Cool tier, private container)                         |
| Infrastructure as Code  | Terraform (HCL)                                                            |
| Containerisation        | Docker, Azure Container Registry (ACR)                                     |
| Orchestration           | Azure Container Apps (KEDA scaling to zero)                                |
| CI/CD                   | GitHub Actions (tests, security scans, deployment)                         |
| Monitoring              | Azure Application Insights, Log Analytics, custom OpenTelemetry metrics    |
| Dashboards              | Grafana (queries Log Analytics)                                            |
| Testing                 | Pytest (52 tests, coverage >80%), Locust (load testing)                    |

## Repository Structure
.  
├── .github/workflows/ # CI/CD pipeline  
├── app/ # Backend FastAPI application  
│ ├── database.py # Qdrant + SecretManager  
│ ├── main.py # API endpoints  
│ └── telemetry.py # OpenTelemetry setup  
├── frontend/ # Streamlit UI  
│ └── app.py  
├── scraper/ # Web crawling & PII redaction  
│ ├── crawler.py  
│ ├── ingest.py  
│ ├── redactor.py  
│ └── reindex.py  
├── tests/ # Unit & integration tests (52 tests)  
│ ├── locustfile.py  
│ ├── test_api.py  
│ ├── test_crawler.py  
│ ├── test_database.py   
│ ├── test_ingest.py  
│ ├── test_redactor.py  
│ └── test_reindex.py  
├── infra/ # Terraform configuration  
│ ├── app-services.tf  
│ ├── infra-core.tf  
│ ├── provider.tf  
│ ├── security.tf  
│ ├── storage.tf  
│ └── variables.tf  
├── docker/ # Dockerfiles for backend & frontend  
├── demo-documents/ # Sample dummy documents  
├── adminOps/ # Utility scripts (dev only)  
├── Makefile # Automation for local development  
├── ARCHITECTURE.md # System architecture (Mermaid diagram)  
└── requirements.txt # Python dependencies  

## Getting Started

### Prerequisites

- [Azure subscription](https://azure.microsoft.com/en-us/free/) (student subscription for my works)
- [Terraform CLI](https://developer.hashicorp.com/terraform/downloads) (≥1.7.0)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (optional, for local container builds)
- Python 3.11+ with `pip`

### 1. Clone the repository

**Bash:**
```
git clone https://github.com/TheFeing/CouncilConnect-AI.git
cd CouncilConnect-AI
```

### 2. Set up environment variables (local development)
Create a .env file with:
```
GEMMA_API_KEY=your_google_gemma_api_key
QDRANT_URL=https://your-qdrant-cluster-url
QDRANT_API_KEY=your_qdrant_api_key
APPLICATIONINSIGHTS_CONNECTION_STRING=your_app_insights_conn_string   # optional for local
```

>Note: In production, all secrets are injected directly from Azure Key Vault using a system‑assigned managed identity. No secret values are stored in Terraform state or plaintext configuration files.

### 3. Install Python dependencies
**Bash:**
```
python -m venv venv
source venv/bin/activate      # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

### 4. Run tests
**Bash:**
```
make test
```
> All 52 tests should pass with coverage >80%.

### 5. Run locally (optional)
**Bash:**
```
uvicorn app.main:app_instance --reload --port 8000   # backend
streamlit run frontend/app.py                        # frontend
```

## Deployment (Azure)
All infrastructure and application code are deployed via GitHub Actions on every push to main. The pipeline:

1. Runs make lint and make test.
2. Scans dependencies with pip-audit and code with bandit.
3. Builds Docker images (backend & frontend) and pushes to ACR.
4. Runs terraform plan and, on main, terraform apply.
5. Updates the live Container Apps with the new images.

To deploy manually (for testing):  
**Bash:**
```
# Authenticate to Azure
az login
az account set --subscription <your-subscription-id>

# Deploy infrastructure
cd infra
terraform init
terraform apply -auto-approve

# Build and push images
make deploy-docker-backend
make deploy-docker-frontend
```

## Key Features
|Feature	|Implementation|
|---------|--------------|
Custom metric	|`pii.redactions.total` exported via OpenTelemetry to Application Insights|
Feature toggle	|`APP_VERSION` environment variable controls experimental UI (branching by abstraction)|
Fully automated CI/CD	|GitHub Actions builds, scans, tests, and deploys on every `main` push|
Scheduled patching	|Weekly cron trigger rebuilds images (immutable infrastructure)|
Dependency & SAST scanning	|`pip-audit` + `bandit` in CI pipeline
PII redaction	|Email, phone, health ID, NI‑style refs, dynamic name sweeping
Infrastructure as Code	|Terraform (resource group, Key Vault, ACR, Container Apps, budget, monitoring)|
Secure secret handling|	Secrets referenced directly from Key Vault using system‑assigned managed identity|
Durable disaster recovery	|Every ingested document (PDF/crawl) is backed up to Azure Blob Storage|
Rollback (MTTR)	|Container Apps revision mode `Multiple` - rollback in <2 minutes|
User stories & acceptance	|Three personas: director (cost + rollback), admin (ingestion), resident (speed + accuracy)|

## Monitoring
- Application Insights receives:
  - Standard metrics (CPU, memory, request rate)
  - Custom metric `pii.redactions.total`
  - Traces from the FastAPI app
- Log Analytics stores all logs and metrics (30‑day retention)
- Grafana visualises data from Log Analytics (custom dashboards)
- Budget alert (£10/month) prevents cost overruns

## Troubleshooting (Example)
**Issue:** `terraform plan` fails with `403 Forbidden` when reading Key Vault secrets.  

**Cause:** The dynamic role assignment `admin_access` used `data.azurerm_client_config.current.object_id`, which changed between local (developer) and pipeline (service principal) runs.  

**Fix:** Replaced dynamic principal with a fixed `var.developer_object_id` variable and granted the pipeline separate `Key Vault Secrets User` role. See `security.tf` and `variables.tf`.

## Contributing
This is a personal project for an apprenticeship assessment. Issues and suggestions are welcome via GitHub Issues.

## License
MIT - feel free to use and adapt for educational purposes.

## Acknowledgements
- [Salford City Council](https://www.salford.gov.uk/) - Use case inspiration
- [Google](https://ai.google.dev/) - Gemma 4 & Gemini embedding models
- [Qdrant](https://qdrant.tech/) - Vector database
- [Azure Container Apps](https://azure.microsoft.com/en-us/products/container-apps/) - Serverless hosting
- [Streamlit](https://streamlit.io/) - Rapid UI prototyping