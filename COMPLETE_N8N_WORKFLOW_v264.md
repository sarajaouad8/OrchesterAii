# 📋 COMPLETE n8n WORKFLOW FOR PROJECT SPECS ANALYSIS (v2.6.4)

## 🎯 **Your Friend's Setup - n8n Version 2.6.4**

### **WORKFLOW NAME:** Project Specs Analyzer
### **WEBHOOK URL:** https://claudia-superterrestrial-larkishly.ngrok-free.dev/analyse-pdf

---

## 🔧 **NODE 1: WEBHOOK TRIGGER**

```
Node Type: Webhook
Node Name: Receive Project Specs

Configuration:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HTTP Method: POST
Path: analyse-pdf
Authentication: None
Response: Respond to Webhook
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

What it receives from your Flask:
{
  "project_id": 1,
  "project_name": "E-Commerce Website",
  "specs_text": "extracted text from PDF...",
  "specs_filename": "project_specs.pdf",
  "callback_url": "https://untrumpeted-prenational-celeste.ngrok-free.dev/manager/api/project/update",
  "metadata": {...}
}
```

---

## 🤖 **NODE 2: AI ANALYSIS**

```
Node Type: OpenAI / LLM / AI Agent
Node Name: Analyze Project Requirements

Configuration:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Prompt:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Analysez ce cahier des charges et extrayez les informations suivantes au format JSON:

{
  "project_type": "type de projet (ex: application web, application mobile, site vitrine, e-commerce, etc.)",
  "complexity": "complexité (simple, medium, complex)",
  "estimated_duration": "durée estimée (ex: 2 mois, 6 semaines, 3 mois)",
  "description": "résumé du projet en français",
  "required_skills": {
    "programming_languages": ["Python", "JavaScript", "PHP"],
    "frameworks": ["React", "Django", "Laravel"],
    "databases": ["PostgreSQL", "MySQL"],
    "tools": ["Docker", "Git", "AWS"]
  },
  "tech_stack": {
    "frontend": ["React", "Vue.js", "HTML/CSS"],
    "backend": ["Python", "Node.js", "PHP"],
    "database": ["PostgreSQL", "MongoDB"],
    "deployment": ["Docker", "Heroku", "AWS"]
  },
  "key_features": [
    "Authentification utilisateur",
    "Tableau de bord",
    "Gestion des données",
    "Interface responsive"
  ]
}

IMPORTANT: Répondez UNIQUEMENT avec du JSON valide, rien d'autre.

Cahier des charges à analyser:
{{ $json.specs_text }}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input Data: {{ $json.specs_text }}
Output Format: JSON
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 📤 **NODE 3: HTTP REQUEST (Send Results Back)**

```
Node Type: HTTP Request
Node Name: Send Analysis to Flask

Configuration for n8n v2.6.4:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Request Method: POST
URL: {{ $json.callback_url }}

Send Body: ✅ YES (Enable this checkbox/toggle)
Body Content Type: JSON

Headers:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Click "Add Header"
Name: Content-Type
Value: application/json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

JSON Body (paste exactly in the body field):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{
  "project_id": {{ $node["Receive Project Specs"].json["project_id"] }},
  "project_type": "={{ $node["Analyze Project Requirements"].json["project_type"] }}",
  "complexity": "={{ $node["Analyze Project Requirements"].json["complexity"] }}",
  "estimated_duration": "={{ $node["Analyze Project Requirements"].json["estimated_duration"] }}",
  "description": "={{ $node["Analyze Project Requirements"].json["description"] }}",
  "required_skills": {{ $node["Analyze Project Requirements"].json["required_skills"] }},
  "tech_stack": {{ $node["Analyze Project Requirements"].json["tech_stack"] }},
  "key_features": {{ $node["Analyze Project Requirements"].json["key_features"] }}
}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## ✅ **NODE 4: RESPOND TO WEBHOOK**

