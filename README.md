# Situated Learning System

A comprehensive web application for generating situational assignments, evaluating student submissions, and managing academic content with AI-powered insights.

## 🚀 Features

### 📤 Upload & Processing
- **Upload Past Assignments**: Build reference corpus with PDF/DOCX support
- **Automatic Processing**: AI-powered text extraction and topic tagging
- **MinIO Storage**: Scalable cloud storage for files and extracted content

### 🎯 Assignment Generation
- **Situational Assignments**: Generate up to 10 industry-relevant assignments per request
- **Smart Course Selection**: Course name and code auto-suggestion
- **Rubric Generation**: Detailed rubrics aligned to outcomes and taxonomy levels
- **Edit & Revision**: Inline editing with version tracking and reasoning capture

### 🔍 Evaluation & Assessment
- **Multi-format Support**: Evaluate PDF/DOCX student submissions
- **OCR Processing**: Handwritten/scan text extraction with layout detection
- **AI-Powered Scoring**: Auto-evaluate against rubrics with criterion-level feedback
- **Quality Assurance**: Ambiguity detection and faculty review workflows

### 📊 Analytics & Reporting
- **Usage Analytics**: Track assignment generation and modification rates
- **Content Analytics**: Monitor rubric editing and course-wise statistics
- **Learning Analytics**: Student submission and evaluation insights
- **PDF Reports**: Export comprehensive analytics reports

## 🏗️ Architecture

### Backend (FastAPI) - Multi-Server Architecture
- **Upload Server** (Port 8020): Handles file uploads and processing
- **Generation Server** (Port 8021): Manages assignment and rubric generation
- **Evaluation Server** (Port 8022): Handles student submission evaluation
- **Analytics Server** (Port 8023): Provides analytics and reporting APIs
- **PostgreSQL**: Primary database for metadata and relationships
- **MinIO**: Object storage for files and content
- **SQLAlchemy**: ORM for database operations
- **LLM Integration**: OpenAI and vLLM support for AI analysis

### Frontend (React)
- **React 18**: Modern UI framework
- **Vite**: Fast build tool
- **React Router**: Client-side routing
- **CSS Modules**: Scoped styling
- **FontAwesome**: Icon library
- **Chart.js**: Data visualization for analytics

## 🛠️ Technology Stack

### Backend
- **Python 3.9+**
- **FastAPI**
- **PostgreSQL**
- **MinIO**
- **SQLAlchemy**
- **PyMuPDF** (PDF processing)
- **Pillow** (Image processing)
- **OpenAI API** / **vLLM** (LLM services)

### Frontend
- **Node.js 16+**
- **React 18**
- **Vite**
- **React Router**
- **CSS Modules**

### Infrastructure
- **Docker** (containerization)
- **Docker Compose** (orchestration)

## 📋 Prerequisites

- **Python 3.9+**
- **Node.js 16+**
- **PostgreSQL 12+**
- **MinIO** (or compatible S3 service)
- **OpenAI API Key** (optional, for cloud LLM)
- **vLLM** (optional, for local LLM)

## 🚀 Quick Start

### For First-Time Users (Windows) 🪟

1. **Clone and Setup Environment**
   ```cmd
   git clone <repository-url>
   cd Situated_Learning
   
   # Setup backend environment
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   cd ..
   
   # Setup frontend environment
   cd frontend
   npm install
   cd ..
   ```

2. **Setup Environment Variables**
   ```cmd
   python setup_local_env.py
   ```

3. **Start Databases & Initialize**
   ```cmd
   .\setup_database.bat
   ```
   *This will start PostgreSQL and MinIO containers and initialize the database structure*

4. **Start Application**
   ```cmd
   .\start_separated_servers.bat
   ```

5. **Access Application**
   - **Frontend**: http://localhost:3000
   - **MinIO Console**: http://localhost:9001 (admin/password1234)

### For First-Time Users (Linux/macOS) 🐧

