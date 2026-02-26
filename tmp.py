import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
import time

def extract_hrefs_from_html(html_content):
    """HTML 텍스트에서 특정 href 추출"""
    soup = BeautifulSoup(html_content, 'html.parser')
    hrefs = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith('/wk/a/b/1500/empDetailAuthView.do'):
            hrefs.append(href)
    return hrefs

def main():
    start_time = datetime.now()
    start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    # ★ 핵심 팁: resultCnt를 100으로 설정해서 페이지 수를 획기적으로 줄입니다!
    # pageIndex와 currentPageNo 부분만 {page} 변수로 포맷팅하도록 수정했습니다.
    base_url = "https://www.work24.go.kr/wk/a/b/1200/retriveDtlEmpSrchList.do?basicSetupYn=&careerTo=&keywordJobCd=&occupation=&seqNo=&cloDateEndtParam=&payGbn=&templateInfo=&rot2WorkYn=&shsyWorkSecd=&resultCnt=100&keywordJobCont=N&cert=&moreButtonYn=&minPay=&codeDepth2Info=11000&currentPageNo={page}&eventNo=&mode=&major=&resrDutyExcYn=&eodwYn=&sortField=DATE&staArea=&sortOrderBy=DESC&keyword=&termSearchGbn=&carrEssYns=&benefitSrchAndOr=O&disableEmpHopeGbn=&actServExcYn=&keywordStaAreaNm=N&maxPay=&emailApplyYn=&codeDepth1Info=11000&keywordEtcYn=&regDateStdtParam=&publDutyExcYn=&keywordJobCdSeqNo=&viewType=&exJobsCd=&templateDepthNmInfo=&region=&employGbn=&empTpGbcd=&computerPreferential=&infaYn=&cloDateStdtParam=&siteClcd=all&searchMode=Y&birthFromYY=&indArea=&careerTypes=&subEmpHopeYn=&tlmgYn=&academicGbn=&templateDepthNoInfo=&foriegn=&entryRoute=&mealOfferClcd=&basicSetupYnChk=&station=&holidayGbn=&srcKeyword=&academicGbnoEdu=noEdu&enterPriseGbn=&cloTermSearchGbn=&birthToYY=&keywordWantedTitle=N&stationNm=&benefitGbn=&keywordFlag=&notSrcKeyword=&essCertChk=&depth2SelCode=&keywordBusiNm=N&preferentialGbn=&rot3WorkYn=&regDateEndtParam=&pfMatterPreferential=&pageIndex={page}&termContractMmcnt=&careerFrom=&laborHrShortYn="

    # 서버에 '나 브라우저야' 라고 속이는 헤더 (가져오신 데이터 활용)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'Referer': 'https://www.work24.go.kr/wk/a/b/1200/retriveDtlEmpSrchList.do'
    }

    all_hrefs = []
    error_page = []
    
    # Session 객체를 사용하면 네트워크 연결을 유지해서 속도가 30% 이상 더 빨라집니다.
    with requests.Session() as session:
        session.headers.update(headers)
        
        print("첫 번째 페이지 접속 중...")
        # 1페이지 요청
        first_page_url = base_url.format(page=1)
        response = session.get(first_page_url)
        response.raise_for_status() # 에러 발생 시 프로그램 중단
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. 전체 게시글 수 파악
        txt_total_element = soup.find('span', class_='txt_total')
        if txt_total_element:
            txt_total = int(re.sub(r'[^\d]', '', txt_total_element.get_text()))
            print(f"전체 게시글 수: {txt_total}")
        else:
            print("경고: txt_total 요소를 찾을 수 없습니다. 테스트를 위해 임의 진행합니다.")
            txt_total = 1000
            
        # ★ 한 페이지당 100개씩 가져오므로 전체 페이지 수 계산 변경
        # total_page = (txt_total // 100) + (1 if txt_total % 100 > 0 else 0)
        
        # [주의] 테스트를 원하시면 아래 주석을 풀고 페이지 수를 줄이세요!
        total_page = 5
        
        # 2. 1페이지 링크 추출
        hrefs = extract_hrefs_from_html(response.text)
        all_hrefs.extend(hrefs)
        print(f"페이지 1/{total_page} 처리 완료 ({len(hrefs)}개 추출)")
        
        # 3. 2페이지부터 끝까지 반복
        for page_index in range(2, total_page + 1):
            next_url = base_url.format(page=page_index)
            
            try:
                resp = session.get(next_url)
                resp.raise_for_status()
                
                hrefs = extract_hrefs_from_html(resp.text)
                all_hrefs.extend(hrefs)
                print(f"페이지 {page_index}/{total_page} 처리 완료 ({len(hrefs)}개 추출)")
                
                # 서버에 과부하를 주지 않기 위해 아주 짧은 휴식 (Playwright보다 훨씬 짧아도 됨)
                time.sleep(0.3) 
                
            except Exception as e:
                print(f"에러 발생 - 페이지 {page_index}: {e}")
                error_page.append(page_index)

    # 4. 결과 HTML 파일 생성 (기존 로직과 동일)
    end_time = datetime.now()
    end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n=== 추출 완료 ===")
    print(f"추출된 총 링크 수: {len(all_hrefs)}")
    
    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>sentinel: work24(고용노동부) 동적 href 수집</title>
</head>
<body>
__time__
__error_pages__
__href_lists__
</body>
</html>
'''
    collected_time = end_time - start_time
    collected_time_str = str(collected_time).split('.')[0] 
    time_string = f'<p>점검 시작 시각: {start_time_str}</p> \n <p>점검 종료 시각: {end_time_str}</p>\n <p>수집 시간: {collected_time_str}</p>\n'
    html_template = html_template.replace('__time__', time_string)

    error_string = '<p style="color: red;">에러가 발생한 페이지: ' + ', '.join(map(str, error_page)) + '</p>\n' if error_page else ''
    html_template = html_template.replace('__error_pages__', error_string)

    string = ''
    for idx, href in enumerate(all_hrefs, 1):
        string += f'\t<a href="https://www.work24.go.kr{href}">{idx}번째 게시글</a><br>\n'

    html_template = html_template.replace('__href_lists__', string)
    
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
        print(f"\n결과가 'index.html' 파일로 저장되었습니다.")

if __name__ == "__main__":
    main()