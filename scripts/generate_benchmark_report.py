"""
54개 케이스 벤치마크 결과를 상세 HTML 보고서로 생성 (실제 사례 6개 포함)
A: 전통적 피싱 10개 | B: 정상 4개 | C: URL 피싱 10개 | D: 신규 공격 4개
E: 고난도 12개 | F: Hard Negatives 3개 | G: Hard Positives 3개 | H: Contextual 2개
I: 실제 사례 6개 (test.txt)
"""
import sys
import os
import io
import json
import datetime

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from src.llm.gemini_detector import GeminiPhishingDetector
import time

# === 전체 테스트 케이스 ===
test_cases = [
    # Category A: 전통적 보이스피싱 (1-10)
    {"id": "A01", "cat": "A", "name": "노골적 위협", "text": "야, 서울지검인데 너 대포통장 신고 들어왔어. 지금 당장 가까운 모텔로 튀어와. 안 오면 바로 수배 때린다. 폰 끄지 말고 링크 보내는 거 깔아.", "min": 90, "type": "phishing"},
    {"id": "A02", "cat": "A", "name": "어설픈 사칭", "text": "여기는 중앙지방검찰청입니다. 본인 계좌가 범죄에 연루되어 동결 예정입니다. 보안 검사를 위해 모텔 등 조용한 곳으로 이동해서 '팀뷰어' 어플을 설치하십시오.", "min": 85, "type": "phishing"},
    {"id": "A03", "cat": "A", "name": "전형적 시나리오", "text": "김철수 검사입니다. 수사 기밀 유지를 위해 제3자가 없는 독립된 공간이 필요합니다. 주변 소음이 섞이면 녹취가 증거로 채택이 안 됩니다. 근처 숙박업소로 이동하시고, 비대면 조사를 위한 보안 앱을 설치해주세요.", "min": 85, "type": "phishing"},
    {"id": "A04", "cat": "A", "name": "피해자 구제 빙자", "text": "선생님, 지금 선생님이 피의자가 아니라 피해자 입장이신 걸 소명하려는 겁니다. 다만, 녹취 중에 주변 잡음이나 타인의 목소리가 섞이면 증거 효력이 사라져요. 그래서 댁보다는 방음이 확실한 스터디룸이나 비즈니스 호텔을 권장 드리는 겁니다.", "min": 75, "type": "phishing"},
    {"id": "A05", "cat": "A", "name": "기술 지원 위장", "text": "지금 폰이 해킹된 상태라 위치 추적이 되고 있어요. 댁으로 가시면 범인들이 알 수 있습니다. 일단 공공 와이파이가 없는 안전한 장소로 피신하셔야 하고요, 해킹 차단을 위해 한국인터넷진흥원(KISA) 인증 툴을 보내드릴 테니 실행해주세요.", "min": 75, "type": "phishing"},
    {"id": "A06", "cat": "A", "name": "금감원 사칭", "text": "금융감독원 자산보호팀입니다. 현재 자금이 해외로 빠져나가고 있어 지급정지 요청을 해야 하는데, 본인 인증이 계속 실패하네요. 통신 보안이 확실한 곳에서 대기해주시면, 저희가 원격으로 '금융 보안 모듈'을 재설정해 드리겠습니다.", "min": 70, "type": "phishing"},
    {"id": "A07", "cat": "A", "name": "가족 사칭", "text": "아버님, 저 김 대리입니다. 아까 따님이 사고 합의 건으로 급하게 연락 주셨는데, 지금 상대방 보험사 직원이랑 대화 내용을 녹음해야 해요. 주변이 시끄러우면 안 되니까 조용한 방 잡고 계시면, 제가 보내드리는 '보험사 전용 녹취 앱' 켜두세요. 따님 바꿔드릴게요.", "min": 70, "type": "phishing"},
    {"id": "A08", "cat": "A", "name": "면접 위장", "text": "안녕하세요, OO기업 인사팀입니다. 1차 합격 축하드립니다. 2차는 AI 역량 검사로 진행되는데요, 부정행위 방지를 위해 독립된 공간(숙박 시설 등)에서 360도 카메라 세팅이 필요합니다. 보내드리는 '시험 감독 프로그램' 설치 후 응시 부탁드립니다.", "min": 65, "type": "phishing"},
    {"id": "A09", "cat": "A", "name": "가짜 백신", "text": "고객님, OO카드 FDS(이상거래탐지)팀입니다. 지금 고객님 폰에 악성코드가 심어져서 계속 결제 시도가 들어옵니다. 저희가 이걸 막으려면 '백신'을 업데이트해야 하는데, 데이터가 손실될 수 있으니 이동하지 마시고 한자리에서 와이파이 끄고 진행해 주세요.", "min": 65, "type": "phishing"},
    {"id": "A10", "cat": "A", "name": "생체인증 위장", "text": "네, 고객님. 불편 드려 죄송합니다. 최근 딥보이스 범죄가 늘어나서, 본인 확인 절차가 강화되었습니다. 현재 고객님 목소리의 생체 파형(Voice Print)을 등록해야 계좌 잠금이 풀리는데요, 이게 미세한 소음에도 오류가 납니다. 번거로우시겠지만, 지금 계신 카페는 소음 수치가 높아서 진행이 불가능합니다. 근처에 공유 오피스나 조용한 숙소 같은 곳을 잠시 이용해 주실 수 있을까요?", "min": 60, "type": "phishing"},

    # Category B: 정상 케이스 (11-14, 총 4개)
    {"id": "B01", "cat": "B", "name": "[정상] 심리상담", "text": "안녕하세요, OO정신건강의학과입니다. 예약하신 비대면 진료 시간 되셔서 연락드렸습니다. 진료 내용에 민감한 개인 정보가 포함될 수 있으니, 지금 주변에 사람이 없는 조용한 방이나 독립된 공간으로 이동해 주실 수 있나요? 카페나 공공장소시면 진료가 어렵습니다. 준비되시면 카카오톡으로 보내드린 '닥터나우(또는 줌)' 링크 눌러서 화상 진료실로 입장해 주세요.", "max": 30, "type": "legitimate"},
    {"id": "B02", "cat": "B", "name": "[정상] 원격지원", "text": "고객님, 말씀하신 와이파이 끊김 현상은 설정 충돌 문제로 보입니다. 제가 고객님 휴대폰 화면을 보면서 설정을 좀 잡아드려야 할 것 같은데요. 휴대폰 기본 설정 메뉴에 보시면 '원격 상담' 기능이 있습니다. 그거 누르시고 화면에 뜨는 6자리 접속 번호를 저한테 불러주시겠어요? 연결되면 제가 화면을 제어하면서 해결해 드리겠습니다.", "max": 30, "type": "legitimate"},
    {"id": "B03", "cat": "B", "name": "[정상] 채용검사", "text": "안녕하세요, OO그룹 인사팀 채용 담당자입니다. 서류 합격 축하드립니다. 내일부터 진행되는 온라인 AI 역량 검사 관련해서 안내 전화 드렸습니다. 부정행위 방지를 위해서 반드시 혼자 계신 공간에서 응시하셔야 하고요, 웹캠으로 주변 360도를 비춰주셔야 합니다. 시험 프로그램은 저희 채용 홈페이지 '마이페이지'에서 다운로드 가능하시니까 미리 설치하고 테스트 부탁드립니다.", "max": 30, "type": "legitimate"},
    {"id": "B04", "cat": "B", "name": "[정상] 부동산 잔금", "text": "아, 선생님! 저 황금부동산입니다. 지금 집주인분 오셨는데, 오늘 잔금 2억 5천 바로 넣으셔야 키 불출이 돼요. 은행 마감 시간 다 되어가서 서두르셔야겠는데요? 아, 네네 지금 바로 보낼게요. 계좌번호가 계약서에 있는 거 맞죠? 네, 그 국민은행 계좌 맞고요. 그리고 법무사님이 지금 신분증 사본이 흐릿하다고 하셔서요. 죄송한데 신분증 앞면만 사진 찍어서 문자로 다시 좀 보내주시겠어요? 지금 바로요. 아, 그래요? 알겠습니다. 지금 이체하고 바로 찍어서 보낼게요. 근데 이체 한도가 걸릴까 봐 걱정이네요. 일단 1억 먼저 보내시고 나머지는 나눠서 보내셔도 돼요. 입금 확인되면 바로 등기 칠게요.", "max": 30, "type": "legitimate"},

    # Category C: URL 기반 피싱 (15-24, 총 10개)
    {"id": "C01", "cat": "C", "name": "대법원 위장", "text": "본인 사건이 맞는지 직접 확인해보세요. 인터넷 주소창에 scourt-law.com 입력하시면 대법원 형사 사법 포털 나옵니다. 거기서 '사건 조회' 누르시고 성함 입력해 보세요. 판결문 자세히 보시려면 보안 뷰어(Viewer) 설치하라고 뜨죠? 그거 설치하세요.", "min": 70, "type": "phishing"},
    {"id": "C02", "cat": "C", "name": "검찰청 위장", "text": "바쁘시니까 서울중앙지검 홈페이지(spo-invest.net) 접속하셔서 '비대면 조사실' 배너 클릭하세요. 공인인증서 대신 '수사기관용 본인확인 앱'으로 로그인하셔야 합니다.", "min": 75, "type": "phishing"},
    {"id": "C03", "cat": "C", "name": "금감원 동결", "text": "지금 계좌가 1시간 뒤에 동결됩니다. 금융감독원 민원 포털(fss-secure.co.kr) 들어가셔서 '불법 계좌 해제 신청' 누르세요. 거기서 하라는 대로 보안 프로그램 업데이트하셔야 동결 막습니다.", "min": 75, "type": "phishing"},
    {"id": "C04", "cat": "C", "name": "국세청 환급", "text": "고객님, 국세청입니다. 2024년도 미환급 세액 320만 원이 조회되시는데 신청이 안 되어 있어서요. 모바일 홈택스 주소 보내드릴게요(hometax-refund.info). 여기 접속해서 '환급 신청서' 다운받아 작성해서 다시 올리세요.", "min": 70, "type": "phishing"},
    {"id": "C05", "cat": "C", "name": "건강검진 위장", "text": "건강검진센터입니다. 이번 검사 결과에서 중대한 이상 소견이 발견되어 정밀 검사가 필요합니다. 자세한 수치는 의료 포털(health-check.kr)에서 결과지 조회해 보세요. 결과지 확인 버튼 누르면 의료 정보 암호화 모듈 설치 필요 팝업 뜰 겁니다.", "min": 65, "type": "phishing"},
    {"id": "C06", "cat": "C", "name": "장학금 위장", "text": "한국장학재단입니다. 부모님 소득 정보 오류로 장학금 환수 대상이 되셨어요. 이의 신청하시려면 재단 사이트(kosaf-support.com) 가셔서 증빙 서류 제출 앱을 까셔야 합니다.", "min": 70, "type": "phishing"},
    {"id": "C07", "cat": "C", "name": "대환대출 위장", "text": "정부 지원 '햇살론' 대상자로 선정되셨습니다. 기존 고금리 대출을 3%대로 대환해 드립니다. KB국민은행 특판 사이트(kb-loancenter.net)에서 한도 조회하고 신청 앱 설치하세요.", "min": 65, "type": "phishing"},
    {"id": "C08", "cat": "C", "name": "택배 스미싱", "text": "[CJ대한통운] 운송장 번호 450-*** 주소지 불명으로 반송 대기 중. 실시간 주소지 수정: cj-logistics-help.com 본인 확인을 위해 휴대폰 번호를 입력하고 인증 앱을 설치하세요.", "min": 60, "type": "phishing"},
    {"id": "C09", "cat": "C", "name": "코인 거래소", "text": "업비트 보안팀입니다. 미국에서 로그인이 시도되어 출금이 제한됐습니다. 해제하시려면 전용 보안 페이지(upbit-security.org)에서 OTP 재설정 앱을 다운로드하셔야 합니다.", "min": 70, "type": "phishing"},
    {"id": "C10", "cat": "C", "name": "2차 피해", "text": "사이버수사대입니다. 지난번 신고하신 사기 피해금 찾았습니다. 환급 절차 밟으시려면 경찰청 사이버 안전국(cyber-police.me) 접속하셔서 '피해 구제 신청서' 작성하세요.", "min": 70, "type": "phishing"},

    # Category D: 신규 공격 유형 (25-28, 총 4개)
    {"id": "D01", "cat": "D", "name": "로맨스 스캠", "text": "오빠, 나 오늘 이더리움 선물로 20% 먹었어 ㅋㅋ 저번에 말한 그 AI 매매 프로그램 덕분이야. 내가 쓰는 거래소는 아직 한국에 안 알려진 비공개 거래소(Private Exchange)인데, 레버리지를 100배까지 줘. 오빠도 퀀트 관심 많으니까 내가 초대 코드 줄게. 딱 100만 원만 넣어서 테스트해 봐.", "min": 60, "type": "phishing"},
    {"id": "D02", "cat": "D", "name": "딥보이스 납치", "text": "(울먹이는 목소리로) 아빠! 나 사고 쳤어... 횡단보도에서 사람을 쳤는데 합의금 안 주면 당장 구속된대. 핸드폰도 뺏겼어. 옆에 아저씨 바꿔줄게. (공범 등장) 자녀분이 지금 사람을 크게 다치게 했습니다. 경찰 부르기 전에 조용히 합의 보시죠. 지금 당장 3,000만 원 보내시면 없던 일로 합니다.", "min": 70, "type": "phishing"},
    {"id": "D03", "cat": "D", "name": "부고장 스미싱", "text": "[부고] 모친상. 장례식장: 연세세브란스병원. 바쁘시더라도 참석 부탁드립니다. 약도/모바일 부고장 보기: bit.ly/funeral_kr", "min": 50, "type": "phishing"},
    {"id": "D04", "cat": "D", "name": "고수익 알바", "text": "저희는 법무사 사무실인데요, 세금 문제 때문에 법인 통장을 못 써요. 세영 씨 개인 계좌로 돈을 받아서 저희가 알려주는 계좌로 이체만 해주시면 건당 10만 원 드려요. 혹시 지금 면접 보러 오기 힘드시면, 먼저 업무 테스트부터 해볼게요. 지금 입금된 돈 찾아서 근처 코인 ATM기 가서 송금해 보세요.", "min": 60, "type": "phishing"},

    # Category E: 고난도 애매한 케이스 (29-40, 총 12개)
    {"id": "E01", "cat": "E", "name": "[피싱] 쿠팡 환불 원격제어", "text": "안녕하세요, 쿠팡 와우 멤버십 고객센터입니다. 정세영 고객님 맞으시죠? 다름이 아니라 시스템 오류로 지난달 멤버십 비용 4,990원이 중복 결제가 되셔서요. 이거 환불 도와드리려고 연락드렸어요. 지금 전산상에서 고객님 단말기 로그가 꼬여있어서 '본인 확인' 버튼이 비활성화되어 있거든요. 플레이스토어에 '팀뷰어' 검색하시면 '퀵 서포트' 앱이 있거든요? 그거 켜서 숫자만 불러주시면 제가 원격으로 접속해서 환불 버튼만 딱 눌러드릴게요.", "min": 75, "type": "phishing"},
    {"id": "E02", "cat": "E", "name": "[피싱] 카드사 FDS팀", "text": "여보세요, 정세영 고객님 되시죠? 여기 OO카드 소비자보호팀입니다. 다름이 아니라 아까 10분 전에 '티몬'에서 98만 원짜리 가전제품 결제 승인이 올라왔는데, 평소 고객님 사용 패턴이랑 달라서 저희 FDS 시스템에서 일단 '보류' 처리를 해뒀거든요. 이거 고객님이 직접 하신 거 맞으실까요? 본인이 아니시다면 이의 제기 신청을 전산상으로 남겨주셔야 최종 취소가 되세요. 제가 지금 문자 하나 보내드렸어요. 그 링크 누르시면 '명의도용 방지 보안관' 앱이 뜨는데, 그거 설치해서 '아니요' 버튼만 한 번 눌러주시면 저희 쪽에서 바로 사건 종결해드릴게요.", "min": 80, "type": "phishing"},
    {"id": "E03", "cat": "E", "name": "[피싱] 대환대출 선입금", "text": "안녕하세요, 정세영 고객님. 여기는 서민금융진흥원 위탁센터입니다. 고객님 지금 00저축은행에서 1,500만 원 쓰고 계신 거 금리가 14.8% 잡혀 있으신데요. 이번에 정부에서 '안심전환대출' 추경 예산이 편성돼서요. 고객님 성실 상환자라 대상자로 선정되셨거든요. 이거 연 3.2% 고정금리로 대환 처리가 가능하세요. 이게 정부 자금이라 중복 수혜가 안 돼요. 그래서 기존 저축은행 대출금을 오늘 오전까지 전액 상환 처리하셔서 전산상 '0'으로 만드셔야 저희 쪽 자금이 실행되거든요. 은행 방문하실 필요 없이 저희가 알려드리는 가상계좌로 상환금 넣으시면 오후 2시에 3.2%짜리 2천만 원 바로 입금됩니다.", "min": 75, "type": "phishing"},
    {"id": "E04", "cat": "E", "name": "[피싱] 병원 수술비 선납", "text": "보호자분 되시죠? 여기 세브란스병원 응급의료센터입니다. 지금 아드님이 전동 킥보드 사고로 이송되셨는데 의식이 혼미합니다. CT상으로 '경막하 출혈' 소견이 보이고요, 왼쪽 대퇴부 복합 골절이라 지금 당장 응급 수술 들어가야 합니다. 골든타임 놓치면 뇌 손상이 올 수 있어요. 지금 사용해야 하는 지혈제랑 인공관절이 '비급여' 품목이라서요. 원무과 접수 전에 이 약재비 450만 원이 먼저 선납이 되어야 약제실에서 불출이 됩니다. 수술 동의서랑 같이 처리해야 하니까 지금 불러드리는 원무과 법인 계좌로 이체하시고 바로 수술실 앞으로 오세요.", "min": 75, "type": "phishing"},
    {"id": "E05", "cat": "E", "name": "[피싱] 로맨스스캠 초기", "text": "어? 이거 김민준 전무님 번호 아닌가요? 골프 모임에서 뵀던... 아이고, 제가 번호를 잘못 저장했나 보네요. 죄송합니다. 목소리가 너무 점잖으셔서 실례인 줄 모르고... 저는 무역 사업 하는 '이수진'이라고 합니다. 이것도 인연인데 혹시 카톡 친구 해도 될까요? 제가 죄송해서 커피 기프티콘이라도 하나 보내드리고 싶어서요.", "min": 65, "type": "phishing"},
    {"id": "E06", "cat": "E", "name": "[피싱] 헤드헌터 사칭", "text": "안녕하세요, 정세영 님 맞으시죠? 여기는 글로벌 헤드헌팅사 '링크드'의 박 부장입니다. 이번에 구글 코리아 퀀트 팀에서 TO가 났는데, 세영 님 깃허브 보고 너무 인상 깊어서 연락드렸어요. 이게 비공개 채용이라 급해서요. 일단 매칭을 위해 주민등록증 사본이랑, 급여 통장 내역서, 그리고 가족 관계 증명서를 지금 바로 제 개인 메일로 좀 보내주시겠어요? 평판 조회 때문에 동의서 작성도 필요한데, 보내드린 URL 눌러서 본인 인증 한번만 해주세요.", "min": 70, "type": "phishing"},
    {"id": "E07", "cat": "E", "name": "[정상] 보험금 지급", "text": "여보세요, 정세영 고객님? 삼성화재 대물보상 담당자입니다. 아까 접수된 접촉 사고 건 때문에 전화드렸어요. 과실 비율 100:0 확정되셨고요. 미수선 수리비로 현금 처리 받으시는 게 유리하실 것 같아서요. 합의금 120만 원 책정되셨는데, 동의하시면 지금 불러주시는 계좌로 바로 송금해드릴게요. 세금 처리 때문에 주민번호 뒷자리도 알려주셔야 합니다.", "max": 30, "type": "legitimate"},
    {"id": "E08", "cat": "E", "name": "[정상] 월세 독촉", "text": "아니, 정세영 씨! 지금 월세가 두 달이나 밀렸는데 전화도 안 받고 뭐 하는 겁니까? 사정이고 뭐고, 오늘 중으로 입금 안 되면 저도 방법 없어요. 내용증명 보내고 명도 소송 걸어서 짐 다 뺄 거니까 알아서 하세요! 당장 송금해요!", "max": 30, "type": "legitimate"},
    {"id": "E09", "cat": "E", "name": "[정상] 경찰서 가족인계", "text": "여보세요? 정세영 씨 핸드폰 맞습니까? 여기 서대문경찰서 신촌지구대 김철수 경위입니다. 놀라지 마시고 들으세요. 지금 아버님 되시는 정OO 님이 길가에 쓰러져 계신 걸 시민분이 신고하셔서 저희가 보호 조치 중입니다. 외상은 없으신데 술을 좀 드신 것 같아요. 지금 바로 지구대로 오셔서 인계해 가셔야 합니다. 오실 때 가족관계 증명할 수 있는 신분증하고 등본 같은 거 챙겨서 오세요. 신촌역 3번 출구 앞 파출소입니다.", "max": 30, "type": "legitimate"},
    {"id": "E10", "cat": "E", "name": "[정상] 중고거래 의심", "text": "저기요, 보내주신 계좌번호 조회해보니까 더치트(사기 조회)에는 안 뜨는데, 제가 불안해서요. 인증 좀 더 해주실 수 있어요? 요즘 벽돌 보내는 사기꾼들이 많아서 그러죠. 혹시 영상통화로 물건 보여주실 수 있어요? 그리고 주민등록증도 가리고 사진 하나만 보내주세요. 확신이 안 서서요. 참나, 5만 원짜리 파는데 무슨 신분증까지 달라 그래요? 됐고요, 정 의심되시면 번개페이(안전결제)로 하시던가요. 수수료는 그쪽이 부담하시고요.", "max": 30, "type": "legitimate"},
    {"id": "E11", "cat": "E", "name": "[피싱] 가족 사칭 급전", "text": "엄마! 나 지금 큰일 났어. 나 지금 홍대인데 지갑을 잃어버렸어. 집에 갈 차비도 없고 카드도 다 정지시켜서 아무것도 못 해. 어, 폰은 있는데 배터리 3%야. 끊어지면 안 돼. 엄마, 나 지금 친구 계좌로 10만 원만 빨리 보내줘. 내가 집 가서 바로 줄게. 급해 진짜. 어, '박민수'고 카카오뱅크야. 내가 문자로 찍어보낼게. 지금 당장 좀 넣어줘. 나 택시 타야 돼.", "min": 70, "type": "phishing"},
    {"id": "E12", "cat": "E", "name": "[정상] 투자 사기 항의", "text": "야, 너네가 500% 수익 난다며! 지금 마이너스 40%인데 이게 말이 돼? 당장 환불해줘. 안 그러면 금감원에 신고하고 경찰서 가서 고소장 접수할 거야! 회원님, 진정하시고요. 투자 손실은 본인 책임이라고 약관에 동의하셨잖아요. 웃기지 마. 너네 처음에 가입비 500만 원 입금하면 원금 보장해준다며 녹취 다 있어. 당장 내 계좌로 돈 다시 송금해.", "max": 30, "type": "legitimate"},

    # Category F: 엣지 케이스 - Hard Negatives (41-43, 총 3개)
    {"id": "F01", "cat": "F", "name": "[주의] 불법 채권 추심", "text": "야, 김철수 씨. 전화 좀 피하지 맙시다? 오늘까지 이자 입금 안 되면 내일 당장 회사 찾아가서 뒤집어 엎는다고 했죠? 당신 와이프한테도 연락할 거야. 법대로 하라며? 그래 법대로 딱지 붙여줄 테니까 당장 입금해.", "min": 40, "max": 70, "type": "caution"},
    {"id": "F02", "cat": "F", "name": "[경고] CEO Fraud/BEC", "text": "김 대리, 나 지금 미팅 들어왔는데 거래처에서 입금 확인이 안 된다고 난리네? 지금 내가 OTP를 안 가져와서 그런데, 일단 법인 계좌에서 500만 원만 지금 바로 저쪽 대표님 개인 계좌로 쏴줘요. 내가 카톡으로 계좌 남길게. 나 지금 급하니까 결재 나중에 올리고 처리부터 해.", "min": 70, "type": "phishing"},
    {"id": "F03", "cat": "F", "name": "[주의] 중고거래 사기", "text": "아, 안전결제는 정산이 너무 늦어서요. 제가 직거래는 지방이라 힘들고, 그냥 쿨거래 하시면 택포 5만 원에 드릴게요. 제 더치트 조회해보시면 깨끗해요. 지금 바로 입금 가능하세요? 다른 분도 연락 와서요.", "min": 40, "max": 60, "type": "caution"},

    # Category G: 엣지 케이스 - Hard Positives (44-46, 총 3개)
    {"id": "G01", "cat": "G", "name": "[피싱] 돼지도살 빌드업", "text": "어머, 죄송해요. 제가 갤러리 큐레이터 김민정 실장님 번호인 줄 알고... 저장된 번호가 바뀌었나 봐요. 목소리가 되게 차분하시네요? 혹시 그림 좋아하세요? 제가 이번에 코엑스에서 전시회 하는데, 인연도 신기한데 모바일 초대권 하나 보내드려도 될까요?", "min": 60, "type": "phishing"},
    {"id": "G02", "cat": "G", "name": "[피싱] 정부지원금 컨설팅", "text": "대표님, 이번에 중기부에서 소상공인 에너지 바우처 예산이 증액돼서 연락드렸습니다. 대출은 아니시고요, 환급금 조회해보니까 300 정도 나오시는데 신청 기간이 오늘까지라요. 서류 접수는 저희가 대행해드리니까, 사업자 등록증이랑 통장 사본만 팩스로 보내주시겠어요?", "min": 65, "type": "phishing"},
    {"id": "G03", "cat": "G", "name": "[피싱] Web3 에어드랍", "text": "안녕하세요, 재단 운영팀입니다. 지난번 스냅샷 기준으로 거버넌스 토큰 에어드랍 대상자신데, 지금 지갑 연결이 해제되셔서 클레임이 안 되고 계세요. 가스비는 저희가 지원하니까, 보내드리는 공식 브릿지 사이트 접속하셔서 트랜잭션 서명만 한번 해주시면 됩니다.", "min": 70, "type": "phishing"},

    # Category H: 엣지 케이스 - Contextual Ambiguity (47-48, 총 2개)
    {"id": "H01", "cat": "H", "name": "[애매] 자녀 폰 분실", "text": "엄마, 나 민지인데. 나 지금 친구 폰으로 전화하는 거야. 학원 앞에서 폰 떨어뜨렸는데 액정 다 깨져서 터치가 안 돼. 수리 맡겨야 하는데 보험 청구하려면 통신사 인증이 필요하대. 엄마 폰으로 인증 번호 가면 그것만 좀 불러줘. 급해.", "min": 70, "type": "phishing"},
    {"id": "H02", "cat": "H", "name": "[애매] 경품 제세공과금", "text": "축하드립니다! 지난번 마트 경품 행사 1등 당첨되셔서 안마의자 받으시게 됐어요. 근데 이게 5만 원 초과 경품이라 제세공과금 22%는 본인 부담이시거든요. 오늘 중으로 입금해주셔야 발주 들어가는데, 수령 거부하실 건가요?", "min": 50, "max": 70, "type": "phishing"},

    # Category I: 실제 보이스피싱 사례 (test.txt) (49-54, 총 6개)
    {"id": "I01", "cat": "I", "name": "[실제] 수사관 사칭", "text": "정세영씨 맞습니까? 아, 네 맞아요. 네 수고하십니다. 서울 중앙지검 정다혜 수사관입니다. 잠시 통화 괜찮으십니까? 네. 개인정보 유출 사건 관련해서 몇 가지 확인 차 연락을 드린 거구요. 부산 출신인 김수영씨라고 아시는 지인 분은 맞습니까? 저희 측에서 얼마 전에 김수영씨 중심으로 한 금융범죄사기단을 검거한 현장에서 지금 정세영씨 명의로 되어있는 농협은행과 우리은행 통장이 발견이 되셨구요. 본인 명의의 통장이 발견되었다고 해서 본인을 무조건 가해자로 보는 건 아닙니다. 다만 아직까지 피해자라고 입증 가능한 증거가 없기 때문에 현재 지금 피해자 입증 조사를 해주셔야 되시는 부분이고요. 이 부분은 3자 목소리, 잡음 소리 들리면 증거품으로 법원 측에서 채택 자체가 불가능하신데 혹시 메모지랑 볼펜 챙기시고요 잠시만 조용한 공간으로 이동 좀 가능하시겠습니까? 아… 지금 당장은… 조사자 분 측에서 통화가 어렵다라고 했을 경우 저희측에서 소환장 보내드릴 테니깐요. 본청을 방문해서 소환 조사를 받으시면 되십니다. 혹시 언제 방문해야 되나요? 빠르시면 금요일 안쪽으로도 무조건 방문을 해야 되는 부분입니다. 날짜는 서류 상에 기재가 되어있으시고요. 검찰청에서 조사 받는 것 때문에 잠깐 통화를 해야 된다 이렇게 얘기하면 아무래도 직장 내 시선이라는 게 좋지만은 않을 겁니다 잠깐 뭐 친구하고 통화를 하고 온다든지 이 부분은 유도리 있게 대처하시고요, 이거 신속하게 진술만 해주셔야 되는 부분입니다.", "min": 85, "type": "phishing"},
    {"id": "I02", "cat": "I", "name": "[실제] 검찰 사칭", "text": "네 저는 이석규 사무관이고요 제가 피해자 입증 절차를 위해서 담당 검사님께 연결해드릴 거예요 지금. 검사님 연결 되시면 본인 사건 번호랑 성함 말씀하시면 됩니다. 네. 네, 전화연결 됐습니다. 저는 이번 7404 보안 건 3팀 팀장을 맡고 있는 김진아 검사라고 합니다. 네 일단 정세영씨가 조사 받으시면서 , 유의하셔야 될 점들이 두 가지가 있기 때문에 말씀을 좀 드릴 겁니다. 첫번 째로는, 수사 중에 전화가 5분 이상 끊어질 경우 가해자 혐의를 은닉하는 시간으로 판단하고 자동 영장 집행 되실겁니다. 두번째로는, 본 사건은 검거되지 않은 공범들이 있기 때문에 비공개 수사 중입니다. 본 사건에 대해서 제 3자에게 발설 시에는 정세영 씨 혐의와는 무관하게 비밀누설죄와 위계에 의한 공무집행방해죄로 가실 수 있고요, 네네. 현재 공문은 실물로 받아본 게 아니라고 전달을 받았는데요, 어떻게 받아보신 건가요? 그.. 앞전에… 통화하시던 분이… 그 인터넷에 검색하라고 한 숫자 검색하고 제 이름이랑 주민번호를 치니까 이제 사건 조회에 나와 가지고 통화하고 있어요. 조사 방법부터 설명을 드리고 진행을 도와드릴 건데요, 일단 구속 수사와 약식 수사 두 가지가 있습니다. 구속수사는 본인이 할 일이 없어요. 14일에서 최대 20일 동안 서울 구치소에 수감되셔서 조사 받으시면 됩니다. 이어서 약식 조사 설명을 드릴게요, 지금 처럼 유선 상으로 비대면으로 수사를 진행하는 건데 만만하게 생각하시면 안됩니다. 네. 협조가 잘 이루어지지 않고, 제 3자 유포가 우려될 시에는 저의 판단 하에 언제든지 약식 조사 철회하고 구속 수사 전환시킬 겁니다. 네. 어떤 수사로 진행하실 건지 지금 말씀하시면 돼요. 그러면 구조상 직장을 다녀야 돼서 약식으로 해야 될 것 같아요. 예 답변 받았구요, 저희 검찰은 피해자 입증 절차를 대비해서 조사만 할 뿐이고, 정세영 씨 피해자 입증은 실질적으로 금융감독원에서 이루어질 예정입니다. 따라서 금일 금융감독원으로 이동하실건데, 지금 연차나 반차 사용하러 가셔서 나오면 제가 마저 공문서 설명드리고 그 다음에 이동을 할거예요. 아 , 지금 당장 나와야 되나요? 네 맞습니다. 본인이 공문을 열람하신 후부터 사건에 대해서 인지 다 하셨잖아요. 네. 본인 앞으로 집행명령 시간이 발부가 되어있기 때문에 그 시간안에 방문이 안 되시면 본인 체포영장 떨어져요", "min": 90, "type": "phishing"},
    {"id": "I03", "cat": "I", "name": "[실제] 납치 빙자", "text": "세영이 엄마죠? 네네. 네 세영이 바꿔 줄게요. 네. 받아 봐. 엄마. 왜. 빨리와.. 뭐? 이 사람이 때렸어. 어? 누가. 술취한 사람이. 어디? 어딘데 너? 골목에… 너 어디.. 어디 골목인데? 세영아 줘 봐 울지말라고 야. 누구세요? 아 아니, 저희 딸.. 저희딸한테 왜 그러세요. 내가 말하는 거 듣고 너는 말을 하지 마. 네. 뭘 해주면 될까요부터 물어봐. 네, 뭘 해주면 되는데요? 내 계좌에100만원, 100만원, 200만원만 넣어줘. 농협 불러줄게요. 지금 바로 입금하세요. 아니 저희 딸을 어디 데리고. 네 딸을 위한 네 마지막 기회인데. 계좌번호 알려주세요. 그러면 백 만원 지금 이체하세요. 20초 내로 안 보내면 전화 끊겠다. 이체 완료 됐나? 네. 지금 잔액 얼마 남았나? 제가 월급날 마저 보내드릴게요. 제 딸만 무사히 보내주세요. 보내준다고 했잖아 그래서 너는 엄청 고마운 거야. 그래서 조금 전에 돈 보낸거 사진 보내달라고 했잖아. 지금 잔액이 70만원인데 왜 거짓말 했을까? 사람은 거짓말을 하면 안돼. 내가 계좌번호 다른거 불러줄 테니까 여기에 70 넣으세요. 다시 통째로 다 보낼게요. 저희 딸 어딨는데요? 그거 송금하고 나서. 야 전화 끊을까? 아줌마. 지금 남편한테 전화해서 이래서 돈을 보내는 데 신고하지 말자 하고 남편 보고 내 번호로 전화하라 해. 지금 바로.", "min": 95, "type": "phishing"},
    {"id": "I04", "cat": "I", "name": "[실제] 카드 배송", "text": "여보세요? 예 여보세요? 예. 아 예 카드배송 기사인데요. 예. 예. 정세영씨 맞으세요? 네. 아 이거 00카드 배송하려고 하는데 지금 댁에 계실까요? 아 지금 2~3분 내로 들어갈거예요. 아 다섯시 내에 들어갈거예요. 지금은 아니구요. 아니 근데 00에서 무슨 카드요? 000씨 아니세요? 아 맞아요. 제가 뭘 신청했나? 근데 신청 안하셨어요? 네. 신청을 안 하셨는데 카드가 나올 일이 없는데 잠시만요. 카드 우편물을 보면 000씨. 네 맞아요. 58년생 0월 0일 전화번호, 정보가 다 맞다구요? 네. 그럼 제가 지금 배송지점 들어가기 전에. 네. 확인전화 드린 건데 주소.. 자택 주소가. 서울 마포구 도화동.. 아니 서울이 아니고 여기 청주예요. 청주시라구요? 네. 어 이거 그럼 신청하신 것도 아니고, 본사랑 통화를 또 안하셨잖아요. 주소도 틀리고 .. 00카드사에 전화하셔서 취소 접수를 한 번 해주시겠어요? 제가 반송처리 하게. 예 예 알겠습니다. 아 이왕이면 사고예방팀이라고 있거든요. 거기로 찾아서 전화한 번 해보세요. 사고 예방팀? 주소도 틀리고 하니까요. 주소가 왜 서울로 되어있어요? 그거는 제가 저 배송기사라.. 잠시만요. 이 우편물에 보면 00카드 사고 예방팀 전화번호 있는데 불러드릴게요. 예 불러주세요. 예 1800-0000이요. 이게 재발급인지 이게 뭔지 주소도 틀리다고 한 번 얘기를 해보시고. 예. 그럼 저는 전화가 오면 반송 처리하든가 아니면 이거 주소 변경하면 그거 해드리겠습니다. 네 알겠습니다. 예", "min": 75, "type": "phishing"},
    {"id": "I05", "cat": "I", "name": "[실제] 대출 빙자", "text": "고객님 지금 휴대폰에 은행 어플 이용하는 거 있으시죠? 네. 네 그 은행어플 안에 고객님 금융인증서나 공동인증서 있으시잖아요. 네. 요즘 워낙에 인증서 해킹을 통한 스미싱, 보이스피싱 범죄가 빈번하게 일어나서, 지금 현재 저희 쪽 보안 프로그램 작동하게 되면서 고객님 인증서 보호를 위해 은행 어플 같은게 잠시 차단이 될 거예요. 차단이 되셨다고 해서 고객님께서 다시 설치하셔서 사용하는게 아니고요, 전자서명 하시면 전산 복구처리 되시기 때문에 불편하시더라도 서명하기 전까지만 은행권 어플 사용은 안 되실거구요. 서명하시고 나서는 은행권 어플 전산 풀어드릴 거고 고객님 대출금 들어온 거 확인해보셔야 되잖아요. 그 다음에 은행권 어플 사용은 가능하세요. 그러시고 지금 신청서 작성해주신거 결제부로 이관처리 도와드릴거고, 한 시간 안쪽으로 저희 대표번호로 연락 들어가실 거예요. 최종 승인전화 들어가시는 건데 고객님께서 대출 신청한 게 맞는지, 뭐 결제일은 며칠로 지정을 할 건지 등등 여쭤보실건데 그 때 말씀만 잘 해주시면 되고요. 네 알겠습니다. 아 그리고 한 가지만 말씀드리고 싶은데요. 제가 지금 전화상으로 하는 거기 때문에. 네 맞아요. 제가 지금 제 정보를 전부 다 드렸잖아요. 네. 그래서 저 사실 보이스 피싱이 될 까봐 걱정도 되거든요. 지금 대출받아서 대출금을 받지도 않았고. 그래서 지금 0000이 저축은행에서 지금 지수님 이지수? 지금 직함이? 대리예요. 대리님 이거 제가 확인한번 해볼거예요. 지금 여기 0000 저축은행으로. 네 가능하십니다. 저도 걱정이 되기 때문에 그렇다고 지금. 네. 어차피 지금 제가 정보를 다 드렸기 떄문에. 지금 조금 늦은 감이 없진 않지만 그래도 좀 확인한 번 해보고 싶어서요. 어 네 확인 한 번 해보세요 고객님. 그리고 제게 문자 한번 남겨주세요. 네 알겠습니다", "min": 70, "type": "phishing"},
    {"id": "I06", "cat": "I", "name": "[실제] 성매매 협박", "text": "피해보실 만한 일이 좀 생겨서 연락드리게되었습니다. 피해요? 네좀 간단하게 좀 말씀드릴게요 정세영씨. 네. 그 때 당시에 저희가 장사가 너무 안 돼서. 밑에 있는 실장들 시켜서 방마다 카메라를 설치해두고. 네. 영상을 좀 촬영했고요. 그 영상을 정리하던 중에. 정세영씨 영상이 나오게 되어서 지금 연락 한 통 드리게 된 거고. 저희가 흥신소를 같이 운영하다 보니까 정세영씨 뭐 00년 00월 00생인것까지 해서 본인 가족, 지인들 연락처를 한 40개 정도 확보한 상태에서 이렇게 연락을 드리게 되었고요. 정세영 씨 지금 사태파악이 잘 안되시는 것 같은데, 내가 지금부터 사태파악이 되게끔 단톡방 하나 만들어서 가족, 지인들 한 스무 명 초대해 놓고 본인 영상 올려서 지저분하게 얘기할까요? 아니면 나랑 좋게 한 번 얘기해보실래요? 뭐 일단 확인부터 좀 해볼게요. 장난 같아요? 장난 아니죠. 지금 단톡방 하나 만들 테니까 거기서 확인하시고. 네. 신고자 전화 끊음", "min": 85, "type": "phishing"},
]

