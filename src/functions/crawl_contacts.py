from typing import List
from ..agents.contact_crawler import extract_contacts_from_url
from ..integrations.base import DatabaseIntegration
from ..types.database import LeadRecord

async def crawl_and_store_contacts(
    url: str,
    leads_db: DatabaseIntegration
) -> List[str]:
    """
    Crawl contacts from a URL and store them using the provided database integration.
    
    Args:
        url (str): The URL to crawl for contacts
        leads_db: Database integration for leads
        
    Returns:
        List[str]: List of database record IDs for the created records
        
    Raises:
        Exception: If there's an error during crawling or storing
    """
    # Extract contacts
    contact_list = extract_contacts_from_url(url)
    
    # Store each contact
    record_ids = []
    for contact in contact_list.leads:
        # Convert contact to LeadRecord format
        lead_data: LeadRecord = {
            "Name": contact.name or "Unknown",
            "Email_Address": contact.email or "",
            "Profile": contact.role or "",
            "Contact_Status": "New",
            "Linkedin": None,  # Use None instead of empty string for URL fields
            "Company": [],
            "Emails": [],
        }
        
        # Insert using database integration
        record_id = await leads_db.insert_record(lead_data)
        record_ids.append(record_id)
    
    return record_ids