1. **Clone and Setup Environment**
   ```bash
   git clone <repository-url>
   cd Situated_Learning
   
   # Setup backend environment
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   cd ..
   
   # Setup frontend environment
   cd frontend
   npm install
   cd ..
   ```

2. **Setup Environment Variables**
   ```bash
   python setup_local_env.py
   ```

3. **Start Databases**
   ```bash
   docker-compose up postgres minio -d
   ```

4. **Initialize Database Structure**
   ```bash
   python setup_database.py
   ```

5. **Start Application**
   ```bash
   chmod +x start_separated_servers.sh
   ./start_separated_servers.sh
   ```

6. **Access Application**
   - **Frontend**: http://localhost:3000
   - **MinIO Console**: http://localhost:9001 (admin/password1234)

### Option 1: Local Development (Recommended for Development)

#### Prerequisites
- **Python 3.9+**
- **Node.js 16+**
- **PostgreSQL 12+** (running locally on port 5432)
- **MinIO** (running locally on port 9000)

#### 1. Clone Repository
```bash
git clone <repository-url>
cd Situated_Learning
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables for local development
python ../setup_local_env.py
# This will automatically create .env with localhost configurations
```

#### 3. Database Setup
```bash
# Start PostgreSQL and MinIO containers
docker-compose up postgres minio -d

# Initialize database and bucket structure
python setup_database.py
```

#### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install
```

#### 5. Start All Services

**Windows:**
```cmd
# From project root
.\start_separated_servers.bat
```

**Linux/macOS:**
```bash
# From project root
chmod +x start_separated_servers.sh
./start_separated_servers.sh
```

#### 6. Access Application
- **Frontend**: http://localhost:3000
- **Upload API**: http://localhost:8020
- **Generation API**: http://localhost:8021
- **Evaluation API**: http://localhost:8022
- **Analytics API**: http://localhost:8023
- **API Documentation**: Available at each server's `/docs` endpoint

### Option 2: Docker Deployment (Recommended for Production)

#### 1. Clone Repository
```bash
git clone <repository-url>
cd Situated_Learning
```

#### 2. Start All Services with Docker Compose
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### 3. Access Application
- **Frontend**: http://localhost:3000
- **Upload API**: http://localhost:8020
- **Generation API**: http://localhost:8021
- **Evaluation API**: http://localhost:8022
- **Analytics API**: http://localhost:8023
- **MinIO Console**: http://localhost:9001 (admin/password1234)

## ⚙️ Configuration

### Environment Variables (.env)

#### For Local Development
```env
# Server Configuration
HOST=0.0.0.0
DEBUG=false
LOG_LEVEL=INFO

# Database (Local PostgreSQL)
DATABASE_URL=postgresql://admin:password1234@localhost:5432/situated_learning_db

# MinIO Configuration (Local MinIO)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password1234
MINIO_BUCKET=situated-learning
MINIO_SECURE=false

# LLM Configuration
USE_OPENAI=false  # Set to true for OpenAI, false for vLLM
OPENAI_API_KEY=your_openai_api_key  # Only needed if USE_OPENAI=true

# File Processing
MAX_FILE_SIZE=50MB
UPLOAD_DIR=./uploads
OUTPUT_DIR=./outputs
TEMP_DIR=./temp

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://frontend:3000,http://localhost:8080
```

#### For Docker Deployment
```env
# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# Database (Docker container)
DATABASE_URL=postgresql://admin:password1234@postgres:5432/situated_learning_db

# MinIO Configuration (Docker container)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password1234
MINIO_BUCKET=situated-learning
MINIO_SECURE=false

# LLM Configuration
USE_OPENAI=false  # Set to true for OpenAI, false for vLLM
OPENAI_API_KEY=your_openai_api_key  # Only needed if USE_OPENAI=true

