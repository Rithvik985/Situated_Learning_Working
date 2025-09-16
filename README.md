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
- **Upload Server** (Port 8001): Handles file uploads and processing
- **Generation Server** (Port 8002): Manages assignment and rubric generation
- **Evaluation Server** (Port 8003): Handles student submission evaluation
- **Analytics Server** (Port 8004): Provides analytics and reporting APIs
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
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   │   ├── Analytics.jsx  # New analytics page
│   │   │   └── ...
│   │   ├── styles/        # CSS files
│   │   └── utils/         # Frontend utilities
│   ├── package.json       # Node.js dependencies
│   └── vite.config.js     # Vite configuration
├── start_*.py            # Server startup scripts
├── docker-compose.yml    # Database and MinIO setup
└── README.md            # This file
```

## 📋 Prerequisites

- **Python 3.9+**
- **Node.js 16+**
- **PostgreSQL 12+**
- **MinIO** (or compatible S3 service)
- **OpenAI API Key** (optional, for cloud LLM)
- **vLLM** (optional, for local LLM)

## 🚀 Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/spandaai/Situated_Learning.git
cd Situated_Learning
```

### 2. Database & Storage Setup
```bash
# Start PostgreSQL and MinIO containers
docker-compose up postgres minio -d

# Wait for services to be ready (about 30 seconds)
# Initialize database schema
python init.sql
```

### 3. Backend Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional dependencies for analytics
pip install reportlab
```

### 4. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Install additional dependencies for analytics
npm install chart.js react-chartjs-2
```

### 5. Start All Servers

#### Option A: Start Individual Servers (Recommended for Development)
```bash
# Terminal 1: Upload Server (Port 8001)
python start_upload_server.py

# Terminal 2: Generation Server (Port 8002)
python start_generation_server.py

# Terminal 3: Evaluation Server (Port 8003)
python start_evaluation_server.py

# Terminal 4: Analytics Server (Port 8004)
python start_analytics_server.py

# Terminal 5: Frontend (Port 3000)
cd frontend
npm run dev
```

#### Option B: Quick Start Scripts
```bash
# Start all backend servers
python start_all_servers.py

# Start frontend (in another terminal)
cd frontend
npm run dev
```

### 6. Access Application
- **Frontend**: http://localhost:3000
- **Upload API**: http://localhost:8001/docs
- **Generation API**: http://localhost:8002/docs
- **Evaluation API**: http://localhost:8003/docs
- **Analytics API**: http://localhost:8004/docs
- **MinIO Console**: http://localhost:9001 (admin/password1234)

## 🔧 Development

### Environment Variables
The application uses environment variables for configuration. Create a `.env` file in the root directory:

```env
# Database Configuration
DATABASE_URL=postgresql://admin:password1234@localhost:5432/situated_learning_db

# MinIO Configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=password1234
MINIO_BUCKET=situated-learning
MINIO_SECURE=false

# LLM Configuration
USE_OPENAI=false
OPENAI_API_KEY=your_openai_api_key

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://frontend:3000
```

### Server Architecture
The application uses a microservices architecture with separate servers for different functionalities:

- **Upload Server** (Port 8001): Handles file uploads and processing
- **Generation Server** (Port 8002): Manages assignment and rubric generation  
- **Evaluation Server** (Port 8003): Handles student submission evaluation
- **Analytics Server** (Port 8004): Provides analytics and reporting APIs

### Development Tips
- Each server can be started independently for focused development
- Use the individual startup scripts for debugging specific components
- The frontend automatically connects to all backend servers
- Database and MinIO are shared across all servers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request
