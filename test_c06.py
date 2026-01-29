"""
Test C06 case to debug Rule Filter behavior
"""
from src.llm.gemini_detector import GeminiPhishingDetector

text = '한국장학재단입니다. 부모님 소득 정보 오류로 장학금 환수 대상이 되셨어요. 이의 신청하시려면 재단 사이트(kosaf-support.com) 가셔서 증빙 서류 제출 앱을 까셔야 합니다.'

print('=== C06 케이스 테스트 (장학금 위장) ===')
print(f'텍스트: {text}')
print()

detector = GeminiPhishingDetector()
result = detector.analyze(text, enable_filter=True)

print(f'최종 점수: {result["score"]}')
print(f'LLM 원점수: {result["llm_score"]}')
print(f'Rule Filter 적용: {result["filter_applied"]}')
print(f'키워드 분석: {result.get("keyword_analysis", {})}')
print()

# 텍스트를 소문자로 변환해서 키워드 체크
text_lower = text.lower()

# Rule Filter 키워드들
crime_kws = ['송금', '계좌', '입금', '출금', '이체', '환불', '환급', '대포통장', '금전', '돈', '현금', '카드번호', '비밀번호', '보안코드', 'OTP', '공인인증서', '금융거래', '검찰', '경찰', '검사', '형사', '수사', '범죄', '피의자', '영장', '체포', '구속', '수배', '조사', '출석', '금감원', '금융감독원', '금융위원회', '한국은행', '예금보험공사', '신용정보원', '모텔', '숙박', '호텔', '독립된 공간', '조용한 곳', '이동', '장소', '위치', '폰 끄지', 'APK', '설치', '다운로드', '링크', 'URL', '접속', '.com', '.net', '.info', 'bit.ly']
legit_kws = ['서비스센터', '고객센터', '상담센터', '콜센터', 'AS', 'A/S', '기사님', '상담사', '담당자', '예약', '예정', '일정', '시간', '공식 홈페이지', '공식 사이트', '공식 앱', '공식 어플', '마이페이지', '카카오톡', '줌', 'Zoom', '화상', '접속번호', '원격 상담', '기본 설정', '기본 기능', '설정 메뉴', '화면 공유', '채용', '면접', '인사팀', '합격', '지원', '응시', '시험', '검사', '역량', '서류', '진료', '상담', '병원', '의사', '환자', '프라이버시']
urgency_kws = ['지금 당장', '즉시', '급히', '바로', '빨리', '안 하면', '하지 않으면', '불이익', '손해', '시간 내', '마감', '기한']

detected_crime = [kw for kw in crime_kws if kw in text_lower]
detected_legit = [kw for kw in legit_kws if kw in text_lower]
detected_urgency = [kw for kw in urgency_kws if kw in text_lower]

print(f'탐지된 범죄 키워드 ({len(detected_crime)}개): {detected_crime}')
print(f'탐지된 정상 키워드 ({len(detected_legit)}개): {detected_legit}')
print(f'탐지된 긴급성 키워드 ({len(detected_urgency)}개): {detected_urgency}')
print()

# 가짜 URL 체크
fake_url_patterns = ['-support.com', '-center.com', '-help.com', '-service.com', '-verify.com', '-security.com', '-update.com', '-login.com', '-bank.net', '-govt.net', '-official.net', 'bit.ly', 'tinyurl', 'short']
has_fake_url = any(pattern in text_lower for pattern in fake_url_patterns)
print(f'가짜 URL 패턴 감지: {has_fake_url}')

if has_fake_url:
    detected_patterns = [p for p in fake_url_patterns if p in text_lower]
    print(f'  → 감지된 패턴: {detected_patterns}')

print()
print('===결론===')
print(f'벤치마크 기대값: ≥70점')
print(f'현재 결과: {result["score"]}점')
print(f'테스트 결과: {"✓ PASS" if result["score"] >= 70 else "✗ FAIL"}')
