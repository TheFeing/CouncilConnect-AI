# CouncilConnect AI Architecture
```Mermaid
graph TB
    subgraph "Development & CI/CD"
        Dev["💻 System Admin / Developer (VS Code, Git, Make)"]
        GitHub[("GitHub Repository")]
        Pipeline["⚙️ GitHub Actions Pipeline (.github/workflows/pipeline.yml)"]
        Dev -->|git push| GitHub
        GitHub -->|trigger| Pipeline
    end

    subgraph "Azure Cloud"
        subgraph "Container App Environment"
            Env["🌍 Container App Environment (env-councilconnect-ai)"]
            subgraph "Compute Tier"
                FrontendApp["🌐 Frontend Container App (ui-councilconnect-ai)"]
                BackendApp["⚙️ Backend Container App (app-councilconnect-ai)"]
            end
        end

        subgraph "Storage & Secrets"
            ACR["📦 Azure Container Registry (acrcouncilconnectai)"]
            KeyVault["🔐 Azure Key Vault (kv-councilconnect-ai)"]
            Qdrant[("🗄️ Qdrant Vector DB (council_knowledge)")]
            Identity["👤 User-Assigned Identity (id-acr-puller)"]
            BlobStorage["☁️ Blob Storage Cool Tier (sacouncilconnect-knowledge-base-backups)"]
        end

        subgraph "Observability & Governance"
            AppInsights["📊 Application Insights (ai-councilconnect-ai)"]
            LogAnalytics["📜 Log Analytics Workspace (logs-councilconnect-ai)"]
            Grafana["📈 Grafana Dashboards"]
            Budget["💰 Consumption Budget (10 GBP monthly limit)"]
        end
    end

    Pipeline -->|build & push image| ACR
    Pipeline -.->|read secrets via Terraform| KeyVault
    Pipeline -.->|Terraform provision| Env
    Pipeline -.->|Terraform provision| Identity

    Identity -->|assigned to| FrontendApp
    Identity -->|assigned to| BackendApp
    ACR -->|pull via identity| FrontendApp
    ACR -->|pull via identity| BackendApp

    FrontendApp -->|HTTP requests| BackendApp

    BackendApp -->|read/write vectors| Qdrant
    BackendApp -->|fetch secrets| KeyVault
    BackendApp -->|send telemetry| AppInsights
    BackendApp -->|upload JSON backup| BlobStorage

    AppInsights -->|logs/metrics| LogAnalytics
    Grafana -->|query| LogAnalytics
    Grafana -.->|query| AppInsights

    Budget -.->|monitors spending| Env
```