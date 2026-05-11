# Tools and Technologies Used - 8 Key Points

## 1. React & Vite (Frontend Framework & Build Tool)

React is a JavaScript library for building user interfaces with reusable components and efficient state management. Vite is a modern build tool that provides fast development server startup and optimized production builds. Together, they enable rapid frontend development with hot module replacement (HMR) for instant feedback during coding. React's component-based architecture makes the codebase maintainable and scalable, while Vite's fast build process improves developer productivity.

---

## 2. Flask & Python (Backend Framework & Language)

Flask is a lightweight Python web framework perfect for building REST APIs. Python's simplicity and extensive libraries make it ideal for backend development. Flask handles HTTP routing, request processing, and response generation. Python's rich ecosystem provides libraries for PDF processing, database management, and API integration. The combination enables rapid backend development with clean, readable code.

---

## 3. SQLite (Database)

SQLite is a file-based relational database that requires no server setup or configuration. It's perfect for small to medium applications and provides ACID compliance for data integrity. SQLite stores user accounts, chat messages, conversation history, and manual metadata. The database is lightweight, portable, and can be easily backed up by copying a single file. It's ideal for deployment on resource-constrained environments like Render's free tier.

---

## 4. BM25 Algorithm (Search & Retrieval)

BM25 is a probabilistic ranking function used for full-text search and information retrieval. It ranks documents based on term frequency, inverse document frequency, and document length. BM25 is lightweight (100KB memory), fast, and effective for technical documentation search. It's implemented using the rank-bm25 Python library and forms the core of the RAG pipeline for retrieving relevant manual chunks based on user queries.

---

## 5. Groq API (Audio Transcription)

Groq API provides real-time speech-to-text transcription capabilities. It converts audio recordings from the browser into text, enabling hands-free voice input for technicians. The API is integrated into the backend's `/api/chat/transcribe` endpoint. Groq's fast processing ensures minimal latency between recording and transcription, providing a smooth user experience. API credentials are securely stored in environment variables.

---

## 6. Tailwind CSS (Styling & UI Framework)

Tailwind CSS is a utility-first CSS framework that enables rapid UI development with pre-built classes. It provides responsive design capabilities, dark mode support, and consistent styling across the application. Tailwind's utility classes make it easy to create professional-looking interfaces without writing custom CSS. The framework ensures responsive design that works on mobile, tablet, and desktop devices.

---

## 7. Render & Vercel (Cloud Deployment Platforms)

Render hosts the Flask backend with 512MB RAM, persistent disk storage, and automatic scaling. Vercel hosts the React frontend with global CDN distribution, automatic HTTPS, and optimized SPA routing. Both platforms offer free tiers suitable for development and small production deployments. Render provides Linux container environment for Python applications, while Vercel specializes in optimized hosting for React applications. Both support automatic deployments from GitHub.

---

## 8. GitHub & Git (Version Control & Collaboration)

Git is a distributed version control system that tracks code changes and enables collaboration. GitHub is a cloud-based Git repository hosting service. GitHub provides secret scanning to prevent accidental exposure of API keys and sensitive credentials. The repository serves as the single source of truth for all code. GitHub Actions can be configured for automated testing and deployment. Git's branching and merging capabilities enable parallel development and code review workflows.

---

## Technology Stack Summary

| Category | Technology | Purpose |
|----------|-----------|---------|
| Frontend | React, Vite, Tailwind CSS | User interface and styling |
| Backend | Flask, Python | REST API and business logic |
| Database | SQLite | Data persistence |
| Search | BM25 Algorithm | Information retrieval |
| APIs | Groq API | Audio transcription |
| Deployment | Render, Vercel | Cloud hosting |
| Version Control | GitHub, Git | Code management |
| Build Tools | Vite, pip | Development and dependency management |

