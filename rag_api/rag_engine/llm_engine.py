import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

# Why: Loads environment configurations (API keys) when running locally during diagnostics.
load_dotenv()

class LLMEngine:
    """
    The Brain Connection Hub.
    Wraps LangChain's connection wrapper to feed inputs directly into OpenAI's API.
    """
    def __init__(self, model_name: str = "gpt-4o-mini", temperature: float = 0.0):
        # Why: Resolves connection credential from the environment.
        # Connectivity: Passed down from the host OS via docker-compose configuration.
        api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("❌ OPENAI_API_KEY not found in environment!")
            
        # Why: Instantiates the LangChain OpenAI client wrapper with zero temperature for reliable SQL structure.
        self.llm = ChatOpenAI(
            openai_api_key=api_key,
            model_name=model_name,
            temperature=temperature
        )
        
    def test_connection(self) -> str:
        """
        Simple network handshake diagnostic.
        """
        try:
            response = self.llm.invoke("Hello, are you ready to compile some SQL?")
            return response.content
        except Exception as e:
            return f"❌ Connection Error: {str(e)}"

if __name__ == "__main__":
    # Why: Quick local trace debugging.
    engine = LLMEngine()
    print("Initiating OpenAI Handshake...")
    print(f"Handshake response: {engine.test_connection()}")