# File Processing
MAX_FILE_SIZE=50MB
UPLOAD_DIR=./uploads
OUTPUT_DIR=./outputs
TEMP_DIR=./temp

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://frontend:3000,http://localhost:8080
```

### LLM Configuration

The system supports both OpenAI and local vLLM:

#### OpenAI Setup
```env
USE_OPENAI=true
OPENAI_API_KEY=sk-your-api-key-here
```

#### vLLM Setup
```env
USE_OPENAI=false
```

Start vLLM services:
```bash
# Text model
vllm serve ibnzterrell/Meta-Llama-3.3-70B-Instruct-AWQ-INT4 --port 8012

# Vision model
vllm serve Qwen/Qwen2.5-VL-32B-Instruct-AWQ --port 8011
```

**Note**: When running vLLM locally and the application in Docker containers, the containers will automatically use `host.docker.internal` to access your local vLLM services. The docker-compose.yml is configured to use:
- `LLM_BASE_URL=http://host.docker.internal:8012/v1`
- `VISION_LLM_BASE_URL=http://host.docker.internal:8011/v1`

## 📁 Project Structure

```
Situated_Learning/
├── backend/
│   ├── database/           # Database models and connections
│   ├── routers/           # API endpoints
│   ├── servers/           # Multi-server architecture
│   │   ├── upload_server.py
│   │   ├── generation_server.py
│   │   ├── evaluation_server.py
│   │   └── analytics_server.py
│   ├── services/          # Business logic
│   ├── storage/           # MinIO client
│   ├── utils/             # Utilities and helpers
│   ├── config/            # Configuration management
│   ├── Dockerfile         # Main backend Dockerfile
│   ├── Dockerfile.upload  # Upload server Dockerfile
│   ├── Dockerfile.generation  # Generation server Dockerfile
│   ├── Dockerfile.evaluation  # Evaluation server Dockerfile
│   ├── Dockerfile.analytics   # Analytics server Dockerfile
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── config/        # API configuration
│   │   ├── styles/        # CSS files
│   │   └── utils/         # Frontend utilities
│   ├── package.json       # Node.js dependencies
│   ├── vite.config.js     # Vite configuration
│   └── Dockerfile         # Frontend Dockerfile
├── database/
│   └── init.sql          # Database initialization
├── start_*.py            # Server startup scripts
├── docker-compose.yml    # Docker orchestration
└── README.md            # This file
```

## 🗄️ Database Management

### Database Setup and Initialization

The system uses two database components:

#### PostgreSQL Database
- **Purpose**: Stores metadata, assignments, submissions, evaluations, and analytics
- **Initialization**: Automatically handled by `setup_database.py`
- **Schema**: Defined in `database/init.sql`

#### MinIO Object Storage
- **Purpose**: Stores uploaded files, generated assignments, and evaluation reports
- **Bucket Structure**: Created automatically when files are uploaded
- **Structure**:
  ```
  situated-learning/
  ├── past-assignments/
  │   └── {assignment_id}/{filename}
  ├── generated-assignments/
  │   └── {assignment_id}/{filename}
  └── submissions/
      └── {submission_id}/{filename}
  ```

### Database Setup Commands

```bash
# Start database containers
docker-compose up postgres minio -d

# Initialize database and bucket structure
python setup_database.py

# Initialize only MinIO buckets
python setup_minio_buckets.py
```

### Database Access

#### PostgreSQL
- **Host**: localhost:5432
- **Database**: situated_learning_db
- **Username**: admin
- **Password**: password1234

#### MinIO Console
- **URL**: http://localhost:9001
- **Username**: admin
- **Password**: password1234

### Troubleshooting

#### Database Connection Issues
```bash
# Check if containers are running
docker ps

# View PostgreSQL logs
docker logs situated_learning_postgres

# View MinIO logs
docker logs situated_learning_minio

# Restart database containers
docker-compose restart postgres minio
```

#### Reset Database
```bash
# Stop containers
docker-compose down

# Remove volumes (WARNING: This will delete all data)
docker volume rm situated_learning_postgres_data situated_learning_minio_data

# Start fresh
docker-compose up postgres minio -d
python setup_database.py
```

## 🔧 Development

The application uses a microservices architecture with separated servers:

