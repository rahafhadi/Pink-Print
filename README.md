# Pink Print - An Arabic AI-Powered Breast Health Awareness and Follow-Up
Project directory: Miria

# About Pink Print:
    Pink Print is an AI-powered breast health web application designed to support breast health awareness, personal tracking, breast cancer risk assessment, and access to reliable medical information.

    The project combines traditional medical risk assessment tools with Retrieval-Augmented Generation (RAG) to provide users with educational information grounded in a curated medical knowledge base.

    Important: pink print is an educational and awareness-support tool. It is not a diagnostic system and does not replace professional medical evaluation, clinical screening, or medical advice.

# Table of Contents

- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [AI Architecture](#ai-architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [How the RAG System Works](#how-the-rag-system-works)
- [Patient Data Integration](#patient-data-integration)
- [Installation and Setup](#installation-and-setup)
- [Running the Application](#running-the-application)
- [Medical Safety and Limitations](#medical-safety-and-limitations)
- [Privacy and Security](#privacy-and-security)
- [Development Status](#development-status)

# Project Overview

    Breast health awareness and access to reliable medical information are important components of early medical evaluation.

    pink print aims to make breast health information more accessible through a web-based application that brings together:

       - Breast cancer risk assessment.
       - Breast self-examination tracking.
       - Medical educational resources.
       - An AI-powered medical chatbot.
       - Personalized context based on user-recorded information, when explicitly authorized.

    The system is designed to distinguish between established medical knowledge, calculated risk estimates, and user-recorded observations.

# Features:
1. Breast Cancer Risk Assessment

    pink print includes a Python implementation of the Gail Model to estimate a woman's risk of developing invasive breast cancer over a defined period.

    The assessment uses the model's supported input variables and produces a statistical risk estimate.

    The result is intended for educational and risk-awareness purposes. It is not a diagnosis or a prediction of whether an individual will develop cancer.

2. Breast Self-Examination Tracker

    A personal tracking feature that allows users to record breast observations over time.

    Users can document:

        - Breast changes and symptoms.
        - Pain or discomfort.
        - Lumps or unusual findings.
        - Changes in the appearance of the breast or nipple.
        - Dates of recorded observations.

    The tracker helps users maintain a record that may be useful during a medical consultation.

    It does not determine whether a finding is benign or malignant.

3. Medical AI Chatbot

    An AI-powered chatbot designed to answer breast health questions using retrieved information from the project's medical knowledge base.

    The chatbot uses:

        - Local medical document retrieval.
        - Semantic search.
        - Context-aware response generation.
        - Source and page references for retrieved materials.

4. Medical Knowledge Base

    A collection of medical PDF references covering topics such as:

        - Breast cancer.
        - Breast cancer risk factors.
        - Gail Model.
        - Benign breast conditions.
        - Breast self-examination.

    The knowledge base is processed locally to extract text, divide it into smaller chunks, and generate embeddings for semantic retrieval.

5. Patient Context Integration

    With explicit user consent, the chatbot can use selected information recorded in the application's database, such as:

        - Previous Gail Model assessment results.
        - Recent breast self-examination tracker entries.

    Patient-specific data is handled separately from the public medical knowledge base.

# AI Architecture:
    pink print uses a Retrieval-Augmented Generation (RAG) architecture.

    1. Offline Knowledge Preparation Pipeline
        This pipeline prepares the medical knowledge base before runtime.

            ```mermaid
            flowchart TD
            A["Medical PDF References"] --> B["PDF Discovery"]
            B --> C["PyMuPDF Text Extraction"]
            C --> D["extracted_text.json"]
            D --> E["Text Chunking"]
            E --> F["chunks.json"]
            F --> G["Multilingual E5 Small"]
            G --> H["Passage Embeddings"]
            H --> I["Reference Cleaning"]
            I --> J["embeddings_clean.npy"]
            I --> K["chunk_metadata_clean.json"]

            style A fill:#F5DCE6,stroke:#914664,color:#49333E
            style J fill:#F5DCE6,stroke:#914664,color:#49333E
            style K fill:#F5DCE6,stroke:#914664,color:#49333E
            ```

    2. Runtime RAG Pipeline 
        This pipeline describes how pink print processes user questions and generates context-aware responses.
            
            ```mermaid
            flowchart TD
            A["User Question"] --> B["Flask Backend"]
            B --> C["Authentication and Ownership Validation"]
            C --> D["Load Conversation History"]
            D --> E["Local E5 Query Embedding"]
            E --> F["NumPy Similarity Search"]
            F --> G["Top 5 Relevant Chunks"]

            H["SQLite Patient Records"] --> I{"Patient Data Consent?"}
            I -->|Yes| J["Retrieve Authorized Patient Context"]
            I -->|No| K["Patient Context Excluded"]

            G --> L["Context Assembly"]
            J --> L
            K --> L
            D --> L

            L --> M["Groq API - LLM Generation"]
            M --> N["AI Response"]
            M --> O["Retrieved Source References"]

            N --> P["Save Assistant Message in SQLite"]
            O --> Q["Return Sources to Frontend"]
            P --> R["Frontend Response"]
            Q --> R

            style A fill:#F5DCE6,stroke:#914664,color:#49333E
            style M fill:#D88EAB,stroke:#914664,color:#49333E
            style R fill:#F5DCE6,stroke:#914664,color:#49333E
            ```

    3. Gail Model – Independent Risk Assessment
        The Gail Model is calculated independently using Python.

            ```mermaid
            flowchart TD
            A["User Risk Assessment Inputs"] --> B["Flask Backend"]
            B --> C["gail_model.py"]
            C --> D["Gail Model Calculation"]
            D --> E["Risk Estimate"]
            E --> F["Store Assessment in SQLite"]
            F --> G["Display Result to User"]

            style C fill:#F5DCE6,stroke:#914664,color:#49333E
            style E fill:#D88EAB,stroke:#914664,color:#49333E
            ```

    Instead of relying exclusively on the language model's pre-existing knowledge, the system retrieves relevant passages from its curated medical references and provides them as context for answer generation.

    The architecture consists of two main processes:
        **Offline Knowledge Preparation**

            1. Medical PDF collection.
            2. Text extraction using PyMuPDF.
            3. Text chunking.
            4. Local embedding generation.
            5. Storage of embeddings and source metadata.

        ** Runtime Question Answering**

               1. User submits a question.
               2. Flask handles the request and authentication.
               3. The local embedding model converts the question into a vector.
               4. NumPy performs similarity search against stored medical embeddings.
               5. Relevant text chunks are retrieved.
               6. Authorized patient context may be added when consent is enabled.
               7. Groq API generates the response using the supplied context.
               8. The response and retrieved source references are stored and returned to the frontend.

# Technology Stack:
    Component ______ Technology

    Backend   ______  Python, Flask

    Frontend  ______  HTML, CSS, JavaScript
 
    Database  ______  SQLite

    Risk Assessment ______ Python – Gail Model

    PDF Text Extraction ______ PyMuPDF

    Text Embeddings ______ SentenceTransformers

    Embedding Model ______ intfloat multilingual-e5-small

    Vector Similarity Search ______ NumPy

    AI Response Generation ______ Groq API 

    Medical Knowledge Retrieval ______ RAG

# Project Structure:
    miria/
    │
    ├── app.py
    ├── gail_model.py
    ├── database.db
    ├── requirements.txt
    ├── .env.example
    ├── .gitignore
    ├── README.md
    │
    ├── chatbot/
    │   ├── __init__.py
    │   ├── database.py
    │   ├── routes.py
    │   ├── ingest.py
    │   ├── chunking.py
    │   ├── test_embeddings.py
    │   ├── create_embeddings.py
    │   ├── test_retrieval.py
    │   └── patient_context.py
    │
    ├── knowledge_base/
    │   ├── pdfs/
    │   ├── processed/
    │   └── models/
    │       └── multilingual-e5-small/
    │
    ├── templates/
    │   ├── login.html
    │   ├── main.html
    │   ├── risk_assessment.html
    │   ├── reports.html
    │   ├── report_details.html
    │   ├── tracker.html
    │   ├── self_examination.html
    │   └── chatbot.html
    │
    └── static/
        ├── css/
        │   ├── style.css
        │   ├── main2.css
        │   ├── reports.css
        │   ├── report_details.css
        │   ├── tracker.css
        │   ├── self_examination.css
        │   └── chatbot.css
        │
        ├── javascript/
        │   ├── script.js
        │   ├── trackare.js
        │   ├── self_examination.js
        │   └── chatbot.js
        │
        ├── images/
        └── videos/

# How the RAG System Works:
    1. PDF Text Extraction

        Medical PDF files are stored in:
            knowledge_base/pdfs/

        PyMuPDF extracts text page by page while preserving the source filename and page number.

        The extracted content is saved in:
            knowledge_base/processed/extracted_text.json

    2. Text Chunking

        The extracted text is divided into smaller sections to improve retrieval.

        Current configuration:
            - Chunk size: 300 words.
            - Chunk overlap: 50 words.
            - Page-level source tracking.

        Each chunk retains metadata including:
            - Source filename.
            - Page number.
            - Unique chunk ID.
            - Word count.
            - Extracted text.

    3. Embedding Generation
        The local embedding model:

            intfloat/multilingual-e5-small

            converts text chunks into numerical vectors.

            The model produces 384-dimensional embeddings.

            The system uses:

                - passage: prefix for document chunks.
                - query: prefix for user questions.
                - Normalized embeddings for cosine-similarity retrieval.

    4. Similarity Search

        NumPy calculates similarity between the user's question embedding and stored document embeddings.

        The system retrieves the most relevant chunks and uses them as context for response generation.

        The current prototype uses a small local vector collection rather than a dedicated vector database.

    5. Response Generation

        The retrieved medical passages are sent as context to the language model through the Groq API.

        The chatbot is instructed to:
            - Ground medical answers in retrieved references.
            - Identify the source filename and page number when available.
            - Acknowledge insufficient information.
            - Avoid presenting itself as a diagnostic tool.
            - Distinguish risk estimates from diagnoses.
            - Encourage professional assessment of concerning breast changes.


# Patient Data Integration:
    pink print separates two types of information:

    **Medical Knowledge**
        - Public medical references.
        - Clinical educational material.
        - Retrieved PDF passages.

    **Patient-Specific Information**
        - Gail Model assessment records.
        - Breast self-examination tracker observations.
        - Relevant application records.
    
    Patient-specific information is retrieved from SQLite only when the user has explicitly authorized its use.

    The Gail Model calculation is performed by the Python implementation rather than delegated to the language model.

    The AI may explain recorded results, but it must not independently modify patient records or treat tracker observations as confirmed medical findings.

# Installation and Setup:
    Requirements
        - macOS, Linux, or Windows.
        - Python 3.11 or compatible version.
        - pip.
        - Visual Studio Code or another Python editor.
        - A Groq API key.

    1. Clone the Repository
        git clone YOUR_REPOSITORY_URL
        cd miria

    2. Create a Virtual Environment

        python3 -m venv venv

        Activate it:

            source venv/bin/activate

        For Windows:

            venv\Scripts\activate
    
    3. Install Dependencies

        python -m pip install --upgrade pip
        python -m pip install -r requirements.txt

    4. Configure Environment Variables

        Create your local .env file using .env.example as a template.

        Example:

            FLASK_SECRET_KEY=replace_with_your_own_secret
            GROQ_API_KEY=your_groq_api_key
            GROQ_MODEL=openai/gpt-oss-120b

        Never publish real API keys or secret values.

        Make sure the application is configured to load these environment variables before running it.

    5. Download the Embedding Model

        Download the required model from its official Hugging Face repository:

        Multilingual E5 Small – Hugging Face

        Place the model files in:

            knowledge_base/models/multilingual-e5-small/

        The application is configured to load the local model.

    6. Prepare the Medical Knowledge Base

        Place the medical PDF files in:

            knowledge_base/pdfs/

        If the processed knowledge-base files are not included in the repository, run the preparation scripts in order:

            python chatbot/ingest.py
            python chatbot/chunking.py
            python chatbot/create_embeddings.py

        These scripts generate the extracted text, chunks, embeddings, and associated metadata.

# Running the Application:
    Activate the virtual environment:

        source venv/bin/activate

    Start the Flask application:

        python app.py

    Open the application in your browser:

        http://127.0.0.1:5001

    The local development server should be used for development and testing, not as a production deployment server.

# Medical Safety and Limitations:
    pink print is designed for medical education and awareness support.

    Important limitations:

        - The Gail Model provides a statistical risk estimate and does not diagnose breast cancer.

        - Risk estimates depend on the model's eligibility criteria, supported population, and input accuracy.

        - A low estimated risk does not rule out breast cancer.

        - Breast self-examination tracking does not establish whether a breast finding is benign or malignant.

        - Breast self-examination is not a substitute for recommended screening or professional clinical evaluation.

        - A new lump, persistent breast change, nipple discharge, skin change, or other concerning symptom should be assessed by a qualified healthcare professional.

        - AI-generated responses may be incomplete or incorrect and should be checked against appropriate medical sources and clinical judgment.

# Privacy and Security:
    pink print is designed with separation between public medical knowledge and individual patient records.

    Privacy-related design considerations include:

        - Authentication and conversation ownership checks.

        - Explicit consent before automatically attaching selected patient records to chatbot context.

        - Separate storage of patient data and medical reference material.

        - Local PDF extraction and embedding generation.

        - No publication of API keys, credentials, or real patient records.

    External AI processing: When the chatbot generates an answer through Groq, the question, relevant conversation history, and retrieved context are transmitted to the external API. If patient context is authorized and included, selected patient information may also be transmitted.

    Do not use real patient-identifying information in development or testing. Use synthetic data whenever possible.

# Development Status:
    pink print is an evolving AI x Healthcare project.

    The current prototype includes:

        - Flask-based web application.

        - SQLite database integration.

        - Python Gail Model implementation.

        - Breast self-examination tracking.

        - Local medical PDF processing.

        - Local multilingual embedding generation.

        - NumPy-based semantic retrieval.

        - Groq-powered chatbot response generation.

        - Optional patient-context integration with consent.

    Further development may include expanded medical references, improved retrieval evaluation, enhanced clinical safety testing, and additional privacy controls.