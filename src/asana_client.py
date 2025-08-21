"""
Asana Client Module
Handles creation of tasks in Asana from extracted action items
"""

import os
import logging
import json
from typing import List, Dict, Optional
import asana
from asana.rest import ApiException

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG)
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
        
        # Initialize Asana client with debug mode
        configuration = asana.Configuration()
        configuration.access_token = self.access_token
        configuration.debug = True  # Enable debug mode to see HTTP requests
        self.api_client = asana.ApiClient(configuration)
        
        # Create API instances
        self.tasks_api = asana.TasksApi(self.api_client)
        self.users_api = asana.UsersApi(self.api_client)
        self.projects_api = asana.ProjectsApi(self.api_client)
        self.sections_api = asana.SectionsApi(self.api_client)
        
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
    
    def create_section(self, 
                       project_id: str,
                       section_name: str,
                       workspace_id: Optional[str] = None) -> Optional[str]:
        """
        Create a section in an Asana project
        
        Args:
            project_id: Asana project ID
            section_name: Name for the section
            workspace_id: Workspace ID (optional)
            
        Returns:
            Section ID if created successfully, None otherwise
        """
        logger.info("="*50)
        logger.info("CREATING SECTION")
        logger.info(f"Project ID: {project_id} (type: {type(project_id)})")
        logger.info(f"Section Name: {section_name} (type: {type(section_name)})")
        logger.info(f"Workspace ID: {workspace_id} (type: {type(workspace_id) if workspace_id else 'None'})")
        
        if not workspace_id and self.user_info.get('workspaces'):
            workspace_id = self.user_info['workspaces'][0]['gid']
            logger.info(f"Using default workspace: {workspace_id}")
        
        try:
            section_payload = {
                "data": {
                    "name": section_name
                }
            }
            
            # The SDK expects the payload wrapped in opts with 'body' key
            opts = {'body': section_payload}
            
            logger.info("Payload being sent to create_section_for_project:")
            logger.info(json.dumps(section_payload, indent=2))
            logger.info(f"Method call: sections_api.create_section_for_project('{project_id}', opts={opts})")
            
            created_section = self.sections_api.create_section_for_project(project_id, opts)
            
            logger.info(f"✅ Created section: {section_name} (ID: {created_section.get('gid', 'Unknown')})") 
            logger.info(f"Response: {created_section}")
            return created_section.get('gid')
            
        except ApiException as e:
            logger.error("❌ ASANA API EXCEPTION in create_section:")
            logger.error(f"Error: {e}")
            logger.error(f"Status: {e.status if hasattr(e, 'status') else 'N/A'}")
            logger.error(f"Reason: {e.reason if hasattr(e, 'reason') else 'N/A'}")
            logger.error(f"Body: {e.body if hasattr(e, 'body') else 'N/A'}")
            logger.error(f"Headers: {e.headers if hasattr(e, 'headers') else 'N/A'}")
            return None
        except Exception as e:
            logger.error(f"❌ UNEXPECTED ERROR in create_section: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def create_tasks(self, 
                    action_items: List[Dict[str, str]], 
                    project_id: str,
                    workspace_id: Optional[str] = None,
                    section_name: Optional[str] = None,
                    meeting_context: Optional[str] = None,
                    recording_link: Optional[str] = None) -> List[Dict]:
        """
        Create tasks in Asana from action items
        
        Args:
            action_items: List of action items with 'title' and 'description'
            project_id: Asana project ID to create tasks in
            workspace_id: Workspace ID (optional, will use first workspace if not provided)
            section_name: Name for the section to create (optional)
            meeting_context: Meeting context to add to task descriptions (optional)
            recording_link: Link to the meeting recording (optional)
            
        Returns:
            List of created task details
        """
        if not workspace_id and self.user_info.get('workspaces'):
            workspace_id = self.user_info['workspaces'][0]['gid']
        
        if not workspace_id:
            logger.error("No workspace ID available")
            return []
        
        logger.info("="*50)
        logger.info("STARTING TASK CREATION PROCESS")
        logger.info(f"Project ID: {project_id}")
        logger.info(f"Workspace ID: {workspace_id}")
        logger.info(f"Section Name: {section_name}")
        logger.info(f"Meeting Context: {meeting_context}")
        logger.info(f"Number of action items: {len(action_items)}")
        
        # Create section if section name is provided
        section_id = None
        if section_name:
            logger.info(f"Attempting to create section: {section_name}")
            section_id = self.create_section(project_id, section_name, workspace_id)
            if section_id:
                logger.info(f"✅ Section created with ID: {section_id}")
            else:
                logger.error("❌ Failed to create section, continuing without section")
        
        created_tasks = []
        
        for idx, item in enumerate(action_items, 1):
            try:
                logger.info(f"\nCreating task {idx}/{len(action_items)}: {item.get('title', 'Unknown')}")
                
                # Build enhanced description with context, link, and timestamp
                original_desc = item.get('description', '')
                timestamp = item.get('timestamp', None)
                is_question = item.get('is_question', False)
                
                # Format the title for questions
                if is_question and not item['title'].startswith('Customer Question:'):
                    item['title'] = f"Customer Question: {item['title']}"
                
                # Build description sections
                desc_parts = []
                
                # Add meeting context
                if meeting_context:
                    desc_parts.append(f"📅 {meeting_context}")
                
                # Add recording link with timestamp
                if recording_link:
                    if timestamp:
                        desc_parts.append(f"🎥 Recording: {recording_link}")
                        desc_parts.append(f"⏱️ Timestamp: {timestamp}")
                    else:
                        desc_parts.append(f"🎥 Recording: {recording_link}")
                
                # Add separator and original description
                if desc_parts:
                    item['description'] = '\n'.join(desc_parts) + f"\n{'━' * 30}\n{original_desc}"
                else:
                    item['description'] = original_desc
                
                task = self._create_single_task(item, project_id, workspace_id, section_id)
                if task:
                    created_tasks.append(task)
                    logger.info(f"✅ Task created: {task.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"❌ Failed to create task '{item.get('title', 'Unknown')}': {str(e)}")
                continue
        
        logger.info(f"Successfully created {len(created_tasks)} out of {len(action_items)} tasks")
        return created_tasks
    
    def _create_single_task(self, 
                           action_item: Dict[str, str], 
                           project_id: str,
                           workspace_id: str,
                           section_id: Optional[str] = None) -> Optional[Dict]:
        """
        Create a single task in Asana
        
        Args:
            action_item: Action item with title and description
            project_id: Project ID
            workspace_id: Workspace ID
            section_id: Section ID to add task to (optional)
            
        Returns:
            Created task details or None if failed
        """
        logger.info("-"*30)
        logger.info(f"Creating single task: {action_item.get('title', 'Untitled Task')}")
        logger.info(f"Project ID: {project_id} (type: {type(project_id)})")
        logger.info(f"Workspace ID: {workspace_id} (type: {type(workspace_id)})")
        logger.info(f"Section ID: {section_id} (type: {type(section_id) if section_id else 'None'})")
        
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
            
            logger.info("Task payload being sent:")
            logger.info(json.dumps(task_payload, indent=2))
            
            # Create the task - requires empty opts parameter
            logger.info("Calling tasks_api.create_task()...")
            created_task = self.tasks_api.create_task(task_payload, {})
            logger.info(f"✅ Task created with GID: {created_task.get('gid', 'Unknown')}")
            
            # If section_id is provided, add task to section
            if section_id and created_task.get('gid'):
                try:
                    add_to_section_payload = {"data": {"task": created_task['gid']}}
                    # The SDK expects the payload wrapped in opts with 'body' key
                    opts = {'body': add_to_section_payload}
                    
                    logger.info(f"Adding task to section {section_id}")
                    logger.info(f"Payload: {json.dumps(add_to_section_payload, indent=2)}")
                    
                    self.sections_api.add_task_for_section(
                        section_id,
                        opts
                    )
                    logger.info(f"✅ Task added to section")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to add task to section: {e}")
            
            logger.info(f"Created task: {created_task.get('name', 'Unknown')} (ID: {created_task.get('gid', 'Unknown')})")
            
            return {
                'gid': created_task.get('gid', ''),
                'name': created_task.get('name', ''),
                'notes': created_task.get('notes', ''),
                'permalink_url': created_task.get('permalink_url', '')
            }
            
        except ApiException as e:
            logger.error("❌ ASANA API EXCEPTION in _create_single_task:")
            logger.error(f"Error: {e}")
            logger.error(f"Status: {e.status if hasattr(e, 'status') else 'N/A'}")
            logger.error(f"Reason: {e.reason if hasattr(e, 'reason') else 'N/A'}")
            logger.error(f"Body: {e.body if hasattr(e, 'body') else 'N/A'}")
            return None
        except Exception as e:
            logger.error(f"❌ UNEXPECTED ERROR in _create_single_task: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
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