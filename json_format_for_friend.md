📋 **CORRECT JSON FORMAT FOR N8N → FLASK API**
=====================================================

👤 **Tell your friend to use this EXACT JSON structure:**

```json
{
  "metadata": {
    "cv_filename": "{{ $json.metadata.cv_filename }}"
  },
  "personal_info": {
    "full_name": "{{ $json.personal_info.full_name }}",
    "email": "{{ $json.personal_info.email }}",
    "phone": "{{ $json.personal_info.phone }}",
    "professional_headline": "{{ $json.personal_info.professional_headline }}",
    "location": {
      "city": "{{ $json.personal_info.location.city }}",
      "country": "{{ $json.personal_info.location.country }}"
    }
  },
  "technical_skills": {{ $json.technical_skills }},
  "certifications": {{ $json.certifications }},
  "languages": {{ $json.languages }},
  "work_experience": {{ $json.work_experience }}
}
```

🔑 **KEY POINTS FOR YOUR FRIEND:**

1. **Method:** POST
2. **URL:** https://untrumpeted-prenational-celeste.ngrok-free.dev/manager/api/employee/create
3. **Body Type:** JSON (application/json)
4. **CRITICAL:** Must include `technical_skills` field - this was missing!

🚨 **WHAT WAS WRONG:**
- She was only sending: `"personal_info": {{ $json.personal_info }}`
- She was MISSING: `"technical_skills": {{ $json.technical_skills }}`

✅ **WHAT TO FIX:**
- Include ALL fields: personal_info, technical_skills, certifications, languages, work_experience
- The `technical_skills` field is what contains the extracted skills from CV analysis

📊 **EXPECTED RESULT:**
After this fix:
- Employee data will be created ✅
- Technical skills will be populated (not empty {}) ✅  
- All CV analysis data will be stored ✅

💡 **FOR N8N WORKFLOW:**
Tell her to check that her AI analysis step outputs these fields:
- technical_skills (this is the missing piece!)
- personal_info
- certifications  
- languages
- work_experience