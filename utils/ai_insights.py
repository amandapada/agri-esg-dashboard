from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import streamlit as st
import os

@st.cache_data(ttl=3600)  # Cache for 1 hour
def generate_ai_insights(
    esg_score: float,
    e_score: float,
    s_score: float,
    emissions_per_ha: float,
    emissions_per_tonne: float,
    yield_per_ha: float,
    female_share: float,
    accidents: float,
    farm_id: str,
    farmer_name: str = None 
) -> list[str]:
    """
    Generate AI-powered, farmer-friendly insights using Gemini.
    Note: 'farmer_name' argument now receives the Farm Name from app.py.
    """
    
    # Check if API key exists
    api_key = os.getenv("GOOGLE_API_KEY")
    # Clean up the name (if it's just 'Farm', treat as generic)
    greeting_name = str(farmer_name) if farmer_name and str(farmer_name).lower() != 'nan' else "Farm Team"
    
    if not api_key:
        return [
            f"Hello {greeting_name}! Set up your Google API key to get personalized advice.",
            "Check your .env file for GOOGLE_API_KEY configuration."
        ]
    
    # Create prompt template
    # We explicitly tell the AI to use the Farm Name in the greeting
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a helpful farming advisor speaking to the team at {greeting_name}.

Rules:
- ALWAYS start your response with exactly: "Hello {greeting_name}!"
- Then provide 3-4 simple, actionable tips to improve their sustainability.
- Use SIMPLE words (plain English).
- NO technical jargon (say "soil health" instead of "agronomic substrate analysis").
- Focus on practical wins: saving money on fertilizer, improving soil, or safety.
- If their score is low, be encouraging. If high, say "Keep it up!".

Example Output Format:
Hello {greeting_name}!
Try using less fertilizer on the North Field to save costs.
Planting cover crops this winter could help your soil health.
Your safety record is great—keep checking those machinery logs.
"""),
        
        ("user", f"""Farm Data:
- Overall Sustainability Score: {esg_score}/100
- Environment Score: {e_score}/100 
- Social Score: {s_score}/100
- Emissions: {emissions_per_ha} kg/ha (Lower is better)
- Yield Estimate: {yield_per_ha:.1f} tons/ha

Give me a simple list of advice.""")
    ])
    
    try:
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash", 
            temperature=0.7,
            google_api_key=api_key
        )
        
        # Create chain
        chain = prompt | llm
        
        # Invoke
        response = chain.invoke({})
        
        # Parse response into list
        content = response.content.strip()
        
        insights = []
        for line in content.split('\n'):
            line = line.strip()
            # Remove bullet points or numbering
            clean_line = line.lstrip('•-*123456789. ')
            
            # Check if it's the greeting or a substantial tip
            is_greeting = clean_line.lower().startswith(('hello', 'hi ', 'dear', 'greetings'))
            
            if clean_line and (len(clean_line) > 10 or is_greeting):
                insights.append(clean_line)
        
        if insights:
            return insights[:4]
        else:
            return [f"Hello {greeting_name}! I couldn't generate specific tips right now."]
    
    except Exception as e:
        return [
            f"Hello {greeting_name}!",
            f"System is busy. Your score is {round(esg_score, 0)}/100.",
            "Please try refreshing the page."
        ]