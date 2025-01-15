from typing import Optional
from ..types.database import LeadRecord, EmailRecord
from ..integrations.base import DatabaseIntegration
from ..agents.email_drafter import generate_email, Email
from ..types.filters import FilterOperator, FieldFilter, CompositeFilter

async def draft_first_contact(
    lead_id: int,
    user_prmpt: str,
    leads_db: DatabaseIntegration,
    emails_db: DatabaseIntegration
) -> Optional[Email]:
    """
    Draft first contact email for a lead if it doesn't exist yet.
    
    Args:
        lead_id: ID of the lead
        user_prmpt: Prompt for email writing
        leads_db: Database integration for leads
        emails_db: Database integration for emails
        
    Returns:
        Email object if a new email was generated, None if first contact already exists
    """
    # Get lead information
    lead_filter = FieldFilter(
        field="ID",
        operator=FilterOperator.EQUALS,
        value=lead_id
    )
    leads = await leads_db.get_records(filter_params=lead_filter)
    if not leads:
        raise ValueError(f"Lead with ID {lead_id} not found")
    lead = leads[0]
    
    # Check if first contact email exists
    email_filter = CompositeFilter(
        operator=FilterOperator.AND,
        filters=[
            FieldFilter(
                field="Recipient",
                operator=FilterOperator.CONTAINS,
                value=lead["id"]
            ),
            FieldFilter(
                field="Type",
                operator=FilterOperator.EQUALS,
                value="first_contact"
            )
        ]
    )
    existing_emails = await emails_db.get_records(filter_params=email_filter)
    
    if existing_emails:
        return None

    # Generate new first contact email
    prompt = """
        Write an email based on the example below to start a conversation with {name}, 
        a person with this profile: {profile}, working at {company}.
        
        In the beginning of the email write only the last name and not in uppercase, only capital initials.
        If the subject they teach is not present, stay more general and of that the project can be useful both for courses, research, analyzing documents, videos, audio, etc.

        You must return in the required format email subject and text. The text must be ready to be sent so already filled in. The email details below are correct, I would say just fill it in.

       {user_prmpt}
    """
    
    email = generate_email(
        prompt,
        name=lead.get("Name", ""),
        profile=lead.get("Profile", ""),
        company=lead.get("Company", "General"),
        user_prmpt=user_prmpt
    )
    
    email_data: EmailRecord = {
        "Object": email.object,
        "Text": email.body,
        "Type": "first_contact",
        "Recipient": [{"id": lead["id"]}],
        "Email_Status": "to_be_sent"
    }
    
    # Create email and get its ID
    email_id = await emails_db.insert_record(email_data)
    
    # Update lead with the new email relation
    lead_emails = lead.get("Emails", [])
    lead_emails.append({"id": email_id})
    await leads_db.update_record(
        page_id=lead["id"],
        data={"Emails": lead_emails}
    )
    
    return email

async def draft_all_first_contacts(
    leads_db: DatabaseIntegration,
    emails_db: DatabaseIntegration,
    user_prmpt: str
) -> list[Email]:
    """
    Draft first contact emails for all leads that don't have one yet.
    
    Args:
        leads_db: Database integration for leads
        emails_db: Database integration for emails
        prompt: Prompt to use for email generation
        
    Returns:
        List of generated Email objects
    """
    # Get all leads
    leads = await leads_db.get_records()
    
    generated_emails = []
    for lead in leads:
        try:
            email = await draft_first_contact(
                lead_id=lead["ID"],
                user_prmpt=user_prmpt,
                leads_db=leads_db,
                emails_db=emails_db
            )
            if email:
                generated_emails.append(email)
        except Exception as e:
            print(f"Error drafting email for lead {lead['id']}: {str(e)}")
            continue
    
    return generated_emails
