from typing import Any, Dict
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from .models import ResearchState, CompanyInfo
from .firecrawl import FirecrawlService
from .prompts import DeveloperToolsPrompts
# 导入新的数据处理模块
from . import data_parser

class Workflow:
    def __init__(self):
        self.firecrawl = FirecrawlService()
        self.llm = ChatOpenAI(
            model="deepseek/deepseek-chat-v3.1:free", 
            base_url="https://openrouter.ai/api/v1",
            temperature=0.1 )
        self.prompts = DeveloperToolsPrompts()
        self.workflow = self._build_workflow()

    def _build_workflow(self):
        graph = StateGraph(ResearchState)
        graph.add_node("extract_tools", self._extract_tools_step)
        graph.add_node("research", self._research_step)
        graph.add_node("analyze", self._analyze_step)
        graph.set_entry_point("extract_tools")
        graph.add_edge("extract_tools", "research")
        graph.add_edge("research", "analyze")
        graph.add_edge("analyze", END)
        return graph.compile()

    def _extract_tools_step(self, state: ResearchState) -> Dict[str, Any]:
        print(f"🔍 Finding articles about : {state.query}")
        article_query = f"{state.query} tools comparison best alternatives"
        
        search_results = self.firecrawl.search_companies(article_query, num_results=3)
        
        # 调用数据处理函数来获取内容
        all_content = data_parser.parse_search_results_for_content(
            search_results, 
            self.firecrawl.scrape_company_page
        )

        messages = [
            SystemMessage(content=self.prompts.TOOL_EXTRACTION_SYSTEM),
            HumanMessage(content=self.prompts.tool_extraction_user(state.query, all_content))
        ]

        try:
            response = self.llm.invoke(messages)
            # 调用数据处理函数来清理工具列表
            tool_names = data_parser.clean_llm_tool_extraction(response.content, state.query)

            print(f"✅ Extracted tools: {', '.join(tool_names[:5])}")
            return {"extracted_tools": tool_names}
        except Exception as e:
            print(f"⚠️ Error during tool extraction: {e}")
            return {"extracted_tools": []}

    def _research_step(self, state: ResearchState) -> Dict[str, Any]:
        original_tool = state.query
        extracted_alternatives = state.extracted_tools

        # 1. 组合原始工具和替代品
        tools_to_research = [original_tool] + [
            tool for tool in extracted_alternatives if tool.lower() != original_tool.lower()
        ]
        
        # 2. 确定最终要研究的工具列表（最多4个）
        tool_names = tools_to_research[:4]

        print(f"🔬 Researching specific tools (including original): {', '.join(tool_names)}")
        print()

        companies = []
        for tool_name in tool_names:
            tool_search_results = self.firecrawl.search_companies(tool_name + " official site", num_results=1)
            
            if not (tool_search_results and tool_search_results.web):
                print(f"⚠️ No search results found for tool: {tool_name}")
                continue

            result = tool_search_results.web[0]
            # 调用数据处理函数获取 URL 和 content
            url, content = data_parser.get_url_and_content_from_search_result(result)
            
            if not url:
                print(f"⚠️ No URL found for tool: {tool_name}")
                continue

            if not content:
                scraped = self.firecrawl.scrape_company_page(url)
                if scraped and scraped.markdown:
                    content = scraped.markdown

            company = CompanyInfo(name=tool_name, description="", website=url)

            if content:
                analysis = self._analyze_company_content(company.name, content)
                company.pricing_model = analysis.pricing_model
                company.is_open_source = analysis.is_open_source
                company.tech_stack = analysis.tech_stack
                company.description = analysis.description
                company.api_available = analysis.api_available
                company.language_support = analysis.language_support
                company.integration_capabilities = analysis.integration_capabilities
            else:
                print(f"⚠️ Could not retrieve content for {tool_name}")
                company.description = "Content retrieval failed."

            companies.append(company)
            
        return {"companies": companies}

    def _analyze_company_content(self, company_name: str, content: str) -> Dict[str, Any]:
        print(f"   ...Analyzing content for {company_name}")
        
        clean_content = " ".join(content.split())[:8000]
        messages = [
            SystemMessage(content=self.prompts.TOOL_ANALYSIS_SYSTEM),
            HumanMessage(content=self.prompts.tool_analysis_user(company_name, clean_content))
        ]
        try:
            response_str = self.llm.invoke(messages).content
            # 调用数据处理函数解析 LLM 的响应
            return data_parser.parse_company_analysis_from_llm(response_str)
        except Exception as e:
            print(f"   ❌ Error during company analysis for {company_name}: {e}")
            # 返回一个符合 CompanyAnalysis 结构的默认失败对象
            return CompanyInfo(
                pricing_model="Unknown", description="Analysis failed due to an error."
            )

    def _analyze_step(self, state: ResearchState) -> Dict[str, Any]:
        print("正在生成最终建议...")
        company_data = ", ".join([c.model_dump_json() for c in state.companies])
        messages = [
            SystemMessage(content=self.prompts.RECOMMENDATIONS_SYSTEM),
            HumanMessage(content=self.prompts.recommendations_user(state.query, company_data))
        ]
        response = self.llm.invoke(messages)
        return {"analysis": response.content}
        
    def run(self, query: str) -> ResearchState:
        initial_state = ResearchState(query=query)
        final_state = self.workflow.invoke(initial_state)
        return ResearchState(**final_state)