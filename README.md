*请向下滚动以查看中文说明*

## Introduction

This software application is designed to perform the following functions:  

1. Given a .csv file containing a list of Digital Object Identifiers (DOIs) of "papers to be queried" listed row by row, the program automatically queries "which papers have cited them," and outputs the DOI, title, author(s), and publication year of each citing paper into a separate .csv file.  

2. Given the Crossref ID* of a journal, the program automatically retrieves all papers published in that journal, queries "which papers have cited them," and compiles the DOI, title, author(s), and publication year of each citing paper into a .csv file**.  

*The Crossref ID of a journal follows the format of "J" followed by a six-digit code (e.g., "J297249"). The six-digit code of the ID can be retrieved via the following link:  
https://www.crossref.org/titleList/  

**By default, the program will save the generated .csv files to the D: drive. If the D: drive is not available on your computer, the files will be stored in the current directory.

The intended users of this program include scholars and research institutions interested in tracking citation metrics of published papers, as well as publishers requiring statistical analysis of journal performance.

## Installation / Requirements

This program is written in Python 3. To run the source code, you need to install the required dependency:
```bash
pip install requests
```



## Acknowledgments

This software relies on the following open-source libraries and public data services to function. We gratefully acknowledge their contributions to the open science community:

*   **OpenAlex [<sup>1</sup>](https://openalex.org/)**: Used as a primary source for retrieving citation data and linking global research works.

*   **OpenCitations [<sup>2</sup>](https://opencitations.net/)**: Used to cross-reference citation links and ensure data completeness.

*   **Crossref [<sup>3</sup>](https://www.crossref.org/)**: Used for retrieving accurate metadata (titles, authors, publication years) and accessing journal depositor reports.

*   **Requests [<sup>4</sup>](https://requests.readthedocs.io/)**: An elegant and simple HTTP library for Python used to handle API requests.

Please note that while this tool is free to use, the data retrieved is subject to the usage policies of the respective API providers.

## License

This project is licensed under the MIT License.

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.



该程序的功能是：
1.给定一个.csv文件，文件中逐行记载了一批“待查询论文”的 DOI，自动查询“有哪些论文引用了它”，并把每条引用论文的 DOI、标题、作者、发表年份汇总输出到一个.csv文件
2.输入一本期刊的Crossref ID，自动获取这本期刊中的所有论文，自动查询“有哪些论文引用了它”，并把每条引用论文的DOI、标题、作者、发表年份汇总输出到一个.csv文件
其中，期刊的Crossref ID格式为J+6位数字组成的编码（例如"J297249"），其中数字部分可以在以下链接中查询获取：https://www.crossref.org/titleList/
本程序默认会将生成的.csv文件储存在D盘。如果您的电脑没有D盘，则保存到当前目录。
该程序的预期使用者是关心论文发表引用情况的学者、科研机构，以及需要统计期刊运营成果的出版社等。