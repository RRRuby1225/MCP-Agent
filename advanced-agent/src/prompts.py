
class DeveloperToolsPrompts:
    """Collection of prompts for analyzing developer tools and technologies"""

    # Tool extraction prompts
    TOOL_EXTRACTION_SYSTEM ="""You are a senior solutions architect specializing in developer tool ecosystems. 
                            Your expertise lies in identifying competing and alternative platforms, not just related technologies. 
                            You are precise and ignore tools that are merely components or partners of the queried tool."""

    @staticmethod
    def tool_extraction_user(query: str, content: str) -> str:
        return f"""
                Primary Tool for Comparison: "{query}"

                Article Content to Analyze:
                ---
                {content}
                ---

                Your Task:
                From the article content, extract a list of tools that are direct **alternatives** or **competitors** to "{query}".
                This means they should solve the same core problem and target a similar developer need.

                Critical Rules to Follow:
                1.  **Focus on "Replacement" Relationship**: The extracted tools must be something a developer would choose **instead of** "{query}", not **in addition to** "{query}".
                2.  **Strictly Exclude Ecosystem Partners**: Do NOT extract tools that are foundational models (like OpenAI), vector databases (like Pinecone), cloud providers (like AWS), or any other tool that integrates with or is a component used by "{query}".
                3.  **Limit to the Top 5**: Return only the 5 most relevant and direct alternatives.
                4.  **Clean, List-Only Output**: Return just the tool names, one per line. No numbers, no bullet points, no explanations.

                Examples to guide your judgment for the query "{query}":
                'langchain':
                positive_examples = "    - Good examples of alternatives: LangGraph, LlamaIndex, CrewAI, Flowise"
                negative_examples = "    - Bad examples (do NOT include): OpenAI, Gemini, Pinecone, ChromaDB, Streamlit"

                Example Output Format:
                Supabase
                Appwrite
                Nhost
                """

    # Company/Tool analysis prompts
    TOOL_ANALYSIS_SYSTEM = """You are analyzing developer tools and programming technologies. 
                            Focus on extracting information relevant to programmers and software developers. 
                            Pay special attention to programming languages, frameworks, APIs, SDKs, and development workflows."""

    @staticmethod
    def tool_analysis_user(company_name: str, content: str) -> str:
        return f"""Company/Tool: {company_name}
                Website Content: {content[:2500]}

                Analyze this content from a developer's perspective and provide:
                - pricing_model: One of "Free", "Freemium", "Paid", "Enterprise", or "Unknown"
                - is_open_source: true if open source, false if proprietary, null if unclear
                - tech_stack: List of programming languages, frameworks, databases, APIs, or technologies supported/used
                - description: Brief 1-sentence description focusing on what this tool does for developers
                - api_available: true if REST API, GraphQL, SDK, or programmatic access is mentioned
                - language_support: List of programming languages explicitly supported (e.g., Python, JavaScript, Go, etc.)
                - integration_capabilities: List of tools/platforms it integrates with (e.g., GitHub, VS Code, Docker, AWS, etc.)

                Focus on developer-relevant features like APIs, SDKs, language support, integrations, and development workflows."""

    # Recommendation prompts
    RECOMMENDATIONS_SYSTEM = """You are a senior software engineer providing quick, concise tech recommendations. 
                            Keep responses brief and actionable - maximum 3-4 sentences total."""

    @staticmethod
    def recommendations_user(query: str, company_data: str) -> str:
        return f"""Developer Query: {query}
                Tools/Technologies Analyzed: {company_data}

                Provide a brief recommendation (3-4 sentences max) covering:
                - Which tool is best and why
                - Key cost/pricing consideration
                - Main technical advantage

                Be concise and direct - no long explanations needed."""