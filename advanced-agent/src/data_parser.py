import json
from typing import List, Optional, Dict, Any
from .models import CompanyAnalysis

def parse_search_results_for_content(search_results: Optional[object], scrape_func) -> str:
    """
    从 Firecrawl 的搜索结果中提取并组合所有页面的 Markdown 内容。
    """
    all_content = ""
    if not (search_results and hasattr(search_results, 'web')):
        return all_content

    for result in search_results.web:
        url = None
        if hasattr(result, 'metadata') and hasattr(result.metadata, 'url'):
            url = result.metadata.url
        elif hasattr(result, 'url'):
            url = result.url
        
        if not url:
            print("⚠️ 无法处理的搜索结果格式:", result)
            continue

        print(f"抓取页面内容: {url}")
        scraped = scrape_func(url)
        if scraped and hasattr(scraped, 'markdown') and scraped.markdown:
            all_content += scraped.markdown[:2000] + "\n\n" # 增加单页内容长度
            
    return all_content

def clean_llm_tool_extraction(response_content: str, original_query: str) -> List[str]:
    """
    清理 LLM 返回的工具列表，移除引导语、编号和原始查询词。
    """
    tool_names = []
    lines = response_content.split("\n")
    query_lower = original_query.lower()

    for name in lines:
        clean_name = name.strip()
        # 过滤掉空行、引导语和包含原始查询词的行
        if clean_name and "based on the" not in clean_name.lower() and "here are" not in clean_name.lower():
            # 去掉 "1. ToolName" 这种格式中的编号
            if "." in clean_name:
                clean_name = clean_name.split(".", 1)[1].strip()
            
            # 确保不添加与原始查询词相同的工具
            if clean_name.lower() != query_lower:
                tool_names.append(clean_name)
                
    return tool_names

def parse_company_analysis_from_llm(response_str: str) -> CompanyAnalysis:
    """
    从 LLM 的原始字符串回复中提取并解析 JSON, 返回 CompanyAnalysis 对象。
    """
    # 1. 找到第一个 '{' 和最后一个 '}' 的位置
    start_index = response_str.find('{')
    end_index = response_str.rfind('}')
    
    # 2. 如果都找到了，就提取它们之间的子字符串
    if start_index != -1 and end_index != -1 and end_index > start_index:
        json_str = response_str[start_index : end_index + 1]
    else:
        raise ValueError("Could not find a valid JSON object in the LLM response.")

    # 3. 解析提取出的纯净 JSON 字符串
    data = json.loads(json_str)
    
    analysis = CompanyAnalysis(**data)

    # 4. 校验和修复，防止 NoneType 错误
    if analysis.tech_stack is None:
        analysis.tech_stack = []
    if analysis.language_support is None:
        analysis.language_support = []
    if analysis.integration_capabilities is None:
        analysis.integration_capabilities = []
    
    return analysis

def get_url_and_content_from_search_result(result: object) -> (Optional[str], Optional[str]):
    """从单个搜索结果对象中提取 URL 和 Markdown 内容。"""
    url = None
    content = None
    if hasattr(result, 'metadata') and hasattr(result.metadata, 'url'):
        url = result.metadata.url
    elif hasattr(result, 'url'):
        url = result.url
    
    if hasattr(result, 'markdown') and result.markdown:
        content = result.markdown
        
    return url, content