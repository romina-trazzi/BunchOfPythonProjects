"""
Swagger/OpenAPI Configuration
"""

# Custom CSS for Swagger UI
swagger_ui_custom_css = """
.swagger-ui .topbar {
    background-color: #1f2937;
}

.swagger-ui .topbar .download-url-wrapper {
    display: none;
}

.swagger-ui .info .title {
    color: #3b82f6;
}

.swagger-ui .scheme-container {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
}

.swagger-ui .opblock.opblock-post {
    border-color: #10b981;
    background: rgba(16, 185, 129, 0.1);
}

.swagger-ui .opblock.opblock-get {
    border-color: #3b82f6;
    background: rgba(59, 130, 246, 0.1);
}

.swagger-ui .opblock.opblock-delete {
    border-color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
}

.swagger-ui .opblock-tag {
    font-size: 18px;
    font-weight: bold;
    color: #1f2937;
}
"""

# Custom JavaScript for Swagger UI
swagger_ui_custom_js = """
window.onload = function() {
    // Add custom behavior here if needed
    console.log('LangChain RAG API Documentation Loaded');
}
"""

# OpenAPI tags metadata
tags_metadata = [
    {
        "name": "🏥 Health",
        "description": "Health check and system status endpoints",
    },
    {
        "name": "🔍 RAG Queries",
        "description": "Core RAG functionality for querying documents with AI",
    },
    {
        "name": "📚 Document Management",
        "description": "Upload, process, and manage documents in the knowledge base",
    },
    {
        "name": "🤖 AI Agents",
        "description": "Specialized AI agents for different types of tasks",
    },
    {
        "name": "💬 Session Management",
        "description": "Manage conversation sessions and chat history",
    },
    {
        "name": "⚡ Streaming",
        "description": "Real-time streaming responses and WebSocket connections",
    },
    {
        "name": "🔧 Custom Chains",
        "description": "Create and execute custom LangChain workflows",
    },
    {
        "name": "🔍 Search",
        "description": "Search and similarity operations on the knowledge base",
    },
]

# Example requests for documentation
example_requests = {
    "query_request": {
        "question": "What is the main topic of the uploaded documents?",
        "include_sources": True,
        "k": 5
    },
    "agent_query_request": {
        "query": "Analyze the key findings in the research papers",
        "session_id": "research_session_001",
        "agent_type": "analysis"
    },
    "custom_chain_request": {
        "prompt_template": "Based on the context: {context}\n\nQuestion: {question}\n\nProvide a detailed analysis:",
        "query": "What are the main conclusions?",
        "session_id": "custom_session_001"
    }
}