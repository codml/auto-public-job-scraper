import requests
import json
import os
from datetime import datetime

# 1. 설정 및 상수 정의
API_KEY = os.environ.get("API_KEY")  # Github Secrets에서 가져옴
API_URL = "https://apis.data.go.kr/1051000/recruitment/list"

def fetch_all_jobs(max_pages=10):
    """1페이지부터 max_pages까지 데이터를 모두 수집하여 리스트로 반환"""
    aggregated_jobs = []
    
    for page in range(1, max_pages + 1):
        params = {
            "serviceKey": API_KEY,
            "page": page,
            "perPage": 10,       # 페이지당 최대 10개
            "returnType": "json",
            
            # [코드 정의서 기반 필터링 파라미터]
            # 실제 API 파라미터 변수명(key)은 API 명세서를 확인하여 수정 필요
            "hire_se_code": "R2010",   # 신입 
            "ncs_cd": "R600020",       # 정보통신(전산직) 
        }
        
        try:
            print(f"Fetching page {page}...")
            response = requests.get(API_URL, params=params, timeout=10)
            
            # 에러 처리
            if response.status_code != 200:
                print(f"Error on page {page}: {response.status_code}")
                continue
                
            data = response.json()
            
            # 응답 구조에 따라 키 이름 변경 필요 (예: 'result', 'data', 'body' 등)
            # 여기서는 일반적인 구조인 'result' 혹은 'data'로 가정
            items = data.get('result', []) 
            if not items:
                items = data.get('data', [])
            
            if not items:
                print(f"Page {page} is empty. Stopping loop.")
                break
                
            aggregated_jobs.extend(items)
            
        except Exception as e:
            print(f"Exception on page {page}: {e}")
            break
            
    return aggregated_jobs

def calculate_d_day(end_date_str):
    """마감일 문자열(YYYYMMDD or YYYY-MM-DD)을 받아 D-Day와 상태 아이콘 반환"""
    try:
        # 날짜 형식이 다양할 수 있어 정제
        end_date_str = end_date_str.replace("-", "").replace(".", "")[:8]
        end_date = datetime.strptime(end_date_str, "%Y%m%d")
        today = datetime.now()
        delta = (end_date - today).days + 1 # 당일 포함 계산
        
        if delta < 0:
            return "마감", "⚫"
        elif delta == 0:
            return "D-Day", "🔥"
        elif delta <= 3:
            return f"D-{delta}", "🚨"
        else:
            return f"D-{delta}", "🟢"
    except:
        return "-", "⚪"

def update_readme(jobs):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # README 헤더 작성
    content = f"""# 🏦 공기업 전산직(IT) 채용 현황
> **업데이트 시간:** {current_time} (한국 시간 기준)
>
> 🔍 **조건:** 신입 | 전산직(정보통신)

<br>

## 📋 채용 공고 목록 ({len(jobs)}건)

| 상태 | D-Day | 기관명 | 공고명 | 마감일 | 링크 |
|:---:|:---:|---|---|:---:|:---:|
"""

    if not jobs:
        content += "| ⚪ | - | - | 현재 조건에 맞는 공고가 없습니다. | - | - |\n"
    else:
        for job in jobs:
            # 필드명 매핑 (API 실제 응답 키값으로 수정 필수)
            inst_name = job.get('instNm', '기관명 없음')
            title = job.get('recrutPbancTtl', '제목 없음')
            end_date_raw = job.get('pbancEndDe', '20991231')
            url = job.get('srcUrl', '')
            
            d_day_str, status_icon = calculate_d_day(end_date_raw)
            
            # 마감된 공고는 리스트에서 제외하고 싶다면 여기서 continue 처리
            if d_day_str == "마감":
                continue

            # 링크 버튼 처리
            link_md = f"[바로가기]({url})" if url else "-"
            
            content += f"| {status_icon} | **{d_day_str}** | {inst_name} | {title} | {end_date_raw} | {link_md} |\n"

    content += """
<br>

---
*이 페이지는 GitHub Actions에 의해 매일 자동 업데이트됩니다.*
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    print("Starting job update process...")
    
    # 1. 데이터 수집 (최대 10페이지)
    all_data = fetch_all_jobs(max_pages=10)
    print(f"Total items fetched: {len(all_data)}")
    
    # 3. README 작성
    update_readme(all_data)
    print("README.md updated successfully.")
