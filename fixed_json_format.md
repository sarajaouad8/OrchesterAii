📋 **FIXED JSON FORMAT - HANDLES MISSING FIELDS**
=====================================================

🛠️ **Tell your friend to use this SAFER JSON structure:**

```json
{
  "metadata": {
    "cv_filename": "{{ $json.metadata?.cv_filename || 'unknown_cv.pdf' }}"
  },
  "personal_info": {
    "full_name": "{{ $json.personal_info.full_name }}",
    "email": "{{ $json.personal_info.email }}",
    "phone": "{{ $json.personal_info?.phone || '' }}",
    "professional_headline": "{{ $json.personal_info?.professional_headline || '' }}",
    "location": {
      "city": "{{ $json.personal_info?.location?.city || '' }}",
      "country": "{{ $json.personal_info?.location?.country || '' }}"
    }
  },
  "technical_skills": {{ $json.technical_skills || {} }},
  "certifications": {{ $json.certifications || [] }},
  "languages": {{ $json.languages || [] }},
  "work_experience": {{ $json.work_experience || [] }}
}
```

⚠️ **IF n8n DOESN'T SUPPORT || OPERATOR, USE THIS SIMPLER VERSION:**

```json
{
  "personal_info": {{ $json.personal_info }},
  "technical_skills": {{ $json.technical_skills }},
  "certifications": [],
  "languages": [],
  "work_experience": {{ $json.work_experience }}
}
```

🔧 **OR EVEN SIMPLER - ONLY ESSENTIAL FIELDS:**

```json
{
  "personal_info": {
    "full_name": "{{ $json.personal_info.full_name }}",
    "email": "{{ $json.personal_info.email }}"
  },
  "technical_skills": {{ $json.technical_skills }}
}
```

💡 **DEBUGGING STEPS FOR YOUR FRIEND:**

1. **Check what her AI analysis outputs** - print/log the JSON structure
2. **Start with minimal fields** - only personal_info + technical_skills
3. **Add other fields** only if they exist in her AI output

🎯 **MOST IMPORTANT:**
Make sure `technical_skills` exists in her AI analysis output!