```
Node Type: Respond to Webhook
Node Name: Confirm Analysis Complete

Configuration:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Response Code: 200
Response Body: 
{
  "status": "success",
  "message": "Cahier des charges analysé avec succès",
  "project_id": {{ $json.project_id }}
}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🔗 **WORKFLOW CONNECTIONS**

```
Receive Project Specs → Analyze Project Requirements → Send Analysis to Flask → Confirm Analysis Complete
```

---

## 🧪 **COMPLETE SETUP CHECKLIST FOR YOUR FRIEND**

### **Step 1: Create New Workflow**
- [ ] Click "New Workflow" in n8n
- [ ] Name: "Project Specs Analyzer"

### **Step 2: Add Node 1 - Webhook**
- [ ] Add "Webhook" node
- [ ] Set HTTP Method: POST
- [ ] Set Path: `analyse-pdf`
- [ ] Authentication: None
- [ ] Response: "Respond to Webhook"

### **Step 3: Add Node 2 - AI Analysis**
- [ ] Add OpenAI/LLM node after webhook
- [ ] Paste the complete prompt from above
- [ ] Set input: `{{ $json.specs_text }}`
- [ ] Set output format: JSON

### **Step 4: Add Node 3 - HTTP Request**
- [ ] Add "HTTP Request" node
- [ ] Method: POST
- [ ] URL: `{{ $json.callback_url }}`
- [ ] Enable "Send Body"
- [ ] Set Body Type: JSON
- [ ] Add Header: Content-Type = application/json
- [ ] Paste the JSON body exactly as shown above

### **Step 5: Add Node 4 - Response**
- [ ] Add "Respond to Webhook" node
- [ ] Response Code: 200
- [ ] Set response body as shown above

### **Step 6: Connect Nodes**
- [ ] Connect all nodes in sequence
- [ ] Webhook → AI → HTTP Request → Response

### **Step 7: Activate**
- [ ] Click "Active" toggle (turn workflow ON)
- [ ] Test webhook URL: https://claudia-superterrestrial-larkishly.ngrok-free.dev/analyse-pdf

---

## 📊 **EXPECTED AI OUTPUT FORMAT**

Your friend's AI should output this exact structure:

```json
{
  "project_type": "application web e-commerce",
  "complexity": "medium", 
  "estimated_duration": "3 mois",
  "description": "Plateforme e-commerce avec gestion des utilisateurs, catalogue produits et paiement en ligne",
  "required_skills": {
    "programming_languages": ["Python", "JavaScript", "HTML/CSS"],
    "frameworks": ["React", "Flask", "TailwindCSS"], 
    "databases": ["PostgreSQL"],
    "tools": ["Docker", "Git", "Stripe API"]
  },
  "tech_stack": {
    "frontend": ["React", "TailwindCSS"],
    "backend": ["Python", "Flask"],
    "database": ["PostgreSQL"], 
    "deployment": ["Docker", "AWS"]
  },
  "key_features": [
    "Authentification et inscription utilisateur",
    "Catalogue produits avec recherche",
    "Panier d'achat et commandes",
    "Paiement en ligne sécurisé",
    "Interface d'administration"
  ]
}
```

---

## 🔧 **TROUBLESHOOTING FOR n8n v2.6.4**

### **Common Issues:**
1. **"Headers not found"** → Look for "Additional Headers" or "Custom Headers"
2. **Body not sending** → Make sure "Send Body" checkbox is checked 
3. **JSON errors** → Use the exact format above, check for missing quotes
4. **Node references** → Use `$node["Node Name"].json["field"]` format

### **Alternative Body Format if Above Doesn't Work:**
```json
{
  "project_id": ={{$node["Receive Project Specs"].json["project_id"]}},
  "project_type": "={{$node["Analyze Project Requirements"].json["project_type"]}}",
  "complexity": "={{$node["Analyze Project Requirements"].json["complexity"]}}",
  "estimated_duration": "={{$node["Analyze Project Requirements"].json["estimated_duration"]}}",
  "description": "={{$node["Analyze Project Requirements"].json["description"]}}",
  "required_skills": {{$node["Analyze Project Requirements"].json["required_skills"]}},
  "tech_stack": {{$node["Analyze Project Requirements"].json["tech_stack"]}},
  "key_features": {{$node["Analyze Project Requirements"].json["key_features"]}}
}
```

---

## 🧪 **TEST THE COMPLETE WORKFLOW**

### **Test Data to Send:**
```bash
curl -X POST https://claudia-superterrestrial-larkishly.ngrok-free.dev/analyse-pdf \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 999,
    "project_name": "Test Project",
    "specs_text": "Créer une application web avec authentification utilisateur, tableau de bord et gestion des données. Technologies recommandées: React, Python Flask, PostgreSQL.",
    "callback_url": "https://untrumpeted-prenational-celeste.ngrok-free.dev/manager/api/project/update"
  }'
```

---

## ✅ **FINAL SUMMARY**

**Your URLs:**
- **You send specs to:** `https://claudia-superterrestrial-larkishly.ngrok-free.dev/analyse-pdf`
- **Friend sends results to:** `https://untrumpeted-prenational-celeste.ngrok-free.dev/manager/api/project/update`

**Complete flow:**
1. Manager uploads project specs PDF
2. Flask extracts text → sends to friend's n8n
3. AI analyzes specs → extracts structured data  
4. n8n sends results back → Flask updates project
5. Manager sees AI-analyzed project requirements

**Ready to go! 🚀**