"""
Test script to verify AI matching with DeepSeek API
Run this to see if your API key works and how the AI matching behaves.
"""

import sys
import os
sys.path.append('.')

# Set up Flask app context
from app import app
from models import db
from models.user import User
from models.project import Project, Task
from utils.matching import ai_match_task_to_employees, auto_match_tasks

def create_test_data():
    """Create some test employees and tasks"""
    with app.app_context():
        # Clear existing test data
        User.query.filter(User.username.like('test_%')).delete()
        db.session.commit()
        
        # Create test employees
        emp1 = User(
            username='test_frontend_dev',
            name='Alice Johnson', 
            role='employee',
            status='active',
            technical_skills={
                'frontend': ['React', 'JavaScript', 'HTML', 'CSS'],
                'tools': ['Git', 'VS Code']
            },
            years_of_experience=3,
            password_hash='dummy'
        )
        
        emp2 = User(
            username='test_backend_dev',
            name='Bob Smith',
            role='employee', 
            status='active',
            technical_skills={
                'backend': ['Python', 'Flask', 'SQL', 'PostgreSQL'],
                'tools': ['Docker', 'Git']
            },
            years_of_experience=5,
            password_hash='dummy'
        )
        
        emp3 = User(
            username='test_fullstack_dev',
            name='Carol Wilson',
            role='employee',
            status='active', 
            technical_skills={
                'frontend': ['React', 'TypeScript'],
                'backend': ['Node.js', 'Express', 'MongoDB'],
                'tools': ['AWS', 'Docker']
            },
            years_of_experience=4,
            password_hash='dummy'
        )
        
        db.session.add_all([emp1, emp2, emp3])
        db.session.commit()
        
        print("✅ Test employees created:")
        print(f"   • {emp1.full_name}: {emp1.get_all_skills()}")
        print(f"   • {emp2.full_name}: {emp2.get_all_skills()}")
        print(f"   • {emp3.full_name}: {emp3.get_all_skills()}")
        
        return [emp1, emp2, emp3]

def test_ai_matching():
    """Test the AI matching with sample tasks"""
    with app.app_context():
        employees = create_test_data()
        
        # Test Task 1: Simple frontend task
        print("\n🧪 TEST 1: Simple Frontend Task")
        print("-" * 40)
        
        class MockTask:
            def __init__(self, nom, priorite, duree, sous_taches):
                self.nom = nom
                self.priorite = priorite
                self.duree_estimee_jours = duree
                self.sous_taches = sous_taches
        
        simple_task = MockTask(
            nom="Build user login page",
            priorite="Moyenne", 
            duree=3,
            sous_taches=[
                {'competences_requises': ['React', 'HTML', 'CSS']},
                {'competences_requises': ['JavaScript', 'Forms']}
            ]
        )
        
        matches = ai_match_task_to_employees(simple_task, employees)
        
        print(f"Task: {simple_task.nom}")
        print(f"AI Matches: {len(matches)}")
        for match in matches:
            emp = User.query.get(match['employee_id'])
            print(f"  • {emp.full_name} - Score: {match['confidence_score']}%")
            print(f"    Reason: {match['reasoning']}")
        
        # Test Task 2: Complex full-stack task
        print("\n🧪 TEST 2: Complex Full-Stack Task")
        print("-" * 40)
        
        complex_task = MockTask(
            nom="Build e-commerce platform with real-time features",
            priorite="Haute",
            duree=15,
            sous_taches=[
                {'competences_requises': ['React', 'TypeScript', 'Frontend']},
                {'competences_requises': ['Python', 'Flask', 'API']}, 
                {'competences_requises': ['PostgreSQL', 'Database']},
                {'competences_requises': ['WebSockets', 'Real-time']},
                {'competences_requises': ['Docker', 'DevOps']},
                {'competences_requises': ['AWS', 'Deployment']}
            ]
        )
        
        matches = ai_match_task_to_employees(complex_task, employees)
        
        print(f"Task: {complex_task.nom}")
        print(f"AI Matches: {len(matches)} (Complex task - can assign 2 people)")
        for i, match in enumerate(matches):
            emp = User.query.get(match['employee_id'])
            role = "Primary" if i == 0 else "Secondary"
            print(f"  • {role}: {emp.full_name} - Score: {match['confidence_score']}%")
            print(f"    Reason: {match['reasoning']}")

if __name__ == '__main__':
    print("🤖 Testing AI Matching with DeepSeek...")
    print("=" * 50)
    
    try:
        test_ai_matching()
        print("\n✅ AI Matching test completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n💡 Possible issues:")
        print("   • Check your DeepSeek API key")
        print("   • Verify internet connection") 
        print("   • Make sure environment variable is set correctly")