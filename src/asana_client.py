"""
Asana Client Module
Handles creation of tasks in Asana from extracted action items
"""

import os
import logging
from typing import List, Dict, Optional
import asana
from asana.rest import ApiException

logger = logging.getLogger(__name__)


class AsanaTaskCreator:
    """Create tasks in Asana from action items"""
    
    def __init__(self, access_token: Optional[str] = None):
        """
        Initialize Asana client
        
        Args:
            access_token: Asana Personal Access Token (if None, will use environment variable)
        """
        self.access_token = access_token or os.getenv('ASANA_ACCESS_TOKEN')
        if not self.access_token:
            raise ValueError("Asana access token is required. Set ASANA_ACCESS_TOKEN environment variable.")
        
        # Initialize Asana client
        configuration = asana.Configuration()
        configuration.access_token = self.access_token
        self.api_client = asana.ApiClient(configuration)
        
        # Create API instances
        self.tasks_api = asana.TasksApi(self.api_client)
        self.users_api = asana.UsersApi(self.api_client)
        self.projects_api = asana.ProjectsApi(self.api_client)
        
        # Get user info
        self.user_info = self._get_user_info()
        logger.info(f"Initialized Asana client for user: {self.user_info.get('name', 'Unknown')}")
    
    def _get_user_info(self) -> Dict:
        """Get current user information"""
        try:
            me = self.users_api.get_user("me", {})
            return {
                'gid': me.get('gid', ''),
                'name': me.get('name', ''),
                'workspaces': me.get('workspaces', [])
            }
        except ApiException as e:
            logger.error(f"Failed to get user info: {e}")
            return {}
    
    def create_tasks(self, 
                    action_items: List[Dict[str, str]], 
                    project_id: str,
                    workspace_id: Optional[str] = None) -> List[Dict]:
        """
        Create tasks in Asana from action items
        
        Args:
            action_items: List of action items with 'title' and 'description'
            project_id: Asana project ID to create tasks in
            workspace_id: Workspace ID (optional, will use first workspace if not provided)
            
        Returns:
            List of created task details
        """
        if not workspace_id and self.user_info.get('workspaces'):
            workspace_id = self.user_info['workspaces'][0]['gid']
        
        if not workspace_id:
            logger.error("No workspace ID available")
            return []
        
        created_tasks = []
        
        for item in action_items:
            try:
                task = self._create_single_task(item, project_id, workspace_id)
                if task:
                    created_tasks.append(task)
            except Exception as e:
                logger.error(f"Failed to create task '{item.get('title', 'Unknown')}': {str(e)}")
                continue
        
        logger.info(f"Successfully created {len(created_tasks)} out of {len(action_items)} tasks")
        return created_tasks
    
    def _create_single_task(self, 
                           action_item: Dict[str, str], 
                           project_id: str,
                           workspace_id: str) -> Optional[Dict]:
        """
        Create a single task in Asana
        
        Args:
            action_item: Action item with title and description
            project_id: Project ID
            workspace_id: Workspace ID
            
        Returns:
            Created task details or None if failed
        """
        try:
            # Build task payload
            task_payload = {
                "data": {
                    "name": action_item.get('title', 'Untitled Task'),
                    "notes": action_item.get('description', ''),
                    "projects": [project_id],
                    "workspace": workspace_id
                }
            }
            
            # Add optional fields if present
            if 'priority' in action_item:
                # Map priority to Asana format if needed
                priority_map = {
                    'high': 'high',
                    'medium': 'medium',
                    'low': 'low'
                }
                priority = action_item['priority'].lower()
                if priority in priority_map:
                    task_payload['data']['priority'] = priority_map[priority]
            
            # Create the task
            created_task = self.tasks_api.create_task(task_payload, {})
            
            logger.info(f"Created task: {created_task.get('name', 'Unknown')} (ID: {created_task.get('gid', 'Unknown')})")
            
            return {
                'gid': created_task.get('gid', ''),
                'name': created_task.get('name', ''),
                'notes': created_task.get('notes', ''),
                'permalink_url': created_task.get('permalink_url', '')
            }
            
        except ApiException as e:
            logger.error(f"Asana API error creating task: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error creating task: {e}")
            return None
    
    def get_projects(self, workspace_id: Optional[str] = None) -> List[Dict]:
        """
        Get list of projects in workspace
        
        Args:
            workspace_id: Workspace ID (optional, will use first workspace if not provided)
            
        Returns:
            List of projects with name and ID
        """
        if not workspace_id and self.user_info.get('workspaces'):
            workspace_id = self.user_info['workspaces'][0]['gid']
        
        if not workspace_id:
            return []
        
        try:
            projects = self.projects_api.get_projects_for_workspace(workspace_id, {})
            return [
                {
                    'name': project.get('name', ''),
                    'gid': project.get('gid', '')
                }
                for project in projects
            ]
        except ApiException as e:
            logger.error(f"Failed to get projects: {e}")
            return []
    
    def test_connection(self) -> bool:
        """
        Test the Asana connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to get user info
            me = self.users_api.get_user("me", {})
            return bool(me.get('gid'))
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False