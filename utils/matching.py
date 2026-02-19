"""
AI-powered task-employee matching using DeepSeek API.
Supports up to 2 employees per complex task.
"""

import os
import json
from datetime import datetime
from models import db
from models.user import User
from models.project import Project, Task

# Configure DeepSeek API (new OpenAI client format)
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY") or "sk-1fa56a5b658f410aacbdbac6ead4a26a",
    base_url="https://api.deepseek.com/v1"
)

MAX_TASKS_PER_EMPLOYEE = 2


def _current_task_count(employee_id):
    """Count how many non-completed tasks this employee already has."""
    return (
        Task.query
        .join(Project)
        .filter(
            Task.assigned_employee_id == employee_id,
            Task.status != 'completed',
            Project.status != 'completed',
        )
        .count()
    )


def _get_available_employees():
    """Get employees who are not at max capacity."""
    employees = User.query.filter_by(role='employee', status='active').all()
    available = []
    
    for emp in employees:
        current_load = _current_task_count(emp.id)
        if current_load < MAX_TASKS_PER_EMPLOYEE:
            available.append(emp)
    
    return available


def ai_match_task_to_employees(task_data, available_employees):
    """
    Use DeepSeek AI to match employees to a task.
    Returns up to 2 employees for complex tasks.
    """
    if not available_employees:
        return []
    
    # Extract required skills from sous_taches
    required_skills = []
    if task_data.sous_taches:
        for st in task_data.sous_taches:
            if 'competences_requises' in st:
                required_skills.extend(st['competences_requises'])
    required_skills = list(set(required_skills))  # Remove duplicates
    
    # Determine if task is complex (needs 2 people)
    is_complex = (
        task_data.duree_estimee_jours and task_data.duree_estimee_jours >= 7
    ) or (
        task_data.priorite == 'Haute'
    ) or (
        len(required_skills) >= 4
    ) or (
        task_data.sous_taches and len(task_data.sous_taches) >= 5
    )
    
    max_assignees = 2 if is_complex else 1
    
    prompt = f"""
You are an expert HR AI. Match the best employee(s) for this task.

TASK:
- Name: {task_data.nom}
- Required Skills: {required_skills}
- Priority: {task_data.priorite}
- Duration: {task_data.duree_estimee_jours} days
- Sub-tasks: {len(task_data.sous_taches or [])}
- Complex Task (needs {max_assignees} people): {is_complex}

AVAILABLE EMPLOYEES:
{json.dumps([{
    'id': emp.id,
    'name': emp.full_name,
    'skills': emp.get_all_skills(),
    'experience_years': emp.years_of_experience or 0,
    'current_tasks': _current_task_count(emp.id)
} for emp in available_employees], indent=2)}

INSTRUCTIONS:
- For simple tasks: Return 1 best employee
- For complex tasks: Return up to 2 employees who can work together
- Consider skill overlap, experience, and current workload
- Score each match 0-100

Return ONLY valid JSON:
{{
    "matches": [
        {{
            "employee_id": 123,
            "confidence_score": 92,
            "reasoning": "Strong React experience, perfect for frontend work"
        }},
        {{
            "employee_id": 456,
            "confidence_score": 85,
            "reasoning": "Backend expertise complements first employee"
        }}
    ],
    "is_complex": {is_complex},
    "total_matches": 1
}}
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Extract JSON from response (in case AI adds extra text)
        if "```json" in ai_response:
            ai_response = ai_response.split("```json")[1].split("```")[0]
        elif "```" in ai_response:
            ai_response = ai_response.split("```")[1].split("```")[0]
        
        result = json.loads(ai_response)
        matches = result.get('matches', [])
        
        # Limit to max_assignees
        return matches[:max_assignees]
        
    except Exception as e:
        print(f"❌ AI Matching failed: {e}")
        # Fallback to simple rule-based matching
        return _fallback_match(task_data, available_employees, max_assignees)


def _fallback_match(task_data, employees, max_assignees):
    """Simple fallback matching if AI fails."""
    required_skills = []
    if task_data.sous_taches:
        for st in task_data.sous_taches:
            if 'competences_requises' in st:
                required_skills.extend(st['competences_requises'])
    
    if not required_skills:
        # No skills required, just pick least busy
        employees.sort(key=lambda emp: _current_task_count(emp.id))
        return [{
            'employee_id': employees[0].id,
            'confidence_score': 50,
            'reasoning': 'Fallback assignment - least busy employee'
        }] if employees else []
    
    # Score employees by skill overlap
    scored = []
    for emp in employees:
        emp_skills = [s.lower() for s in emp.get_all_skills()]
        req_skills = [s.lower() for s in required_skills]
        
        matched = sum(1 for req in req_skills if any(req in skill or skill in req for skill in emp_skills))
        score = (matched / len(req_skills)) * 100 if req_skills else 0
        
        # Add experience bonus
        exp_bonus = min((emp.years_of_experience or 0) * 2, 20)
        final_score = score + exp_bonus
        
        scored.append({
            'employee': emp,
            'score': final_score,
            'current_load': _current_task_count(emp.id)
        })
    
    # Sort by score, then by current load
    scored.sort(key=lambda x: (-x['score'], x['current_load']))
    
    # Return top matches
    results = []
    for i, match in enumerate(scored[:max_assignees]):
        results.append({
            'employee_id': match['employee'].id,
            'confidence_score': round(match['score'], 1),
            'reasoning': f'Fallback match - skill overlap {match["score"]:.1f}%'
        })
    
    return results


def auto_match_tasks(project_id):
    """
    Main function: Auto-assign employees to all unassigned tasks in a project.
    Called by Flask routes after project analysis.
    """
    try:
        # Get unassigned tasks
        tasks = Task.query.filter_by(
            project_id=project_id, 
            assigned_employee_id=None
        ).order_by(
            Task.priorite.desc(),  # High priority first
            Task.duree_estimee_jours.desc()  # Complex tasks first
        ).all()
        
        if not tasks:
            return []
        
        results = []
        
        for task in tasks:
            # Get currently available employees
            available_employees = _get_available_employees()
            
            if not available_employees:
                print(f"⚠️ No available employees for task {task.task_id}")
                continue
            
            # Get AI matches for this task
            matches = ai_match_task_to_employees(task, available_employees)
            
            # Assign the matches
            for i, match in enumerate(matches):
                if i == 0:
                    # Primary assignee
                    task.assigned_employee_id = match['employee_id']
                    task.assigned_at = datetime.utcnow()
                    task.match_score = match['confidence_score']
                    
                    emp_name = User.query.get(match['employee_id']).full_name
                    results.append({
                        'task_id': task.task_id,
                        'task_name': task.nom,
                        'employee_id': match['employee_id'],
                        'employee_name': emp_name,
                        'score': match['confidence_score'],
                        'reasoning': match['reasoning'],
                        'role': 'Primary'
                    })
                    
                else:
                    # TODO: Add support for secondary assignee in Task model
                    # For now, just log it
                    emp_name = User.query.get(match['employee_id']).full_name
                    print(f"🤝 Secondary assignee for {task.task_id}: {emp_name} ({match['confidence_score']}%)")
        
        db.session.commit()
        return results
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Auto-matching error: {e}")
        return []


# Backward compatibility - keep old function name
def ai_match_employee_to_task(task, employees):
    """Legacy function name - redirects to new AI matching."""
    return ai_match_task_to_employees(task, employees)