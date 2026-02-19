# 📋 N8N WORKFLOW CONFIGURATION FOR PROJECT SPECS ANALYSIS

## 🚀 **Complete n8n Workflow Setup for Your Friend**

---

## **WORKFLOW 2: Project Specs Analysis**

### **Overview:**
```
You → Upload Specs → n8n → AI Analyzes → n8n Sends Back → Updated Project
```

---

### **Node 1: Webhook (Receives project specs from you)**
```
Type: Webhook Trigger
HTTP Method: POST
Path: project-analysis
Authentication: None
Response Mode: Respond to Webhook

What it receives from your Flask app:
{
  "project_id": 1,
  "project_name": "E-Commerce Website",
  "specs_text": "extracted text from PDF...",
  "specs_filename": "specs.pdf",
  "callback_url": "https://your-ngrok.ngrok-free.dev/manager/api/project/update",
  "metadata": {...}
}
```

---

### **Node 2: AI Analysis (Extract structured data from specs)**
```
Type: OpenAI / LLM Node / AI Agent

Prompt:
"Analyze this project specification document and extract the following information in JSON format:

1. project_type: (e.g., 'web application', 'mobile app', 'data analysis', etc.)
2. complexity: ('simple', 'medium', 'complex')
3. estimated_duration: (e.g., '2 months', '6 weeks')
4. required_skills: {
     "programming_languages": ["Python", "JavaScript"],
     "frameworks": ["React", "Django"],
     "databases": ["PostgreSQL"],
     "tools": ["Docker", "AWS"]
   }
5. tech_stack: {
     "frontend": ["React", "TailwindCSS"],
     "backend": ["Python", "Flask"],
     "database": ["PostgreSQL"],
     "deployment": ["Docker", "AWS"]
   }
6. key_features: ["User authentication", "Payment processing", ...]
7. description: "Brief AI-generated summary of the project"

Project Specifications:
{{ $json.specs_text }}"

Output: JSON
```

---

### **Node 3: HTTP Request (Send analysis back to you)**
```
Type: HTTP Request
Method: POST
URL: {{ $json.callback_url }}

HEADERS (REQUIRED):
- Content-Type: application/json

BODY TYPE: JSON

BODY CONTENT:
{
  "project_id": {{ $json.project_id }},
  "project_type": "{{ $json.project_type }}",
  "complexity": "{{ $json.complexity }}",
  "estimated_duration": "{{ $json.estimated_duration }}",
  "required_skills": {{ $json.required_skills }},
  "tech_stack": {{ $json.tech_stack }},
  "key_features": {{ $json.key_features }},
  "description": "{{ $json.description }}"
}
```

---

### **Node 4: Respond to Original Webhook**
```
Type: Respond to Webhook
Response Code: 200
Response Body: 
{
  "status": "success",
  "message": "Project specs analyzed successfully"
}
```

---

## 🎯 **n8n Configuration for Old Version (v2.6.4)**

If your friend has n8n v2.6.4, use this configuration for Node 3:

```
Node 3: HTTP Request
--------------------
Request Method: POST
URL: ={{ $json.callback_url }}

Send Body: YES (Enable toggle)
Body Content Type: JSON

JSON Body (paste exactly):
{
  "project_id": ={{ $json.project_id }},
  "project_type": "={{ $json.project_type }}",
  "complexity": "={{ $json.complexity }}",
  "estimated_duration": "={{ $json.estimated_duration }}",
  "required_skills": ={{ $json.required_skills }},
  "tech_stack": ={{ $json.tech_stack }},
  "key_features": ={{ $json.key_features }},
  "description": "={{ $json.description }}"
}

Headers:
- Name: Content-Type
- Value: application/json
```

---

## 📊 **Expected JSON Format from AI**

Tell your friend the AI should output this structure:

```json
{
  "project_type": "web application",
  "complexity": "medium",
  "estimated_duration": "3 months",
  "required_skills": {
    "programming_languages": ["Python", "JavaScript", "HTML/CSS"],
    "frameworks": ["React", "Flask", "TailwindCSS"],
    "databases": ["PostgreSQL"],
    "tools": ["Docker", "Git", "AWS"]
  },
  "tech_stack": {
    "frontend": ["React", "TailwindCSS"],
    "backend": ["Python", "Flask"],
    "database": ["PostgreSQL"],
    "deployment": ["Docker", "AWS EC2"]
  },
  "key_features": [
    "User authentication and authorization",
    "Shopping cart functionality",
    "Payment processing integration",
    "Admin dashboard",
    "Order management system"
  ],
  "description": "An e-commerce platform with user management, product catalog, shopping cart, and payment integration"
}
```

---

## 🧪 **Testing the Workflow**

### **Test Data to Send:**
```bash
curl -X POST https://toshia-nonfacetious-rachael.ngrok-free.dev/webhook/project-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 999,
    "project_name": "Test Project",
    "specs_text": "Build a web application with user authentication...",
    "callback_url": "https://untrumpeted-prenational-celeste.ngrok-free.dev/manager/api/project/update"
  }'
```

---

## ✅ **Checklist for Your Friend**

- [ ] Create webhook trigger with path: `/webhook/project-analysis`
- [ ] Add AI analysis node with proper prompt
- [ ] Configure HTTP Request node with callback URL
- [ ] Add response node
- [ ] Connect all nodes in sequence
- [ ] Activate workflow (toggle ON)
- [ ] Test with sample data

---

## 🎯 **What Happens After Setup:**

1. **Manager uploads project specs** → PDF automatically sent to n8n
2. **n8n AI analyzes** → Extracts requirements, skills, tech stack
3. **n8n sends results back** → Your Flask API receives structured data
4. **Database updated** → Project now has AI-analyzed information
5. **Manager can view** → Structured project requirements in dashboard

---

**Your Flask API Endpoints:**
- **Sends to:** `https://toshia-nonfacetious-rachael.ngrok-free.dev/webhook/project-analysis`
- **Receives from:** `https://untrumpeted-prenational-celeste.ngrok-free.dev/manager/api/project/update`