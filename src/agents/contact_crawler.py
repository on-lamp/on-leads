import os
from typing import List
from firecrawl import FirecrawlApp
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage

# Initialize FirecrawlApp
app = FirecrawlApp(api_key=os.getenv('FIRECRAWL_API_KEY'))

class Lead(BaseModel):
    name: str = Field(
        description="Full name of the person"
    )
    email: str = Field(
        description="Email address"
    )
    role: str = Field(
        description="Role or position of the person"
    )

class LeadList(BaseModel):
    leads: List[Lead] = Field(description="List of contact records")

def split_text(text: str, max_length: int) -> List[str]:
    """Split text into chunks of maximum length."""
    if not isinstance(text, str):
        text = str(text)
    return [text[i:i+max_length] for i in range(0, len(text), max_length)]

# Initialize models at module level
gpt_model = ChatOpenAI(model="gpt-4o-mini")
gemini_model = ChatGoogleGenerativeAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash-exp",
)
model_with_structured_output = gpt_model.with_structured_output(LeadList)

prompt_template = PromptTemplate(
    input_variables=["content"],
    template="""
        Extract contact information including name, email, and role/position of people from the following web page content: {content}
    """
)

def extract_contacts_from_url(url: str, max_chunk_length: int = 30000) -> LeadList:
    """
    Extract contact information from a given URL.
    
    Args:
        url (str): The URL to scrape
        max_chunk_length (int): Maximum length of text chunks to process
    
    Returns:
        LeadList: List of contacts with their details
    """
    # Scrape the URL
    response = app.scrape_url(url=url, params={
        'formats': ['markdown'],
    })
    
    # Ensure we're working with string content
    content = response.get('markdown', str(response))
    
    # Split content into chunks
    content_chunks = split_text(content, max_chunk_length)
    
    # Process each chunk
    combined_leads = []
    for chunk in content_chunks:
        prompt = prompt_template.format(content=chunk)
        response = model_with_structured_output.invoke([HumanMessage(content=prompt)])
        combined_leads.extend(response.leads)
    
    return LeadList(leads=combined_leads)


