graph TB
    subgraph "Development & CI/CD"
        Dev[💻 System Admin / Developer<br/>VS Code, Git, Make]
        GitHub[(GitHub Repository)]
        Pipeline[⚙️ GitHub Actions Pipeline<br/>.github/workflows/pipeline.yml]
        Dev -->|git push| GitHub
        GitHub -->|trigger| Pipeline
    end

    subgraph "Azure Cloud"
        subgraph "Container App Environment"
            Env[🌍 Container App Environment<br/>env-councilconnect-ai]
            subgraph "Compute Tier"
                FrontendApp[🌐 Frontend Container App<br/>ui-councilconnect-ai]
                BackendApp[⚙️ Backend Container App<br/>app-councilconnect-ai]
            end
        end

        subgraph "Storage & Secrets"
            ACR[📦 Azure Container Registry<br/>acrcouncilconnectai]
            KeyVault[🔐 Azure Key Vault<br/>kv-councilconnect-ai]
            Qdrant[(🗄️ Qdrant Vector DB<br/>council_knowledge)]
            Identity[👤 User-Assigned Identity<br/>id-acr-puller]
        end

        subgraph "Observability & Governance"
            AppInsights[📊 Application Insights<br/>ai-councilconnect-ai]
            LogAnalytics[📜 Log Analytics Workspace<br/>logs-councilconnect-ai]
            Grafana[📈 Grafana Dashboards]
            Budget[💰 Consumption Budget<br/>£10 monthly limit]
        end
    end

    %% CI/CD interactions
    Pipeline -->|build & push image| ACR
    Pipeline -.->|read secrets (Terraform)| KeyVault
    Pipeline -.->|Terraform provision| Env
    Pipeline -.->|Terraform provision| Identity

    %% Identity for ACR pull
    Identity -->|assigned to| FrontendApp
    Identity -->|assigned to| BackendApp
    ACR -->|pull via identity| FrontendApp
    ACR -->|pull via identity| BackendApp

    %% Frontend –> Backend
    FrontendApp -->|HTTP requests| BackendApp

    %% Backend dependencies
    BackendApp -->|read/write vectors| Qdrant
    BackendApp -->|fetch secrets (optional)| KeyVault
    BackendApp -->|send telemetry| AppInsights

    %% Monitoring flows
    AppInsights -->|logs/metrics| LogAnalytics
    Grafana -->|query| LogAnalytics
    Grafana -.->|optional query| AppInsights

    %% Budget alert (no direct data flow, but highlights governance)
    Budget -.->|monitors spending| Env