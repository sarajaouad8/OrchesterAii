"""
Script to remove all task assignments from a specific project
This allows testing the auto-matching system with fresh unassigned tasks.
"""

import sys
sys.path.append('.')

from app import app
from models import db
from models.project import Project, Task

def unassign_project_tasks():
    """Remove all employee assignments from the hotel project"""
    with app.app_context():
        # Find the project
        project_name = "Solution logicielle d'hôtellerie de nouvelle génération"
        project = Project.query.filter(
            Project.nom_projet.like(f"%{project_name}%") | 
            Project.name.like(f"%{project_name}%")
        ).first()
        
        if not project:
            print(f"❌ Project '{project_name}' not found")
            print("\nAvailable projects:")
            projects = Project.query.all()
            for p in projects:
                print(f"  • ID: {p.id} | Name: {p.name} | Nom: {p.nom_projet}")
            return
        
        print(f"✅ Found project: {project.nom_projet or project.name} (ID: {project.id})")
        
        # Get all tasks for this project
        tasks = Task.query.filter_by(project_id=project.id).all()
        print(f"📋 Found {len(tasks)} tasks")
        
        # Count currently assigned tasks
        assigned_count = sum(1 for task in tasks if task.assigned_employee_id)
        print(f"👥 Currently assigned tasks: {assigned_count}")
        
        if assigned_count == 0:
            print("✨ All tasks are already unassigned!")
            return
        
        # Show current assignments
        print("\n📝 Current assignments:")
        for task in tasks:
            if task.assigned_employee_id:
                from models.user import User
                emp = User.query.get(task.assigned_employee_id)
                emp_name = emp.full_name if emp else f"ID:{task.assigned_employee_id}"
                score = f" ({task.match_score}%)" if task.match_score else ""
                print(f"  • {task.task_id}: {task.nom[:50]}... → {emp_name}{score}")
        
        # Remove all assignments
        print(f"\n🔄 Removing assignments from {assigned_count} tasks...")
        for task in tasks:
            if task.assigned_employee_id:
                task.assigned_employee_id = None
                task.assigned_at = None
                task.match_score = None
        
        # Save changes
        db.session.commit()
        print("✅ All task assignments removed!")
        print("\n🎯 You can now test auto-matching by:")
        print(f"1. Going to: http://localhost:5000/manager/project/{project.id}")
        print("2. Clicking the '⚡ Auto-Match' button")
        print("3. Or uploading new project specs to trigger automatic matching")

if __name__ == '__main__':
    print("🧹 Unassigning tasks for matching test...")
    print("=" * 50)
    unassign_project_tasks()