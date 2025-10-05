from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from .models import ResearchState, CompanyAnalysis, CompanyInfo
from .firecrawl import FirecrawlService
from .prompts import DeveloperToolsPrompts

"""
The whole point of a workflow class is to handle all nodes of our langgraph graph and to compile it as well. 
All Langgraph functionality will be written within the class itself and we can simply run the workflow from our main file.
"""

class Workflow:

    def __init__(self):
        self.firecrawl = FirecrawlService()     # Initialize our firecrawl service
        self.llm = ChatOpenAI(model='gpt-4o')   # Initialize our llm we plan to use
        self.prompts = DeveloperToolsPrompts()  # Initialize our dev tools so we can assess the various prompts we have setup
        self.workflow = self._build_graph()        # This function will build the graph itself with the nodes and edges and stuff


    def _build_graph(self):

        # Our graph will have the state outlined in ResearchState
        graph = StateGraph(ResearchState)

        # Our graph will have the following nodes
        graph.add_node("extract_tools", self._extract_tools_step)
        graph.add_node("research", self._research_tools_step)
        graph.add_node("analyze", self._analyze_step)

        """
        The graph is simple in concept with just 3 steps:

        Extract tools -> Research Tools -> Analyze Research -> Output

        For each step, we have functions that handle the inputs and outputs and we have a structured way of transferring data
        from one step to another due to the schemas we defined within the models class. 
        """

        # Linear graph; very simple structure
        graph.add_edge(START, "extract_tools")
        graph.add_edge("extract_tools", "research")
        graph.add_edge("research", "analyze")
        graph.add_edge("analyze", END)

        return graph.compile()


    # Method to run the entire workflow from an external script
    def run(self, query:str) -> ResearchState:

        # Initialize our state
        initial_state = ResearchState(query=query)
        
        # Return the final state after the workflow is complete
        final_state = self.workflow.invoke(initial_state)

        # We unpack the final_state and store all the values into a new ResearchState Object and return it
        return ResearchState(**final_state)
    

    # Step 1: Extract Tools by searching the web and using an LLM to get the tool names out of the scraped content
    def _extract_tools_step(self, state: ResearchState) -> Dict[str, Any]:      # Rmr we are updating now by returning a dict where the key is the state variable we want to update and the value is its new state
        """
        The goal with this step is to find a proper list of alternatives to the tool provided in the query 
        or anything else as requested by the user. 
        """
        
        print(f"🔍 Finding articles about: {state.query}")      # Log the current step

        article_query = f"{state.query} tools comparison best alternatives"     # Our search query for scraping the web

        # After getting the search results from firecrawl, parse through them
        search_results = self.firecrawl.search_companies(article_query)

        all_content = ""        # Append all search results content to an empty string
        for result in search_results.data:
            url = result.get("url", "")     # Get the url of each search result
            scraped = self.firecrawl.scrape_company_pages(url)      # Scrape the URL of each search result
            if scraped:
                all_content + scraped.markdown[:1500] + "\n\n"      # Add the first 1500 characters of the scraped content of the url in markdown format

        # Make a list of messages to pass into the LLM 
        messages = [
            SystemMessage(content=self.prompts.TOOL_EXTRACTION_SYSTEM),
            HumanMessage(content=self.prompts.tool_extraction_user(state.query, all_content))
        ]

        try:
            response = self.llm.invoke(messages)        # Get the response from the LLM after passing in the user query and the scraped website content
            tool_names = [name.strip() for name in response.content.strip().split("\n") if name.strip()]    # Make a list of only tool names because rmr your system prompt told it to do that
            print(f"Extracted Tools: {", ".join(tool_names[:5])}")      # Display the first 5 tools extracted for the user to see
            return {"extracted_tools": tool_names}      # Now we update our state variable with the tool_names list that we extracted from the web

        except Exception as e:
            print(f"An Error Occured Whilst Communicating with the LLM: {e}")
            return {"extracted_tools": []}      # You don't wanna raise an error and mess up the whole system


    # Step 2: Research
    def _research_tools_step(self, state:ResearchState) -> Dict[str, Any]:
        extracted_tools = getattr(state, "extracted_tools", [])         # Get the extracted tools from step 1 and if none then get empty []

        if not extracted_tools:         # If no extracted tools found, try to find them using direct search of the query 

            print("⚠️ No extracted tools found, falling back to direct search")

            search_results = self.firecrawl.search_companies(state.query, num_results=4)        # Search for companies again with user's query this time
            tool_names = [
                result.get("metadata", {}).get("title", "Unknown")              # Instead of using LLM call, get tool names from metadata this time
                for result in search_results.data
            ]       
        else:
            tool_names = extracted_tools[:4]           # Get the first 4 tools only

        print(f"🔬 Researching specific tools: {', '.join(tool_names)}")       


        # Now for each tool name, we are going to make a web search and find its company information
        companies = []
        for tool_name in tool_names:
            tool_search_results = self.firecrawl.search_companies(tool_name + " official site", num_results=1)  # Search for tool company name

            if tool_search_results:
                result = tool_search_results.data[0]        # Description of the company
                url = result.get("url", "")                 # Url of the company's website; now we need to scrape this
                
                # Add some company info that we already have to an object that we will append to our List initialize above of companies
                company = CompanyInfo(
                    name=tool_name,
                    description=result.get("markdown", ""),
                    website=url,
                    tech_stack=[],
                    competitors=[]
                )

                scraped = self.firecrawl.scrape_company_pages(url)          # Scrape the current company's website

                if scraped:
                    content = scraped.markdown

                    # Call the analyze function which uses an llm to turn instructured markdown content into structured data
                    analysis = self._analyze_company_content(company.name, content)

                    company.pricing_model = analysis.pricing_model          # Recall that analysis is a CompanyAnalysis object
                    company.is_open_source = analysis.is_open_source
                    company.tech_stack = analysis.tech_stack
                    company.description = analysis.description
                    company.api_available = analysis.api_available
                    company.language_support = analysis.language_support
                    company.integration_capabilities = analysis.integration_capabilities

                companies.append(company)       # Add to the list of companies

        return {"companies": companies}     # Update the state with the new companies as a list of CompanyInfo objects
    
    # Helper function for research step
    def _analyze_company_content(self, company_name: str, content:str) -> CompanyAnalysis:
        """
        Given the company name and the markdown content from its website, we parse the markdown and convert it into structured 
        data according to the CompanyAnalysis Schema after which we can take that data and add it to the CompanyInfo schema
        """

        # First we need to create a structured llm based on a schema
        structured_llm = self.llm.with_structured_output(CompanyAnalysis)

        # Then we need to create the prompt
        messages = [
            SystemMessage(content=self.prompts.TOOL_ANALYSIS_SYSTEM),
            HumanMessage(content=self.prompts.tool_analysis_user(company_name, content))
        ]

        try:
            # get the response
            analysis = structured_llm.invoke(messages)
            return analysis
        except Exception as e:
            print(e)

            return CompanyAnalysis(             # If llm call doesn't work, return default values
                pricing_model="Unknown",
                is_open_source=None,
                tech_stack=[],
                description="Failed",
                api_available=None,
                language_support=[],
                integration_capabilities=[],
            )


    # Step 3: Analysis
    def _analyze_step(self, state:ResearchState) -> Dict[str, Any]:
        print("Generating recommendations")

        company_data = ", ".join([                                  # Join all the company data into one string
            company.json() for company in state.companies
        ])


        # Make the recommendations prompt
        messages = [
            SystemMessage(content=self.prompts.RECOMMENDATIONS_SYSTEM),
            HumanMessage(content=self.prompts.recommendations_user(state.query, company_data))
        ]

        # Get the response from the llm
        response = self.llm.invoke(messages)
        return {"analysis": response.content}           # Update the state with the response
