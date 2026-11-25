# Agricultural Data Sources & Provenance Policy

KrishiMitra strictly restricts knowledge-base answers to verified, approved agricultural publications. No synthetic or unverified advice is presented as authoritative guidance.

## 1. Indexed Knowledge Sources (`data/raw_pdfs/`)

| Document | Publisher | URL | Topics / Crops | Approval |
|---|---|---|---|---|
| `cotton_and_soybean_advisory_icarcicr.pdf` | ICAR-CICR Nagpur & MPKV Rahuri | https://cicr.org.in | Cotton yellow spots, sucking pests, Alternaria blight, Soybean | Approved |
| `wheat_and_paddy_cultivation_handbook.pdf` | ICAR-IIWBR & MPKV Rahuri | https://icar.org.in | Wheat yellowing, yellow rust, NPK, CRI irrigation, Paddy | Approved |
| `crop_protection_and_ipm_manual.pdf` | Directorate of Plant Protection (DPPQS) & KVK | https://ppqs.gov.in | IPM biological control, Neem/NSKE, ETL thresholds | Approved |
| `government_agricultural_schemes_guide.pdf` | Ministry of Agriculture & Farmers Welfare, GoI | https://pmkisan.gov.in | PM-KISAN, PMFBY, KCC, Soil Health Card | Approved |

## 2. Live Data APIs (Never Stored in Static Vector Store)

| Service | Provider | Data Type | Refresh / Cache Policy |
|---|---|---|---|
| **Weather & Advisories** | Open-Meteo (Primary free live) / OpenWeatherMap | Current weather, rainfall, 3-day forecast | 15-minute TTL cache; tagged `is_live` & timestamped |
| **APMC Mandi Prices** | Agmarknet (`api.data.gov.in`) | Min, Max, Modal prices per quintal | 30-minute TTL cache; explicit `credentials_required` when unconfigured |

## 3. Approval & Governance Workflow
1. New PDFs uploaded via the Admin Console can be marked `pending` or `approved`.
2. Retrieval filters strictly to `approval_status == "approved"`.
3. Administrators can approve, reject, or delete documents (which removes vectors and rebuilds FAISS).
