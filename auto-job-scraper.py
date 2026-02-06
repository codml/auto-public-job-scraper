import requests
import json
import os
from datetime import datetime

# 1. 설정 및 상수 정의
API_KEY = os.environ.get("API_KEY")  # Github Secrets에서 가져옴
API_URL = "https://apis.data.go.kr/1051000/recruitment"

# PDF에서 추출한 필터링 코드 적용
PARAMS = {
    "serviceKey": API_KEY,
    "page": 1,
    "perPage": 100,
    "returnType": "json",
    
    # 문서 기반 코드 적용
    "hire_se_code": "R2010",    # 신입 
    "ncs_cd": "R600020",        # 정보통신(전산직) 
    
    # 금융 기관 필터링은 API 파라미터 지원 여부에 따라 여기서 하거나, 아래 for문에서 처리합니다.
    # 만약 API가 기관분류 파라미터를 지원한다면: "inst_clsf": "02" 
}

def fetch_jobs():
    try:
        response = requests.get(API_URL, params=PARAMS)
        response.raise_for_status()
        data = response.json()
        
        # 데이터 구조는 API마다 다를 수 있으므로 'data' 키나 'dataList' 등을 확인해야 합니다.
        # 예시: data['data'] 리스트를 순회
        return data.get('data', [])
    except Exception as e:
        print(f"API 호출 중 오류 발생: {e}")
        return []

def filter_financial_jobs(jobs):
    financial_jobs = []
    for job in jobs:
        # [중요] 문서 3.4절에 따라 기관분류(INST_CLSF)가 '02'(금융)인 경우만 추출 
        # API 응답 필드명에 따라 'instClsf', 'inst_clsf', 또는 기관유형 코드를 확인해야 함
        # 데이터에 코드가 없다면 기관명 리스트로 필터링해야 할 수도 있습니다.
        
        # 예시 로직: 응답 데이터에 기관 분류 코드가 포함되어 있다고 가정
        if job.get('instClsf') == '02' or job.get('inst_clsf') == '02':
            financial_jobs.append(job)
            
        # (대안) 코드가 안 넘어오는 경우 기관명에 '금융', '은행', '보증' 등이 포함된 경우 등
        # elif any(keyword in job.get('instNm', '') for keyword in ['금융', '은행', '투자', '신용', '기술보증']):
        #     financial_jobs.append(job)
            
    return financial_jobs

def update_readme(jobs):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    readme_content = f"""# 🏦 금융 공기업 전산직(IT) 채용 공고
(자동 업데이트: {current_time})

| 기관명 | 공고명 | 마감일 | 링크 |
|---|---|---|---|
"""
    
    if not jobs:
        readme_content += "| - | 현재 조건에 맞는 채용 공고가 없습니다. | - | - |\n"
    else:
        for job in jobs:
            # 필드명은 실제 API 응답에 맞춰 수정 필요 (예: recrutPbancTtl, pbancEndDe 등)
            name = job.get('instNm', '기관명')
            title = job.get('recrutPbancTtl', '공고명')
            end_date = job.get('pbancEndDe', '마감일')
            link = job.get('srcUrl', '#') # URL 필드가 있다면
            
            readme_content += f"| {name} | {title} | {end_date} | [바로가기]({link}) |\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

if __name__ == "__main__":
    all_jobs = fetch_jobs()
    target_jobs = filter_financial_jobs(all_jobs)
    update_readme(target_jobs)
    print(f"업데이트 완료: 총 {len(target_jobs)}건의 금융/IT 공고")