def main():
    print("\n" + "="*100)
    print("🔬 Gemini Detector + Rule Filter 벤치마크 - 상세 결과 수집")
    print("="*100 + "\n")

    detector = GeminiPhishingDetector()

    if not detector.is_available():
        print("❌ Gemini API를 사용할 수 없습니다.")
        return

    print("✅ Gemini Phishing Detector 초기화 완료\n")

    all_results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"[{i}/{len(test_cases)}] {test_case['id']}: {test_case['name']} 테스트 중...")

        try:
            result = detector.analyze(test_case["text"], enable_filter=True)

            all_results.append({
                "id": test_case["id"],
                "category": test_case["cat"],
                "name": test_case["name"],
                "type": test_case["type"],
                "input_text": test_case["text"],
                "expected_min": test_case.get("min", 0),
                "expected_max": test_case.get("max", 100),
                "llm_score": result.get("llm_score", 0),
                "final_score": result.get("score", 0),
                "is_phishing": result.get("is_phishing", False),
                "risk_level": result.get("risk_level", ""),
                "reasoning": result.get("reasoning", ""),
                "filter_applied": result.get("filter_applied", False),
                "keyword_analysis": result.get("keyword_analysis", {}),
                "detected_techniques": result.get("detected_techniques", [])
            })

            print(f"  ✅ LLM: {result.get('llm_score', 0)} → 최종: {result.get('score', 0)}")
        except Exception as e:
            print(f"  ❌ 에러: {e}")
            all_results.append({
                "id": test_case["id"],
                "category": test_case["cat"],
                "name": test_case["name"],
                "type": test_case["type"],
                "input_text": test_case["text"],
                "expected_min": test_case.get("min", 0),
                "expected_max": test_case.get("max", 100),
                "llm_score": 0,
                "final_score": 0,
                "is_phishing": False,
                "risk_level": "오류",
                "reasoning": f"Error: {e}",
                "filter_applied": False,
                "keyword_analysis": {},
                "detected_techniques": []
            })

        time.sleep(0.5)  # Reduced delay for faster execution

    # JSON 파일로 저장
    output_json = "benchmark_results_detailed.json"
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump({
            "test_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_cases": len(all_results),
            "results": all_results
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 상세 결과가 {output_json}에 저장되었습니다.")

    # 통계 출력
    total = len(all_results)
    correct = sum(1 for r in all_results if (
        (r["type"] == "legitimate" and r["final_score"] <= r.get("expected_max", 100)) or
        (r["type"] == "phishing" and r["final_score"] >= r.get("expected_min", 0)) or
        (r["type"] == "caution" and r.get("expected_min", 0) <= r["final_score"] <= r.get("expected_max", 100))
    ))
    accuracy = (correct / total * 100) if total > 0 else 0

    print(f"\n📊 최종 통계:")
    print(f"  - 전체 케이스: {total}개")
    print(f"  - 정답 케이스: {correct}개")
    print(f"  - 오답 케이스: {total - correct}개")
    print(f"  - 정확도: {accuracy:.1f}%")

    # 오답 케이스 출력
    wrong_cases = [r for r in all_results if not (
        (r["type"] == "legitimate" and r["final_score"] <= r.get("expected_max", 100)) or
        (r["type"] == "phishing" and r["final_score"] >= r.get("expected_min", 0)) or
        (r["type"] == "caution" and r.get("expected_min", 0) <= r["final_score"] <= r.get("expected_max", 100))
    )]

    if wrong_cases:
        print(f"\n❌ 오답 케이스 {len(wrong_cases)}개:")
        for r in wrong_cases:
            if r['type'] == 'caution':
                expected_range = f"{r.get('expected_min', 0)}-{r.get('expected_max', 100)}"
            elif r['type'] == 'phishing':
                expected_range = f"≥{r.get('expected_min', 0)}"
            else:  # legitimate
                expected_range = f"≤{r.get('expected_max', 100)}"
            print(f"  [{r['id']}] {r['name']} - 예상: {expected_range}, 실제: {r['final_score']} (타입: {r['type'].upper()})")

    # # HTML 보고서 생성 (주석 처리)
    # print("\n이제 HTML 보고서를 생성합니다...\n")
    # generate_html_report(all_results)

def generate_html_report(results):
    """HTML 보고서 생성"""

    # 카테고리별 분류
    categories = {
        "A": {"name": "전통적 보이스피싱", "results": []},
        "B": {"name": "정상 케이스", "results": []},
        "C": {"name": "URL 기반 피싱", "results": []},
        "D": {"name": "신규 공격 유형", "results": []},
        "E": {"name": "고난도 애매한 케이스", "results": []},
        "F": {"name": "엣지 케이스 - Hard Negatives (정상을 피싱으로 오판 방지)", "results": []},
        "G": {"name": "엣지 케이스 - Hard Positives (피싱을 정상으로 오판 방지)", "results": []},
        "H": {"name": "엣지 케이스 - Contextual Ambiguity (맥락 모호)", "results": []},
        "I": {"name": "실제 보이스피싱 사례 (test.txt 녹취록)", "results": []}
    }

    for r in results:
        categories[r["category"]]["results"].append(r)

    # 통계 계산
    total = len(results)
    correct = sum(1 for r in results if (
        (r["type"] == "legitimate" and r["final_score"] <= r["expected_max"]) or
        (r["type"] == "phishing" and r["final_score"] >= r["expected_min"]) or
        (r["type"] == "caution" and r["expected_min"] <= r["final_score"] <= r["expected_max"])
    ))
    accuracy = (correct / total * 100) if total > 0 else 0

    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>보이스피싱 탐지 벤치마크 결과</title>
    <style>
        body {{
            font-family: 'Malgun Gothic', sans-serif;
            margin: 20px;
            background: #f5f5f5;
            font-size: 12px;
        }}

        .container {{
            max-width: 100%;
            margin: 0 auto;
            background: white;
            padding: 20px;
        }}

        h1 {{
            font-size: 1.5em;
            margin-bottom: 5px;
        }}

        .summary {{
            background: #f8f9fa;
            padding: 10px;
            margin: 10px 0;
            border-left: 3px solid #333;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}

        th {{
            background: #333;
            color: white;
            padding: 6px;
            text-align: left;
            font-weight: normal;
            font-size: 11px;
        }}

        td {{
            padding: 6px;
            border-bottom: 1px solid #ddd;
            vertical-align: top;
        }}

        tr:hover {{
            background: #f8f9fa;
        }}

        .pass {{
            color: #28a745;
            font-weight: bold;
        }}

        .fail {{
            color: #dc3545;
            font-weight: bold;
        }}

        .phishing {{
            color: #dc3545;
        }}

        .legitimate {{
            color: #28a745;
        }}

        .caution {{
            color: #ffc107;
        }}

        .text-content {{
            font-size: 11px;
            line-height: 1.4;
            max-width: 400px;
        }}

        .input-section {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
        }}

        .section-title {{
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}

        .input-text {{
            color: #333;
            line-height: 1.8;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
        }}

        .analysis-section {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 15px;
        }}

        .score-display {{
            display: flex;
            gap: 20px;
            margin: 15px 0;
            flex-wrap: wrap;
        }}

        .score-box {{
            background: #f8f9fa;
            padding: 15px 25px;
            border-radius: 10px;
            text-align: center;
            flex: 1;
            min-width: 120px;
        }}

        .score-box .score {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}

        .score-box .score.high {{
            color: #dc3545;
        }}

        .score-box .score.low {{
            color: #28a745;
        }}

        .score-box .label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}

        .reasoning {{
            color: #555;
            line-height: 1.8;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }}

        .filter-badge {{
            background: #fff3cd;
            color: #856404;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            margin-left: 10px;
        }}

        .keywords {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }}

        .keyword {{
            background: #667eea;
            color: white;
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.85em;
        }}

        .footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 30px;
            margin-top: 40px;
        }}

        @media print {{
            body {{
                background: white;
                padding: 0;
            }}

            .container {{
                box-shadow: none;
            }}

            .test-case {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔬 Gemini 보이스피싱 탐지 벤치마크 보고서</h1>
            <div class="subtitle">Gemini 2.5 Flash + Rule Filter 통합 시스템</div>
            <div class="subtitle" style="margin-top: 10px; font-size: 1em;">테스트 일시: {datetime.datetime.now().strftime("%Y년 %m월 %d일 %H:%M:%S")}</div>
        </div>

        <div class="summary">
            <div class="stat-card">
                <div class="number">{total}</div>
                <div class="label">전체 테스트 케이스</div>
            </div>
            <div class="stat-card">
                <div class="number">{correct}</div>
                <div class="label">정답 케이스</div>
            </div>
            <div class="stat-card">
                <div class="number">{accuracy:.1f}%</div>
                <div class="label">정확도</div>
            </div>
            <div class="stat-card">
                <div class="number">{sum(1 for r in results if r['filter_applied'])}</div>
                <div class="label">필터 적용 케이스</div>
            </div>
        </div>

        <div class="content">
"""

    # 카테고리별 결과
    for cat_id in ["A", "B", "C", "D", "E", "F", "G", "H", "I"]:
        cat_data = categories[cat_id]
        cat_results = cat_data["results"]

        if not cat_results:
            continue

        cat_correct = sum(1 for r in cat_results if (
            (r["type"] == "legitimate" and r["final_score"] <= r["expected_max"]) or
            (r["type"] == "phishing" and r["final_score"] >= r["expected_min"])
        ))
        cat_accuracy = (cat_correct / len(cat_results) * 100) if cat_results else 0

        html += f"""
            <div class="category">
                <div class="category-header">
                    <div class="category-title">[{cat_id}] {cat_data['name']}</div>
                    <div class="category-stats">정답률: {cat_accuracy:.1f}% ({cat_correct}/{len(cat_results)})</div>
                </div>
"""

        for r in cat_results:
            is_correct = (
                (r["type"] == "legitimate" and r["final_score"] <= r["expected_max"]) or
                (r["type"] == "phishing" and r["final_score"] >= r["expected_min"]) or
                (r["type"] == "caution" and r["expected_min"] <= r["final_score"] <= r["expected_max"])
            )

            case_class = "phishing" if r["type"] == "phishing" else ("caution" if r["type"] == "caution" else "legitimate")
            badge_class = "pass" if is_correct else "fail"
            badge_text = "✅ 정답" if is_correct else "❌ 오답"

            filter_badge = f'<span class="filter-badge">🔧 필터 적용</span>' if r["filter_applied"] else ''

            if r['type'] == 'caution':
                expected_range = f"{r['expected_min']}-{r['expected_max']}"
            elif r['type'] == 'phishing':
                expected_range = f"{r['expected_min']}-{r['expected_max']}"
            else:
                expected_range = f"0-{r['expected_max']}"

            llm_score_class = "high" if r["llm_score"] >= 70 else "low"
            final_score_class = "high" if r["final_score"] >= 70 else "low"

            keywords_html = ""
            if r["detected_techniques"]:
                keywords_html = '<div class="keywords">' + "".join(
                    f'<span class="keyword">{kw}</span>' for kw in r["detected_techniques"][:10]
                ) + '</div>'

            html += f"""
                <div class="test-case {case_class}">
                    <div class="case-header">
                        <span class="case-id">[{r['id']}]</span>
                        <span class="case-name">{r['name']}</span>
                        <span class="badge {r['type']}">{r['type'].upper()}</span>
                        <span class="badge {badge_class}">{badge_text}</span>
                        {filter_badge}
                    </div>

                    <div class="input-section">
                        <div class="section-title">📝 입력 문장 전문</div>
                        <div class="input-text">{r['input_text']}</div>
                    </div>

                    <div class="analysis-section">
                        <div class="section-title">🤖 Gemini 분석 결과</div>

                        <div class="score-display">
                            <div class="score-box">
                                <div class="score {llm_score_class}">{r['llm_score']}</div>
                                <div class="label">LLM 점수</div>
                            </div>
                            <div class="score-box">
                                <div class="score {final_score_class}">{r['final_score']}</div>
                                <div class="label">최종 점수</div>
                            </div>
                            <div class="score-box">
                                <div class="score" style="font-size: 1.2em; color: #666;">{expected_range}</div>
                                <div class="label">기대 범위</div>
                            </div>
                            <div class="score-box">
                                <div class="score" style="font-size: 1.2em; color: #666;">{r['risk_level']}</div>
                                <div class="label">위험도</div>
                            </div>
                        </div>

                        <div class="section-title" style="margin-top: 20px;">💬 판정 이유</div>
                        <div class="reasoning">{r['reasoning']}</div>

                        {keywords_html}
                    </div>
                </div>
"""

        html += """
            </div>
"""

    html += """
        </div>

        <div class="footer">
            <p><strong>Sentinel-Voice 프로젝트</strong></p>
            <p>Gemini 2.5 Flash + Rule-based Filter 통합 시스템</p>
            <p style="margin-top: 10px; opacity: 0.8;">본 보고서는 자동 생성되었습니다.</p>
        </div>
    </div>
</body>
</html>
"""

    output_html = "benchmark_report.html"
    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ HTML 보고서가 {output_html}에 저장되었습니다.")
    return output_html

if __name__ == "__main__":
    main()
