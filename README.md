# EchoList

EchoList is a voice-first productivity and personal memory assistant designed to make capturing, recalling, and sharing thoughts, tasks, and reminders effortless.

## Features

- **Voice-First Interaction**: Speak or type notes in real-time with AI transcription
- **Member Tagging & Permissions**: Collaborate with family, friends, and colleagues with customized access levels
- **Modular & Customizable Sections**: Create personalized sections for different aspects of your life
- **Smart Organization**: AI-driven organization and retrieval of your notes and tasks
- **Social Collaboration**: Share and collaborate on lists with trusted connections

## Technical Stack

- **Backend**: Python FastAPI
- **Database**: PostgreSQL
- **Environment**: Conda
- **Containerization**: Docker
- **Authentication**: JWT
- **AI Components**: Speech-to-text, vector embeddings for semantic search

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Conda (for local development)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/echolist.git
   cd echolist
   ```

2. Create and activate a Conda environment:
   ```bash
   conda create -n echolist python=3.10
   conda activate echolist
   pip install -r requirements.txt
   ```

3. Start the PostgreSQL database:
   ```bash
   docker-compose up -d
   ```

4. Run database migrations:
   ```bash
   # Initialize Alembic (first time only)
   alembic init migrations
   
   # Create a new migration
   alembic revision --autogenerate -m "Initial migration"
   
   # Apply migrations to the database
   alembic upgrade head
   ```

5. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

6. Access the API documentation:
   ```
   http://localhost:8000/docs
   ```

## Project Structure

```
echolist/
├── app/
│   ├── api/           # API endpoints organized by feature
│   ├── core/          # Core application components
│   ├── db/            # Database connection and migrations
│   ├── models/        # Database models
│   ├── schemas/       # Pydantic schemas for request/response validation
│   ├── services/      # Business logic
│   ├── utils/         # Utility functions
├── docker/            # Docker configuration files
├── requirements.txt   # Python dependencies
├── docker-compose.yml # Docker services configuration
├── main.py            # Application entry point
```

## Database Schema

The application uses the following database tables:

- **Users**: User account information and preferences
- **Connections**: Relationships between users (Family, Friend, Colleague)
- **Sections**: Customizable modules for organizing content
- **SectionAccess**: Permission settings for sections
- **Items**: Notes, tasks, and reminders with metadata

## API Endpoints

- **Auth**: `/api/auth/login`, `/api/auth/register`
- **Users**: `/api/users/`
- **Connections**: `/api/connections/`
- **Sections**: `/api/sections/`
- **Items**: `/api/items/`

## License

[MIT License](LICENSE)
