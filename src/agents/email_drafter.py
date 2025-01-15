import os
from pydantic import BaseModel, Field
from langchain.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage


class Email(BaseModel):
    object: str = Field(
        description="Object of the email"
    )
    body: str = Field(
        description="Body of the email"
    )

gemini_model = ChatGoogleGenerativeAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini-2.0-flash-exp",
)

def generate_email(prompt: str, **kwargs) -> Email:
    """
    Generate an email based on the provided prompt and parameters.
    
    Args:
        prompt: The main prompt containing instructions for email generation
        **kwargs: Additional parameters to be formatted into the prompt
        
    Returns:
        Email object containing subject and body
    """
    ready_to_send_instructions = "\nCreate a complete, ready-to-send email. Do not include any placeholders or template variables. The email should be immediately usable without any modifications."
    
    enhanced_prompt = prompt + ready_to_send_instructions
    
    prompt_template = PromptTemplate(
        input_variables=list(kwargs.keys()),
        template=enhanced_prompt
    )

    model_with_structured_output = gemini_model.with_structured_output(Email)
    formatted_prompt = prompt_template.format(**kwargs)
    
    return model_with_structured_output.invoke([HumanMessage(content=formatted_prompt)])