#### Start All Services
**Windows:**
```bash
start_separated_servers.bat
```

**Linux/macOS:**
```bash
chmod +x start_separated_servers.sh
./start_separated_servers.sh
```

#### Individual Server Development

**Upload Server (Port 8020):**
```bash
cd backend
python servers/upload_server.py
```

**Generation Server (Port 8021):**
```bash
cd backend
python servers/generation_server.py
```

**Evaluation Server (Port 8022):**
```bash
cd backend
python servers/evaluation_server.py
```

**Analytics Server (Port 8023):**
```bash
cd backend
python servers/analytics_server.py
```

**Frontend Development:**
```bash
cd frontend
npm run dev
```

### Database Migrations
```bash
cd backend
python setup_database.py
```

### Testing
```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

## 🐳 Docker Deployment

### Using Docker Compose
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Individual Services
```bash
# Upload server only
docker build -t situated-learning-upload ./backend -f backend/Dockerfile.upload
docker run -p 8020:8020 situated-learning-upload

# Generation server only
docker build -t situated-learning-generation ./backend -f backend/Dockerfile.generation
docker run -p 8021:8021 situated-learning-generation

# Evaluation server only
docker build -t situated-learning-evaluation ./backend -f backend/Dockerfile.evaluation
docker run -p 8022:8022 situated-learning-evaluation

# Analytics server only
docker build -t situated-learning-analytics ./backend -f backend/Dockerfile.analytics
docker run -p 8023:8023 situated-learning-analytics

# Frontend only
docker build -t situated-learning-frontend ./frontend
docker run -p 3000:3000 situated-learning-frontend
```

### DOCX → PDF Conversion (Linux/Docker)

- The backend containers now include LibreOffice and common fonts, enabling reliable, layout-preserving DOCX to PDF conversion in headless mode.
- No additional setup is required when running via Docker Compose.

### DOCX → PDF Conversion (Windows)

- Install LibreOffice or Microsoft Word locally if you run the backend without Docker.
- Ensure `libreoffice` or `soffice` is available on PATH. The app auto-detects and prefers LibreOffice for highest fidelity.
- Alternatively, install `docx2pdf` and Microsoft Word (Windows-only) if you prefer Word-based conversion.

### Fonts and Layout Fidelity

- To preserve layout, ensure required fonts are available. The Docker image ships with DejaVu, Liberation, and Microsoft core fonts. For custom institutional fonts, mount them into the container and register via fontconfig:

```bash
docker run -v /path/to/fonts:/usr/share/fonts/truetype/custom:ro \
  --entrypoint bash situated-learning-upload -lc "fc-cache -f && fc-list | wc -l"
```

If you notice layout deviations, add the missing fonts to the container.

## 📊 API Endpoints

The application uses separated servers, each with its own API endpoints:

### Upload Server (Port 8020)
- `POST /uploadAss/past-assignments` - Upload past assignments
- `GET /uploadAss/assignments` - List uploaded assignments
- `GET /uploadAss/assignments/{id}` - Get assignment details
- **Documentation**: http://localhost:8020/docs

### Generation Server (Port 8021)
- `POST /generation/generate` - Generate assignments
- `GET /generation/status` - Get generation status
- `POST /generation/rubric` - Generate rubrics
- **Documentation**: http://localhost:8021/docs

### Evaluation Server (Port 8022)
- `GET /evaluation/courses` - Get courses for evaluation
- `POST /evaluation/submissions/upload` - Upload student submissions
- `POST /evaluation/evaluate` - Evaluate submissions
- `GET /evaluation/assignments/{id}/report` - Download evaluation report
- **Documentation**: http://localhost:8022/docs

### Analytics Server (Port 8023)
- `GET /analytics/overview` - Get analytics overview
- `GET /analytics/usage` - Get usage statistics
- `GET /analytics/content` - Get content analytics
- `GET /analytics/learning` - Get learning analytics
- **Documentation**: http://localhost:8023/docs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
