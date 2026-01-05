#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论文引用查询工具
功能：查询论文被哪些文献引用，获取引用文献的DOI、标题和作者信息
"""

import csv
import sys
import os
import re
import time
import requests
from collections import OrderedDict
from datetime import datetime
from urllib.parse import unquote  # 用于处理URL编码的DOI

# API配置
OPENALEX_BASE_URL = "https://api.openalex.org"
OPENCITATIONS_BASE_URL = "https://opencitations.net/index/api/v1"
CROSSREF_BASE_URL = "https://api.crossref.org/works"
CROSSREF_DEPOSITORREPORT_URL = "https://data.crossref.org/depositorreport"

# 请求配置
REQUEST_TIMEOUT = 30
RETRY_COUNT = 3
DELAY_BETWEEN_REQUESTS = 0.5  # 秒

# 请求头
HEADERS = {
    "User-Agent": "CitationFinder/1.1 (mailto:your-email@example.com)",
    "Accept": "application/json"
}


def print_banner():
    """打印程序横幅"""
    print("=" * 70)
    print("                    论文引用查询工具")
    print("=" * 70)
    print("功能：查询论文被哪些文献引用")
    print("数据源：OpenAlex + OpenCitations + Crossref")
    print("=" * 70)
    print()


def normalize_doi(doi):
    """
    标准化DOI格式 (核心修复函数)
    1. URL解码 (处理 %2F, %28 等)
    2. 移除前缀
    3. 去除空格
    4. 转换为小写 (DOI大小写不敏感)
    """
    if not doi:
        return None
    
    # 1. 转换为字符串并解码 (处理 URL encoded 字符)
    doi = unquote(str(doi)).strip()
    
    # 2. 移除常见前缀 (忽略大小写)
    doi_lower = doi.lower()
    prefixes = [
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    ]
    
    for prefix in prefixes:
        if doi_lower.startswith(prefix):
            doi = doi[len(prefix):] # 移除前缀，保留原字符串的大小写用于后续处理
            break
    
    # 3. 再次去除可能存在的空格
    doi = doi.strip()
    
    # 4. 验证DOI格式 (宽松匹配，允许 10.xxxx/...)
    # 最终返回小写版本，确保全局唯一性
    if re.match(r'^10\.\d{4,}/.+$', doi, re.IGNORECASE):
        return doi.lower()
    
    return None


def read_dois_from_csv(file_path):
    """从CSV文件读取DOI列表"""
    dois = []
    
    try:
        # 尝试不同的编码
        encodings = ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    # 读取第一行检测编码是否正确
                    first_line = f.readline()
                    f.seek(0)
                    
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    
                    if not headers:
                        continue
                    
                    # 查找DOI列
                    doi_column = None
                    for header in headers:
                        if header and 'doi' in header.lower():
                            doi_column = header
                            break
                    
                    if not doi_column:
                        # 如果没有找到DOI列名，尝试在所有列中查找DOI格式的数据
                        f.seek(0)
                        reader = csv.reader(f)
                        next(reader)  # 跳过标题行
                        
                        for row in reader:
                            for cell in row:
                                doi = normalize_doi(cell)
                                if doi:
                                    dois.append(doi)
                    else:
                        for row in reader:
                            doi = normalize_doi(row.get(doi_column, ''))
                            if doi:
                                dois.append(doi)
                    
                    if dois:
                        break
                        
            except UnicodeDecodeError:
                continue
            except Exception as e:
                continue
        
        if not dois:
            print(f"警告：在文件 {file_path} 中未找到有效的DOI")
            
    except Exception as e:
        print(f"读取文件时出错: {e}")
    
    return dois


def make_request(url, params=None, retry=RETRY_COUNT):
    """发送HTTP请求，带重试机制"""
    for attempt in range(retry):
        try:
            response = requests.get(
                url, 
                params=params, 
                headers=HEADERS, 
                timeout=REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
            elif response.status_code == 429:  # Rate limited
                wait_time = (attempt + 1) * 5
                print(f"  请求频率限制，等待 {wait_time} 秒...")
                time.sleep(wait_time)
            else:
                time.sleep(1)
                
        except requests.exceptions.Timeout:
            print(f"  请求超时，重试 {attempt + 1}/{retry}")
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            print(f"  请求错误: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"  未知错误: {e}")
            time.sleep(1)
    
    return None


def is_crossref_depositor_pubid(value):
    """判断输入是否为 Crossref Depositor PubID（如 J645505）"""
    if not value:
        return False
    return re.fullmatch(r'[Jj]\d+', str(value).strip()) is not None
def make_text_request(url, params=None, retry=RETRY_COUNT):
    """发送HTTP请求获取文本，带重试机制"""
    for attempt in range(retry):
        try:
            headers = dict(HEADERS)
            headers["Accept"] = "text/plain"
            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=REQUEST_TIMEOUT
            )
            if response.status_code == 200:
                return response.text
            elif response.status_code == 404:
                return None
            elif response.status_code == 429:  # Rate limited
                wait_time = (attempt + 1) * 5
                print(f"  请求频率限制，等待 {wait_time} 秒...")
                time.sleep(wait_time)
            else:
                time.sleep(1)
        except requests.exceptions.Timeout:
            print(f"  请求超时，重试 {attempt + 1}/{retry}")
            time.sleep(2)
        except requests.exceptions.RequestException as e:
            print(f"  请求错误: {e}")
            time.sleep(1)
        except Exception as e:
            print(f"  未知错误: {e}")
            time.sleep(1)
    return None
def read_dois_from_crossref_depositor_report(pubid):
    """从Crossref Depositor Report获取DOI列表（按原顺序，不去重）"""
    text = make_text_request(CROSSREF_DEPOSITORREPORT_URL, params={"pubid": pubid})
    if not text:
        return []
    dois = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # 跳过表头行（以 DOI 开头）
        if line.upper().startswith("DOI"):
            continue
        # 第一列即 DOI
        first_col = line.split(None, 1)[0]
        doi = normalize_doi(first_col)
        if doi:
            dois.append(doi)
    return dois

def get_citations_from_openalex(doi):
    """从OpenAlex获取引用该DOI的文献"""
    citations = []
    
    try:
        # 首先获取该DOI对应的OpenAlex ID
        work_url = f"{OPENALEX_BASE_URL}/works/doi:{doi}"
        work_data = make_request(work_url)
        
        if not work_data:
            return citations
        
        openalex_id = work_data.get('id', '').replace('https://openalex.org/', '')
        cited_by_count = work_data.get('cited_by_count', 0)
        
        if cited_by_count == 0:
            return citations
        
        # 获取引用列表
        cursor = "*"
        page_count = 0
        max_pages = 50  # 限制最大页数
        
        while cursor and page_count < max_pages:
            citations_url = f"{OPENALEX_BASE_URL}/works"
            params = {
                "filter": f"cites:{openalex_id}",
                "per-page": 200,
                "cursor": cursor,
                "select": "doi,title,authorships,publication_year"
            }
            
            data = make_request(citations_url, params)
            
            if not data or 'results' not in data:
                break
            
            for work in data.get('results', []):
                raw_doi = work.get('doi', '')
                if raw_doi:
                    # 使用 normalize_doi 而非 replace
                    # 这能处理 https://doi.org/ 以及潜在的空格和编码问题
                    citing_doi = normalize_doi(raw_doi)
                    
                    if citing_doi:
                        citations.append({
                            'doi': citing_doi,
                            'title': work.get('title', ''),
                            'authors': extract_authors_from_openalex(work.get('authorships', [])),
                            'year': str(work.get('publication_year')) if work.get('publication_year') else '',
                            'source': 'OpenAlex'
                        })
            
            # 获取下一页游标
            meta = data.get('meta', {})
            cursor = meta.get('next_cursor')
            page_count += 1
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
    except Exception as e:
        print(f"  OpenAlex查询出错: {e}")
    
    return citations


def extract_authors_from_openalex(authorships):
    """从OpenAlex数据中提取作者名字"""
    authors = []
    
    for authorship in authorships:
        author_info = authorship.get('author', {})
        name = author_info.get('display_name', '')
        if name:
            authors.append(name)
    
    return authors


def get_citations_from_opencitations(doi):
    """从OpenCitations获取引用该DOI的文献"""
    citations = []
    
    try:
        # OpenCitations API
        url = f"{OPENCITATIONS_BASE_URL}/citations/{doi}"
        data = make_request(url)
        
        if not data:
            return citations
        
        for item in data:
            citing_doi = item.get('citing', '')
            if citing_doi:
                # OpenCitations返回的是完整DOI，需要清理
                citing_doi = normalize_doi(citing_doi)
                if citing_doi:
                    citations.append({
                        'doi': citing_doi,
                        'title': '',  # OpenCitations不提供标题
                        'authors': [],  # OpenCitations不提供作者
                        'year': '',
                        'source': 'OpenCitations'
                    })        
    except Exception as e:
        print(f"  OpenCitations查询出错: {e}")
    
    return citations


def get_metadata_from_crossref(doi):
    """从Crossref获取论文的标题、作者和发表年份"""
    try:
        url = f"{CROSSREF_BASE_URL}/{doi}"
        data = make_request(url)
        
        if not data or 'message' not in data:
            return None, [], ''
        
        message = data['message']
        
        # 获取标题
        title = ''
        titles = message.get('title', [])
        if titles:
            title = titles[0] if isinstance(titles, list) else titles
        
        # 获取作者
        authors = []
        author_list = message.get('author', [])
        for author in author_list:
            given = author.get('given', '')
            family = author.get('family', '')
            
            if given and family:
                full_name = f"{given} {family}"
            elif family:
                full_name = family
            elif given:
                full_name = given
            else:
                full_name = author.get('name', '')
            
            if full_name:
                authors.append(full_name.strip())
        
        # 获取发表年份（优先 issued，其次 published-print / published-online / created）
        year = ''
        for field in ['issued', 'published-print', 'published-online', 'created']:
            date_info = message.get(field, {})
            if isinstance(date_info, dict):
                date_parts = date_info.get('date-parts', [])
                if date_parts and isinstance(date_parts, list) and date_parts[0]:
                    year_value = date_parts[0][0] if len(date_parts[0]) > 0 else None
                    if year_value:
                        year = str(year_value)
                        break
        
        return title, authors, year
        
    except Exception as e:
        # Crossref 经常报 404，不打印详细错误以免刷屏，除非调试
        # print(f"  Crossref查询出错 ({doi}): {e}")
        return None, [], ''


def merge_citations(openalex_citations, opencitations_citations):
    """合并并去重来自不同来源的引用"""
    merged = OrderedDict()
    
    # 辅助函数：将引用添加到合并字典
    def add_to_merged(citations_list):
        for citation in citations_list:
            # 此时 citation['doi'] 已经被 normalize_doi 处理过，是小写且干净的
            doi = citation['doi']
            if doi not in merged:
                merged[doi] = citation
            else:
                # 如果已存在，尝试补充信息（例如OpenAlex有标题，OpenCitations没有）
                existing = merged[doi]
                if not existing['title'] and citation['title']:
                    existing['title'] = citation['title']
                if not existing['authors'] and citation['authors']:
                    existing['authors'] = citation['authors']
                if not existing.get('year') and citation.get('year'):
                    existing['year'] = citation['year']

    # 先添加OpenAlex的结果（通常信息更完整）
    add_to_merged(openalex_citations)
    
    # 添加OpenCitations的结果
    add_to_merged(opencitations_citations)
    
    return list(merged.values())


def enrich_citation_metadata(citations, progress_callback=None):
    """使用Crossref补全引用的元数据"""
    total = len(citations)
    
    for i, citation in enumerate(citations):
        if progress_callback:
            progress_callback(i + 1, total)
        
        # 如果缺少标题、作者或发表年份，从Crossref获取
        if not citation.get('title') or not citation.get('authors') or not citation.get('year'):
            title, authors, year = get_metadata_from_crossref(citation['doi'])
            
            if title and not citation.get('title'):
                citation['title'] = title
            
            if authors and not citation.get('authors'):
                citation['authors'] = authors
            if year and not citation.get('year'):
                citation['year'] = year
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
    
    return citations


def process_single_doi(doi, index, total):
    """处理单个DOI的引用查询"""
    print(f"\n[{index}/{total}] 正在处理: {doi}")
    
    # 从OpenAlex获取引用
    print("  → 查询OpenAlex...")
    openalex_citations = get_citations_from_openalex(doi)
    print(f"    找到 {len(openalex_citations)} 条引用")
    time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # 从OpenCitations获取引用
    print("  → 查询OpenCitations...")
    opencitations_citations = get_citations_from_opencitations(doi)
    print(f"    找到 {len(opencitations_citations)} 条引用")
    time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # 合并去重
    merged_citations = merge_citations(openalex_citations, opencitations_citations)
    print(f"  → 合并去重后: {len(merged_citations)} 条引用")
    
    # 使用Crossref补全信息
    if merged_citations:
        print("  → 从Crossref补全元数据 (可能较慢)...")
        
        def progress(current, total):
            if current % 5 == 0 or current == total:
                print(f"    进度: {current}/{total}")
        
        merged_citations = enrich_citation_metadata(merged_citations, progress)
    
    return merged_citations


def save_results_to_csv(results, output_path):
    """将结果保存到CSV文件"""
    try:
        # 确保目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            
            # 写入标题行
            writer.writerow([
                '被查询论文DOI',
                '引用论文DOI',
                '引用论文标题',
                '引用论文作者',
                '引用论文发表年份'
            ])
            
            # 写入数据
            for queried_doi, citations in results.items():
                if not citations:
                    # 如果没有引用，也写入一行表示
                    writer.writerow([queried_doi, '(无引用记录)', '', '', ''])
                else:
                    # 再次确保写入前没有重复 (虽然merge_citations已经处理过)
                    seen_citing_dois = set()
                    
                    for citation in citations:
                        citing_doi = citation.get('doi', '')
                        
                        # 如果这个引用DOI已经在这个源DOI下写过了，跳过
                        if citing_doi in seen_citing_dois:
                            continue
                        seen_citing_dois.add(citing_doi)
                        
                        authors_str = '; '.join(citation.get('authors', []))
                        writer.writerow([
                            queried_doi,
                            citing_doi,
                            citation.get('title', ''),
                            authors_str,
                            citation.get('year', '')
                        ])
        
        print(f"\n结果已保存至: {output_path}")
        return True
        
    except Exception as e:
        print(f"\n保存文件时出错: {e}")
        return False


def generate_summary_report(results):
    """生成摘要报告"""
    print("\n" + "=" * 70)
    print("                         查询结果摘要")
    print("=" * 70)
    
    total_queried = len(results)
    total_citations = sum(len(citations) for citations in results.values())
    
    print(f"查询论文总数: {total_queried}")
    print(f"找到引用总数: {total_citations}")
    print()
    
    # 按引用数排序
    sorted_results = sorted(results.items(), key=lambda x: len(x[1]), reverse=True)
    
    print("各论文引用情况:")
    print("-" * 70)
    
    for doi, citations in sorted_results[:20]:  # 只显示前20个
        print(f"  {doi[:50]:<50} | {len(citations):>5} 条引用")
    
    if len(sorted_results) > 20:
        print(f"  ... 以及其他 {len(sorted_results) - 20} 篇论文")
    
    print("-" * 70)


def main():
    """主函数"""
    print_banner()
    
    # 获取输入（CSV文件路径 或 Crossref PubID 代码）
    if len(sys.argv) > 1:
        input_value = sys.argv[1]
    else:
        print("请输入CSV文件路径（可直接拖拽文件到此处），或输入期刊对应的crossref编号（例如J297249）")
        input_value = input().strip().strip('"').strip("'")
    
    if not input_value:
        print("错误：未提供文件路径")
        input("按回车键退出...")
        return
    # 如果输入形如 J645505，则从 Crossref Depositor Report 获取 DOI 列表（不去重）
    if is_crossref_depositor_pubid(input_value):
        pubid = input_value.strip().upper()
        report_url = f"{CROSSREF_DEPOSITORREPORT_URL}?pubid={pubid}"
        print(f"\n正在从Crossref Depositor Report获取DOI列表: {report_url}")
        
        dois = read_dois_from_crossref_depositor_report(pubid)
        if not dois:
            print("错误：未从Depositor Report中找到有效的DOI")
            input("按回车键退出...")
            return
        
        unique_dois = dois  # 不合并去重
        print(f"找到 {len(unique_dois)} 个DOI")
    else:
        input_file = input_value
        if not os.path.exists(input_file):
            print(f"错误：文件不存在 - {input_file}")
            input("按回车键退出...")
            return
        
        # 读取DOI
        print(f"\n正在读取文件: {input_file}")
        dois = read_dois_from_csv(input_file)
        
        if not dois:
            print("错误：未在文件中找到有效的DOI")
            input("按回车键退出...")
            return
        
        # 去重 (使用OrderedDict保持顺序)
        unique_dois = list(OrderedDict.fromkeys(dois))
        print(f"找到 {len(dois)} 个DOI，去重后: {len(unique_dois)} 个")
    
    # 确认继续
    print(f"\n将要查询 {len(unique_dois)} 篇论文的引用情况")
    print("这可能需要一些时间，具体取决于引用数量...")
    
    confirm = input("\n是否继续？(y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消操作")
        return
    
    # 处理每个DOI
    results = OrderedDict()
    start_time = time.time()
    
    for i, doi in enumerate(unique_dois, 1):
        try:
            citations = process_single_doi(doi, i, len(unique_dois))
            results[doi] = citations
        except KeyboardInterrupt:
            print("\n\n用户中断操作")
            break
        except Exception as e:
            print(f"  处理出错: {e}")
            results[doi] = []
    
    # 计算耗时
    elapsed_time = time.time() - start_time
    print(f"\n查询完成，总耗时: {elapsed_time:.1f} 秒")
    
    # 生成摘要
    generate_summary_report(results)
    
    # 保存结果
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"Citation_Results_{timestamp}.csv"
    output_path = os.path.join("D:\\", output_filename)
    
    # 如果D盘不存在，保存到当前目录
    if not os.path.exists("D:\\"):
        output_path = os.path.join(os.getcwd(), output_filename)
        print(f"D盘不存在，将保存到当前目录")
    
    save_results_to_csv(results, output_path)
    
    print("\n" + "=" * 70)
    print("                         处理完成！")
    print("=" * 70)
    input("\n按回车键退出...")


if __name__ == "__main__":
    main()
