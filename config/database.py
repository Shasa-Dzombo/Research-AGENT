"""
Supabase database client configuration
"""
from supabase import create_client, Client
from functools import lru_cache
from config.config import get_settings

@lru_cache()
def get_supabase_client() -> Client:
    """Get cached Supabase client instance"""
    settings = get_settings()
    
    if not settings.supabase_url or not settings.supabase_key:
        raise ValueError("Supabase URL and key must be configured")
    
    return create_client(settings.supabase_url, settings.supabase_key)

class SupabaseManager:
    """Manager class for Supabase operations"""
    
    def __init__(self):
        self.client = get_supabase_client()
    
    def save_research_session(self, session_data: dict) -> dict:
        """Save research session to Supabase"""
        try:
            result = self.client.table('research_sessions').insert(session_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"Error saving session: {e}")
            return {}
    
    def get_research_session(self, session_id: str) -> dict:
        """Get research session from Supabase"""
        try:
            result = self.client.table('research_sessions').select("*").eq('session_id', session_id).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"Error getting session: {e}")
            return {}
    
    def update_research_session(self, session_id: str, update_data: dict) -> dict:
        """Update research session in Supabase"""
        try:
            result = self.client.table('research_sessions').update(update_data).eq('session_id', session_id).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"Error updating session: {e}")
            return {}
    
    def save_selected_questions(self, session_id: str, selected_main_question_ids: list) -> dict:
        """Save selected main question IDs for a session"""
        try:
            selection_data = {
                'session_id': session_id,
                'selected_main_question_ids': selected_main_question_ids,
                'created_at': 'now()'
            }
            result = self.client.table('question_selections').insert(selection_data).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            print(f"Error saving question selection: {e}")
            return {}
    
    def get_selected_questions(self, session_id: str) -> list:
        """Get selected main question IDs for a session"""
        try:
            result = self.client.table('question_selections').select("selected_main_question_ids").eq('session_id', session_id).execute()
            if result.data:
                return result.data[0].get('selected_main_question_ids', [])
            return []
        except Exception as e:
            print(f"Error getting question selection: {e}")
            return []

# Global instance
supabase_manager = SupabaseManager()
