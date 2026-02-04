"""
F01 케이스만 디버깅
"""
import sys
import os
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from src.filters.rule_filter import RuleBasedFilter

text = "야, 김철수 씨. 전화 좀 피하지 맙시다? 오늘까지 이자 입금 안 되면 내일 당장 회사 찾아가서 뒤집어 엎는다고 했죠? 당신 와이프한테도 연락할 거야. 법대로 하라며? 그래 법대로 딱지 붙여줄 테니까 당장 입금해."

filter = RuleBasedFilter()

print(f"입력: {text}\n")
print("채권 추심 키워드:", filter.DEBT_COLLECTION_KEYWORDS)
print()

# 키워드 체크
text_lower = text.lower()
matched = [kw for kw in filter.DEBT_COLLECTION_KEYWORDS if kw in text_lower]
print(f"매칭된 키워드: {matched}")
print(f"매칭 개수: {len(matched)}")
print()

# 패턴 감지
is_debt = filter.detect_debt_collection(text)
print(f"채권 추심 감지: {is_debt}")
