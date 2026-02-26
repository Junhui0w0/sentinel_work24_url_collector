from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import time
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

def extract_hrefs_from_page(page):
    """페이지에서 /wk/a/b/1500/empDetailAuthView.do로 시작하는 모든 href 추출"""
    html_content = page.content()
    soup = BeautifulSoup(html_content, 'html.parser')
    
    hrefs = []
    # <a href="/wk/a/b/1500/empDetailAuthView.do?로 시작하는 모든 a 태그 찾기
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith('/wk/a/b/1500/empDetailAuthView.do'):
            hrefs.append(href)
    
    return hrefs

def update_page_index(url, new_page_index):
    """URL의 pageIndex 값을 업데이트"""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    params['pageIndex'] = [str(new_page_index)]
    
    # URL 재구성
    new_query = urlencode(params, doseq=True)
    new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
    return new_url

def main():
    main_url = "https://www.work24.go.kr/wk/a/b/1200/retriveDtlEmpSrchList.do?ba" \
    "sicSetupYn=&careerTo=&keywordJobCd=&occupation=&seqNo=&cloDateEndtParam=&payGbn=&templateInfo=&rot2WorkYn=&shsyWorkSecd=&resultCnt=50&keywordJobCont=N&cert=&moreButtonYn=&minPay=&codeDepth2Info=11000&currentPageNo=2380&eventNo=&mode=&major=&resrDutyExcYn=&eodwYn=&sortField=DATE&staArea=&sortOrderBy=DESC&keyword=&termSearchGbn=&carrEssYns=&benefitSrchAndOr=O&disableEmpHopeGbn=&actServExcYn=&keywordStaAreaNm=N&maxPay=&emailApplyYn=&codeDepth1Info=11000&keywordEtcYn=&regDateStdtParam=&publDutyExcYn=&keywordJobCdSeqNo=&viewType=&exJobsCd=&templateDepthNmInfo=&region=&employGbn=&empTpGbcd=1&computerPreferential=&infaYn=&cloDateStdtParam=&siteClcd=all&searchMode=Y&birthFromYY=&indArea=&careerTypes=&subEmpHopeYn=&tlmgYn=&academicGbn=&templateDepthNoInfo=&foriegn=&entryRoute=&mealOfferClcd=&basicSetupYnChk=&station=&holidayGbn=&srcKeyword=&academicGbnoEdu=noEdu&enterPriseGbn=&cloTermSearchGbn=&birthToYY=&keywordWantedTitle=N&stationNm=&benefitGbn=&keywordFlag=&notSrcKeyword=&essCertChk=&depth2SelCode=&keywordBusiNm=N&preferentialGbn=&rot3WorkYn=&regDateEndtParam=&pfMatterPreferential=&pageIndex=1&termContractMmcnt=&careerFrom=&laborHrShortYn="
    
    all_hrefs = []
    txt_total = 0
    error_page = []
    
    with sync_playwright() as p:
        # 브라우저 실행
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print(f"첫 번째 페이지 접속 중: {main_url}")
        page.goto(main_url)
        
        # 동적 컨텐츠 로딩 대기
        page.wait_for_load_state('networkidle')
        time.sleep(2)  # 추가 대기
        
        # HTML 추출
        html_content = page.content()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. txt_total 추출 - <span class="txt_total"> 태그의 텍스트
        txt_total_element = soup.find('span', class_='txt_total')
        if txt_total_element:
            txt_total_text = txt_total_element.get_text().strip()
            # 숫자만 추출 (쉼표 제거)
            txt_total = int(re.sub(r'[^\d]', '', txt_total_text))  # +1은 페이지 인덱스가 1부터 시작하기 때문
            # txt_total = 10 # 테스트를 위해 10으로 고정
            print(f"전체 게시글 수 (txt_total): {txt_total}")
        else:
            print("경고: txt_total 요소를 찾을 수 없습니다.")
            browser.close()
            return
        
        # cur_page = txt_total // 50 + 1
        cur_page = 10  # 테스트를 위해 10으로 고정


        # 2. 첫 페이지의 href 추출
        print(f"\n페이지 1/{cur_page} 처리 중...")
        hrefs = extract_hrefs_from_page(page)
        all_hrefs.extend(hrefs)
        print(f"페이지 1에서 {len(hrefs)}개의 링크 추출")

        if len(hrefs) != 50:
            print(f"경고: 페이지 1에서 예상된 50개의 링크가 아닌 {len(hrefs)}개의 링크가 추출되었습니다.")
            error_page.append(cur_page)
        
        # 3. pageIndex를 2부터 cur_page까지 반복
        for page_index in range(2, cur_page + 1):
            print(f"\n페이지 {page_index}/{cur_page} 처리 중...")
            
            # URL의 pageIndex 업데이트
            next_url = update_page_index(main_url, page_index)
            
            # 페이지 이동
            page.goto(next_url)
            page.wait_for_load_state('networkidle')
            time.sleep(1)  # 추가 대기
            
            # href 추출
            hrefs = extract_hrefs_from_page(page)
            all_hrefs.extend(hrefs)
            print(f"페이지 {page_index}에서 {len(hrefs)}개의 링크 추출")
        
        browser.close()
    
    # 결과 출력
    print(f"\n\n=== 추출 완료 ===")
    print(f"전체 게시글 수 (txt_total): {txt_total}")
    print(f"추출된 총 링크 수: {len(all_hrefs)}")
    print(f"\n추출된 링크 목록:")

    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="UTF-8">
	<meta name="viewport" content="width=device-width, initial-scale=1.0">
	<title>Document</title>
</head>
<body>
__replacement__
</body>
</html>
'''

    string = ''
    for idx, href in enumerate(all_hrefs, 1):
        print(f"https://www.work24.go.kr{href}")
        string += f'\t<a href="https://www.work24.go.kr{href}">{idx}번째 게시글</a><br>\n'


    html_template = html_template.replace('__replacement__', string)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_template)

        print(f"\n결과가 'index.html' 파일로 저장되었습니다.")

if __name__ == "__main__":
    main()